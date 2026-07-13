"""Loads and chunks the project's knowledge base for retrieval.

Canonical corpus loader -- benchmark/corpus.py re-exports from here rather
than duplicating this logic, so the benchmark harness is always testing the
same chunking the production retrieval router actually uses.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "data" / "fixtures" / "benchmark_corpus"

_FACT_TAG_RE = re.compile(r"\[FACT[^\]]*\]")
_HEADER_RE = re.compile(r"^#{1,3}\s+(.*)$")


@dataclass(frozen=True)
class Chunk:
    """A retrieval unit: one paragraph of a corpus document, with its nearest
    heading prepended for context. The [FACT ...] annotation is stripped here
    -- retrieval systems see prose only, never the machine-readable tag."""

    chunk_id: str
    source_doc: str
    heading: str
    text: str


def _strip_fact_tags(paragraph: str) -> str:
    return _FACT_TAG_RE.sub("", paragraph).strip()


def _chunk_markdown(path_name: str, content: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    heading = ""
    para_lines: list[str] = []
    idx = 0

    def flush() -> None:
        nonlocal idx
        text = _strip_fact_tags(" ".join(para_lines))
        if text:
            chunks.append(
                Chunk(
                    chunk_id=f"{path_name}#{idx}",
                    source_doc=path_name,
                    heading=heading,
                    text=f"{heading}. {text}" if heading else text,
                )
            )
            idx += 1
        para_lines.clear()

    for line in content.splitlines():
        stripped = line.strip()
        header_match = _HEADER_RE.match(stripped)
        if header_match:
            flush()
            heading = header_match.group(1)
            continue
        if not stripped:
            flush()
            continue
        para_lines.append(stripped)
    flush()
    return chunks


def _corpus_doc_paths() -> list[Path]:
    """README.md is a provenance note, not searchable content -- excluded
    from both retrieval and fact extraction."""
    return sorted(p for p in CORPUS_DIR.glob("*.md") if p.name != "README.md")


@lru_cache(maxsize=1)
def load_corpus_chunks() -> tuple[Chunk, ...]:
    """Loads every markdown document in the corpus and splits it into
    paragraph-level retrieval chunks. See
    data/fixtures/benchmark_corpus/README.md for what this corpus is and how
    it was authored."""
    chunks: list[Chunk] = []
    for md_path in _corpus_doc_paths():
        content = md_path.read_text(encoding="utf-8")
        chunks.extend(_chunk_markdown(md_path.name, content))
    return tuple(chunks)


@lru_cache(maxsize=1)
def load_corpus_raw_text() -> str:
    """Full concatenated corpus text, [FACT ...] tags included -- used by
    benchmark/systems/ours_extractor.py, never by retrieval."""
    parts = [md_path.read_text(encoding="utf-8") for md_path in _corpus_doc_paths()]
    return "\n\n".join(parts)
