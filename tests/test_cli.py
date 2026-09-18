"""Tests for the read-only Episteme CLI review surface."""

import json

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

    monkeypatch.setattr("sys.argv", ["episteme", "--store", str(store_path), "reviews", "--target-kind", "record", "--target-id", record.id])
    assert main() == 0
    assert [item["id"] for item in json.loads(capsys.readouterr().out)] == [review.id]
