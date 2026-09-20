# Phase 18 — Public Discovery Finding Inspection

**Status:** Complete  
**Phase:** 18

## Goal

Expose the existing persisted `DiscoveryFinding` artifact through Episteme's read-only public scientific instrument.

## Pressure

Phases 14–17 progressively exposed workflow history, artifact-to-execution lineage, relationships, and generated epistemic artifacts. Discovery findings are already persisted, already form part of discovery trails, and already serve as inputs to downstream generated artifacts, but they lacked a direct public retrieval/listing surface.

That leaves an unnecessary gap between:

- a discovery finding identified by a trail or downstream artifact; and
- the finding itself as an inspectable generated artifact.

Phase 18 closes that public-instrument gap without adding new discovery semantics.

## Invariant

> **Public discovery-finding inspection may expose what Episteme discovered and the basis it recorded; it may not turn a generated finding into grounded evidence merely by exposing it.**

A discovery finding remains generated material. Public visibility does not change its epistemic status.

## Boundary

The boundary is:

**persisted DiscoveryFinding → public Python API → read-only CLI / HTTP**

The existing `DiscoveryFinding` model and Store persistence remain authoritative.

## Public Python surface

Phase 18 provides:

- `get_discovery_finding(store, finding_id)`
- `list_discovery_findings(store, kind=None)`

Both return the existing `DiscoveryFinding.to_dict()` representation.

Listings preserve the Store's deterministic ordering and may optionally filter by the existing discovery-finding kind.

Missing findings use the existing `PublicNotFoundError` semantics.

## CLI surface

Read-only commands:

- `discovery <finding_id>`
- `discoveries`
- `discoveries --kind <kind>`

No mutation surface is introduced.

## HTTP surface

Versioned read-only routes:

- `GET /api/v1/discoveries`
- `GET /api/v1/discoveries?kind=<kind>`
- `GET /api/v1/discoveries/{finding_id}`

Unexpected query parameters continue to use the existing HTTP error semantics.

## Scope

Phase 18 includes:

- direct retrieval of persisted discovery findings;
- deterministic listing;
- existing kind filtering;
- read-only CLI inspection;
- read-only `/api/v1` HTTP inspection;
- preservation of the existing serialized finding representation;
- executable tests for the public boundary.

## Out of scope

Phase 18 does not introduce:

- new discovery algorithms;
- new finding kinds;
- inference;
- ranking or universal significance scores;
- truth adjudication;
- mutation;
- a second finding model or store;
- a second provenance graph;
- automatic promotion of findings to grounded evidence;
- replacement of discovery trails, lineage, or reports.

## Exit condition

A researcher can directly inspect a persisted discovery finding and deterministically list existing findings through Episteme's public Python, CLI, and HTTP surfaces, while the finding remains explicitly generated and retains its existing content and provenance relationships.

## Exit Audit

The implemented Phase 18 behavior satisfies the stated exit condition.

- existing persisted `DiscoveryFinding` objects are directly retrievable and listable through the public Python API;
- existing finding kinds can be used as a deterministic listing filter;
- CLI retrieval and listing remain read-only;
- versioned `/api/v1` routes expose retrieval and listing without introducing mutation;
- the public surface returns the existing `DiscoveryFinding.to_dict()` representation rather than creating a second finding representation;
- missing findings retain the existing public not-found behavior;
- discovery trails, lineage, and reports remain separate inspection surfaces;
- generated discovery findings remain generated and do not become grounded evidence through public inspection;
- Phase 18 tests cover Python, CLI, HTTP, deterministic listing/filtering, and missing-resource behavior.

**Status:** Complete.
