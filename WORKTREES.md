# Active Worktree Register

**Snapshot date:** 2026-10-17  
**Status:** Operational inventory; re-check local state before acting.  
**Authority:** `WORKTREE_LIFECYCLE.md` and the linked GitHub PRs govern lifecycle and retirement.

This register records the two Episteme review worktrees found on Bucky during the 2026-10-17 local reconciliation. It is a dated snapshot, not a guarantee that local paths or PR state remain unchanged.

| Path | Purpose | Task | State | Local state at snapshot | Disposition | Exit condition | Next action |
|---|---|---|---|---|---|---|---|
| `~/projects/.worktrees/episteme/episteme-pr43-test` | Isolated review/test checkout for host-derived experiment resolution | [Episteme PR #43](https://github.com/mythologyprospector-hub/episteme/pull/43) | Detached at `bd58c07c1fdb3e6f9c1b6e5b1b39769efff94411`; remote branch `fix/host-derived-experiment-resolution` | Clean; no untracked files observed; HEAD matched the remote PR head at inspection | `WAITING` | PR #43 is resolved, then the retirement protocol confirms no valuable local-only state remains | Keep available for review; do not merge or remove based on this register |
| `~/projects/.worktrees/episteme/episteme-pr59-test` | Isolated review/test checkout for Phase 29 rule verification | [Episteme PR #59](https://github.com/mythologyprospector-hub/episteme/pull/59) | Detached at `4dbc7101fd58d0f570d57796b2d31cc569d7d236`; remote branch `fix/phase29-rule-verification` | Clean; no untracked files observed; HEAD matched the remote PR head at inspection | `WAITING` | PR #59 is resolved, then the retirement protocol confirms no valuable local-only state remains | Keep available for review; do not merge or remove based on this register |

## Operating rules

- Re-run both Git registration and physical-directory discovery before relying on this snapshot.
- A clean worktree is not disposable merely because it is detached or its task is old.
- Do not remove either worktree until its linked PR is resolved and the full retirement protocol in `WORKTREE_LIFECYCLE.md` passes.
- No cleanup, tests, merge, or code changes were performed during the inventory.
