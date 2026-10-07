"""Phase 29 historical rediscovery fixture.

Only pre-discovery information is exposed through pre_discovery_records.
The later held-out record is deliberately separate and is never part of the
planner input fixture.
"""

from __future__ import annotations

from dataclasses import dataclass
from episteme.model import Provenance, Record, RecordKind

FIXTURE_CAPTURED_AT = "1885-12-31T00:00:00+00:00"
FIXTURE_SOURCE = "phase29-rsc-historical-fixture"
FIXTURE_VERSION = "1"
FIXTURE_LOCATION = "https://www.rsc.org/images/23_The_Periodic_Law_tcm18-30005.pdf"


@dataclass(frozen=True)
class RediscoveryFixture:
    pre_discovery_records: tuple[Record, ...]
    held_out_record: Record


def _provenance() -> tuple[Provenance, ...]:
    return (
        Provenance(
            source_id=FIXTURE_SOURCE,
            captured_at=FIXTURE_CAPTURED_AT,
            source_location=FIXTURE_LOCATION,
            source_version=FIXTURE_VERSION,
            note="Bounded pre-discovery historical fixture; later discovery data is excluded.",
        ),
    )


def build_mendeleev_fixture() -> RediscoveryFixture:
    provenance = _provenance()

    pre_discovery = (
        Record(
            id="10000000-0000-4000-8000-000000000001",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "carbon",
                "family": "group_14",
                "period": 2,
                "relative_atomic_mass": 12.01,
                "density_g_cm3": 2.26,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
        Record(
            id="10000000-0000-4000-8000-000000000002",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "silicon",
                "family": "group_14",
                "period": 3,
                "relative_atomic_mass": 28.09,
                "density_g_cm3": 2.33,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
        Record(
            id="10000000-0000-4000-8000-000000000003",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "tin",
                "family": "group_14",
                "period": 5,
                "relative_atomic_mass": 118.71,
                "density_g_cm3": 7.31,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
        Record(
            id="10000000-0000-4000-8000-000000000004",
            kind=RecordKind.OBSERVATION,
            payload={
                "label": "lead",
                "family": "group_14",
                "period": 6,
                "relative_atomic_mass": 207.2,
                "density_g_cm3": 11.34,
            },
            provenance=provenance,
            created_at=FIXTURE_CAPTURED_AT,
        ),
    )

    held_out = Record(
        id="20000000-0000-4000-8000-000000000001",
        kind=RecordKind.OBSERVATION,
        payload={
            "label": "held_out_element",
            "family": "group_14",
            "period": 4,
            "relative_atomic_mass": 72.63,
            "density_g_cm3": 5.3234,
        },
        provenance=provenance,
        created_at="1886-12-31T00:00:00+00:00",
    )

    return RediscoveryFixture(
        pre_discovery_records=pre_discovery,
        held_out_record=held_out,
    )
