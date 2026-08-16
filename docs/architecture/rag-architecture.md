# RAG Architecture

## Workflow
1. Ingestion: PDF/Markdown document parsing and semantic chunking.
2. Embedding: Vector generation stored in PostgreSQL (pgvector).
3. Retrieval & Reranking: Dense retrieval + hybrid BM25 search with cross-encoder reranking.
