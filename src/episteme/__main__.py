"""Command-line interface for the read-only public Episteme instrument."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .public import discovery_lineage, discovery_report, discovery_trail, get_record, list_records
from .store import Store


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m episteme",
        description="Inspect Episteme state without modifying the repository.",
    )
    parser.add_argument(
        "--store",
        default=":memory:",
        help="SQLite store path (default: :memory:)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    records = subparsers.add_parser("records", help="List grounded records.")
    records.add_argument("--kind", default=None, help="Filter by record kind.")

    record = subparsers.add_parser("record", help="Inspect one grounded record.")
    record.add_argument("record_id")

    for name, help_text in (
        ("trail", "Reconstruct a discovery trail."),
        ("lineage", "Return timestamp-independent discovery lineage."),
        ("report", "Return an inspectable discovery report."),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("finding_id")
        command.add_argument(
            "--created-at",
            required=True,
            help="Timestamp to place in the full trail representation.",
        )

    return parser


def main() -> int:
    args = _parser().parse_args()
    store_path = Path(args.store) if args.store != ":memory:" else args.store

    with Store(store_path) as store:
        if args.command == "records":
            result = list_records(store, kind=args.kind)
        elif args.command == "record":
            result = get_record(store, args.record_id)
        elif args.command == "trail":
            result = discovery_trail(store, args.finding_id, args.created_at)
        elif args.command == "lineage":
            result = discovery_lineage(store, args.finding_id, args.created_at)
        else:
            result = discovery_report(store, args.finding_id, args.created_at)

    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
