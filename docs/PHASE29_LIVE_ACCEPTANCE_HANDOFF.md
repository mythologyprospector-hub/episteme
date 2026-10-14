# Phase 29 Live Acceptance Handoff

**Purpose:** Resume PR #59 safely if the working conversation disappears. This file is a handoff, not evidence that the benchmark passed.

## Current disposition

- PR: https://github.com/mythologyprospector-hub/episteme/pull/59
- Branch: `fix/phase29-rule-verification`
- State: open, draft, unmerged. Keep it that way until the blinded live acceptance criteria pass.
- Current branch head at the time of this handoff update: `013f02a2aba1c8b52c85d54ad1e3c10e2dd09c9b` (structured rejected-action feedback changes; not yet live-tested).
- GitHub Actions run #1088 passed on this head. This proves the automated suite passed, not that live acceptance passed.
- Latest Bucky live acceptance tested code at `287ae9203162ab7bf51b3ac464fa7a33401d1527` and failed (2026-10-14; `qwen:14b`, blind mode, one run per property, 300-second timeout; exit status 1). No behavior change has been live-tested after that run.

## Bucky checkout

The PR worktree is:

```bash
cd ~/projects/.worktrees/episteme/episteme-pr59-test
git fetch origin
git checkout --detach origin/fix/phase29-rule-verification
git status --short --branch
```

Use this worktree for PR #59. Do not work in the main clone `~/projects/episteme` as a substitute. The main clone has previously had an unrelated untracked `uv.lock`; leave it untouched. Also leave the unrelated PR43 worktree `~/projects/.worktrees/episteme/episteme-pr43-test` untouched.

## Latest live result

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

- Relative atomic mass: one host-verified geometric-mean rule using positions `[2, 3]`; competing hypothesis retries repeated the existing rule.
- Density: one host-verified addition-with-previous-interval rule using positions `[3, 5]`; competing hypothesis retries repeated the existing rule.
- Melting point: one host-verified geometric-mean rule using positions `[3, 5]`; competing hypothesis retries repeated the existing rule.
- Each property ended after three attempts with a duplicate-rule rejection. The planner did not recover by choosing a genuinely distinct executable rule.
- No valid persisted experiment evidence was produced.
- The acceptance diagnostics reported that not all numeric forecasts matched their independently computed source rules, and no rule-verified forecast met tolerance and matched or beat the baseline.
- Held-out values remained hidden and blinded-name checks passed for all three properties.

The full local log is at `/tmp/episteme-pr59-acceptance.log` on Bucky; it is not itself a durable GitHub artifact.

## What the branch already enforces

- Host-side quantitative-rule validation before hypothesis persistence.
- Host-side numeric forecast validation against its source hypothesis rule before prediction persistence.
- Bounded retries for rejected planner actions.
- Rejection feedback includes structured rejected-action fields (`kind`, `target_ids`, `quantitative_rule`, `predicted_numeric_values`) while deliberately excluding free-form model-authored text.
- The Ollama prompt's allowed field list includes `quantitative_rule`.
- Regression tests cover relevant validation and prompt contracts.

The previous retry-feedback change did not fix live behavior: the model repeated a duplicate rule after rejection. Code inspection confirmed that feedback text was passed to Ollama, and the adapter-level test established that the text reached the request. A structural improvement is now committed: `DiscoveryContext` carries rejected action fields separately in `rejected_actions`; the next Ollama request includes this as a machine-readable JSON array, and target IDs are converted to planner handles. The prompt explicitly tells the planner that these rejected proposals are authoritative and must not be repeated. Regression tests cover persistence across retries and serialized structure/handle mapping. CI #1097 passed on commit `013f02a2aba1c8b52c85d54ad1e3c10e2dd09c9b`. This has not yet been live-tested; do not assume it fixes the model behavior. Do not claim that improved feedback alone fixes model behavior.

## Next work

1. Inspect the full retry loop and the exact serialized Ollama request for rejected-action feedback, using tests or a safe captured payload. Keep the held-out answer and blinded identities out of planner input and diagnostic feedback.
2. Determine why the planner repeats the duplicate quantitative rule despite the rejection and structured action details.
3. Add a focused regression test for the identified failure/contract before changing behavior.
4. Run GitHub Actions on the new commit.
5. Only then rerun the blinded Bucky live acceptance with the command above.
6. Record the outcome in the PR discussion and update this handoff when the state changes.

## Non-negotiable constraints

- Do not merge PR #59 or mark it ready while live acceptance fails.
- Do not relax acceptance criteria, weaken host validation, unblind the planner, or provide the held-out answer to the planner.
- Do not replace model-authored forecasts with host-computed forecasts and describe them as autonomous predictions.
- A green CI run is necessary but not sufficient. Live acceptance must explicitly pass, including valid persisted experiment evidence, source-rule-consistent forecasts, and held-out isolation.
- Treat model-authored stop reasons as unverified claims, not ground truth.
- Preserve Episteme's canonical invariant: no information gains epistemic authority merely by passing through Episteme.

## Durable record

CI #1088 passed on handoff commit `9f033b7f3ea239b4659a3f94dfa0872e9a7f0b27`; CI #1091 passed on the adapter-feedback regression test commit `c934abb461a314bd372c649c10edf49ac462fd1a`; CI #1092 passed on handoff update `e17681eb6fb93eb6c5d8dbbfa04135820fccb844`; CI #1097 passed on structured rejected-action feedback commit `013f02a2aba1c8b52c85d54ad1e3c10e2dd09c9b`.

The PR discussion contains prior live failures and implementation notes:
https://github.com/mythologyprospector-hub/episteme/pull/59

The current handoff should be updated as the branch head, CI status, and acceptance result change.
