"""Tests for the browser-facing static public instrument."""

from episteme import RecordKind, Store, render_discovery_report_html
from episteme.model import Provenance, make_record
from episteme.model import DiscoveryFinding, DiscoveryFindingKind


CREATED = "2026-09-18T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="html-test",
        captured_at=CREATED,
        source_location="https://example.org/html-test",
        source_version="1",
    ),
)


def test_render_discovery_report_html_is_self_contained_and_read_only():
    record = make_record(
        kind=RecordKind.OBSERVATION,
        payload={"value": "browser-fixture"},
        provenance=PROVENANCE,
        created_at=CREATED,
    )
    finding = DiscoveryFinding(
        id="77777777-7777-4777-8777-777777777777",
        kind=DiscoveryFindingKind.TENSION,
        title="Browser fixture",
        description="A deterministic browser report fixture.",
        input_ids=(record.id,),
        method="html-test",
        method_version="1",
        rationale="Test fixture only.",
        measures=(),
        created_at=CREATED,
    )
    with Store() as store:
        store.put_record(record)
        store.put_discovery_finding(finding)
        from episteme import discovery_report
        report = discovery_report(store, finding.id, "2026-09-18T00:01:00Z")
        before = record.to_dict()
        rendered = render_discovery_report_html(report)
        assert record.to_dict() == before

    assert "<!doctype html>" in rendered
    assert "Grounded records" in rendered
    assert "Generated artifacts" in rendered
    assert record.id in rendered
    assert finding.id in rendered
    assert "This page does not adjudicate truth." in rendered
