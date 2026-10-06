# Autonomous structural discovery boundary

The autonomous driver now has a narrow host-owned bridge from bounded exploration into existing structural-gap discovery.

The path is:

scout -> assess_exploration -> admit_exploration -> discover_gap

The planner can request each action, but it cannot choose the grounded inputs, detector, position field, step, executor, or structural-discovery configuration.

For the initial implementation, the host binding is `PositionalGapDiscoveryRuntime`. It invokes the existing deterministic `detect_positional_gap` primitive and persists the resulting GAP finding. A missing gap is a bounded failure, not permission for the planner to invent one.

This keeps the epistemic topology intact:

- exploration observations remain generated;
- admission creates an explicit discovery finding representing the accepted observation;
- structural discovery operates on host-owned grounded records;
- the structural GAP remains generated analysis;
- no generated observation is converted into grounded evidence.

The real-model acceptance harness exercises this path with Qwen3:8b:

```text
scout -> assess_exploration -> admit_exploration -> discover_gap
```

The acceptance also verifies that the original grounded input IDs survive into both discovery findings and that the generated exploration observation is not stored as a grounded record.


