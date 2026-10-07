from episteme.rediscovery import build_mendeleev_fixture


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
    assert "72.63" not in public_text
    assert "5.3234" not in public_text
    assert "atomic_number" not in public_text
    assert fixture.held_out_record.payload["label"] == "held_out_element"


def test_phase29_held_out_record_is_not_in_pre_discovery_inputs():
    fixture = build_mendeleev_fixture()

    pre_ids = tuple(record.id for record in fixture.pre_discovery_records)
    assert fixture.held_out_record.id not in pre_ids
    assert fixture.held_out_record.created_at > max(
        record.created_at for record in fixture.pre_discovery_records
    )
