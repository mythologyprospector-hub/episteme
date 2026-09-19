"""Tests for the read-only Episteme CLI review surface."""

import json
from pathlib import Path

from episteme import Provenance, RecordKind, Store, make_record
from episteme.model import Review, ReviewDisposition, ReviewTargetKind
from episteme.__main__ import main


CREATED = "2026-09-18T00:00:00Z"
PROVENANCE = (Provenance(source_id="cli-test", captured_at=CREATED),)


def test_cli_can_inspect_reviews(tmp_path, capsys, monkeypatch):
    store_path = tmp_path / "episteme.sqlite"
    record = make_record(RecordKind.OBSERVATION, {"value": "cli"}, PROVENANCE, CREATED)
    review = Review(
        id="77777777-7777-4777-8777-777777777777",
        target_kind=ReviewTargetKind.RECORD,
        target_id=record.id,
        reviewer="cli-reviewer",
        disposition=ReviewDisposition.NOTE,
        basis="CLI inspection test.",
        rationale="The review should be visible without mutation.",
        provenance=PROVENANCE,
        reviewed_at=CREATED,
    )
    with Store(store_path) as store:
        store.put_record(record)
        store.put_review(review)

    monkeypatch.setattr("sys.argv", ["episteme", "--store", str(store_path), "review", review.id])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["id"] == review.id

    monkeypatch.setattr(
        "sys.argv",
        [
            "episteme",
            "--store",
            str(store_path),
            "reviews",
            "--target-kind",
            "record",
            "--target-id",
            record.id,
        ],
    )
    assert main() == 0
    assert [item["id"] for item in json.loads(capsys.readouterr().out)] == [review.id]


def test_cli_serve_does_not_require_a_subcommand(monkeypatch):
    called = {}

    def fake_serve(store_path, host, port):
        called.update(store_path=store_path, host=host, port=port)

    monkeypatch.setattr("episteme.__main__.serve", fake_serve)
    monkeypatch.setattr(
        "sys.argv",
        [
            "episteme",
            "--serve",
            "--store",
            "fixture.sqlite",
            "--host",
            "127.0.0.2",
            "--port",
            "8123",
        ],
    )

    assert main() == 0
    assert called == {"store_path": Path("fixture.sqlite"), "host": "127.0.0.2", "port": 8123}


def test_cli_requires_an_existing_store_argument(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["episteme", "records"])

    try:
        main()
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("CLI should require an explicit existing store path")
