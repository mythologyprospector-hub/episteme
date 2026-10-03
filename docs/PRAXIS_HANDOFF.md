# Praxis Evidence Handoff

**Status:** Canonical integration boundary  
**Version:** 1

## Purpose

Episteme may receive an admitted evidence item from Praxis without importing Praxis as a runtime dependency.

The boundary is an explicit JSON-compatible handoff packet produced by Praxis. Episteme consumes that packet through a narrow adapter that creates an Episteme Record with a new Episteme-owned UUID.

## Rules

1. The Praxis evidence and Praxis human-admission objects are preserved as supplied payload data.
2. Episteme does not interpret the Praxis admission as an Episteme review, assessment, or authorization.
3. The Episteme RecordKind is supplied explicitly by the caller. The adapter does not infer it from Praxis evidence.
4. source_id and captured_at are supplied explicitly and become Episteme provenance.
5. The optional source location is preserved as provenance.
6. Episteme generates its own record identity; the Praxis evidence identity remains inside the payload.
7. The adapter does not generate claims, hypotheses, assessments, relationships, or other interpretive artifacts.
8. No runtime dependency on the Praxis package is introduced.
9. Malformed or incomplete handoff packets are rejected rather than repaired.
10. A successful translation establishes an Episteme grounded record with provenance; it does not establish that the external claim is scientifically true.

This is a translation boundary, not a semantic merge of the two projects.
