"""Tests for the read-only public Episteme instrument."""

from episteme import (
    DiscoveryFinding,
    DiscoveryFindingKind,
    DiscoveryMeasure,
    Provenance,
    RecordKind,
    Store,
    discovery_lineage,
    discovery_report,
    discovery_trail,
    get_record,
    list_records,
    make_record,
)


CREATED = "2026-09-18T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="public-test",
        captured_at=CREATED,
        source_location="https://example.org/public-test",
        source_version="1",
    ),
)


def test_public_api_reads_grounded_records_without_changing_them():
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "fixture"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )

    with Store() as store:
        store.put_record(record)
        before = record.to_dict()

        assert get_record(store, record.id) == before
        assert list_records(store) == [before]
        assert record.to_dict() == before


def test_public_api_exposes_trail_and_report_without_reinterpreting_state():
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "fixture"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    finding = DiscoveryFinding(
        id="66666666-6666-4666-8666-666666666666",
        kind=DiscoveryFindingKind.TENSION,
        title="Public inspection fixture",
        description="A deterministic finding used to exercise the public surface.",
        input_ids=(record.id,),
        method="public-test",
        method_version="1",
        rationale="Test fixture only.",
        measures=(
            DiscoveryMeasure(
                name="input_count",
                value=1.0,
                scale="count",
                basis="one grounded fixture record",
            ),
        ),
        created_at=CREATED,
    )

    with Store() as store:
        store.put_record(record)
        store.put_discovery_finding(finding)

        trail = discovery_trail(store, finding.id, "2026-09-18T00:01:00Z")
        lineage = discovery_lineage(store, finding.id, "2026-09-18T00:01:00Z")
        report = discovery_report(store, finding.id, "2026-09-18T00:01:00Z")

    assert trail["finding_id"] == finding.id
    assert lineage["finding_id"] == finding.id
    assert "created_at" not in lineage
    assert report["report"] == "episteme-discovery-report-v1"
    assert report["grounded_records"][0]["id"] == record.id
    assert report["generated_artifacts"][0]["id"] == finding.id
    assert report["lineage"] == lineage



def test_cli_records_reads_a_store(tmp_path, capsys):
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "cli-fixture"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    store_path = tmp_path / "episteme.sqlite"
    with Store(store_path) as store:
        store.put_record(record)

    from episteme.__main__ import main

    import sys
    original = sys.argv
    try:
        sys.argv = ["python -m episteme", "--store", str(store_path), "records"]
        assert main() == 0
    finally:
        sys.argv = original

    import json
    assert json.loads(capsys.readouterr().out) == [record.to_dict()]
