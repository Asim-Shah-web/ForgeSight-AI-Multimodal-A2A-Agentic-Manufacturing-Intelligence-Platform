"""
Document chunking module — paragraph/section-level chunking strategy,
selected in Phase 4 Section 3.2 (docs/architecture/rag-architecture.md).

Chunk boundaries follow the Markdown heading structure of ForgeSight's
synthetic SOPs (Purpose, Scope, Referenced Standards, Procedure, Acceptance
Criteria, Related Records, Revision History), splitting an oversized section
further only at paragraph boundaries with a small token overlap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import tiktoken
import yaml

from forgesight.config.settings import settings

_HEADING_PATTERN = re.compile(r"^(#{2,3})\s+(.*)$", re.MULTILINE)
_FRONT_MATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
_NUMBERED_HEADING_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")

_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Approximate token count using a general-purpose tokenizer.

    This is an approximation for chunk-sizing purposes only — it does not
    need to match the embedding model's own tokenizer exactly, only to give
    a consistent, deterministic size signal for the 150-400 token target
    established in Phase 4 Section 3.2.
    """
    return len(_encoding.encode(text))


@dataclass
class SectionBlock:
    section_title: str
    section_number: str
    raw_text: str


@dataclass
class ParsedDocument:
    metadata: dict
    sections: list[SectionBlock]


@dataclass
class ChunkCandidate:
    section_title: str
    section_reference: str
    chunk_index: int
    chunk_text: str
    token_count: int


def parse_front_matter(raw_text: str) -> tuple[dict, str]:
    """Split a Markdown file into (front-matter metadata dict, body text)."""
    match = _FRONT_MATTER_PATTERN.match(raw_text)
    if not match:
        return {}, raw_text

    front_matter_raw, body = match.group(1), match.group(2)
    metadata = yaml.safe_load(front_matter_raw) or {}
    return metadata, body


def parse_markdown_sections(body_text: str) -> list[SectionBlock]:
    """Split a document body into sections at level-2 (##) and level-3 (###)
    Markdown headings. Content before the first heading (e.g. the H1 title
    line) is discarded — it carries no retrievable procedural content."""
    matches = list(_HEADING_PATTERN.finditer(body_text))
    sections: list[SectionBlock] = []

    for i, match in enumerate(matches):
        heading_text = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        raw_text = body_text[start:end].strip()

        number_match = _NUMBERED_HEADING_PATTERN.match(heading_text)
        if number_match:
            section_number, section_title = number_match.group(1), number_match.group(2).strip()
        else:
            section_number, section_title = "", heading_text

        if raw_text:
            sections.append(
                SectionBlock(section_title=section_title, section_number=section_number, raw_text=raw_text)
            )

    return sections


def parse_document(raw_text: str) -> ParsedDocument:
    """Parse a full synthetic SOP file (front matter + heading-delimited body)."""
    metadata, body = parse_front_matter(raw_text)
    sections = parse_markdown_sections(body)
    return ParsedDocument(metadata=metadata, sections=sections)


def _split_into_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs if paragraphs else [text.strip()]


def _section_reference(section: SectionBlock) -> str:
    if section.section_number:
        return f"Section {section.section_number}"
    return section.section_title


def chunk_section(
    section: SectionBlock,
    max_tokens: int | None = None,
    overlap_tokens: int | None = None,
) -> list[ChunkCandidate]:
    """
    Chunk a single section per Phase 4 Section 3.2:
    - If the whole section fits within max_tokens, it is a single chunk.
    - Otherwise, split at paragraph boundaries, carrying `overlap_tokens`
      worth of trailing text from the previous chunk into the next one.
    """
    max_tokens = max_tokens if max_tokens is not None else settings.rag_chunk_max_tokens
    overlap_tokens = overlap_tokens if overlap_tokens is not None else settings.rag_chunk_overlap_tokens

    reference = _section_reference(section)
    full_token_count = count_tokens(section.raw_text)

    if full_token_count <= max_tokens:
        return [
            ChunkCandidate(
                section_title=section.section_title,
                section_reference=reference,
                chunk_index=0,
                chunk_text=section.raw_text,
                token_count=full_token_count,
            )
        ]

    paragraphs = _split_into_paragraphs(section.raw_text)
    chunks: list[ChunkCandidate] = []
    current_paragraphs: list[str] = []
    current_tokens = 0
    chunk_index = 0

    def _flush(carry_overlap: bool) -> list[str]:
        nonlocal chunk_index
        if not current_paragraphs:
            return []
        chunk_text = "\n\n".join(current_paragraphs)
        chunks.append(
            ChunkCandidate(
                section_title=section.section_title,
                section_reference=(
                    reference if chunk_index == 0 else f"{reference} (part {chunk_index + 1})"
                ),
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                token_count=count_tokens(chunk_text),
            )
        )
        chunk_index += 1
        if carry_overlap:
            overlap_paragraphs: list[str] = []
            running = 0
            for paragraph in reversed(current_paragraphs):
                if running >= overlap_tokens:
                    break
                overlap_paragraphs.insert(0, paragraph)
                running += count_tokens(paragraph)
            return overlap_paragraphs
        return []

    for paragraph in paragraphs:
        paragraph_tokens = count_tokens(paragraph)
        if current_tokens + paragraph_tokens > max_tokens and current_paragraphs:
            current_paragraphs = _flush(carry_overlap=True)
            current_tokens = sum(count_tokens(p) for p in current_paragraphs)

        current_paragraphs.append(paragraph)
        current_tokens += paragraph_tokens

    _flush(carry_overlap=False)
    return chunks


def chunk_document(parsed: ParsedDocument) -> list[ChunkCandidate]:
    """Chunk every section of a parsed document, re-indexing chunk_index
    globally across the whole document rather than per-section."""
    all_chunks: list[ChunkCandidate] = []
    global_index = 0
    for section in parsed.sections:
        for chunk in chunk_section(section):
            chunk.chunk_index = global_index
            all_chunks.append(chunk)
            global_index += 1
    return all_chunks