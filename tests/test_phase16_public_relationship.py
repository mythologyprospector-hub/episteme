"""Phase 16 proof of public relationship inspection."""

import json
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from episteme import (
    Provenance,
    Record,
    RecordKind,
    Relationship,
    Store,
    get_relationship,
    list_relationships,
)
from episteme.http_api import create_http_server


CREATED = "2026-09-20T00:00:00Z"
SUBJECT_ID = "11111111-1111-4111-8111-111111111111"
OBJECT_ID = "22222222-2222-4222-8222-222222222222"
RELATIONSHIP_ID = "33333333-3333-4333-8333-333333333331"
RELATIONSHIP_ID_2 = "33333333-3333-4333-8333-333333333332"

PROVENANCE = (
    Provenance(
        source_id="phase16-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase16",
        source_version="1",
    ),
)


def _seed(path):
    subject = Record(
        id=SUBJECT_ID,
        kind=RecordKind.OBSERVATION,
        payload={"value": "subject"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    obj = Record(
        id=OBJECT_ID,
        kind=RecordKind.RESULT,
        payload={"value": "object"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    first = Relationship(
        id=RELATIONSHIP_ID,
        subject_id=SUBJECT_ID,
        predicate="supports",
        object_id=OBJECT_ID,
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    second = Relationship(
        id=RELATIONSHIP_ID_2,
        subject_id=OBJECT_ID,
        predicate="derived-from",
        object_id=SUBJECT_ID,
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    with Store(path) as store:
        store.put_record(subject)
        store.put_record(obj)
        store.put_relationship(first)
        store.put_relationship(second)
    return first, second


def test_public_relationship_lookup_preserves_representation(tmp_path):
    path = tmp_path / "phase16.sqlite"
    first, second = _seed(path)

    with Store(path, read_only=True) as store:
        assert get_relationship(store, first.id) == first.to_dict()
        assert list_relationships(store) == [first.to_dict(), second.to_dict()]
        assert list_relationships(store, predicate="supports") == [first.to_dict()]


def test_missing_relationship_is_not_found(tmp_path):
    path = tmp_path / "phase16.sqlite"
    _seed(path)

    with Store(path, read_only=True) as store:
        try:
            get_relationship(store, "99999999-9999-4999-8999-999999999999")
        except ValueError as exc:
            assert str(exc).startswith("relationship not found:")
        else:
            raise AssertionError("missing relationship must be rejected")


def test_cli_relationship_inspection_is_read_only(tmp_path, capsys):
    path = tmp_path / "phase16.sqlite"
    first, second = _seed(path)

    from episteme.__main__ import main

    original = sys.argv
    try:
        sys.argv = ["episteme", "--store", str(path), "relationship", first.id]
        assert main() == 0
        assert json.loads(capsys.readouterr().out) == first.to_dict()

        sys.argv = ["episteme", "--store", str(path), "relationships", "--predicate", "supports"]
        assert main() == 0
        assert json.loads(capsys.readouterr().out) == [first.to_dict()]
    finally:
        sys.argv = original

    with Store(path, read_only=True) as store:
        assert [item.id for item in store.iter_relationships()] == [first.id, second.id]


def test_http_relationship_inspection_is_read_only(tmp_path):
    path = tmp_path / "phase16.sqlite"
    first, second = _seed(path)
    server = create_http_server(path, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base = f"http://{host}:{port}/api/v1"

        with urlopen(f"{base}/relationships/{first.id}") as response:
            assert json.loads(response.read()) == first.to_dict()

        with urlopen(f"{base}/relationships?predicate=supports") as response:
            assert json.loads(response.read()) == [first.to_dict()]

        with urlopen(f"{base}/relationships") as response:
            assert json.loads(response.read()) == [first.to_dict(), second.to_dict()]

        try:
            urlopen(f"{base}/relationships/99999999-9999-4999-8999-999999999999")
        except HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("missing relationship must return 404")

        try:
            urlopen(f"{base}/relationships?unexpected=1")
        except HTTPError as exc:
            assert exc.code == 400
        else:
            raise AssertionError("unexpected relationship query must return 400")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
