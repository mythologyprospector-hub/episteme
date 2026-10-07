# Autonomous Evidence Request Boundary

**Status:** Implemented — Phase 28 complete  
**Phase:** Post-27 architectural design  
**Scope:** Boundary between bounded autonomous discovery and existing external acquisition/capture/grounded-ingestion capabilities

## Purpose

Phase 27 establishes that Episteme can conduct a bounded investigation without a human selecting every intermediate planner action.

It deliberately stops at a host-owned experiment boundary.

The next architectural question is not how to give the planner arbitrary access to the network. It is how an autonomous investigation can explicitly state that its current evidence state is insufficient and request an approved external evidence operation while preserving every existing epistemic boundary.

This document defines that boundary before implementation.

## Existing capabilities

Episteme already has the pieces needed on both sides:

1. **Phase 27** provides bounded planner-driven investigation.
2. **Phase 20** provides provider-neutral bounded external acquisition.
3. **Phase 19** preserves the exact received representation as immutable captured content.
4. **Phase 22** links grounded records produced from a capture to that exact capture.
5. **Phase 24** can invoke acquisition from a finite declared workflow.
6. **Phase 23** exposes captured content for inspection.
7. **Phase 25** exposes capture-to-execution lineage.
8. **Phase 11** provides deterministic grounded ingestion through named adapters.

The missing capability is an explicit control boundary connecting autonomous reasoning to those already-declared operations.

## Proposed boundary

The proposed flow is:

**represented state → planner → validated evidence request → host-owned acquisition → immutable capture → optional grounded ingestion → represented state**

The planner does **not** acquire evidence itself.

It requests an evidence operation. The host decides whether and how that request can be fulfilled.

## New conceptual object: Evidence Request

An evidence request is a generated operational request describing what the investigation needs next.

It is not evidence.

It is not a hypothesis.

It is not a source claim.

It is not permission to access arbitrary external systems.

A request should minimally identify:

- the current investigation context;
- the epistemic artifact or prediction that motivates the request;
- the requested resource or resource class;
- the requested acquisition capability;
- bounded request parameters;
- the reason the requested material could discriminate among current alternatives;
- the expected representation type;
- a finite execution boundary.

The request itself remains generated control-plane state.

## Planner authority

The planner may:

- declare that additional external material is required;
- identify the existing prediction, hypothesis, question, or experiment that motivates the request;
- select among explicitly exposed acquisition capabilities;
- provide bounded request parameters accepted by that capability;
- explain the intended discriminating purpose;
- choose to continue, revise the request, or stop after the host reports the result.

The planner may not:

- execute network code;
- construct arbitrary HTTP clients;
- choose arbitrary hosts or protocols outside a host-approved capability;
- bypass acquisition limits;
- change capture storage semantics;
- mark a response as grounded evidence;
- manufacture a successful acquisition result;
- bypass source/capture provenance;
- decide that captured content is scientifically true;
- silently promote generated material into grounded evidence.

## Host authority

The host owns:

- which acquisition providers are available;
- provider credentials and configuration;
- allowed sources/resources;
- request-size and time limits;
- network policy;
- rate limits;
- retry policy;
- capture-root and persistence configuration;
- acquisition method and method version;
- whether a request is admissible for execution;
- exact response capture;
- failure/partial/complete classification;
- optional handoff to a named grounded-ingestion adapter.

The host therefore remains the authority over the real-world operation.

## Why the existing AcquisitionRequest is the right substrate

Phase 20 already defines:

- `source_id`;
- `requested_resource`;
- `request_parameters`;
- `acquisition_method`;
- `acquisition_method_version`.

The proposed autonomous boundary should not create a second acquisition model.

Instead, a validated evidence request should be translated by the host into an existing `AcquisitionRequest`.

That keeps the architecture:

**planner request → host validation/policy → existing AcquisitionRequest → existing provider → existing capture**

rather than:

**planner → new autonomous web subsystem**

## Admission boundary

The most important rule is that planner approval and acquisition approval are different things.

The planner can request.

The host can admit or reject the request for execution.

A rejected request is an operational failure or policy decision, not evidence against the hypothesis.

A successful acquisition produces a capture.

A capture is not automatically grounded evidence.

Only the existing grounded-ingestion boundary can create grounded records, and only through its named adapter and provenance rules.

## Result states

The host should return an explicit operational result rather than pretending every request succeeds.

At minimum:

- **rejected** — host policy or validation prevented execution;
- **failed** — execution was attempted but no usable representation was received;
- **partial** — some representation was received but the acquisition was incomplete;
- **complete** — the requested representation was received and captured.

These states already align with the Phase 19/20 capture boundary.

The autonomous loop must preserve them.

## Capture and lineage

When acquisition succeeds or partially succeeds, the resulting capture identity becomes part of the represented state.

The autonomous trace should therefore be able to establish:

**evidence request → acquisition operation → capture → optional grounded record**

without creating a parallel provenance graph.

The existing capture and workflow lineage mechanisms remain authoritative for the operational history.

## Grounded ingestion remains a separate decision

A completed capture should not automatically become a grounded record.

There are two distinct operations:

1. **Acquire and preserve what was received.**
2. **Translate a captured representation through a named grounded-ingestion adapter.**

The first establishes captured representation.

The second establishes grounded Episteme records.

Keeping those separate prevents an autonomous planner from turning "I found a document" into "the document's claims are now Episteme knowledge."

## Bounded continuation

After the host returns a capture, the planner receives the resulting represented state.

It may then:

- stop;
- inspect the new captured material through existing read surfaces;
- request an explicitly supported ingestion operation;
- revise the investigation;
- propose another bounded experiment;
- request another evidence operation if the finite investigation budget permits.

The loop remains subject to Phase 27's finite step and retry limits.

## Proposed action shape

If implemented, the autonomous action vocabulary should add a narrowly defined evidence-request operation rather than a generic "browse" or "search" action.

Conceptually:

`request_evidence`

The action should identify the investigation need and a host-exposed acquisition capability, but should not contain arbitrary executable instructions.

A future implementation should define its exact schema only after tests establish the required validation boundary.

## What this does not introduce

This design does not introduce:

- autonomous unrestricted browsing;
- autonomous web crawling;
- arbitrary network access;
- a new search engine;
- a second acquisition subsystem;
- a second capture model;
- automatic source trust;
- automatic truth adjudication;
- a universal evidence-quality score;
- automatic canonization;
- a general-purpose agent runtime.

## Security and epistemic invariant

> **The planner may request evidence, but only host-owned acquisition capabilities may touch external systems, and only the existing grounded-ingestion boundary may create grounded records from captured material.**

This preserves the Phase 27 invariant:

> **The planner may choose among declared bounded operations, but only host-owned Episteme capabilities determine what those operations actually do.**

## Design exit condition

This design is ready for implementation only when tests can demonstrate all of the following:

- an autonomous planner can request additional evidence without receiving arbitrary network authority;
- the host can reject unsupported or unsafe requests before acquisition;
- admitted requests translate into the existing `AcquisitionRequest` model;
- acquisition outcomes remain complete, partial, failed, or rejected;
- exact received material still passes through the existing immutable capture boundary;
- capture identity and acquisition lineage remain inspectable;
- captured content does not silently become grounded evidence;
- optional grounded ingestion remains a separate named operation;
- bounded retry and step semantics remain intact;
- no second acquisition, capture, provenance, or epistemic model is introduced.

Until those tests can be specified clearly, implementation should not begin.


## Phase 28 Exit Audit

The implemented Phase 28 behavior satisfies the design exit condition.

- the autonomous planner can request additional evidence without receiving arbitrary network authority;
- the host validates the request and controls admission before acquisition;
- admitted requests translate into the existing `AcquisitionRequest` model rather than introducing a second acquisition model;
- acquisition outcomes remain explicitly bounded and preserve the existing complete/partial/failed semantics, while host rejection remains distinct;
- exact received material passes through the existing immutable capture boundary;
- capture identity and acquisition lineage remain inspectable through the existing capture and execution mechanisms;
- captured content does not silently become grounded evidence;
- grounded ingestion remains a separate named operation;
- bounded retry and step semantics remain intact;
- no second acquisition, capture, provenance, or epistemic model was introduced;
- the real Ollama acceptance harness completed a full bounded path ending in `request_evidence`, with one complete capture through the registered host-owned capability.

**Status:** Complete.
