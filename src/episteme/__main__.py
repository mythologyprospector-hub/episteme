"""Command-line interface for the read-only public Episteme instrument."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .http_api import serve

from .html import render_discovery_report_html
from .model import ReviewTargetKind
from .public import (
    discovery_lineage,
    discovery_report,
    discovery_trail,
    get_record,
    get_review,
    list_records,
    list_reviews,
)
from .store import Store


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="episteme",
        description="Inspect Episteme state without modifying the repository.",
    )
    parser.add_argument(
        "--store",
        default=":memory:",
        help="SQLite store path (default: :memory:)",
    )
    parser.add_argument("--serve", action="store_true", help="Serve the read-only HTTP API.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="HTTP bind port (default: 8000).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    records = subparsers.add_parser("records", help="List grounded records.")
    records.add_argument("--kind", default=None, help="Filter by record kind.")

    record = subparsers.add_parser("record", help="Inspect one grounded record.")
    record.add_argument("record_id")

    reviews = subparsers.add_parser("reviews", help="List reviews.")
    reviews.add_argument("--target-kind", default=None, choices=[kind.value for kind in ReviewTargetKind])
    reviews.add_argument("--target-id", default=None)

    review = subparsers.add_parser("review", help="Inspect one review.")
    review.add_argument("review_id")

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
        if name == "report":
            command.add_argument(
                "--html",
                metavar="PATH",
                help="Write the same report as a self-contained HTML document.",
            )

    return parser


def main() -> int:
    args = _parser().parse_args()
    store_path = Path(args.store) if args.store != ":memory:" else args.store
    if args.serve:
        serve(store_path, host=args.host, port=args.port)
        return 0

    with Store(store_path) as store:
        if args.command == "records":
            result = list_records(store, kind=args.kind)
        elif args.command == "reviews":
            target_kind = ReviewTargetKind(args.target_kind) if args.target_kind else None
            result = list_reviews(store, target_kind=target_kind, target_id=args.target_id)
        elif args.command == "review":
            result = get_review(store, args.review_id)
        elif args.command == "record":
            result = get_record(store, args.record_id)
        elif args.command == "trail":
            result = discovery_trail(store, args.finding_id, args.created_at)
        elif args.command == "lineage":
            result = discovery_lineage(store, args.finding_id, args.created_at)
        else:
            result = discovery_report(store, args.finding_id, args.created_at)
            if args.html:
                Path(args.html).write_text(
                    render_discovery_report_html(result),
                    encoding="utf-8",
                )
                return 0

    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
