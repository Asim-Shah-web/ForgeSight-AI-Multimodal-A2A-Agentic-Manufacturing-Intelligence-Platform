"""Unit tests for the chunking module, tested against the real synthetic SOPs."""

from __future__ import annotations

from pathlib import Path

import pytest

from forgesight.rag.chunking import (
    SectionBlock,
    chunk_document,
    chunk_section,
    count_tokens,
    parse_document,
)

SYNTHETIC_DOCS_DIR = Path("data/documents/synthetic")


def _load(document_id: str) -> str:
    return (SYNTHETIC_DOCS_DIR / f"{document_id}.md").read_text(encoding="utf-8")


@pytest.mark.skipif(not SYNTHETIC_DOCS_DIR.exists(), reason="synthetic SOP fixtures not present")
def test_parses_sop_qual_042_sections_and_metadata() -> None:
    parsed = parse_document(_load("SOP-QUAL-042"))

    assert parsed.metadata["document_id"] == "SOP-QUAL-042"
    assert parsed.metadata["version"] == "v1.0"

    section_titles = {s.section_title for s in parsed.sections}
    assert any("Acceptance Criteria" in title for title in section_titles)
    assert any("Purpose" in title for title in section_titles)


@pytest.mark.skipif(not SYNTHETIC_DOCS_DIR.exists(), reason="synthetic SOP fixtures not present")
def test_short_section_becomes_single_chunk() -> None:
    parsed = parse_document(_load("SOP-QUAL-042"))
    purpose_section = next(s for s in parsed.sections if "Purpose" in s.section_title)

    chunks = chunk_section(purpose_section, max_tokens=400, overlap_tokens=40)
    assert len(chunks) == 1
    assert chunks[0].token_count == count_tokens(purpose_section.raw_text)


def test_oversized_section_splits_with_overlap() -> None:
    long_text = "\n\n".join(f"Paragraph {i} of a long procedural section. " * 20 for i in range(20))
    section = SectionBlock(section_title="Long Test Section", section_number="9.9", raw_text=long_text)

    chunks = chunk_section(section, max_tokens=100, overlap_tokens=20)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.token_count <= 150  # allow slack for carried overlap content


@pytest.mark.skipif(not SYNTHETIC_DOCS_DIR.exists(), reason="synthetic SOP fixtures not present")
def test_chunk_document_produces_globally_indexed_chunks() -> None:
    parsed = parse_document(_load("SOP-MAINT-017"))
    chunks = chunk_document(parsed)

    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert len(chunks) > 0