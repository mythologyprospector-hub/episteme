# Real Ollama exploration acceptance

This acceptance harness exercises the real local planner through the new exploration boundary.

The host supplies:

- the grounded fixture records;
- the bounded scout configuration;
- the assessment acceptance policy;
- assessment method, provenance, rationale, and scope;
- the admission runtime.

The model may only request the bounded actions.

The acceptance target is:

scout -> assess_exploration -> admit_exploration

The test then verifies that:

- one generated exploration observation was persisted;
- one host-owned assessment was persisted;
- one discovery finding was explicitly admitted;
- original grounded input IDs were preserved;
- generated observation and assessment remain explicit context;
- the generated observation was never converted into a grounded record.

Run from the repository checkout:

```bash
python scripts/accept_ollama_exploration.py
```

By default this uses `qwen3:8b`. Set `EPISTEME_OLLAMA_MODEL` to test another locally available model.
