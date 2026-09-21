"""Tests for the read-only Episteme HTTP API."""

from __future__ import annotations

import html
import json
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from episteme.http_api import create_http_server
from episteme.model import (
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
    Provenance,
    RecordKind,
    Review,
    ReviewDisposition,
    ReviewTargetKind,
    make_record,
)
from uuid import uuid4
from episteme.store import Store


def _record() -> object:
    return make_record(
        kind=RecordKind.OBSERVATION,
        payload={"observation": "test"},
        provenance=[Provenance(source_id="test", captured_at="2026-01-01T00:00:00+00:00", source_location="https://example.invalid/fixture")],
        created_at="2026-01-01T00:00:00+00:00",
    )

def _empty_store(path) -> None:
    with Store(path):
        pass



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
        provenance=[Provenance(source_id="test", captured_at="2026-01-02T00:00:00+00:00", source_location="https://example.invalid/fixture")],
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
    store_path = tmp_path / "empty.sqlite"
    _empty_store(store_path)
    server = create_http_server(store_path, port=0)
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


def test_http_rejects_malformed_object_identifiers(tmp_path) -> None:
    store_path = tmp_path / "empty.sqlite"
    _empty_store(store_path)
    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        for url in (
            f"http://{host}:{port}/api/v1/records/not-a-uuid",
            f"http://{host}:{port}/api/v1/reviews/not-a-uuid",
            f"http://{host}:{port}/api/v1/discoveries/not-a-uuid/trail?created_at=2026-01-01T00:00:00+00:00",
        ):
            try:
                urlopen(url)
            except HTTPError as error:
                assert error.code == 400
            else:
                raise AssertionError("malformed identifier unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_returns_404_for_missing_record(tmp_path) -> None:
    store_path = tmp_path / "empty.sqlite"
    _empty_store(store_path)
    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urlopen(f"http://{host}:{port}/api/v1/records/00000000-0000-0000-0000-000000000001")
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("missing record unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_rejects_malformed_discovery_request(tmp_path) -> None:
    store_path = tmp_path / "empty.sqlite"
    _empty_store(store_path)
    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urlopen(f"http://{host}:{port}/api/v1/discoveries/00000000-0000-0000-0000-000000000001/trail")
        except HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError("malformed request unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)



def test_http_root_is_read_only_and_rejects_query_parameters(tmp_path) -> None:
    server = create_http_server(tmp_path / "empty.sqlite", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/api/v1") as response:
            body = json.loads(response.read())
        assert body == {"api": "episteme", "version": "v1", "read_only": True}

        try:
            urlopen(f"http://{host}:{port}/api/v1?unexpected=1")
        except HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError("unexpected root query parameter was accepted")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_rejects_invalid_record_kind_and_unknown_query(tmp_path) -> None:
    store_path = tmp_path / "empty.sqlite"
    _empty_store(store_path)
    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        for url in (
            f"http://{host}:{port}/api/v1/records?kind=not-a-kind",
            f"http://{host}:{port}/api/v1/records?unexpected=1",
        ):
            try:
                urlopen(url)
            except HTTPError as error:
                assert error.code == 400
            else:
                raise AssertionError("malformed records query unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_reads_reviews_and_exact_target_filters(tmp_path) -> None:
    store_path = tmp_path / "episteme.sqlite"
    record = _record()
    review = Review(
        id=str(uuid4()),
        target_kind=ReviewTargetKind.RECORD,
        target_id=record.id,
        reviewer="fixture-reviewer",
        disposition=ReviewDisposition.NOTE,
        basis="fixture basis",
        rationale="fixture rationale",
        provenance=(Provenance(source_id="test", captured_at="2026-01-03T00:00:00+00:00", source_location="https://example.invalid/fixture"),),
        reviewed_at="2026-01-03T00:00:00+00:00",
    )
    with Store(store_path) as store:
        store.put_record(record)
        store.put_review(review)

    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/api/v1/reviews/{review.id}") as response:
            assert json.loads(response.read())["id"] == review.id

        with urlopen(
            f"http://{host}:{port}/api/v1/reviews"
            f"?target_kind=record&target_id={record.id}"
        ) as response:
            body = json.loads(response.read())
        assert [item["id"] for item in body] == [review.id]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_renders_discovery_report_as_json_and_html(tmp_path) -> None:
    store_path = tmp_path / "episteme.sqlite"
    record = _record()
    finding = DiscoveryFinding(
        id=str(uuid4()),
        kind=DiscoveryFindingKind.CONTRADICTION,
        title="Fixture contradiction",
        description="Two fixture records conflict.",
        input_ids=(record.id,),
        method="fixture",
        method_version="1",
        rationale="HTTP route coverage",
        measures=(
            DiscoveryMeasure(
                name="example",
                value=1.0,
                scale="fixture",
                basis="test",
            ),
        ),
        created_at="2026-01-04T00:00:00+00:00",
    )
    with Store(store_path) as store:
        store.put_record(record)
        store.put_discovery_finding(finding)

    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        from urllib.parse import quote

        base = (
            f"http://{host}:{port}/api/v1/discoveries/"
            f"{finding.id}/report?created_at={quote(finding.created_at)}"
        )
        with urlopen(base) as response:
            body = json.loads(response.read())
        assert body["finding_id"] == finding.id
        assert body["grounded_records"][0]["id"] == record.id

        with urlopen(base + "&format=html") as response:
            assert response.headers["Content-Type"].startswith("text/html")
            html = response.read().decode("utf-8")
        assert "Fixture contradiction" in html
        assert "Read-only" in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_observatory_report_link_preserves_timestamp(tmp_path) -> None:
    store_path = tmp_path / "episteme.sqlite"
    record = _record()
    finding = DiscoveryFinding(
        id=str(uuid4()),
        kind=DiscoveryFindingKind.CONTRADICTION,
        title="Encoded timestamp fixture",
        description="The Observatory report link must preserve timezone offsets.",
        input_ids=(record.id,),
        method="fixture",
        method_version="1",
        rationale="Regression coverage for generated report URLs.",
        measures=(),
        created_at="2026-01-06T01:20:58.980922+00:00",
    )
    with Store(store_path) as store:
        store.put_record(record)
        store.put_discovery_finding(finding)

    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/") as response:
            page = response.read().decode("utf-8")

        marker = f"/api/v1/discoveries/{finding.id}/report?"
        start = page.index(marker)
        href = page[start:page.index('"', start)]
        href = html.unescape(href)

        with urlopen(f"http://{host}:{port}{href}") as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("text/html")
            report = response.read().decode("utf-8")

        assert "Encoded timestamp fixture" in report
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_does_not_create_missing_store(tmp_path) -> None:
    store_path = tmp_path / "missing.sqlite"
    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urlopen(f"http://{host}:{port}/api/v1/records")
        except HTTPError as error:
            assert error.code == 500
        else:
            raise AssertionError("missing store unexpectedly succeeded")
        assert not store_path.exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_rejects_invalid_discovery_timestamp(tmp_path) -> None:
    store_path = tmp_path / "empty.sqlite"
    _empty_store(store_path)
    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urlopen(
                f"http://{host}:{port}/api/v1/discoveries/00000000-0000-0000-0000-000000000001/trail"
                "?created_at=not-a-timestamp"
            )
        except HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError("invalid timestamp unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_does_not_misclassify_internal_key_error_as_not_found(tmp_path, monkeypatch) -> None:
    store_path = tmp_path / "empty.sqlite"
    _empty_store(store_path)
    import episteme.http_api as http_api

    def broken_get_record(store, record_id):
        raise KeyError("corrupt persisted state")

    monkeypatch.setattr(http_api, "get_record", broken_get_record)
    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urlopen(
                f"http://{host}:{port}/api/v1/records/00000000-0000-0000-0000-000000000001"
            )
        except HTTPError as error:
            assert error.code == 500
            body = json.loads(error.read())
            assert body["error"]["status"] == 500
        else:
            raise AssertionError("internal KeyError unexpectedly returned success")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

def test_http_root_renders_observatory_without_mutation(tmp_path) -> None:
    store_path = tmp_path / "episteme.sqlite"
    record = _record()
    finding = DiscoveryFinding(
        id=str(uuid4()),
        kind=DiscoveryFindingKind.CONTRADICTION,
        title="Fixture contradiction",
        description="Two fixture records conflict.",
        input_ids=(record.id,),
        method="fixture",
        method_version="1",
        rationale="Observatory route coverage",
        measures=(
            DiscoveryMeasure(
                name="example",
                value=1.0,
                scale="fixture",
                basis="test",
            ),
        ),
        created_at="2026-01-05T00:00:00+00:00",
    )
    with Store(store_path) as store:
        store.put_record(record)
        store.put_discovery_finding(finding)

    server = create_http_server(store_path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/") as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("text/html")
            page = response.read().decode("utf-8")
        assert "Observatory" in page
        assert "Fixture contradiction" in page
        assert f"/api/v1/discoveries/{finding.id}/report" in page
        assert "Read-only" in page

        with Store(store_path) as store:
            assert [item.id for item in store.iter_records()] == [record.id]
            assert [item.id for item in store.iter_discovery_findings()] == [finding.id]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
