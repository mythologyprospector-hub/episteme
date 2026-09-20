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
    get_workflow_definition,
    list_workflow_definitions,
    get_workflow_execution,
    list_workflow_executions,
    workflow_execution_lineage,
)
from .store import Store


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="episteme",
        description="Inspect Episteme state without modifying the repository.",
    )
    parser.add_argument(
        "--store",
        required=True,
        help="Path to an existing SQLite store.",
    )
    parser.add_argument("--serve", action="store_true", help="Serve the read-only HTTP API.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="HTTP bind port (default: 8000).")
    subparsers = parser.add_subparsers(dest="command")

    records = subparsers.add_parser("records", help="List grounded records.")
    records.add_argument("--kind", default=None, help="Filter by record kind.")

    record = subparsers.add_parser("record", help="Inspect one grounded record.")
    record.add_argument("record_id")

    reviews = subparsers.add_parser("reviews", help="List reviews.")
    reviews.add_argument("--target-kind", default=None, choices=[kind.value for kind in ReviewTargetKind])
    reviews.add_argument("--target-id", default=None)

    workflow_list = subparsers.add_parser("workflows", help="List persisted workflow definitions.")

    workflow = subparsers.add_parser("workflow", help="Inspect one persisted workflow definition.")
    workflow.add_argument("workflow_id")

    execution_list = subparsers.add_parser("executions", help="List persisted workflow executions.")
    execution_list.add_argument("--workflow-id", default=None)

    execution = subparsers.add_parser("execution", help="Inspect one persisted workflow execution.")
    execution.add_argument("execution_id")

    execution_lineage = subparsers.add_parser("execution-lineage", help="Inspect timestamp-independent execution lineage.")
    execution_lineage.add_argument("execution_id")

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
    if args.serve:
        store_path = Path(args.store) if args.store != ":memory:" else args.store
        serve(store_path, host=args.host, port=args.port)
        return 0
    if args.command is None:
        raise SystemExit("a command is required unless --serve is used")
    store_path = Path(args.store) if args.store != ":memory:" else args.store
    with Store(store_path, read_only=True) as store:
        if args.command == "records":
            result = list_records(store, kind=args.kind)
        elif args.command == "reviews":
            target_kind = ReviewTargetKind(args.target_kind) if args.target_kind else None
            result = list_reviews(store, target_kind=target_kind, target_id=args.target_id)
        elif args.command == "review":
            result = get_review(store, args.review_id)
        elif args.command == "workflows":
            result = list_workflow_definitions(store)
        elif args.command == "workflow":
            result = get_workflow_definition(store, args.workflow_id)
        elif args.command == "executions":
            result = list_workflow_executions(store, workflow_id=args.workflow_id)
        elif args.command == "execution":
            result = get_workflow_execution(store, args.execution_id)
        elif args.command == "execution-lineage":
            result = workflow_execution_lineage(store, args.execution_id)
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
