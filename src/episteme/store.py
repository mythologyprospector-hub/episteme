"""SQLite persistence for grounded knowledge, integrity records, and discovery artifacts."""

from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from typing import Iterator

from .model import (
    AssessmentTargetKind,
    DiscoveryFinding,
    Hypothesis,
    Model,
    Prediction,
    ExperimentProposal,
    EvidenceAssessment,
    LifecycleEvent,
    Record,
    Relationship,
    Transformation,
    canonical_json,
)


class Store:
    """Repository-owned SQLite store for grounded and derived Episteme state."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def _initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                provenance TEXT NOT NULL,
                created_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object_id TEXT NOT NULL,
                provenance TEXT NOT NULL,
                created_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL,
                FOREIGN KEY(subject_id) REFERENCES records(id),
                FOREIGN KEY(object_id) REFERENCES records(id)
            );

            CREATE INDEX IF NOT EXISTS idx_records_kind
                ON records(kind);

            CREATE INDEX IF NOT EXISTS idx_relationships_subject
                ON relationships(subject_id);

            CREATE INDEX IF NOT EXISTS idx_relationships_object
                ON relationships(object_id);

            CREATE TABLE IF NOT EXISTS lifecycle_events (
                id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                provenance TEXT NOT NULL,
                replacement_record_id TEXT,
                reason TEXT,
                schema_version INTEGER NOT NULL,
                FOREIGN KEY(record_id) REFERENCES records(id),
                FOREIGN KEY(replacement_record_id) REFERENCES records(id)
            );

            CREATE TABLE IF NOT EXISTS evidence_assessments (
                id TEXT PRIMARY KEY,
                target_kind TEXT NOT NULL,
                target_id TEXT NOT NULL,
                method TEXT NOT NULL,
                basis TEXT NOT NULL,
                rationale TEXT NOT NULL,
                provenance TEXT NOT NULL,
                assessed_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discovery_findings (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                input_ids TEXT NOT NULL,
                method TEXT NOT NULL,
                method_version TEXT NOT NULL,
                rationale TEXT NOT NULL,
                measures TEXT NOT NULL,
                created_at TEXT NOT NULL,
                related_finding_id TEXT,
                expectation TEXT,
                schema_version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                statement TEXT NOT NULL,
                finding_ids TEXT NOT NULL,
                input_ids TEXT NOT NULL,
                method TEXT NOT NULL,
                method_version TEXT NOT NULL,
                rationale TEXT NOT NULL,
                assumptions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                hypothesis_ids TEXT NOT NULL,
                input_ids TEXT NOT NULL,
                assumptions TEXT NOT NULL,
                method TEXT NOT NULL,
                method_version TEXT NOT NULL,
                rationale TEXT NOT NULL,
                created_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                consequence TEXT NOT NULL,
                conditions TEXT NOT NULL,
                assumptions TEXT NOT NULL,
                method TEXT NOT NULL,
                method_version TEXT NOT NULL,
                rationale TEXT NOT NULL,
                comparison_hypothesis_ids TEXT NOT NULL,
                created_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS experiment_proposals (
                id TEXT PRIMARY KEY,
                prediction_ids TEXT NOT NULL,
                objective TEXT NOT NULL,
                proposed_observation TEXT NOT NULL,
                discrimination_basis TEXT NOT NULL,
                conditions TEXT NOT NULL,
                assumptions TEXT NOT NULL,
                method TEXT NOT NULL,
                method_version TEXT NOT NULL,
                rationale TEXT NOT NULL,
                created_at TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transformations (
                id TEXT PRIMARY KEY,
                input_ids TEXT NOT NULL,
                operation TEXT NOT NULL,
                operation_version TEXT NOT NULL,
                assumptions TEXT NOT NULL,
                output_ids TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                validation_result TEXT NOT NULL,
                provenance TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );
            """
        )
        discovery_columns = {
            row["name"]
            for row in self._connection.execute("PRAGMA table_info(discovery_findings)")
        }
        if "expectation" not in discovery_columns:
            self._connection.execute(
                "ALTER TABLE discovery_findings ADD COLUMN expectation TEXT"
            )
        self._connection.commit()

    def put_record(self, record: Record) -> None:
        self._connection.execute(
            """
            INSERT INTO records
                (id, kind, payload, provenance, created_at, schema_version)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.kind.value,
                canonical_json(dict(record.payload)),
                canonical_json([item.to_dict() for item in record.provenance]),
                record.created_at,
                record.schema_version,
            ),
        )
        self._connection.commit()

    def get_record(self, record_id: str) -> Record | None:
        row = self._connection.execute(
            """
            SELECT id, kind, payload, provenance, created_at, schema_version
            FROM records
            WHERE id = ?
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return Record.from_dict(
            {
                "id": row["id"],
                "kind": row["kind"],
                "payload": json.loads(row["payload"]),
                "provenance": json.loads(row["provenance"]),
                "created_at": row["created_at"],
                "schema_version": row["schema_version"],
            }
        )

    def iter_records(self, kind: str | None = None) -> Iterator[Record]:
        import json

        if kind is None:
            rows = self._connection.execute(
                """
                SELECT id, kind, payload, provenance, created_at, schema_version
                FROM records
                ORDER BY created_at, id
                """
            )
        else:
            rows = self._connection.execute(
                """
                SELECT id, kind, payload, provenance, created_at, schema_version
                FROM records
                WHERE kind = ?
                ORDER BY created_at, id
                """,
                (kind,),
            )

        for row in rows:
            yield Record.from_dict(
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "payload": json.loads(row["payload"]),
                    "provenance": json.loads(row["provenance"]),
                    "created_at": row["created_at"],
                    "schema_version": row["schema_version"],
                }
            )

    def _object_exists(self, object_id: str) -> bool:
        """Return whether an ID exists in any persisted epistemic collection."""
        tables = (
            "records",
            "relationships",
            "lifecycle_events",
            "evidence_assessments",
            "transformations",
            "discovery_findings",
            "hypotheses",
            "models",
            "predictions",
            "experiment_proposals",
        )
        return any(
            self._connection.execute(
                f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1",
                (object_id,),
            ).fetchone()
            is not None
            for table in tables
        )

    def put_relationship(self, relationship: Relationship) -> None:
        missing = [
            object_id
            for object_id in (relationship.subject_id, relationship.object_id)
            if not self._object_exists(object_id)
        ]
        if missing:
            raise ValueError(
                "relationship references missing object(s): "
                + ", ".join(missing)
            )

        self._connection.execute(
            """
            INSERT INTO relationships
                (id, subject_id, predicate, object_id, provenance, created_at, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                relationship.id,
                relationship.subject_id,
                relationship.predicate,
                relationship.object_id,
                canonical_json([item.to_dict() for item in relationship.provenance]),
                relationship.created_at,
                relationship.schema_version,
            ),
        )
        self._connection.commit()

    def iter_relationships(self, predicate: str | None = None) -> Iterator[Relationship]:
        if predicate is None:
            rows = self._connection.execute(
                """
                SELECT id, subject_id, predicate, object_id, provenance, created_at, schema_version
                FROM relationships
                ORDER BY created_at, id
                """
            )
        else:
            rows = self._connection.execute(
                """
                SELECT id, subject_id, predicate, object_id, provenance, created_at, schema_version
                FROM relationships
                WHERE predicate = ?
                ORDER BY created_at, id
                """,
                (predicate,),
            )

        for row in rows:
            yield Relationship.from_dict(
                {
                    "id": row["id"],
                    "subject_id": row["subject_id"],
                    "predicate": row["predicate"],
                    "object_id": row["object_id"],
                    "provenance": json.loads(row["provenance"]),
                    "created_at": row["created_at"],
                    "schema_version": row["schema_version"],
                }
            )

    def get_relationship(self, relationship_id: str) -> Relationship | None:
        row = self._connection.execute(
            """
            SELECT id, subject_id, predicate, object_id, provenance, created_at, schema_version
            FROM relationships
            WHERE id = ?
            """,
            (relationship_id,),
        ).fetchone()
        if row is None:
            return None
        return Relationship.from_dict(
            {
                "id": row["id"],
                "subject_id": row["subject_id"],
                "predicate": row["predicate"],
                "object_id": row["object_id"],
                "provenance": json.loads(row["provenance"]),
                "created_at": row["created_at"],
                "schema_version": row["schema_version"],
            }
        )


    def put_discovery_finding(self, finding: DiscoveryFinding) -> None:
        missing = [
            input_id
            for input_id in finding.input_ids
            if self.get_record(input_id) is None and self.get_relationship(input_id) is None
        ]
        if missing:
            raise ValueError(
                "discovery finding references missing input(s): " + ", ".join(missing)
            )
        if finding.related_finding_id is not None and self.get_discovery_finding(finding.related_finding_id) is None:
            raise ValueError(
                "discovery finding references missing related finding: "
                + finding.related_finding_id
            )

        self._connection.execute(
            """
            INSERT INTO discovery_findings
                (id, kind, title, description, input_ids, method, method_version,
                 rationale, measures, created_at, related_finding_id, expectation, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                finding.id,
                finding.kind.value,
                finding.title,
                finding.description,
                canonical_json(list(finding.input_ids)),
                finding.method,
                finding.method_version,
                finding.rationale,
                canonical_json([measure.to_dict() for measure in finding.measures]),
                finding.created_at,
                finding.related_finding_id,
                canonical_json(list(finding.expectation)) if finding.expectation is not None else None,
                finding.schema_version,
            ),
        )
        self._connection.commit()

    def get_discovery_finding(self, finding_id: str) -> DiscoveryFinding | None:
        row = self._connection.execute(
            """
            SELECT id, kind, title, description, input_ids, method, method_version,
                   rationale, measures, created_at, related_finding_id, expectation, schema_version
            FROM discovery_findings
            WHERE id = ?
            """,
            (finding_id,),
        ).fetchone()
        if row is None:
            return None

        return DiscoveryFinding.from_dict(
            {
                "id": row["id"],
                "kind": row["kind"],
                "title": row["title"],
                "description": row["description"],
                "input_ids": json.loads(row["input_ids"]),
                "method": row["method"],
                "method_version": row["method_version"],
                "rationale": row["rationale"],
                "measures": json.loads(row["measures"]),
                "created_at": row["created_at"],
                "related_finding_id": row["related_finding_id"],
                "expectation": json.loads(row["expectation"]) if row["expectation"] is not None else None,
                "schema_version": row["schema_version"],
            }
        )

    def iter_discovery_findings(self, kind: str | None = None) -> Iterator[DiscoveryFinding]:
        if kind is None:
            rows = self._connection.execute(
                """
                SELECT id, kind, title, description, input_ids, method, method_version,
                       rationale, measures, created_at, related_finding_id, expectation, schema_version
                FROM discovery_findings
                ORDER BY created_at, id
                """
            )
        else:
            rows = self._connection.execute(
                """
                SELECT id, kind, title, description, input_ids, method, method_version,
                       rationale, measures, created_at, related_finding_id, expectation, schema_version
                FROM discovery_findings
                WHERE kind = ?
                ORDER BY created_at, id
                """,
                (kind,),
            )

        for row in rows:
            yield DiscoveryFinding.from_dict(
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "title": row["title"],
                    "description": row["description"],
                    "input_ids": json.loads(row["input_ids"]),
                    "method": row["method"],
                    "method_version": row["method_version"],
                    "rationale": row["rationale"],
                    "measures": json.loads(row["measures"]),
                    "created_at": row["created_at"],
                    "related_finding_id": row["related_finding_id"],
                    "expectation": json.loads(row["expectation"]) if row["expectation"] is not None else None,
                    "schema_version": row["schema_version"],
                }
            )

    def put_hypothesis(self, hypothesis: Hypothesis) -> None:
        missing_findings = [
            finding_id for finding_id in hypothesis.finding_ids
            if self.get_discovery_finding(finding_id) is None
        ]
        if missing_findings:
            raise ValueError("hypothesis references missing finding(s): " + ", ".join(missing_findings))
        missing_inputs = [
            input_id for input_id in hypothesis.input_ids
            if self.get_record(input_id) is None and self.get_relationship(input_id) is None
        ]
        if missing_inputs:
            raise ValueError("hypothesis references missing input(s): " + ", ".join(missing_inputs))
        self._connection.execute(
            """INSERT INTO hypotheses
               (id, statement, finding_ids, input_ids, method, method_version,
                rationale, assumptions, created_at, schema_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (hypothesis.id, hypothesis.statement,
             canonical_json(list(hypothesis.finding_ids)),
             canonical_json(list(hypothesis.input_ids)), hypothesis.method,
             hypothesis.method_version, hypothesis.rationale,
             canonical_json(list(hypothesis.assumptions)), hypothesis.created_at,
             hypothesis.schema_version),
        )
        self._connection.commit()

    def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        row = self._connection.execute(
            """SELECT id, statement, finding_ids, input_ids, method, method_version,
                      rationale, assumptions, created_at, schema_version
               FROM hypotheses WHERE id = ?""", (hypothesis_id,)
        ).fetchone()
        if row is None:
            return None
        return Hypothesis.from_dict({
            "id": row["id"], "statement": row["statement"],
            "finding_ids": json.loads(row["finding_ids"]),
            "input_ids": json.loads(row["input_ids"]),
            "method": row["method"], "method_version": row["method_version"],
            "rationale": row["rationale"], "assumptions": json.loads(row["assumptions"]),
            "created_at": row["created_at"], "schema_version": row["schema_version"],
        })

    def iter_hypotheses(self) -> Iterator[Hypothesis]:
        rows = self._connection.execute(
            """SELECT id, statement, finding_ids, input_ids, method, method_version,
                      rationale, assumptions, created_at, schema_version
               FROM hypotheses ORDER BY created_at, id"""
        )
        for row in rows:
            yield Hypothesis.from_dict({
                "id": row["id"], "statement": row["statement"],
                "finding_ids": json.loads(row["finding_ids"]),
                "input_ids": json.loads(row["input_ids"]),
                "method": row["method"], "method_version": row["method_version"],
                "rationale": row["rationale"], "assumptions": json.loads(row["assumptions"]),
                "created_at": row["created_at"], "schema_version": row["schema_version"],
            })

    def put_model(self, model: Model) -> None:
        missing_hypotheses = [
            hypothesis_id for hypothesis_id in model.hypothesis_ids
            if self.get_hypothesis(hypothesis_id) is None
        ]
        if missing_hypotheses:
            raise ValueError("model references missing hypothesis(es): " + ", ".join(missing_hypotheses))
        missing_inputs = [
            input_id for input_id in model.input_ids
            if self.get_record(input_id) is None and self.get_relationship(input_id) is None
        ]
        if missing_inputs:
            raise ValueError("model references missing input(s): " + ", ".join(missing_inputs))
        self._connection.execute(
            """INSERT INTO models
               (id, description, hypothesis_ids, input_ids, assumptions, method,
                method_version, rationale, created_at, schema_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (model.id, model.description, canonical_json(list(model.hypothesis_ids)),
             canonical_json(list(model.input_ids)), canonical_json(list(model.assumptions)),
             model.method, model.method_version, model.rationale, model.created_at,
             model.schema_version),
        )
        self._connection.commit()

    def get_model(self, model_id: str) -> Model | None:
        row = self._connection.execute(
            """SELECT id, description, hypothesis_ids, input_ids, assumptions, method,
                      method_version, rationale, created_at, schema_version
               FROM models WHERE id = ?""", (model_id,)
        ).fetchone()
        if row is None:
            return None
        return Model.from_dict({
            "id": row["id"], "description": row["description"],
            "hypothesis_ids": json.loads(row["hypothesis_ids"]),
            "input_ids": json.loads(row["input_ids"]),
            "assumptions": json.loads(row["assumptions"]),
            "method": row["method"], "method_version": row["method_version"],
            "rationale": row["rationale"], "created_at": row["created_at"],
            "schema_version": row["schema_version"],
        })

    def iter_models(self) -> Iterator[Model]:
        rows = self._connection.execute(
            """SELECT id, description, hypothesis_ids, input_ids, assumptions, method,
                      method_version, rationale, created_at, schema_version
               FROM models ORDER BY created_at, id"""
        )
        for row in rows:
            yield Model.from_dict({
                "id": row["id"], "description": row["description"],
                "hypothesis_ids": json.loads(row["hypothesis_ids"]),
                "input_ids": json.loads(row["input_ids"]),
                "assumptions": json.loads(row["assumptions"]),
                "method": row["method"], "method_version": row["method_version"],
                "rationale": row["rationale"], "created_at": row["created_at"],
                "schema_version": row["schema_version"],
            })

    def put_prediction(self, prediction: Prediction) -> None:
        if self.get_hypothesis(prediction.source_id) is None and self.get_model(prediction.source_id) is None:
            raise ValueError("prediction references missing hypothesis or model: " + prediction.source_id)
        missing_comparisons = [
            hypothesis_id for hypothesis_id in prediction.comparison_hypothesis_ids
            if self.get_hypothesis(hypothesis_id) is None
        ]
        if missing_comparisons:
            raise ValueError("prediction references missing comparison hypothesis(es): " + ", ".join(missing_comparisons))
        self._connection.execute(
            """INSERT INTO predictions
               (id, source_id, consequence, conditions, assumptions, method,
                method_version, rationale, comparison_hypothesis_ids, created_at,
                schema_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (prediction.id, prediction.source_id, prediction.consequence,
             prediction.conditions, canonical_json(list(prediction.assumptions)),
             prediction.method, prediction.method_version, prediction.rationale,
             canonical_json(list(prediction.comparison_hypothesis_ids)),
             prediction.created_at, prediction.schema_version),
        )
        self._connection.commit()

    def get_prediction(self, prediction_id: str) -> Prediction | None:
        row = self._connection.execute(
            """SELECT id, source_id, consequence, conditions, assumptions, method,
                      method_version, rationale, comparison_hypothesis_ids,
                      created_at, schema_version
               FROM predictions WHERE id = ?""", (prediction_id,)
        ).fetchone()
        if row is None:
            return None
        return Prediction.from_dict({
            "id": row["id"], "source_id": row["source_id"],
            "consequence": row["consequence"], "conditions": row["conditions"],
            "assumptions": json.loads(row["assumptions"]), "method": row["method"],
            "method_version": row["method_version"], "rationale": row["rationale"],
            "comparison_hypothesis_ids": json.loads(row["comparison_hypothesis_ids"]),
            "created_at": row["created_at"], "schema_version": row["schema_version"],
        })

    def iter_predictions(self) -> Iterator[Prediction]:
        rows = self._connection.execute(
            """SELECT id, source_id, consequence, conditions, assumptions, method,
                      method_version, rationale, comparison_hypothesis_ids,
                      created_at, schema_version
               FROM predictions ORDER BY created_at, id"""
        )
        for row in rows:
            yield Prediction.from_dict({
                "id": row["id"], "source_id": row["source_id"],
                "consequence": row["consequence"], "conditions": row["conditions"],
                "assumptions": json.loads(row["assumptions"]), "method": row["method"],
                "method_version": row["method_version"], "rationale": row["rationale"],
                "comparison_hypothesis_ids": json.loads(row["comparison_hypothesis_ids"]),
                "created_at": row["created_at"], "schema_version": row["schema_version"],
            })


    def put_experiment_proposal(self, proposal: ExperimentProposal) -> None:
        missing = [
            prediction_id for prediction_id in proposal.prediction_ids
            if self.get_prediction(prediction_id) is None
        ]
        if missing:
            raise ValueError(
                "experiment proposal references missing prediction(s): "
                + ", ".join(missing)
            )
        self._connection.execute(
            """INSERT INTO experiment_proposals
               (id, prediction_ids, objective, proposed_observation, discrimination_basis, conditions,
                assumptions, method, method_version, rationale, created_at, schema_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (proposal.id, canonical_json(list(proposal.prediction_ids)),
             proposal.objective, proposal.proposed_observation, proposal.discrimination_basis, proposal.conditions,
             canonical_json(list(proposal.assumptions)), proposal.method,
             proposal.method_version, proposal.rationale, proposal.created_at,
             proposal.schema_version),
        )
        self._connection.commit()

    def get_experiment_proposal(self, proposal_id: str) -> ExperimentProposal | None:
        row = self._connection.execute(
            """SELECT id, prediction_ids, objective, proposed_observation, discrimination_basis, conditions,
                      assumptions, method, method_version, rationale, created_at, schema_version
               FROM experiment_proposals WHERE id = ?""", (proposal_id,)
        ).fetchone()
        if row is None:
            return None
        return ExperimentProposal.from_dict({
            "id": row["id"], "prediction_ids": json.loads(row["prediction_ids"]),
            "objective": row["objective"], "proposed_observation": row["proposed_observation"],
            "discrimination_basis": row["discrimination_basis"], "conditions": row["conditions"], "assumptions": json.loads(row["assumptions"]),
            "method": row["method"], "method_version": row["method_version"],
            "rationale": row["rationale"], "created_at": row["created_at"],
            "schema_version": row["schema_version"],
        })

    def iter_experiment_proposals(self) -> Iterator[ExperimentProposal]:
        rows = self._connection.execute(
            """SELECT id, prediction_ids, objective, proposed_observation, discrimination_basis, conditions,
                      assumptions, method, method_version, rationale, created_at, schema_version
               FROM experiment_proposals ORDER BY created_at, id"""
        )
        for row in rows:
            yield ExperimentProposal.from_dict({
                "id": row["id"], "prediction_ids": json.loads(row["prediction_ids"]),
                "objective": row["objective"], "proposed_observation": row["proposed_observation"],
                "discrimination_basis": row["discrimination_basis"], "conditions": row["conditions"], "assumptions": json.loads(row["assumptions"]),
                "method": row["method"], "method_version": row["method_version"],
                "rationale": row["rationale"], "created_at": row["created_at"],
                "schema_version": row["schema_version"],
            })

    def put_lifecycle_event(self, event: LifecycleEvent) -> None:
        if self.get_record(event.record_id) is None:
            raise ValueError(f"lifecycle event references missing record: {event.record_id}")
        if event.replacement_record_id is not None and self.get_record(event.replacement_record_id) is None:
            raise ValueError(
                "lifecycle event references missing replacement record: "
                + event.replacement_record_id
            )

        self._connection.execute(
            """
            INSERT INTO lifecycle_events
                (id, record_id, kind, occurred_at, provenance, replacement_record_id, reason, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.record_id,
                event.kind.value,
                event.occurred_at,
                canonical_json([item.to_dict() for item in event.provenance]),
                event.replacement_record_id,
                event.reason,
                event.schema_version,
            ),
        )
        self._connection.commit()

    def iter_lifecycle_events(self, record_id: str | None = None) -> Iterator[LifecycleEvent]:
        if record_id is None:
            rows = self._connection.execute(
                """
                SELECT id, record_id, kind, occurred_at, provenance,
                       replacement_record_id, reason, schema_version
                FROM lifecycle_events
                ORDER BY occurred_at, id
                """
            )
        else:
            rows = self._connection.execute(
                """
                SELECT id, record_id, kind, occurred_at, provenance,
                       replacement_record_id, reason, schema_version
                FROM lifecycle_events
                WHERE record_id = ?
                ORDER BY occurred_at, id
                """,
                (record_id,),
            )

        for row in rows:
            yield LifecycleEvent.from_dict(
                {
                    "id": row["id"],
                    "record_id": row["record_id"],
                    "kind": row["kind"],
                    "occurred_at": row["occurred_at"],
                    "provenance": json.loads(row["provenance"]),
                    "replacement_record_id": row["replacement_record_id"],
                    "reason": row["reason"],
                    "schema_version": row["schema_version"],
                }
            )

    def put_evidence_assessment(self, assessment: EvidenceAssessment) -> None:
        if assessment.target_kind is AssessmentTargetKind.RECORD:
            exists = self.get_record(assessment.target_id) is not None
        else:
            exists = self.get_relationship(assessment.target_id) is not None

        if not exists:
            raise ValueError(
                f"assessment references missing {assessment.target_kind.value}: "
                + assessment.target_id
            )

        self._connection.execute(
            """
            INSERT INTO evidence_assessments
                (id, target_kind, target_id, method, basis, rationale,
                 provenance, assessed_at, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment.id,
                assessment.target_kind.value,
                assessment.target_id,
                assessment.method,
                assessment.basis,
                assessment.rationale,
                canonical_json([item.to_dict() for item in assessment.provenance]),
                assessment.assessed_at,
                assessment.schema_version,
            ),
        )
        self._connection.commit()

    def get_evidence_assessment(self, assessment_id: str) -> EvidenceAssessment | None:
        row = self._connection.execute(
            """
            SELECT id, target_kind, target_id, method, basis, rationale,
                   provenance, assessed_at, schema_version
            FROM evidence_assessments
            WHERE id = ?
            """,
            (assessment_id,),
        ).fetchone()
        if row is None:
            return None

        return EvidenceAssessment.from_dict(
            {
                "id": row["id"],
                "target_kind": row["target_kind"],
                "target_id": row["target_id"],
                "method": row["method"],
                "basis": row["basis"],
                "rationale": row["rationale"],
                "provenance": json.loads(row["provenance"]),
                "assessed_at": row["assessed_at"],
                "schema_version": row["schema_version"],
            }
        )

    def put_transformation(self, transformation: Transformation) -> None:
        record_ids = (*transformation.input_ids, *transformation.output_ids)
        missing = [record_id for record_id in record_ids if self.get_record(record_id) is None]
        if missing:
            raise ValueError(
                "transformation references missing record(s): " + ", ".join(missing)
            )

        self._connection.execute(
            """
            INSERT INTO transformations
                (id, input_ids, operation, operation_version, assumptions,
                 output_ids, executed_at, validation_result, provenance, schema_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transformation.id,
                canonical_json(list(transformation.input_ids)),
                transformation.operation,
                transformation.operation_version,
                canonical_json(list(transformation.assumptions)),
                canonical_json(list(transformation.output_ids)),
                transformation.executed_at,
                transformation.validation_result,
                canonical_json([item.to_dict() for item in transformation.provenance]),
                transformation.schema_version,
            ),
        )
        self._connection.commit()

    def get_transformation(self, transformation_id: str) -> Transformation | None:
        row = self._connection.execute(
            """
            SELECT id, input_ids, operation, operation_version, assumptions,
                   output_ids, executed_at, validation_result, provenance, schema_version
            FROM transformations
            WHERE id = ?
            """,
            (transformation_id,),
        ).fetchone()
        if row is None:
            return None

        return Transformation.from_dict(
            {
                "id": row["id"],
                "input_ids": json.loads(row["input_ids"]),
                "operation": row["operation"],
                "operation_version": row["operation_version"],
                "assumptions": json.loads(row["assumptions"]),
                "output_ids": json.loads(row["output_ids"]),
                "executed_at": row["executed_at"],
                "validation_result": row["validation_result"],
                "provenance": json.loads(row["provenance"]),
                "schema_version": row["schema_version"],
            }
        )

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
