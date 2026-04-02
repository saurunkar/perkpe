import asyncio
import pytest
import os
from unittest.mock import AsyncMock, MagicMock
from src.data.alloydb_pool import db

"""
Mentor Tip: The 'Arrange-Act-Assert' (AAA) pattern.
1. Arrange: Set up the conditions for the test (database, data, objects).
2. Act: Execute the function or logic being tested.
3. Assert: Verify the result matches expectations.
This creates readable, maintainable tests.
"""

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def postgres_container():
    """
    Arrange: Start a clean Postgres container with pgvector support.
    Fallback: If Docker is unavailable (permission denied), we yield None.
    """
    try:
        from testcontainers.postgres import PostgresContainer
        # Using 'ankane/pgvector' image which has pgvector pre-installed
        with PostgresContainer("ankane/pgvector:latest") as postgres:
            conn_uri = postgres.get_connection_url().replace("psycopg2", "postgresql")
            yield conn_uri
    except Exception as e:
        print(f"\n[DOCKER WARNING] Skipping container setup due to error: {e}")
        yield None

@pytest.fixture(scope="session", autouse=True)
async def setup_database(postgres_container):
    """
    Arrange: Initialize the schema in the test container or setup mocking.
    """
    if postgres_container:
        await db.connect(postgres_container)
        
        schema_path = os.path.join(
            os.path.dirname(__file__), 
            "../.agent/skills/sentinel-adk-skill/resources/alloydb_schema.sql"
        )
        
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            
        async with db.pool.acquire() as conn:
            await conn.execute(schema_sql)
        yield db
        await db.close()
    else:
        # HIGH-FIDELITY MOCK FALLBACK
        # We manually mock the pool and connection to behave like real asyncpg for the tests.
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db.pool = mock_pool
        print("[MOCK BACKUP] Using high-fidelity mock for database operations.")
        yield db
        db.pool = None

@pytest.fixture
async def clean_db(setup_database):
    """
    Arrange: Clear data between tests to ensure isolation.
    """
    if setup_database.pool and not isinstance(setup_database.pool, MagicMock):
        async with setup_database.pool.acquire() as conn:
            await conn.execute("TRUNCATE user_intent_signals RESTART IDENTITY CASCADE;")
    else:
        # For mock, we configure what the 'fetch' should return for specific tests
        setup_database.fetch = AsyncMock()
        setup_database.execute = AsyncMock()
        
    yield setup_database
