# Episteme Public Scientific Instrument

**Status:** Canonical Phase 8 design
**Version:** 0.4
**Last updated:** 2026-09-18

## Purpose

Phase 8 makes Episteme useful outside its development environment without turning the public interface into a second epistemic authority.

The public instrument is an interface to Episteme's existing epistemic machinery.

It must expose provenance, uncertainty, generated status, lineage, and failure rather than hiding them for convenience.

## Core Decision

Phase 8 begins with a **read-oriented scientific workspace**, not an autonomous researcher and not a broad platform.

The first public surface is a small standard-library command-line interface backed by a documented Python read API, with a self-contained browser-readable report renderer.

The first public surface should let a person:

1. inspect grounded knowledge;
2. inspect generated findings and reasoning artifacts;
3. follow provenance and lineage;
4. run deterministic discovery operations over represented knowledge;
5. inspect reproducible discovery trails;
6. export an inspectable report.

The interface does not decide what is true.

## Public API Boundary

The Python public API is read-only over an existing `Store`. It exposes inspection and trail reconstruction without introducing a second persistence model.

The initial operations are:

- inspect a grounded record by identifier;
- list grounded records in deterministic order;
- reconstruct a discovery trail;
- serialize a trail as full JSON or timestamp-independent lineage JSON;
- produce a deterministic inspection report from a discovery finding;
- render that report as a self-contained HTML document.

The CLI is an interface to these operations, not a separate application domain.

## Public Boundary

The public layer sits above the existing Episteme core:

**grounded knowledge → integrity → discovery → hypotheses/predictions → experiment proposals/results/evaluations → public interface**

The interface may request operations from lower layers, but it must not create a parallel knowledge store or reinterpret epistemic status.

## First Capability Set

Phase 8 first implementation should establish:

- a documented programmatic API for core read/query operations;
- a researcher-facing inspection surface;
- provenance and lineage navigation;
- deterministic discovery/report output;
- clear labels separating grounded records from generated artifacts;
- explicit representation of unknown, conflicting, inconclusive, and failed states.

Collaboration, review workflows, broad public ingestion, and additional domain adapters remain later capabilities unless implementation demonstrates that one is required by the first public workflow.

## Scientific Report Boundary

A reproducible discovery report is a presentation of existing Episteme state.

It is not a new epistemic object.

A report should identify:

- repository/state context;
- starting finding or requested subject;
- grounded inputs;
- generated findings and interpretations;
- hypotheses and predictions;
- experiment proposals;
- results and evaluations;
- provenance;
- reproducible lineage representation;
- generation method/version where applicable.

The report must not silently collapse generated interpretation into grounded evidence.


## Public Knowledge Import Architecture

The next Phase 8 capability is **public knowledge import**, but the first implementation remains deliberately narrower than a web-scale ingestion platform.

The importer boundary is:

**external source representation → source-specific adapter → canonical grounded record → ordinary Episteme validation/persistence**

The adapter is responsible for translating an external representation. The core remains responsible for deciding whether the resulting grounded record is structurally admissible.

A public import must preserve the distinction between **what the source said**, **what the adapter translated**, and **what Episteme later infers**.

### Import Contract

An import operation must:

- identify the external source;
- preserve the source location when available;
- preserve source version, publication timestamp, or equivalent source state when available;
- record when Episteme captured the material;
- preserve source-provided content without silently changing its meaning;
- produce canonical grounded records with ordinary provenance;
- validate records before persistence;
- report rejected material explicitly.

An importer must not:

- infer facts that are absent from the source;
- convert source interpretation into independently observed evidence;
- silently repair malformed source data;
- invent missing provenance;
- silently overwrite existing immutable records;
- silently deduplicate records by semantic similarity;
- silently discard source material that cannot be represented.

If an external format contains both observations and interpretations, the adapter must preserve that distinction rather than placing everything into a generic grounded record. Unsupported interpretive material is retained as source material or explicitly rejected; it is not promoted into grounded evidence merely because the format contains it.

### Source and Translation Provenance

Imported records must retain enough provenance to reconstruct two different questions:

1. **Where did the external material originate?**
2. **How did Episteme represent it?**

The first is source provenance. The second is translation provenance.

A source identifier alone is insufficient when the external material can change over time. Where available, the importer should preserve a stable source location plus source version, publication timestamp, revision identifier, content digest, or equivalent source-state marker. The capture timestamp records when Episteme obtained the material.

Translation details belong to the import operation, not to an invented claim about the external world. Where a transformation record is appropriate, it should preserve the source input, adapter name/version, assumptions, output identifiers, timestamp, and validation result.

### Determinism and Re-import

Import translation should be deterministic for a fixed source representation and adapter version.

Re-importing the same source representation must not require semantic deduplication to remain safe. Record identity remains explicit. If an import produces a new UUID on each run, the repeated records are still distinct unless a later, explicitly documented equivalence mechanism is introduced.

An importer may detect exact source-state repetition for operational reporting, but operational duplicate detection must not be confused with epistemic equivalence.

### First Public Import Scope

The first public importer should use a **caller-supplied, finite source representation** rather than discovering and crawling the public web autonomously.

This keeps the first capability testable, reproducible, offline-capable, and explicit about what Episteme actually received.

The initial implementation should therefore establish:

- one documented external source format or fixture;
- one explicit source-to-record adapter;
- preservation of source and capture provenance;
- deterministic translation;
- explicit rejection of unsupported or malformed material;
- re-import behavior that does not overwrite immutable records;
- tests demonstrating that generated interpretations are not promoted during import.

Network discovery, authentication, rate limiting, crawling, source ranking, universal format support, and web-scale scheduling remain separate decisions.


## Public Ingestion Boundary

Public knowledge imports remain subject to the existing grounded ingestion rules.

A public importer may adapt an external format into canonical Episteme records.

It must not:

- infer missing facts;
- repair malformed evidence silently;
- manufacture provenance;
- promote generated interpretations;
- overwrite immutable grounded records;
- silently deduplicate records by semantic similarity.

## Review Boundary

Human review is an explicit activity over represented material.

A review interface may record an assessment or other existing/generated artifact where the architecture supports it.

A reviewer action must not mutate the underlying grounded evidence merely by being performed.

## Transparency Requirements

A public-facing operation should make it possible to answer:

- What did Episteme receive?
- What did it generate?
- Which method and version produced this?
- Which grounded inputs were used?
- What remains unknown or unresolved?
- What result was actually observed?
- How was that result evaluated?
- Can the lineage be reconstructed?

Convenience must not erase these distinctions.

## Deferred

Phase 8 does not yet establish:

- autonomous scientific agency;
- automatic truth adjudication;
- a universal web-scale ingestion system;
- a universal ontology;
- a universal statistical framework;
- autonomous laboratory control;
- a mandatory frontend framework;
- a distributed deployment architecture.

Those remain separate decisions.

## Researcher Workflow

The intended first-use workflow is deliberately simple:

1. **Start with a subject or discovery finding.**
   Use a known record or finding identifier rather than asking the interface to invent context.
2. **Inspect the grounded material.**
   Records show what Episteme received or recorded, including provenance.
3. **Inspect the generated reasoning chain.**
   A discovery trail connects findings to hypotheses, predictions, experiment proposals, results, evaluations, and explicit knowledge-state consequences where those objects exist.
4. **Check the boundary.**
   The report separates grounded records from generated artifacts. Generated material is never presented as independently grounded evidence.
5. **Follow lineage.**
   The lineage representation removes generation timestamps so the structural chain can be compared reproducibly.
6. **Export the report.**
   The deterministic report is suitable for inspection, archival by the caller, or use as input to another tool.

The interface is therefore an inspection instrument first. It does not require the researcher to understand SQLite, internal Python classes, or the implementation of the discovery algorithms.

### Browser-Readable Surface

The first researcher-facing surface beyond terminal output is a self-contained HTML rendering of an existing discovery report. It requires no web server, JavaScript framework, external assets, or network connection. The renderer presents the same report data rather than creating a second representation of epistemic state.

Programmatically, `render_discovery_report_html(report)` converts an existing public report into a browser-readable document. From the CLI, `report` accepts `--html <path>` to write that document.

The HTML surface is intentionally read-only and keeps the same four major views visible: grounded records, generated artifacts, the full trail, and reproducible lineage.

### Public Acceptance Test

The public surface is tested against a complete representative cycle:

**grounded observation → discovery finding → hypothesis → prediction → experiment proposal → grounded result → prediction evaluation → knowledge-state consequence → renewed discovery finding**

The acceptance test verifies that the resulting report contains both grounded records and generated artifacts, preserves their distinction, and exposes reproducible lineage. This test is an interface contract, not merely an internal implementation test.

## Initial Exit Condition

The first Phase 8 implementation is successful when a person outside the development workflow can inspect a complete Episteme discovery cycle through a documented public interface and reconstruct why each generated step exists without losing the grounded/generated boundary.

## CLI Entry Point

When Episteme is installed, the public inspection surface is also available as the `episteme` command.

The CLI is read-only. It does not provide commands for modifying the store.

Examples:

- `episteme --store path/to/episteme.sqlite records`
- `episteme --store path/to/episteme.sqlite records --kind measurement`
- `episteme --store path/to/episteme.sqlite record <record-id>`
- `episteme --store path/to/episteme.sqlite trail <finding-id> --created-at <timestamp>`
- `episteme --store path/to/episteme.sqlite lineage <finding-id> --created-at <timestamp>`
- `episteme --store path/to/episteme.sqlite report <finding-id> --created-at <timestamp>`
- `episteme --store path/to/episteme.sqlite report <finding-id> --created-at <timestamp> --html report.html`

The module form, `python -m episteme`, remains available and exposes the same surface.
