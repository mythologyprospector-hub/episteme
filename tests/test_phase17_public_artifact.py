"""Phase 17 proof of public epistemic artifact inspection."""

import json
import sys
from threading import Thread
from urllib.request import urlopen

from episteme import (
    ExperimentProposal,
    Hypothesis,
    KnowledgeStateConsequence,
    KnowledgeStateConsequenceKind,
    KnowledgeStateTargetKind,
    Model,
    Prediction,
    PredictionEvaluation,
    PredictionEvaluationOutcome,
    Store,
    Record,
    RecordKind,
    DiscoveryFinding,
    DiscoveryFindingKind,
    get_experiment_proposal,
    get_hypothesis,
    get_knowledge_state_consequence,
    get_model,
    get_prediction,
    get_prediction_evaluation,
    list_experiment_proposals,
    list_hypotheses,
    list_knowledge_state_consequences,
    list_models,
    list_predictions,
    list_prediction_evaluations,
    Provenance,
)

CREATED = "2026-09-20T00:00:00Z"
PROV = (Provenance(source_id="phase17-fixture", captured_at=CREATED, source_location="https://example.org/phase17", source_version="1"),)
HID = "11111111-1111-4111-8111-111111111111"
MID = "22222222-2222-4222-8222-222222222222"
PID = "33333333-3333-4333-8333-333333333333"
EID = "44444444-4444-4444-8444-444444444444"
PEID = "55555555-5555-4555-8555-555555555555"
KID = "66666666-6666-4666-8666-666666666666"
RID = "77777777-7777-4777-8777-777777777777"
OID = "88888888-8888-4888-8888-888888888888"
RESULT_ID = "99999999-9999-4999-8999-999999999999"

def _seed(path):
    h = Hypothesis(HID, "A generated explanation.", (RID,), (OID,), "fixture", "1", "test", (), CREATED)
    m = Model(MID, "A generated model.", (HID,), (), (), "fixture", "1", "test", CREATED)
    p = Prediction(PID, HID, "An expected consequence.", "Under fixture conditions.", (), "fixture", "1", "test", (), CREATED)
    ep = ExperimentProposal(EID, (PID,), "Test the prediction.", "Observe the consequence.", "The observation distinguishes the prediction.", "Fixture conditions.", (), "fixture", "1", "test", CREATED)
    pe = PredictionEvaluation(PEID, RESULT_ID, PID, EID, "Fixture conditions.", (), PredictionEvaluationOutcome.CONSISTENT, "The result is consistent.", "fixture", "1", CREATED)
    k = KnowledgeStateConsequence(KID, (PEID,), KnowledgeStateTargetKind.HYPOTHESIS, HID, KnowledgeStateConsequenceKind.SUPPORTS, (), "The evaluation supports the hypothesis.", "fixture", "1", CREATED)
    with Store(path) as store:
        observation = Record(OID, RecordKind.OBSERVATION, {"value": "fixture"}, PROV, CREATED)
        result = Record(RESULT_ID, RecordKind.RESULT, {"value": "fixture result"}, PROV, CREATED)
        finding = DiscoveryFinding(RID, DiscoveryFindingKind.TENSION, "Fixture tension", "fixture tension", (OID,), "fixture", "1", "test", (), CREATED)
        store.put_record(observation)
        store.put_record(result)
        store.put_discovery_finding(finding)
        store.put_hypothesis(h)
        store.put_model(m)
        store.put_prediction(p)
        store.put_experiment_proposal(ep)
        store.put_prediction_evaluation(pe)
        store.put_knowledge_state_consequence(k)
    return h, m, p, ep, pe, k

def test_public_artifact_inspection_preserves_existing_representations(tmp_path):
    artifacts = _seed(tmp_path / "phase17.sqlite")
    with Store(tmp_path / "phase17.sqlite", read_only=True) as store:
        getters = (
            get_hypothesis(store, HID),
            get_model(store, MID),
            get_prediction(store, PID),
            get_experiment_proposal(store, EID),
            get_prediction_evaluation(store, PEID),
            get_knowledge_state_consequence(store, KID),
        )
        assert getters == tuple(item.to_dict() for item in artifacts)
        assert list_hypotheses(store) == [artifacts[0].to_dict()]
        assert list_models(store) == [artifacts[1].to_dict()]
        assert list_predictions(store) == [artifacts[2].to_dict()]
        assert list_experiment_proposals(store) == [artifacts[3].to_dict()]
        assert list_prediction_evaluations(store) == [artifacts[4].to_dict()]
        assert list_knowledge_state_consequences(store) == [artifacts[5].to_dict()]

def test_missing_artifact_is_not_found(tmp_path):
    _seed(tmp_path / "phase17.sqlite")
    with Store(tmp_path / "phase17.sqlite", read_only=True) as store:
        try:
            get_hypothesis(store, "99999999-9999-4999-8999-999999999999")
        except ValueError as exc:
            assert str(exc).startswith("hypothesis not found:")
        else:
            raise AssertionError("missing hypothesis must be rejected")

def test_cli_artifact_inspection_is_read_only(tmp_path, capsys):
    artifacts = _seed(tmp_path / "phase17.sqlite")
    from episteme.__main__ import main
    original = sys.argv
    try:
        commands = [
            ("hypothesis", HID, artifacts[0]),
            ("model", MID, artifacts[1]),
            ("prediction", PID, artifacts[2]),
            ("experiment-proposal", EID, artifacts[3]),
            ("prediction-evaluation", PEID, artifacts[4]),
            ("knowledge-state-consequence", KID, artifacts[5]),
        ]
        for command, artifact_id, artifact in commands:
            sys.argv = ["episteme", "--store", str(tmp_path / "phase17.sqlite"), command, artifact_id]
            assert main() == 0
            assert json.loads(capsys.readouterr().out) == artifact.to_dict()
    finally:
        sys.argv = original

def test_http_artifact_inspection_is_read_only(tmp_path):
    artifacts = _seed(tmp_path / "phase17.sqlite")
    server = __import__("episteme.http_api", fromlist=["create_http_server"]).create_http_server(tmp_path / "phase17.sqlite", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base = f"http://{host}:{port}/api/v1"
        routes = [
            ("hypotheses", artifacts[0]),
            ("models", artifacts[1]),
            ("predictions", artifacts[2]),
            ("experiment-proposals", artifacts[3]),
            ("prediction-evaluations", artifacts[4]),
            ("knowledge-state-consequences", artifacts[5]),
        ]
        for route, artifact in routes:
            with urlopen(f"{base}/{route}/{artifact.id}") as response:
                assert json.loads(response.read()) == artifact.to_dict()
            with urlopen(f"{base}/{route}") as response:
                assert json.loads(response.read()) == [artifact.to_dict()]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
