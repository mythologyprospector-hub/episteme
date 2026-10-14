# Phase 29 Live Acceptance Handoff

**Purpose:** Resume PR #59 safely if the working conversation disappears. This file is a handoff, not evidence that the benchmark passed.

## Current disposition

- PR: https://github.com/mythologyprospector-hub/episteme/pull/59
- Branch: `fix/phase29-rule-verification`
- State: open, draft, unmerged. Keep it that way until the blinded live acceptance criteria pass.
- Schema-constraint implementation commit: `0a5bbd667ccf50ce1f7af61c76f00f45bdfc6fc0`; CI #1101 and #1102 passed with **356 tests** before the blinded-candidate correction.
- Candidate-key correction commit: `c4e73ff325b05a0e9500794dc5c47990bb9ee561`; GitHub Actions run #1105 passed: https://github.com/mythologyprospector-hub/episteme/actions/runs/38548444634.
- Latest diagnosis: structured `rejected_actions.predicted_numeric_values` retained opaque store IDs as object keys, while the same rejection's `target_ids` were translated to planner handles. This broke the model-facing link between a rejected forecast and H1/H2. Fix committed in `1fbb7296b5838c74636d37e7e8f3b5be38bf083e`; regression test committed in `1625df7f6370bda10ee14cd4c741e06775f8dfc4`. CI is pending; do not live-test before it passes.
- Latest Bucky live acceptance tested head `c4e73ff325b05a0e9500794dc5c47990bb9ee561` on 2026-10-14 (`qwen:14b`, blind mode, one run per property, 300-second timeout; exit status 1).
- The candidate-key correction worked: candidate rules were generated and host-verified hypotheses were persisted. The next failure is model arithmetic: each run proposed numeric forecasts that contradicted the declared source rule, so host validation rejected them after bounded retries. No valid experiment evidence was persisted. Keep PR draft/unmerged.

## Bucky checkout

The PR worktree is:

```bash
cd ~/projects/.worktrees/episteme/episteme-pr59-test
git fetch origin
git checkout --detach origin/fix/phase29-rule-verification
git status --short --branch
```

Use this worktree for PR #59. Do not work in the main clone `~/projects/episteme` as a substitute. The main clone has previously had an unrelated untracked `uv.lock`; leave it untouched. Also leave the unrelated PR43 worktree `~/projects/.worktrees/episteme/episteme-pr43-test` untouched.

## Latest live result (2026-10-14; branch head `c4e73ff`)

Run command:

```bash
EPISTEME_OLLAMA_MODEL=qwen:14b \
EPISTEME_OLLAMA_TIMEOUT=300 \
EPISTEME_OLLAMA_RUNS=1 \
EPISTEME_OLLAMA_BLIND=1 \
python3 scripts/accept_ollama_rediscovery.py 2>&1 | tee /tmp/episteme-pr59-acceptance.log

test_status=${PIPESTATUS[0]}
printf '\n=== Acceptance exit status: %s ===\n' "$test_status"
```

Result: **OVERALL: FAIL**.

- All three properties created two host-verified hypotheses, confirming that blinded candidate generation now works.
- Each then failed to provide forecasts consistent with the source rules. Examples: relative atomic mass proposed `134.5` where its declared geometric-mean rule computes `37.7585367831`; density proposed `0.6` where its declared midpoint rule computes `4.8083`; melting point proposed `0.9` where its declared midpoint rule computes `822.964`.
- The host rejected inconsistent forecasts after bounded retries. Action sequence for every property was `['discover_gap', 'hypothesis', 'hypothesis']`; no valid persisted experiment evidence was produced.
- Rules themselves were persisted and host-verifiable, but numeric forecasts did not all match their independently computed source rules and no forecast met acceptance tolerance while matching or beating baseline.
- Held-out values remained hidden and blinded names remained hidden for all three properties.
- This is a new failure mode after the candidate-key fix. Inspection found that rejected forecast values were sent back under opaque hypothesis IDs instead of planner handles H1/H2, so the model could not reliably associate each rejected value with the hypothesis it belonged to. The adapter now aliases those keys and a regression test checks the serialized feedback. The live arithmetic failure may have more than one cause; this fix is not proven until CI and a new live run. Do not weaken validation or substitute host-computed values for model-authored forecasts.

The full local log is at `/tmp/episteme-pr59-acceptance.log` on Bucky; it is not itself a durable GitHub artifact.

## What the branch already enforces

- Host-side quantitative-rule validation before hypothesis persistence.
- Host-side numeric forecast validation against its source hypothesis rule before prediction persistence.
- Bounded retries for rejected planner actions.
- Rejection feedback includes structured rejected-action fields (`kind`, `target_ids`, `quantitative_rule`, `predicted_numeric_values`) while deliberately excluding free-form model-authored text.
- The Ollama prompt's allowed field list includes `quantitative_rule`.
- During historical rediscovery, the planner schema enumerates executable two-position quantitative rule candidates from host-side grounded observations and excludes operation/property/input-position combinations already used by existing hypotheses. Midpoint candidates are limited to positions symmetric around period 4. If no candidate remains, the adapter fails closed instead of asking the model to invent a rule.
- A blinded-mode mismatch in the host-side position key was corrected: candidate generation reads original `period` fields; only the model-facing payload is renamed to `position`. Regression test is included and CI #1105 passed. The subsequent live run confirmed candidates are generated.
- Rejected numeric forecast feedback now maps opaque hypothesis IDs to the same planner handles used everywhere else in the model-facing context. Regression test verifies that the rejection for each hypothesis is represented as H1/H2, not opaque IDs. Commit `1625df7f6370bda10ee14cd4c741e06775f8dfc4`; CI pending.
- Host-side quantitative-rule and forecast validation remain authoritative; schema constraints are a prevention layer, not a replacement for validation.

The previous retry-feedback change did not fix live behavior: the model repeated a duplicate rule after rejection. Code inspection confirmed that feedback text was passed to Ollama, and the adapter-level test established that the text reached the request. A structural improvement is now committed: `DiscoveryContext` carries rejected action fields separately in `rejected_actions`; the next Ollama request includes this as a machine-readable JSON array, and target IDs are converted to planner handles. The prompt explicitly tells the planner that these rejected proposals are authoritative and must not be repeated. Regression tests cover persistence across retries and serialized structure/handle mapping. CI #1097 passed on commit `013f02a2aba1c8b52c85d54ad1e3c10e2dd09c9b`. This has not yet been live-tested; do not assume it fixes the model behavior. Do not claim that improved feedback alone fixes model behavior.

## Next work

1. Verify GitHub Actions for commit `1625df7f6370bda10ee14cd4c741e06775f8dfc4`, including the new rejected-forecast handle-mapping regression test.
2. If CI passes, rerun the exact blinded Bucky live acceptance unchanged. Confirm whether correctly keyed structured rejection feedback lets the model revise each forecast and complete the bounded experiment.
3. Preserve the boundary that the model authors/selects the forecast; do not silently replace its forecast with a host-computed answer. Do not relax validation or acceptance criteria, and preserve held-out isolation.
4. If the live run still fails, inspect the new log and diagnose the next evidenced cause before another change. Require all existing acceptance criteria, including valid persisted experiment evidence and a rule-verified forecast meeting tolerance and matching or beating baseline.
5. Record the outcome in the PR discussion and update this handoff.

## Non-negotiable constraints

- Do not merge PR #59 or mark it ready while live acceptance fails.
- Do not relax acceptance criteria, weaken host validation, unblind the planner, or provide the held-out answer to the planner.
- Do not replace model-authored forecasts with host-computed forecasts and describe them as autonomous predictions.
- A green CI run is necessary but not sufficient. Live acceptance must explicitly pass, including valid persisted experiment evidence, source-rule-consistent forecasts, and held-out isolation.
- Treat model-authored stop reasons as unverified claims, not ground truth.
- Preserve Episteme's canonical invariant: no information gains epistemic authority merely by passing through Episteme.

## Durable record

CI #1088 passed on handoff commit `9f033b7f3ea239b4659a3f94dfa0872e9a7f0b27`; CI #1091 passed on the adapter-feedback regression test commit `c934abb461a314bd372c649c10edf49ac462fd1a`; CI #1092 passed on handoff update `e17681eb6fb93eb6c5d8dbbfa04135820fccb844`; CI #1097 passed on structured rejected-action feedback commit `013f02a2aba1c8b52c85d54ad1e3c10e2dd09c9b`; CI #1105 passed on blinded-candidate correction commit `c4e73ff325b05a0e9500794dc5c47990bb9ee561`.

The PR discussion contains prior live failures and implementation notes:
https://github.com/mythologyprospector-hub/episteme/pull/59

The current handoff should be updated as the branch head, CI status, and acceptance result change.
