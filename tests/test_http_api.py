"""Tests for the read-only Episteme HTTP API."""

from __future__ import annotations

import json
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from episteme.http_api import create_http_server
from episteme.model import Provenance, RecordKind, make_record
from episteme.store import Store


def _record() -> object:
    return make_record(
        kind=RecordKind.OBSERVATION,
        payload={"observation": "test"},
        provenance=[Provenance(source_id="test", source_location="fixture")],
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_http_reads_records_without_mutation(tmp_path) -> None:
    store_path = tmp_path / "episteme.sqlite"
    record = _record()
    with Store(store_path) as store:
        store.put_record(record)

    server = create_http_server(store_path, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/api/v1/records/{record.id}") as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("application/json")
            body = json.loads(response.read())
        assert body["id"] == record.id

        with Store(store_path) as store:
            assert [item.id for item in store.iter_records()] == [record.id]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_lists_records_deterministically(tmp_path) -> None:
    store_path = tmp_path / "episteme.sqlite"
    first = _record()
    second = make_record(
        kind=RecordKind.MEASUREMENT,
        payload={"value": 2, "unit": "m"},
        provenance=[Provenance(source_id="test", source_location="fixture")],
        created_at="2026-01-02T00:00:00+00:00",
    )
    with Store(store_path) as store:
        store.put_record(first)
        store.put_record(second)

    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/api/v1/records") as response:
            body = json.loads(response.read())
        assert [item["id"] for item in body] == [first.id, second.id]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_rejects_mutation_methods(tmp_path) -> None:
    server = create_http_server(tmp_path / "empty.sqlite", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        request = Request(
            f"http://{host}:{port}/api/v1/records",
            method="POST",
            data=b"{}",
        )
        try:
            urlopen(request)
        except HTTPError as error:
            assert error.code == 405
            body = json.loads(error.read())
            assert body["error"]["status"] == 405
        else:
            raise AssertionError("POST unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_returns_404_for_missing_record(tmp_path) -> None:
    server = create_http_server(tmp_path / "empty.sqlite", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urlopen(f"http://{host}:{port}/api/v1/records/missing")
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("missing record unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_rejects_malformed_discovery_request(tmp_path) -> None:
    server = create_http_server(tmp_path / "empty.sqlite", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urlopen(f"http://{host}:{port}/api/v1/discoveries/missing/trail")
        except HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError("malformed request unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
