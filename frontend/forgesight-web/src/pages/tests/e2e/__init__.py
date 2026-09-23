"""End-to-end tests: full 12-stage investigation workflow against real
running services (Postgres+pgvector, Redis, real MCP subprocesses, real
embedding/reranking/CV inference). Only forgesight.agents.llm_client.call_llm
is mocked, per Phase 13 Mandatory Rule 1."""