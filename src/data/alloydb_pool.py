import os
import asyncpg
from typing import Optional

class AlloyDBPool:
    """
    Manages an asynchronous connection pool to Google Cloud AlloyDB.
    """
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, connection_uri: Optional[str] = None):
        """Initializes the asyncpg connection pool."""
        if connection_uri:
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=connection_uri,
                    min_size=1,
                    max_size=10
                )
                print(f"Successfully initialized AlloyDB pool with DSN.")
                return
            except Exception as e:
                print(f"Failed to initialize AlloyDB pool with DSN: {e}")
                raise

        # Fallback to environment variables
        host = os.environ.get("ALLOYDB_HOST", "127.0.0.1")
        port = os.environ.get("ALLOYDB_PORT", "5432")
        user = os.environ.get("ALLOYDB_USER", "postgres")
        password = os.environ.get("ALLOYDB_PASSWORD", "postgres")
        database = os.environ.get("ALLOYDB_DB", "postgres")
        
        try:
            self.pool = await asyncpg.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                min_size=1,  # Minimum number of connections in the pool
                max_size=10  # Maximum number of connections in the pool
            )
            print("Successfully initialized AlloyDB connection pool.")
        except Exception as e:
            print(f"Failed to initialize AlloyDB pool: {e}")
            raise

    async def close(self):
        """Closes the connection pool gracefully."""
        if self.pool:
            await self.pool.close()
            print("AlloyDB connection pool closed.")
            self.pool = None

    async def execute(self, query: str, *args):
        """Executes a database command (INSERT, UPDATE, DELETE)."""
        if not self.pool:
            raise Exception("Pool is not initialized. Call connect() first.")
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)
            
    async def fetch(self, query: str, *args):
        """Fetches multiple rows from SELECT queries."""
        if not self.pool:
            raise Exception("Pool is not initialized. Call connect() first.")
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)
            
    async def fetchrow(self, query: str, *args):
        """Fetches a single row from SELECT queries."""
        if not self.pool:
            raise Exception("Pool is not initialized. Call connect() first.")
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

# Instantiate a global instance to be used across the application
db = AlloyDBPool()
