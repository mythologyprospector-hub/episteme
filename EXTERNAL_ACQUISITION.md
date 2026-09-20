# Phase 20 — External Acquisition

**Status:** Canonical design  
**Phase:** 20  
**Depends on:** Phase 11 Grounded Evidence Ingestion; Phase 19 External Acquisition / Captured Representation

## Goal

Establish the smallest provider-neutral boundary by which Episteme can request a bounded external resource and turn the resulting external response into a Phase 19 captured representation.

Phase 20 is about **retrieval**, not interpretation.

The acquisition layer answers:

> What did Episteme ask an external source for, what happened when it asked, and what representation did the source return?

The existing Phase 11 adapter answers a different question:

> How can that captured representation be deterministically translated into grounded Episteme records?

These responsibilities remain separate.

## Pressure

Phase 19 established durable storage for externally captured material, but no component yet performs the external interaction that produces a capture.

Without an acquisition boundary, Episteme can preserve material after it has been supplied to it, but cannot itself perform a bounded, inspectable retrieval.

The missing boundary is therefore:

**declared acquisition request → external provider → acquisition result → Phase 19 capture**

followed by the existing:

**captured representation → source adapter → grounded SOURCE record**

## Core Invariant

> **External acquisition records the interaction with an external source; it does not interpret the retrieved material or grant it epistemic authority.**

A successful acquisition therefore produces a captured representation, not a claim, hypothesis, discovery finding, or other epistemic artifact.

## Acquisition Contract

An acquisition operation has four conceptual parts:

1. **Request** — a bounded declaration of the external resource to retrieve.
2. **Provider capability** — the mechanism that performs the external interaction.
3. **Acquisition result** — the observed response and outcome.
4. **Capture handoff** — conversion of the received representation into the existing Phase 19 capture boundary.

The contract must preserve, at minimum:

- provider/source identity;
- requested resource;
- request parameters sufficient to explain the request;
- acquisition method and method version;
- capture timestamp;
- response status when available;
- response media type when available;
- source-provided version when available;
- received content when any content was obtained;
- complete, partial, or failed outcome;
- an explicit failure description when acquisition fails.

The acquisition layer must not silently manufacture missing source metadata. When an external source does not provide a value, the corresponding capture field remains absent.

## Bounded Retrieval

Phase 20 establishes **explicit, finite acquisition**, not autonomous crawling.

An acquisition request must identify a bounded resource or bounded provider operation.

The initial implementation must not establish:

- recursive crawling;
- unbounded pagination;
- autonomous source discovery;
- source ranking;
- relevance scoring;
- scheduling;
- background harvesting;
- model-directed browsing.

If a provider operation can return an unbounded result set, the acquisition boundary must make the selected finite request explicit rather than silently treating the provider as an infinite corpus.

## Provider Boundary

Provider-specific behavior lives outside the stable epistemic primitives.

A provider capability may know:

- how to construct a provider request;
- how to identify the client;
- provider-specific limits;
- how to interpret transport-level success/failure;
- how to expose provider response metadata.

The core acquisition contract must not depend on Crossref-specific fields, URLs, authentication schemes, or response structures.

The first concrete provider proof is **Crossref**, because Episteme already has a named, deterministic crossref-work-metadata source adapter from Phase 11.

The intended vertical path is:

**Crossref request → raw Crossref response → Phase 19 capture → existing Crossref adapter → grounded SOURCE records**

This proves acquisition without creating a second ingestion model.

## Capture Handoff

Acquisition does not write grounded SOURCE records directly.

For a response containing captured material:

1. acquisition obtains the response;
2. acquisition constructs the Phase 19 captured-representation metadata;
3. Phase 19 persistence stores the metadata and immutable content;
4. an existing source adapter may later interpret the captured representation;
5. grounded ingestion persists the resulting SOURCE records.

A failed acquisition may persist acquisition/capture history without captured content.

A partial acquisition may preserve the material actually received while remaining explicitly marked partial.

Neither outcome is silently converted to complete grounded evidence.

## Reproducibility

External state is mutable and may change after an acquisition.

Reproducibility therefore means preserving the exact acquired representation and the metadata needed to explain the request, rather than assuming that repeating the external request will return the same material.

The content digest established by Phase 19 is the identity anchor for received content.

An acquisition method/version identifies the retrieval mechanism, while the captured representation identifies the bytes/content actually received.

A later repeat request is a new acquisition event. Identical content may reuse the existing content-addressed object without collapsing the distinct acquisition histories.

## Failure Semantics

Transport and provider failures remain inspectable outcomes.

Examples include:

- connection failure;
- timeout;
- HTTP error response;
- malformed provider response;
- provider refusal or rate limiting;
- incomplete transfer.

The acquisition layer must distinguish:

**no usable representation received** from **some representation received but incomplete**.

It must not manufacture a successful capture merely because a request was attempted.

## Operational Constraints

External providers impose operational policies that belong to the provider capability rather than Episteme's epistemic core.

The first provider implementation should therefore support explicit client identification, bounded requests, sensible response handling, and provider-appropriate rate/concurrency behavior.

Credentials, secrets, and provider account state remain outside the Episteme data model.

Caching may reduce repeated external load, but cache behavior must not obscure the distinction between a new acquisition event and reused captured content.

## Relationship to Execution History

An acquisition operation may later be invoked as a workflow step.

Workflow execution records **what Episteme's declared procedure did**.

Acquisition history records **what the external source supplied**.

These are complementary histories.

Workflow execution must not replace acquisition metadata, and acquisition must not become an epistemic artifact merely because a workflow invoked it.

## Relationship to Provenance

Phase 19 capture metadata and ordinary artifact provenance answer different questions.

- Capture: what external representation was received?
- Provenance: where did a grounded Episteme record come from?
- Execution history: what declared Episteme procedure produced or connected artifacts?

The source adapter remains responsible for carrying appropriate capture/source information into grounded record provenance.

## Initial Scope

Phase 20 establishes:

- a provider-neutral finite acquisition contract;
- explicit acquisition outcomes;
- a clean provider capability boundary;
- handoff into Phase 19 capture;
- one bounded Crossref acquisition proof;
- preservation of exact retrieved content;
- executable tests for success and failure boundaries;
- an end-to-end proof through the existing Crossref adapter and grounded ingestion boundary.

## Out of Scope

Phase 20 does not establish:

- autonomous research;
- general web crawling;
- universal search;
- source discovery ranking;
- relevance or quality scoring;
- scheduling;
- distributed acquisition;
- authentication architecture;
- long-term archival policy;
- a new epistemic artifact type;
- a second ingestion model;
- automatic interpretation of arbitrary external material.

## Exit Condition

A bounded external request can be performed through an explicit provider capability, with the request and outcome inspectably represented, the exact received representation handed to Phase 19 immutable capture, and the captured representation optionally passed through the existing Crossref adapter into grounded ingestion without acquisition itself changing epistemic status.

## Exit Audit

Phase 20 is complete when executable tests demonstrate:

- a bounded provider request produces a captured representation;
- request/resource and acquisition method metadata survive persistence;
- successful response content is preserved exactly and verified by Phase 19 digest;
- failed acquisition remains distinguishable from successful capture;
- partial acquisition remains explicitly partial;
- provider-specific behavior remains outside the stable capture and epistemic primitives;
- acquisition does not itself create grounded records;
- the captured Crossref response can flow through the existing adapter and grounded ingestion boundary;
- repeated acquisition events remain distinct even when captured content is identical.
