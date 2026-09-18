"""Narrow Phase 1 ingestion adapter for grounded JSON Lines records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TextIO

from .model import Record
from .store import Store


def ingest_jsonl(stream: TextIO, store: Store) -> int:
    """Validate and persist grounded records from a JSON Lines stream."""

    count = 0
    for line_number, line in enumerate(stream, start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            record = Record.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"invalid grounded record on line {line_number}: {exc}"
            ) from exc

        store.put_record(record)
        count += 1

    return count


def ingest_jsonl_file(path: str | Path, store: Store) -> int:
    """Ingest a UTF-8 JSON Lines file into a grounded knowledge store."""

    with Path(path).open("r", encoding="utf-8") as stream:
        return ingest_jsonl(stream, store)
