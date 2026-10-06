"""Regression test for numeric tolerance in structural discovery."""

from episteme.discovery import detect_accounting_gap
from episteme.model import Provenance, Record, RecordKind
from episteme.store import Store


CREATED = "2026-10-06T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="fixture://issue3",
        captured_at=CREATED,
        source_location="fixture://issue3",
        source_version="1",
    ),
)


def _record(record_id: str, quantity: float) -> Record:
    return Record(
        id=record_id,
        kind=RecordKind.OBSERVATION,
        payload={"quantity": quantity},
        provenance=PROVENANCE,
        created_at=CREATED,
    )


def test_accounting_gap_does_not_treat_float_rounding_as_real_residual():
    """Mathematically equal decimal quantities must not create a gap from float noise."""

    total = _record("aaaaaaaa-0001-4aaa-8aaa-aaaaaaaaaaaa", 0.3)
    first = _record("bbbbbbbb-0001-4aaa-8aaa-bbbbbbbbbbbb", 0.1)
    second = _record("cccccccc-0001-4aaa-8aaa-cccccccccccc", 0.2)

    with Store() as store:
        for record in (total, first, second):
            store.put_record(record)

        finding = detect_accounting_gap(
            store,
            total_record_id=total.id,
            component_record_ids=(first.id, second.id),
            quantity_key="quantity",
            created_at=CREATED,
        )

        assert finding is None
