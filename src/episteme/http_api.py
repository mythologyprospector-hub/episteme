"""Read-only HTTP API for the Episteme public scientific instrument."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from .model import ReviewTargetKind
from .public import (
    discovery_lineage,
    discovery_report,
    discovery_trail,
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
    PublicNotFoundError,
)
from .store import Store
from .trail import DiscoveryNotFoundError

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


class EpistemeHTTPError(Exception):
    """A client-visible HTTP error with a stable status code."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _error(status: int, message: str) -> EpistemeHTTPError:
    return EpistemeHTTPError(status, message)


def _require_query(query: dict[str, list[str]], name: str) -> str:
    values = query.get(name, [])
    if len(values) != 1 or not values[0]:
        raise _error(400, f"query parameter required exactly once: {name}")
    return values[0]


def _single_query(query: dict[str, list[str]], name: str) -> str | None:
    values = query.get(name, [])
    if len(values) > 1:
        raise _error(400, f"query parameter supplied more than once: {name}")
    return values[0] if values else None


def _identifier(value: str, name: str) -> str:
    try:
        UUID(value)
    except ValueError as exc:
        raise _error(400, f"invalid {name}: {value}") from exc
    return value


def _nonempty_identifier(value: str, name: str) -> str:
    if not value:
        raise _error(400, f"invalid {name}: {value}")
    return value


def _timestamp(value: str) -> str:
    from datetime import datetime

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _error(400, f"invalid timestamp: {value}") from exc
    return value


def _review_kind(value: str | None) -> ReviewTargetKind | None:
    if value is None:
        return None
    try:
        return ReviewTargetKind(value)
    except ValueError as exc:
        raise _error(400, f"invalid review target kind: {value}") from exc


def _record_kind(value: str | None) -> str | None:
    if value is None:
        return None
    from .model import RecordKind
    try:
        return RecordKind(value).value
    except ValueError as exc:
        raise _error(400, f"invalid record kind: {value}") from exc


def _reject_unexpected_query(query: dict[str, list[str]], allowed: set[str]) -> None:
    unexpected = set(query) - allowed
    if unexpected:
        raise _error(400, f"unexpected query parameter: {sorted(unexpected)[0]}")


class _Handler(BaseHTTPRequestHandler):
    server: "_EpistemeHTTPServer"

    def do_GET(self) -> None:
        try:
            result, content_type = self.server.read(self.path)
            body = result if isinstance(result, bytes) else _json_bytes(result)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except EpistemeHTTPError as exc:
            self._send_error(exc.status, exc.message)
        except (PublicNotFoundError, DiscoveryNotFoundError) as exc:
            self._send_error(404, str(exc))
        except Exception:
            self._send_error(500, "internal server error")

    def do_POST(self) -> None:
        self._send_error(405, "HTTP mutation methods are not supported")

    def do_PUT(self) -> None:
        self._send_error(405, "HTTP mutation methods are not supported")

    def do_PATCH(self) -> None:
        self._send_error(405, "HTTP mutation methods are not supported")

    def do_DELETE(self) -> None:
        self._send_error(405, "HTTP mutation methods are not supported")

    def _send_error(self, status: int, message: str) -> None:
        body = _json_bytes({"error": {"status": status, "message": message}})
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class _EpistemeHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], store_path: str | Path) -> None:
        self.store_path = str(store_path)
        super().__init__(server_address, _Handler)

    def read(self, request_path: str) -> tuple[object, str]:
        parsed = urlparse(request_path)
        path = parsed.path
        query = parse_qs(parsed.query, keep_blank_values=True)

        if not path.startswith(API_PREFIX):
            raise _error(404, "API route not found")

        suffix = path[len(API_PREFIX):]
        if suffix == "":
            _reject_unexpected_query(query, set())
            return {
                "api": "episteme",
                "version": API_VERSION,
                "read_only": True,
            }, "application/json; charset=utf-8"

        parts = [part for part in suffix.split("/") if part]
        with Store(self.store_path, read_only=True) as store:
            if parts == ["records"]:
                _reject_unexpected_query(query, {"kind"})
                kind = _record_kind(_single_query(query, "kind"))
                return list_records(store, kind=kind), "application/json; charset=utf-8"

            if len(parts) == 2 and parts[0] == "records":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_record(store, _identifier(parts[1], "record identifier")), "application/json; charset=utf-8"

            if parts == ["discoveries"]:
                _reject_unexpected_query(query, {"kind"})
                kind = _single_query(query, "kind")
                return list_discovery_findings(
                    store, kind=kind
                ), "application/json; charset=utf-8"
            if len(parts) == 2 and parts[0] == "discoveries":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_discovery_finding(
                    store, _identifier(parts[1], "discovery finding identifier")
                ), "application/json; charset=utf-8"

            if parts == ["hypotheses"]:
                _reject_unexpected_query(query, set())
                return list_hypotheses(store), "application/json; charset=utf-8"
            if len(parts) == 2 and parts[0] == "hypotheses":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_hypothesis(store, _identifier(parts[1], "hypothesis identifier")), "application/json; charset=utf-8"
            if parts == ["models"]:
                _reject_unexpected_query(query, set())
                return list_models(store), "application/json; charset=utf-8"
            if len(parts) == 2 and parts[0] == "models":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_model(store, _identifier(parts[1], "model identifier")), "application/json; charset=utf-8"
            if parts == ["predictions"]:
                _reject_unexpected_query(query, set())
                return list_predictions(store), "application/json; charset=utf-8"
            if len(parts) == 2 and parts[0] == "predictions":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_prediction(store, _identifier(parts[1], "prediction identifier")), "application/json; charset=utf-8"
            if parts == ["experiment-proposals"]:
                _reject_unexpected_query(query, set())
                return list_experiment_proposals(store), "application/json; charset=utf-8"
            if len(parts) == 2 and parts[0] == "experiment-proposals":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_experiment_proposal(store, _identifier(parts[1], "experiment proposal identifier")), "application/json; charset=utf-8"
            if parts == ["prediction-evaluations"]:
                _reject_unexpected_query(query, set())
                return list_prediction_evaluations(store), "application/json; charset=utf-8"
            if len(parts) == 2 and parts[0] == "prediction-evaluations":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_prediction_evaluation(store, _identifier(parts[1], "prediction evaluation identifier")), "application/json; charset=utf-8"
            if parts == ["knowledge-state-consequences"]:
                _reject_unexpected_query(query, set())
                return list_knowledge_state_consequences(store), "application/json; charset=utf-8"
            if len(parts) == 2 and parts[0] == "knowledge-state-consequences":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_knowledge_state_consequence(store, _identifier(parts[1], "knowledge-state consequence identifier")), "application/json; charset=utf-8"

            if parts == ["relationships"]:
                _reject_unexpected_query(query, {"predicate"})
                predicate = _single_query(query, "predicate")
                return list_relationships(
                    store, predicate=predicate
                ), "application/json; charset=utf-8"

            if len(parts) == 2 and parts[0] == "relationships":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_relationship(
                    store, _identifier(parts[1], "relationship identifier")
                ), "application/json; charset=utf-8"

            if parts == ["workflows"]:
                _reject_unexpected_query(query, set())
                return list_workflow_definitions(store), "application/json; charset=utf-8"

            if len(parts) == 2 and parts[0] == "workflows":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_workflow_definition(
                    store, _nonempty_identifier(parts[1], "workflow identifier")
                ), "application/json; charset=utf-8"

            if parts == ["executions"]:
                _reject_unexpected_query(query, {"workflow_id"})
                workflow_id = _single_query(query, "workflow_id")
                if workflow_id is not None:
                    workflow_id = _nonempty_identifier(workflow_id, "workflow identifier")
                return list_workflow_executions(
                    store, workflow_id=workflow_id
                ), "application/json; charset=utf-8"

            if len(parts) == 3 and parts[0] == "executions" and parts[2] == "lineage":
                if query:
                    raise _error(400, "unexpected query parameter")
                execution_id = _nonempty_identifier(parts[1], "workflow execution identifier")
                return workflow_execution_lineage(store, execution_id), "application/json; charset=utf-8"

            if len(parts) == 2 and parts[0] == "executions":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_workflow_execution(
                    store, _identifier(parts[1], "workflow execution identifier")
                ), "application/json; charset=utf-8"

            if len(parts) == 3 and parts[0] == "artifacts" and parts[2] == "executions":
                if query:
                    raise _error(400, "unexpected query parameter")
                artifact_id = _nonempty_identifier(parts[1], "artifact identifier")
                return list_workflow_executions_for_artifact(
                    store, artifact_id
                ), "application/json; charset=utf-8"

            if parts == ["reviews"]:
                _reject_unexpected_query(query, {"target_kind", "target_id"})
                target_kind = _review_kind(_single_query(query, "target_kind"))
                target_id = _single_query(query, "target_id")
                return list_reviews(
                    store,
                    target_kind=target_kind,
                    target_id=target_id,
                ), "application/json; charset=utf-8"

            if len(parts) == 2 and parts[0] == "reviews":
                if query:
                    raise _error(400, "unexpected query parameter")
                return get_review(store, _identifier(parts[1], "review identifier")), "application/json; charset=utf-8"

            if len(parts) == 3 and parts[0] == "discoveries" and parts[2] in {
                "trail",
                "lineage",
                "report",
            }:
                finding_id = _identifier(parts[1], "discovery finding identifier")
                created_at = _timestamp(_require_query(query, "created_at"))
                allowed = {"created_at"}
                if parts[2] == "report" and set(query) == {"created_at", "format"}:
                    format_value = _require_query(query, "format")
                    if format_value != "html":
                        raise _error(400, "unsupported report format")
                    report = discovery_report(store, finding_id, created_at)
                    from .html import render_discovery_report_html
                    return render_discovery_report_html(report).encode("utf-8"), "text/html; charset=utf-8"
                _reject_unexpected_query(query, allowed)
                if parts[2] == "trail":
                    return discovery_trail(store, finding_id, created_at), "application/json; charset=utf-8"
                if parts[2] == "lineage":
                    return discovery_lineage(store, finding_id, created_at), "application/json; charset=utf-8"
                return discovery_report(store, finding_id, created_at), "application/json; charset=utf-8"

        raise _error(404, "API route not found")


def create_http_server(
    store_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> ThreadingHTTPServer:
    """Create a read-only Episteme HTTP server."""
    return _EpistemeHTTPServer((host, port), store_path)


def serve(
    store_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Serve the read-only Episteme HTTP API until interrupted."""
    server = create_http_server(store_path, host=host, port=port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


__all__ = ["API_VERSION", "API_PREFIX", "create_http_server", "serve"]
