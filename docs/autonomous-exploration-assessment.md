# Autonomous exploration assessment boundary

The autonomous driver now supports three separate exploration actions:

1. scout — request a bounded host-owned scouting operation.
2. assess_exploration — request assessment under a host-owned policy.
3. admit_exploration — request explicit discovery admission under a host-owned policy.

The planner supplies only the observation identifier for the second and third steps. It does not supply:

- whether the observation is accepted;
- assessment method or version;
- assessment rationale;
- assessment provenance;
- which grounded inputs are in scope;
- the admission assessment identifier;
- an executor, command, URL, or arbitrary store operation.

The host binds those policies through ExplorationAssessmentRuntime and ExplorationAdmissionRuntime.

The resulting topology is:

host-owned grounded records
        |
        v
bounded scout
        |
        v
ExplorationObservation (generated)
        |
        v
host-owned assessment policy
        |
        +---- rejected -> remains generated
        |
        v
accepted assessment
        |
        v
host-owned explicit admission
        |
        v
DiscoveryFinding (generated discovery context)

Acceptance is not truth. An accepted exploration observation is still not a grounded record or evidence. Its original grounded input IDs remain separate from its generated observation and assessment context.

The admission runtime resolves the accepted assessment itself. The planner cannot select a different assessment record.

This is an intentionally narrow workflow capability, not autonomous truth adjudication or unrestricted research.
