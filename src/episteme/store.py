"""SQLite persistence for the Phase 1 grounded knowledge substrate."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Iterator

from .model import (
    Record,
    Relationship,
    canonical_json,
)


class Store:
    """Repository-owned SQLite store for grounded records and relationships."""

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
            """
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
        import json

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

    def put_relationship(self, relationship: Relationship) -> None:
        missing = [
            record_id
            for record_id in (relationship.subject_id, relationship.object_id)
            if self.get_record(record_id) is None
        ]
        if missing:
            raise ValueError(
                "relationship references missing record(s): "
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
        import json

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

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
