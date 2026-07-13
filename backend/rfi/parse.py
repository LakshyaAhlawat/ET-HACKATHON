"""Parses data/fixtures/benchmark_corpus/rfi_log.md into structured
RFIRecord objects. The log's `## RFI-XXXX (date) — Title` / `Question: ...`
/ `Response: ...` format is regular enough for a deterministic parser --
no LLM needed just to split a heading from its two labeled fields."""

import re
from functools import lru_cache
from pathlib import Path

from app.models.rfi import RFIRecord

REPO_ROOT = Path(__file__).resolve().parents[2]
RFI_LOG_PATH = REPO_ROOT / "data" / "fixtures" / "benchmark_corpus" / "rfi_log.md"

_ENTRY_RE = re.compile(
    r"^## (RFI-[\w-]+) \((\d{4}-\d{2}-\d{2})\) — (.+)$", re.MULTILINE
)


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


@lru_cache(maxsize=1)
def load_rfi_log() -> tuple[RFIRecord, ...]:
    content = RFI_LOG_PATH.read_text(encoding="utf-8")
    headers = list(_ENTRY_RE.finditer(content))
    records = []

    for i, match in enumerate(headers):
        rfi_id, date, title = match.group(1), match.group(2), match.group(3)
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        block = content[match.end():block_end]

        question_match = re.search(r"Question:\s*(.+?)(?=\nResponse:|\Z)", block, re.DOTALL)
        response_match = re.search(r"Response:\s*(.+?)\Z", block, re.DOTALL)

        records.append(
            RFIRecord(
                rfi_id=rfi_id,
                date=date,
                title=title,
                question=_clean(question_match.group(1)) if question_match else "",
                response=_clean(response_match.group(1)) if response_match else "",
            )
        )

    return tuple(records)
