# Phase 23 — Public Captured Content Inspection

**Status:** Canonical

## Goal

Expose the exact immutable captured representation itself through Episteme's existing read-only public scientific instrument.

## Pressure

Phase 21 made capture metadata publicly inspectable, while intentionally leaving captured content private. Phase 22 then made the persisted capture the authoritative material behind content-bound grounded ingestion.

A researcher can therefore inspect a capture's identity and digest, but cannot yet retrieve the exact representation Episteme received through the public instrument.

## Invariant

> **Public captured-content inspection exposes the exact persisted representation; it does not interpret, alter, reacquire, or promote that representation to epistemic authority.**

## Boundary

**public content request → capture identity → existing persisted capture → digest-verified immutable bytes**

The public surface reads the existing capture store. It does not create a second content store or acquisition path.

## Representation

The public content surface returns the stored bytes unchanged.

The capture's persisted media_type is used as the HTTP response media type. When no media type was captured, the public HTTP surface uses application/octet-stream.

No JSON/base64 wrapping is introduced for the HTTP representation.

## Configuration

The existing Store already requires an explicit capture_root when captured content is read.

The public CLI and HTTP server therefore accept an explicit --capture-root / capture_root configuration. Episteme does not guess a filesystem location from the SQLite database path.

Metadata-only capture inspection remains usable without a capture root.

A content request without a configured or readable capture root fails rather than silently substituting another location.

## Public Surfaces

Python:

- get_captured_content(store, capture_id) returns (bytes, media_type).

CLI:

- capture-content <capture_id> --output PATH writes the exact bytes to the requested file;
- without --output, the exact bytes are written to stdout.

HTTP:

- GET /api/v1/captures/{id}/content

The HTTP route is read-only and rejects query parameters.

## Integrity

Content is obtained through the existing Store.read_captured_content() boundary, which verifies the persisted SHA-256 digest before returning bytes.

The public surface therefore does not introduce a second integrity check or a second representation of content identity.

## Failure Semantics

Missing capture, failed capture without content, missing capture-root configuration, missing content, and digest verification failures remain failures of content inspection. They do not create, modify, reinterpret, or suppress capture records.

## Epistemic Boundary

A public captured representation remains a record of what Episteme received.

Making the exact bytes inspectable does not make them scientific evidence, a grounded record, or an endorsed source.

## Scope

Phase 23 establishes:

- exact raw captured-content inspection;
- explicit capture-root configuration for public content access;
- Python, CLI, and HTTP read surfaces;
- media-type preservation on HTTP;
- reuse of the existing digest-verified content read;
- executable tests for raw-content inspection and failure behavior.

## Out of Scope

Phase 23 does not establish:

- acquisition or re-fetching;
- content mutation;
- interpretation or decoding;
- automatic ingestion;
- evidence promotion;
- content transformation;
- range requests or streaming protocols;
- authentication or authorization;
- caching policy;
- distributed content storage;
- archival policy;
- new provenance or lineage models.

## Exit Condition

A researcher can retrieve the exact immutable bytes associated with a persisted capture through Episteme's public Python, CLI, and HTTP surfaces, with explicit capture-root configuration, preserved media type, existing digest verification, deterministic failure behavior, and no change to the capture's epistemic status.
