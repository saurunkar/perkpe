---
name: sentinel-adk-skill
description: High-level orchestration for the Sentinel Finance AI system.
---


## Description
This skill enforces strict production-grade standards for developing the Sentinel Finance multi-agent system using Google ADK, Vertex AI SDK, and AlloyDB.

## Critical Requirements
1. **Zero Mocking:** Do not generate mock data or stub functions. All database calls must utilize `asyncpg` interfacing with the AlloyDB specification.
2. **Framework Alignment:** You MUST execute `scripts/update_adk_docs.sh` at the start of any task utilizing Google ADK to ensure API parameter compliance. Read `resources/llms-full.txt` before implementing `adk_controller.py`.
3. **PDF Processing:** If parsing bank statements or e-invoices via local pipelines instead of Document AI, you must strictly use `pypdf` version `5.4.0`. Do not use `PyPDF2`.
4. **Vector Operations:** Embeddings must be generated using Vertex AI `textembedding-gecko` and stored in AlloyDB utilizing the `pgvector` extension.
5. **Asynchronous Execution:** All API boundaries and network I/O (MCP calls, AlloyDB queries) must use Python `asyncio`.

## Context Injection
Refer to `resources/alloydb_schema.sql` for the `user_intent_signals` table structure. The Arbitrator agent must explicitly query this schema to filter `NEGATIVE` intents before calculating the Effective Realized Value (ERV).