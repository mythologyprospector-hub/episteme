import math
from dataclasses import replace

from episteme.rediscovery import (
    RediscoveryOutcome,
    build_mendeleev_fixture,
    derive_mendeleev_mass_prediction,
    evaluate_mendeleev_mass_prediction,
)


def test_phase29_fixture_separates_pre_discovery_and_held_out_records():
    fixture = build_mendeleev_fixture()

    pre_ids = {record.id for record in fixture.pre_discovery_records}
    assert fixture.held_out_record.id not in pre_ids
    assert len(pre_ids) == len(fixture.pre_discovery_records)
    assert len(fixture.pre_discovery_records) >= 3


def test_phase29_pre_discovery_fixture_contains_the_structural_vacancy():
    fixture = build_mendeleev_fixture()

    periods = sorted(
        record.payload["period"] for record in fixture.pre_discovery_records
        if record.payload["family"] == "group_14"
    )
    assert periods == [2, 3, 5, 6]
    assert fixture.held_out_record.payload["period"] == 4


def test_phase29_planner_fixture_does_not_expose_later_element_identity_or_modern_atomic_number():
    fixture = build_mendeleev_fixture()

    public_payload = [
        record.to_dict()["payload"] for record in fixture.pre_discovery_records
    ]
    public_text = str(public_payload).lower()

    assert "germanium" not in public_text
    assert "72.32" not in public_text
    assert "5.47" not in public_text
    assert "atomic_number" not in public_text
    assert fixture.held_out_record.payload["label"] == "held_out_element"


def test_phase29_held_out_record_is_not_in_pre_discovery_inputs():
    fixture = build_mendeleev_fixture()

    pre_ids = tuple(record.id for record in fixture.pre_discovery_records)
    assert fixture.held_out_record.id not in pre_ids
    assert fixture.held_out_record.created_at > max(
        record.created_at for record in fixture.pre_discovery_records
    )


def test_phase29_host_runtime_derives_nontrivial_mass_prediction_from_pre_discovery_inputs():
    fixture = build_mendeleev_fixture()

    prediction = derive_mendeleev_mass_prediction(fixture.pre_discovery_records)

    assert math.isclose(prediction.predicted_relative_atomic_mass, 73.4)
    assert prediction.input_ids == (
        fixture.pre_discovery_records[1].id,
        fixture.pre_discovery_records[2].id,
    )
    assert prediction.input_ids[0] != fixture.held_out_record.id
    assert prediction.input_ids[1] != fixture.held_out_record.id


def test_phase29_deterministic_evaluator_matches_later_held_out_observation():
    fixture = build_mendeleev_fixture()
    prediction = derive_mendeleev_mass_prediction(fixture.pre_discovery_records)

    evaluation = evaluate_mendeleev_mass_prediction(
        prediction,
        fixture.held_out_record,
        tolerance=0.05,
    )

    assert evaluation.outcome is RediscoveryOutcome.MATCHED
    assert evaluation.observed_relative_atomic_mass == 72.32
    assert evaluation.relative_error < 0.02


def test_phase29_corrupted_held_out_evidence_fails_deterministically():
    fixture = build_mendeleev_fixture()
    prediction = derive_mendeleev_mass_prediction(fixture.pre_discovery_records)
    corrupted_payload = dict(fixture.held_out_record.payload)
    corrupted_payload["relative_atomic_mass"] = 200.0
    corrupted = replace(fixture.held_out_record, payload=corrupted_payload)

    evaluation = evaluate_mendeleev_mass_prediction(
        prediction,
        corrupted,
        tolerance=0.05,
    )

    assert evaluation.outcome is RediscoveryOutcome.FAILED
    assert evaluation.relative_error > 0.5
