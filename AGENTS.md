# Episteme — Agent Instructions

## Authority and project memory

This file governs working method only. Episteme's project canon remains authoritative for what Episteme is and how its epistemic boundaries work.

Start with:
1. `README.md` for orientation and the current documentation reading order.
2. `CANON.md` for governing epistemic commitments.
3. `ARCHITECTURE.md` for the current system design.
4. `ROADMAP.md` and the relevant task-specific documents.
5. The implementation, tests, and current GitHub state that directly bear on the task.

Do not assume the conversation contains the current project state.

## Targeted grounding — Miracle Tokens

Use GitHub as durable project memory and conversation as temporary working context. Retrieve the information needed for the current task instead of repeatedly carrying or reconstructing the entire project in conversation.

- Inspect the current branch/state and relevant files before acting.
- Read the smallest sufficient set of canon, decisions, code, tests, and history.
- Broaden inspection when scientific validity, architecture, provenance, safety, or unresolved conflicts require it.
- Preserve existing project-specific documentation, evidence, provenance, decisions, and historical rationale.
- Never delete, flatten, or summarize away durable project knowledge merely to save conversational tokens.
- Record material new findings in the appropriate existing source of truth; do not create duplicate documents when an established one fits.
- Report briefly and distinguish intended, implemented, tested, and demonstrated behavior.

This is **targeted grounding, not shallow grounding**. Efficiency must never weaken epistemic discipline.

## Epistemic and change discipline

- Evidence, observations, claims, models, hypotheses, predictions, experiments, results, and unknowns must remain distinct.
- AI-generated content does not become evidence merely because Episteme generated it.
- Preserve provenance and uncertainty.
- Inspect before editing; make the smallest coherent change.
- Do not silently change canon or architecture. Follow Episteme's documented canonization and decision process.
- Test the actual behavior changed, and report the real result. Do not imply a local test is CI evidence.
- Treat external reviews as input to verify, not authority.
- Keep this file operational and concise; project-specific truth belongs in Episteme's canonical documents.
