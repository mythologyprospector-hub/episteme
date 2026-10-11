import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.accept_ollama_rediscovery import (
    _contains_blinded_element_name,
    _index_evaluations,
)


def test_evaluations_are_associated_by_prediction_id_not_list_order():
    predictions = (SimpleNamespace(id="p1"), SimpleNamespace(id="p2"))
    evaluation_for_p1 = SimpleNamespace(prediction_id="p1", outcome="consistent")
    evaluation_for_p2 = SimpleNamespace(prediction_id="p2", outcome="inconsistent")

    indexed, integrity_ok = _index_evaluations(
        predictions,
        (evaluation_for_p2, evaluation_for_p1),
    )

    assert integrity_ok
    assert indexed["p1"] is evaluation_for_p1
    assert indexed["p2"] is evaluation_for_p2


def test_evaluation_index_rejects_missing_or_duplicate_evaluation_records():
    predictions = (SimpleNamespace(id="p1"), SimpleNamespace(id="p2"))
    one_evaluation = SimpleNamespace(prediction_id="p1", outcome="consistent")
    duplicate_evaluation = SimpleNamespace(prediction_id="p1", outcome="inconsistent")

    _, missing_ok = _index_evaluations(predictions, (one_evaluation,))
    _, duplicate_ok = _index_evaluations(predictions, (one_evaluation, duplicate_evaluation))

    assert not missing_ok
    assert not duplicate_ok


def test_blinded_name_check_uses_whole_words_not_substrings():
    assert not _contains_blinded_element_name("The hypotheses propose distinct quantitative forecasts.")
    assert not _contains_blinded_element_name("The inquiry continues with the current predictions.")
    assert _contains_blinded_element_name("The missing element may be tin.")
    assert _contains_blinded_element_name("The observations mention silicon and germanium.")
