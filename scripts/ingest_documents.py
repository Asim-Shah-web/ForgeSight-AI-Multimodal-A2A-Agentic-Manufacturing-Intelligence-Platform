"""
Standalone CLI script: ingest every synthetic SOP in data/documents/synthetic/
into the technical_documents / document_chunks tables.

Usage:
    python scripts/ingest_documents.py
"""

from __future__ import annotations

import asyncio
import glob

from forgesight.config.database import create_db_and_tables, session_scope
from forgesight.config.logging import get_logger
from forgesight.rag.ingestion import ingest_document

logger = get_logger(__name__)

SYNTHETIC_DOCS_GLOB = "data/documents/synthetic/*.md"


async def main() -> None:
    await create_db_and_tables()

    file_paths = sorted(glob.glob(SYNTHETIC_DOCS_GLOB))
    if not file_paths:
        logger.warning("no_documents_found", extra={"glob": SYNTHETIC_DOCS_GLOB})
        return

    documents_ingested = 0
    async with session_scope() as session:
        for file_path in file_paths:
            await ingest_document(session, file_path)
            documents_ingested += 1

    logger.info(
        "ingest_documents_complete",
        extra={"documents_ingested": documents_ingested, "files": file_paths},
    )


if __name__ == "__main__":
    asyncio.run(main())