"""Proof of durable generated exploration-observation inspection."""

import json
import sys
from threading import Thread
from urllib.request import urlopen

from episteme import ExplorationObservation, Record, RecordKind, Provenance, Store, get_exploration_observation, list_exploration_observations

CREATED = "2026-09-30T00:00:00Z"
PROV = (Provenance(source_id="exploration-fixture", captured_at=CREATED, source_location="https://example.org/exploration", source_version="1"),)
RID = "77777777-7777-4777-8777-777777777777"
OID = "88888888-8888-4888-8888-888888888888"


def _seed(path):
    with Store(path) as store:
        record = Record(OID, RecordKind.SOURCE, {"title": "fixture"}, PROV, CREATED)
        observation = ExplorationObservation(
            id=RID,
            observation="Two supplied records appear adjacent in the represented metadata.",
            input_ids=(OID,),
            evidence=("Both records are explicitly present in the supplied corpus.",),
            method="fixture-observation",
            method_version="1",
            uncertainty="This is generated observation, not an established relationship.",
            parameters={"model": "fixture"},
            created_at=CREATED,
        )
        store.put_record(record)
        store.put_exploration_observation(observation)
    return observation


def test_exploration_observation_round_trip_and_public_inspection(tmp_path):
    observation = _seed(tmp_path / "exploration.sqlite")
    with Store(tmp_path / "exploration.sqlite", read_only=True) as store:
        assert get_exploration_observation(store, RID) == observation.to_dict()
        assert list_exploration_observations(store) == [observation.to_dict()]


def test_exploration_observation_rejects_missing_grounded_input(tmp_path):
    with Store(tmp_path / "exploration.sqlite") as store:
        observation = ExplorationObservation(
            id=RID, observation="Unbacked generated observation.", input_ids=(OID,),
            evidence=("No grounded record exists for this input.",), method="fixture",
            method_version="1", uncertainty="Uncertain.", parameters=None, created_at=CREATED,
        )
        try:
            store.put_exploration_observation(observation)
        except ValueError as exc:
            assert str(exc).startswith("exploration observation references missing input")
        else:
            raise AssertionError("missing grounded input must be rejected")


def test_cli_and_http_exploration_observation_inspection_is_read_only(tmp_path, capsys):
    observation = _seed(tmp_path / "exploration.sqlite")
    from episteme.__main__ import main
    original = sys.argv
    try:
        sys.argv = ["episteme", "--store", str(tmp_path / "exploration.sqlite"), "exploration-observation", RID]
        assert main() == 0
        assert json.loads(capsys.readouterr().out) == observation.to_dict()
        sys.argv = ["episteme", "--store", str(tmp_path / "exploration.sqlite"), "exploration-observations"]
        assert main() == 0
        assert json.loads(capsys.readouterr().out) == [observation.to_dict()]
    finally:
        sys.argv = original
    server = __import__("episteme.http_api", fromlist=["create_http_server"]).create_http_server(tmp_path / "exploration.sqlite", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base = f"http://{host}:{port}/api/v1"
        with urlopen(f"{base}/exploration-observations/{RID}") as response:
            assert json.loads(response.read()) == observation.to_dict()
        with urlopen(f"{base}/exploration-observations") as response:
            assert json.loads(response.read()) == [observation.to_dict()]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
