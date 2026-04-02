# Execution Queue

- [ ] **Task 1:** Execute `update_adk_docs.sh` and read `llms-full.txt`.
- [ ] **Task 2:** Initialize `pyproject.toml` with `google-cloud-aiplatform`, `asyncpg`, `fastapi`, `uvicorn`, `pydantic`, and `pypdf==5.4.0`.
- [ ] **Task 3:** Implement `src/data/alloydb_pool.py` and execute the schema initialization script against the dev database.
- [ ] **Task 4:** Implement `src/core/vertex_init.py` and `src/mcp/realtime_search.py`. Write corresponding integration tests.
- [ ] **Task 5:** Implement the three Specialist Agents (`src/agents/specialist_*.py`) inheriting from the Google ADK base class.
- [ ] **Task 6:** Implement `src/agents/arbitrator.py`. Ensure vector similarity search logic correctly filters `NEGATIVE` intent from the AlloyDB connection.
- [ ] **Task 7:** Implement `src/api/server.py` and link the Arbitrator execution to the FastAPI router.
- [ ] **Task 8:** Generate `Dockerfile` targeting python:3.11-slim with required system dependencies for `pgvector` compatibility.