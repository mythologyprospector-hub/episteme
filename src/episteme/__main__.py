"""Command-line interface for the read-only public Episteme instrument."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .http_api import serve

from .html import render_discovery_report_html
from .model import ReviewTargetKind
from .public import (
    discovery_lineage,
    discovery_report,
    discovery_trail,
    get_captured_representation,
    list_captured_representations,
    get_captured_content,
    get_record,
    get_discovery_finding,
    list_discovery_findings,
    get_hypothesis,
    list_hypotheses,
    get_model,
    list_models,
    get_prediction,
    list_predictions,
    get_experiment_proposal,
    list_experiment_proposals,
    get_prediction_evaluation,
    list_prediction_evaluations,
    get_knowledge_state_consequence,
    list_knowledge_state_consequences,
    get_review,
    get_relationship,
    list_relationships,
    list_records,
    list_reviews,
    get_workflow_definition,
    list_workflow_definitions,
    get_workflow_execution,
    list_workflow_executions,
    workflow_execution_lineage,
    list_workflow_executions_for_artifact,
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
    parser.add_argument(
        "--capture-root",
        default=None,
        help="Path to the immutable captured-content root.",
    )
    parser.add_argument("--serve", action="store_true", help="Serve the read-only HTTP API.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="HTTP bind port (default: 8000).")
    subparsers = parser.add_subparsers(dest="command")

    captures = subparsers.add_parser("captures", help="List captured external representations.")
    captures.add_argument("--source-id", default=None)
    capture = subparsers.add_parser("capture", help="Inspect one captured external representation.")
    capture.add_argument("capture_id")
    capture_content = subparsers.add_parser(
        "capture-content",
        help="Write one exact captured representation to stdout or a file.",
    )
    capture_content.add_argument("capture_id")
    capture_content.add_argument("--output", metavar="PATH")

    records = subparsers.add_parser("records", help="List grounded records.")
    records.add_argument("--kind", default=None, help="Filter by record kind.")

    record = subparsers.add_parser("record", help="Inspect one grounded record.")
    record.add_argument("record_id")

    reviews = subparsers.add_parser("reviews", help="List reviews.")
    reviews.add_argument("--target-kind", default=None, choices=[kind.value for kind in ReviewTargetKind])
    reviews.add_argument("--target-id", default=None)

    relationship_list = subparsers.add_parser("relationships", help="List grounded relationships.")
    relationship_list.add_argument("--predicate", default=None)

    relationship = subparsers.add_parser("relationship", help="Inspect one grounded relationship.")
    relationship.add_argument("relationship_id")

    workflow_list = subparsers.add_parser("workflows", help="List persisted workflow definitions.")

    workflow = subparsers.add_parser("workflow", help="Inspect one persisted workflow definition.")
    workflow.add_argument("workflow_id")

    execution_list = subparsers.add_parser("executions", help="List persisted workflow executions.")
    execution_list.add_argument("--workflow-id", default=None)

    execution = subparsers.add_parser("execution", help="Inspect one persisted workflow execution.")
    execution.add_argument("execution_id")

    execution_lineage = subparsers.add_parser("execution-lineage", help="Inspect timestamp-independent execution lineage.")
    execution_lineage.add_argument("execution_id")

    artifact_executions = subparsers.add_parser(
        "artifact-executions", help="List persisted workflow executions that reference an artifact."
    )
    artifact_executions.add_argument("artifact_id")

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

    discovery_findings = subparsers.add_parser("discoveries", help="List generated discovery findings.")
    discovery_findings.add_argument("--kind", default=None, help="Filter by discovery finding kind.")
    discovery_finding = subparsers.add_parser("discovery", help="Inspect one generated discovery finding.")
    discovery_finding.add_argument("finding_id")

    hypotheses = subparsers.add_parser("hypotheses", help="List generated hypotheses.")
    hypothesis = subparsers.add_parser("hypothesis", help="Inspect one generated hypothesis.")
    hypothesis.add_argument("artifact_id")

    models = subparsers.add_parser("models", help="List generated models.")
    model = subparsers.add_parser("model", help="Inspect one generated model.")
    model.add_argument("artifact_id")

    predictions = subparsers.add_parser("predictions", help="List generated predictions.")
    prediction = subparsers.add_parser("prediction", help="Inspect one generated prediction.")
    prediction.add_argument("artifact_id")

    experiment_proposals = subparsers.add_parser(
        "experiment-proposals", help="List generated experiment proposals."
    )
    experiment_proposal = subparsers.add_parser(
        "experiment-proposal", help="Inspect one generated experiment proposal."
    )
    experiment_proposal.add_argument("artifact_id")

    prediction_evaluations = subparsers.add_parser(
        "prediction-evaluations", help="List generated prediction evaluations."
    )
    prediction_evaluation = subparsers.add_parser(
        "prediction-evaluation", help="Inspect one generated prediction evaluation."
    )
    prediction_evaluation.add_argument("artifact_id")

    knowledge_state_consequences = subparsers.add_parser(
        "knowledge-state-consequences",
        help="List generated knowledge-state consequences.",
    )
    knowledge_state_consequence = subparsers.add_parser(
        "knowledge-state-consequence",
        help="Inspect one generated knowledge-state consequence.",
    )
    knowledge_state_consequence.add_argument("artifact_id")

    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.serve:
        store_path = Path(args.store) if args.store != ":memory:" else args.store
        serve(
            store_path,
            host=args.host,
            port=args.port,
            capture_root=args.capture_root,
        )
        return 0
    if args.command is None:
        raise SystemExit("a command is required unless --serve is used")
    store_path = Path(args.store) if args.store != ":memory:" else args.store
    with Store(
        store_path,
        read_only=True,
        capture_root=args.capture_root,
    ) as store:
        if args.command == "capture-content":
            content, _media_type = get_captured_content(store, args.capture_id)
            if args.output:
                Path(args.output).write_bytes(content)
                return 0
            sys.stdout.buffer.write(content)
            return 0
        if args.command == "captures":
            result = list_captured_representations(store, source_id=args.source_id)
        elif args.command == "capture":
            result = get_captured_representation(store, args.capture_id)
        elif args.command == "records":
            result = list_records(store, kind=args.kind)
        elif args.command == "reviews":
            target_kind = ReviewTargetKind(args.target_kind) if args.target_kind else None
            result = list_reviews(store, target_kind=target_kind, target_id=args.target_id)
        elif args.command == "review":
            result = get_review(store, args.review_id)
        elif args.command == "relationships":
            result = list_relationships(store, predicate=args.predicate)
        elif args.command == "relationship":
            result = get_relationship(store, args.relationship_id)
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
        elif args.command == "artifact-executions":
            result = list_workflow_executions_for_artifact(store, args.artifact_id)
        elif args.command == "discoveries":
            result = list_discovery_findings(store, kind=args.kind)
        elif args.command == "discovery":
            result = get_discovery_finding(store, args.finding_id)
        elif args.command == "hypotheses":
            result = list_hypotheses(store)
        elif args.command == "hypothesis":
            result = get_hypothesis(store, args.artifact_id)
        elif args.command == "models":
            result = list_models(store)
        elif args.command == "model":
            result = get_model(store, args.artifact_id)
        elif args.command == "predictions":
            result = list_predictions(store)
        elif args.command == "prediction":
            result = get_prediction(store, args.artifact_id)
        elif args.command == "experiment-proposals":
            result = list_experiment_proposals(store)
        elif args.command == "experiment-proposal":
            result = get_experiment_proposal(store, args.artifact_id)
        elif args.command == "prediction-evaluations":
            result = list_prediction_evaluations(store)
        elif args.command == "prediction-evaluation":
            result = get_prediction_evaluation(store, args.artifact_id)
        elif args.command == "knowledge-state-consequences":
            result = list_knowledge_state_consequences(store)
        elif args.command == "knowledge-state-consequence":
            result = get_knowledge_state_consequence(store, args.artifact_id)
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
