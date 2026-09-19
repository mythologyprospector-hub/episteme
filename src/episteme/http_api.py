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
    get_review,
    list_records,
    list_reviews,
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
