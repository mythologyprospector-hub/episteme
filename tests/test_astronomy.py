from episteme import Provenance, RecordKind
from episteme.domains.astronomy import make_astronomy_measurement, validate_measurement


PROVENANCE = (
    Provenance(
        source_id="astronomy-test-source",
        captured_at="2026-09-18T12:00:00+00:00",
        source_location="https://example.org/observation/1",
        source_version="1",
    ),
)


def test_astronomy_translation_produces_normal_grounded_record():
    payload = {
        "quantity": "apparent_magnitude",
        "value": 12.4,
        "unit": "mag",
        "target": "example-star",
        "instrument": "example-camera",
        "observed_at": "2026-09-18T11:30:00+00:00",
        "conditions": {"filter": "V"},
    }

    record = make_astronomy_measurement(payload, PROVENANCE, "2026-09-18T12:00:00+00:00")

    assert record.kind is RecordKind.MEASUREMENT
    assert record.provenance == PROVENANCE
    assert record.payload["domain"] == "astronomy"
    assert record.payload["schema"] == "astronomy-measurement-v1"
    assert record.payload["data"] == payload


def test_missing_measurement_is_explicit_not_zero_or_null():
    payload = {"quantity": "apparent_magnitude", "status": "not_measured"}

    validate_measurement(payload)


def test_unreported_measurement_is_explicit():
    payload = {"quantity": "apparent_magnitude", "status": "not_reported"}

    validate_measurement(payload)


def test_uncertain_measurement_is_explicit():
    payload = {"quantity": "apparent_magnitude", "status": "uncertain"}

    validate_measurement(payload)


def test_non_measured_status_cannot_hide_a_value():
    try:
        validate_measurement(
            {"quantity": "apparent_magnitude", "status": "not_measured", "value": 0}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("non-measured payload with value must be rejected")


def test_domain_validation_does_not_change_provenance():
    payload = {"quantity": "flux", "value": 1.5, "unit": "Jy"}
    record = make_astronomy_measurement(payload, PROVENANCE, "2026-09-18T12:00:00+00:00")
    assert record.provenance[0].to_dict() == PROVENANCE[0].to_dict()


def test_astronomy_record_survives_core_store_round_trip():
    from episteme import Store

    payload = {"quantity": "flux", "value": 2.5, "unit": "Jy", "target": "example-star"}
    record = make_astronomy_measurement(payload, PROVENANCE, "2026-09-18T12:00:00+00:00")

    with Store() as store:
        store.put_record(record)
        restored = store.get_record(record.id)

    assert restored == record


def test_invalid_status_type_is_rejected_as_domain_error():
    try:
        validate_measurement({"quantity": "flux", "status": {"unexpected": "mapping"}})
    except ValueError:
        pass
    else:
        raise AssertionError("non-string status must be rejected")


def test_domain_translation_is_deterministic_except_for_record_identity():
    payload_a = {"quantity": "flux", "unit": "Jy", "value": 2.5, "target": "example-star"}
    payload_b = {"target": "example-star", "value": 2.5, "unit": "Jy", "quantity": "flux"}

    record_a = make_astronomy_measurement(payload_a, PROVENANCE, "2026-09-18T12:00:00+00:00")
    record_b = make_astronomy_measurement(payload_b, PROVENANCE, "2026-09-18T12:00:00+00:00")

    assert record_a.payload == record_b.payload
    assert record_a.to_dict()["payload"] == record_b.to_dict()["payload"]


def test_measured_value_can_carry_domain_uncertainty_metadata():
    payload = {
        "quantity": "apparent_magnitude",
        "value": 12.4,
        "unit": "mag",
        "uncertainty": {"type": "standard_error", "value": 0.2, "unit": "mag"},
    }

    validate_measurement(payload)


def test_uncertainty_does_not_change_core_record_kind():
    payload = {
        "quantity": "flux",
        "value": 1.5,
        "unit": "Jy",
        "uncertainty": {"type": "absolute", "value": 0.1, "unit": "Jy"},
    }
    record = make_astronomy_measurement(payload, PROVENANCE, "2026-09-18T12:00:00+00:00")

    assert record.kind is RecordKind.MEASUREMENT
    assert record.payload["data"]["uncertainty"] == payload["uncertainty"]
