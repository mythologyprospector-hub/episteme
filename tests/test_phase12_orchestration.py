"""Phase 12 proof of finite discovery workflow orchestration."""

from episteme import (
    DiscoveryFindingKind,
    KnowledgeStateConsequence,
    KnowledgeStateConsequenceKind,
    KnowledgeStateTargetKind,
    PredictionEvaluation,
    PredictionEvaluationOutcome,
    Provenance,
    Record,
    RecordKind,
    Store,
    complete_structural_gap,
    detect_positional_gap,
    discover_evaluation_tensions,
    propose_candidate_discrimination_experiment,
    propose_discriminating_prediction,
)
from episteme.orchestration import WorkflowDefinition, WorkflowStep, run_workflow


CREATED = "2026-09-19T00:00:00Z"
PROVENANCE = (
    Provenance(
        source_id="phase12-fixture",
        captured_at=CREATED,
        source_location="https://example.org/phase12",
        source_version="1",
    ),
)


def _records():
    return tuple(
        Record(
            id=f"aaaaaaaa-{index:04d}-4aaa-8aaa-aaaaaaaaaaaa",
            kind=RecordKind.OBSERVATION,
            payload={"position": position},
            provenance=PROVENANCE,
            created_at=CREATED,
        )
        for index, position in enumerate((1.0, 2.0, 4.0), start=1)
    )


def test_declared_workflow_runs_existing_discovery_loop_and_preserves_lineage():
    records = _records()

    with Store() as store:
        for record in records:
            store.put_record(record)

        state = {}

        def gap_step(step):
            gap = detect_positional_gap(
                store,
                record_ids=tuple(record.id for record in records),
                position_key="position",
                step=1.0,
                created_at=CREATED,
            )
            assert gap is not None
            store.put_discovery_finding(gap)
            state["gap"] = gap
            return (gap.id,)

        def candidates_step(step):
            gap = state["gap"]
            candidates = []
            for statement in ("position 3.0", "a different position"):
                candidate = complete_structural_gap(
                    store,
                    gap_id=gap.id,
                    statement=statement,
                    method="phase12-fixture-candidate",
                    method_version="1",
                    rationale="Declared workflow candidate completion.",
                    created_at=CREATED,
                )
                store.put_hypothesis(candidate)
                candidates.append(candidate)
            state["candidates"] = tuple(candidates)
            return tuple(candidate.id for candidate in candidates)

        def predictions_step(step):
            candidates = state["candidates"]
            predictions = []
            consequences = (
                "The measured occupant is at position 3.0.",
                "The measured occupant is not at position 3.0.",
            )
            for candidate, consequence in zip(candidates, consequences):
                prediction = propose_discriminating_prediction(
                    store,
                    candidate_id=candidate.id,
                    competing_candidate_ids=tuple(item.id for item in candidates),
                    consequence=consequence,
                    conditions="Same bounded test conditions.",
                    method="phase12-fixture-prediction",
                    method_version="1",
                    rationale="Declared workflow discrimination.",
                    created_at=CREATED,
                )
                store.put_prediction(prediction)
                predictions.append(prediction)
            state["predictions"] = tuple(predictions)
            return tuple(prediction.id for prediction in predictions)

        def experiment_step(step):
            predictions = state["predictions"]
            proposal = propose_candidate_discrimination_experiment(
                store,
                prediction_ids=tuple(item.id for item in predictions),
                objective="Distinguish the competing candidates.",
                proposed_observation="Measure the missing position.",
                discrimination_basis="The candidates predict different outcomes.",
                conditions="Same bounded test conditions.",
                method="phase12-fixture-experiment",
                method_version="1",
                rationale="Declared workflow experiment.",
                created_at=CREATED,
            )
            store.put_experiment_proposal(proposal)
            state["proposal"] = proposal
            return (proposal.id,)

        def result_step(step):
            result = Record(
                id="55555555-5555-4555-8555-555555555555",
                kind=RecordKind.RESULT,
                payload={"position": 3.0},
                provenance=PROVENANCE,
                created_at=CREATED,
            )
            store.put_record(result)
            state["result"] = result
            return (result.id,)

        def evaluation_step(step):
            predictions = state["predictions"]
            proposal = state["proposal"]
            result = state["result"]
            evaluations = []
            # Give one prediction two grounded results with differing
            # classifications so the existing renewal detector has a real
            # evaluation tension to discover.
            result_inconsistent = Record(
                id="55555555-5555-4555-8555-555555555556",
                kind=RecordKind.RESULT,
                payload={"position": 5.0},
                provenance=PROVENANCE,
                created_at=CREATED,
            )
            store.put_record(result_inconsistent)
            evaluation_specs = (
                ("66666666-6666-4666-8666-666666666661", result.id, predictions[0].id,
                 PredictionEvaluationOutcome.CONSISTENT),
                ("66666666-6666-4666-8666-666666666662", result_inconsistent.id, predictions[0].id,
                 PredictionEvaluationOutcome.INCONSISTENT),
            )
            for evaluation_id, result_id, prediction_id, outcome in evaluation_specs:
                evaluation = PredictionEvaluation(
                    id=evaluation_id,
                    result_id=result_id,
                    prediction_id=prediction_id,
                    experiment_proposal_id=proposal.id,
                    comparison_conditions="Same bounded test conditions.",
                    assumptions=(),
                    outcome=outcome,
                    rationale="Declared workflow evaluation.",
                    method="phase12-fixture-evaluation",
                    method_version="1",
                    created_at=CREATED,
                )
                store.put_prediction_evaluation(evaluation)
                evaluations.append(evaluation)
            state["evaluations"] = tuple(evaluations)
            return tuple(evaluation.id for evaluation in evaluations)

        def consequence_step(step):
            candidates = state["candidates"]
            evaluations = state["evaluations"]
            consequences = []
            kinds = (
                KnowledgeStateConsequenceKind.SUPPORTS,
                KnowledgeStateConsequenceKind.WEAKENS,
            )
            for candidate, evaluation, kind in zip(candidates, evaluations, kinds):
                consequence = KnowledgeStateConsequence(
                    id=f"77777777-7777-4777-8777-77777777777{len(consequences)+1}",
                    evaluation_ids=(evaluation.id,),
                    target_kind=KnowledgeStateTargetKind.HYPOTHESIS,
                    target_id=candidate.id,
                    consequence=kind,
                    assumptions=(),
                    rationale="Declared workflow knowledge-state consequence.",
                    method="phase12-fixture-consequence",
                    method_version="1",
                    created_at=CREATED,
                )
                store.put_knowledge_state_consequence(consequence)
                consequences.append(consequence)
            state["consequences"] = tuple(consequences)
            return tuple(item.id for item in consequences)

        def renewal_step(step):
            findings = discover_evaluation_tensions(store, created_at=CREATED)
            assert len(findings) == 1
            finding = findings[0]
            store.put_discovery_finding(finding)
            state["renewed"] = finding
            return (finding.id,)

        workflow = WorkflowDefinition(
            id="phase12-discovery-loop",
            name="Finite discovery loop",
            method="phase12-finite-discovery-loop",
            method_version="1",
            input_ids=tuple(record.id for record in records),
            steps=(
                WorkflowStep("step-gap", "gap", "structural-gap", "1", tuple(record.id for record in records)),
                WorkflowStep("step-candidates", "candidates", "candidate-completion", "1"),
                WorkflowStep("step-predictions", "predictions", "discriminating-prediction", "1"),
                WorkflowStep("step-experiment", "experiment", "experiment-proposal", "1"),
                WorkflowStep("step-result", "result", "grounded-result", "1"),
                WorkflowStep("step-evaluation", "evaluation", "prediction-evaluation", "1"),
                WorkflowStep("step-consequence", "consequence", "knowledge-consequence", "1"),
                WorkflowStep("step-renewal", "renewal", "renewed-discovery", "1"),
            ),
        )

        execution = run_workflow(
            workflow,
            {
                "gap": gap_step,
                "candidates": candidates_step,
                "predictions": predictions_step,
                "experiment": experiment_step,
                "result": result_step,
                "evaluation": evaluation_step,
                "consequence": consequence_step,
                "renewal": renewal_step,
            },
            started_at=CREATED,
        )

        assert execution.status == "completed"
        assert [item.status for item in execution.step_results] == ["completed"] * 8
        assert execution.step_results[0].input_ids == workflow.input_ids
        assert execution.step_results[-1].output_ids == (state["renewed"].id,)
        assert state["renewed"].kind is DiscoveryFindingKind.TENSION
        assert all(
            store.get_record(record.id) == record
            for record in records
        )
        assert store.get_record(state["result"].id) == state["result"]
        assert store.get_discovery_finding(state["gap"].id) == state["gap"]

        lineage = execution.lineage_dict()
        assert "started_at" not in lineage
        assert "completed_at" not in lineage
        assert execution.lineage_dict() == execution.lineage_dict()


def test_workflow_failure_is_inspectable_and_stops_without_erasing_prior_steps():
    workflow = WorkflowDefinition(
        id="phase12-failure",
        name="Failure fixture",
        method="phase12-failure-workflow",
        method_version="1",
        input_ids=("grounded-input",),
        steps=(
            WorkflowStep("step-one", "first", "fixture", "1", ("grounded-input",)),
            WorkflowStep("step-two", "missing", "fixture", "1"),
        ),
    )

    calls = []

    def first(step):
        calls.append(step.name)
        return ("generated-one",)

    execution = run_workflow(
        workflow,
        {"first": first},
        started_at=CREATED,
    )

    assert execution.status == "failed"
    assert calls == ["first"]
    assert execution.step_results[0].output_ids == ("generated-one",)
    assert execution.step_results[1].status == "failed"
    assert "no executor declared" in execution.step_results[1].error
