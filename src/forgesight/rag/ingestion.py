"""
Document ingestion pipeline — Phase 4 Section 3 (Ingestion & Chunking) and
Section 3.4 (version update handling: retire old chunks, activate new ones).
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.domain.models.knowledge import DocumentChunk, TechnicalDocument
from forgesight.rag.chunking import chunk_document, parse_document
from forgesight.rag.embeddings import embed_batch

logger = get_logger(__name__)


class DocumentIngestionError(Exception):
    """Raised when a document cannot be ingested (missing required metadata, etc.)."""


_REQUIRED_METADATA_FIELDS = (
    "document_id",
    "title",
    "category",
    "version",
    "date",
    "author",
    "approved_by",
    "status",
    "language",
)


def _validate_metadata(metadata: dict, file_path: str) -> None:
    missing = [field for field in _REQUIRED_METADATA_FIELDS if not metadata.get(field)]
    if missing:
        raise DocumentIngestionError(
            f"Document at '{file_path}' is missing required front-matter fields: {missing}. "
            "Per the Phase 4 document governance model, a document without complete "
            "metadata cannot be ingested."
        )


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


async def _retire_prior_chunks(session: AsyncSession, document_id: str) -> int:
    result = await session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.status == "active",
        )
    )
    prior_chunks = result.scalars().all()
    for chunk in prior_chunks:
        chunk.status = "retired"
        session.add(chunk)
    if prior_chunks:
        await session.flush()
    return len(prior_chunks)


async def ingest_document(session: AsyncSession, file_path: str) -> TechnicalDocument:
    """
    Ingest a single Markdown SOP/manual file: parse front matter + sections,
    chunk the body, embed each chunk, and store TechnicalDocument +
    DocumentChunk rows.

    Idempotent: re-ingesting the same document_id at the same version, when
    that version is already active with chunks present, is a no-op.
    """
    path = Path(file_path)
    if not path.exists():
        raise DocumentIngestionError(f"Document file not found: {file_path}")

    raw_text = path.read_text(encoding="utf-8")
    parsed = parse_document(raw_text)
    _validate_metadata(parsed.metadata, file_path)

    document_id = str(parsed.metadata["document_id"])
    version = str(parsed.metadata["version"])

    existing_result = await session.execute(
        select(TechnicalDocument).where(TechnicalDocument.document_id == document_id)
    )
    existing_document = existing_result.scalar_one_or_none()

    if (
        existing_document is not None
        and existing_document.version == version
        and existing_document.status == "active"
    ):
        active_chunks_result = await session.execute(
            select(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.status == "active",
            )
        )
        if active_chunks_result.scalars().first() is not None:
            logger.info(
                "document_ingestion_skipped_already_current",
                extra={"document_id": document_id, "version": version},
            )
            return existing_document

    retired_count = 0
    if existing_document is not None and existing_document.version != version:
        retired_count = await _retire_prior_chunks(session, document_id)
        existing_document.version = version
        existing_document.title = str(parsed.metadata["title"])
        existing_document.category = str(parsed.metadata["category"])
        existing_document.document_date = _parse_date(parsed.metadata["date"])
        existing_document.author = str(parsed.metadata["author"])
        existing_document.approved_by = str(parsed.metadata["approved_by"])
        existing_document.file_path = str(file_path)
        existing_document.status = "active"
        existing_document.language = str(parsed.metadata["language"])
        document = existing_document
        session.add(document)
        await session.flush()
    elif existing_document is None:
        document = TechnicalDocument(
            document_id=document_id,
            title=str(parsed.metadata["title"]),
            category=str(parsed.metadata["category"]),
            version=version,
            document_date=_parse_date(parsed.metadata["date"]),
            author=str(parsed.metadata["author"]),
            approved_by=str(parsed.metadata["approved_by"]),
            file_path=str(file_path),
            status="active",
            language=str(parsed.metadata["language"]),
        )
        session.add(document)
        await session.flush()
        await session.refresh(document)
    else:
        document = existing_document

    chunk_candidates = chunk_document(parsed)
    chunk_texts = [c.chunk_text for c in chunk_candidates]
    embeddings = await embed_batch(chunk_texts)

    for candidate, embedding in zip(chunk_candidates, embeddings):
        session.add(
            DocumentChunk(
                document_id=document_id,
                document_title=document.title,
                document_version=document.version,
                section_title=candidate.section_title,
                section_reference=candidate.section_reference,
                chunk_index=candidate.chunk_index,
                chunk_text=candidate.chunk_text,
                token_count=candidate.token_count,
                embedding=embedding,
                embedding_model=settings.embedding_model_name,
                status="active",
            )
        )
    await session.flush()

    logger.info(
        "document_ingested",
        extra={
            "document_id": document_id,
            "version": version,
            "chunks_created": len(chunk_candidates),
            "chunks_retired": retired_count,
        },
    )
    return document