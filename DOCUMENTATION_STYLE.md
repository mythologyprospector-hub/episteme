# Documentation Standard

**Status:** Canonical project standard  
**Version:** 0.1  
**Last updated:** 2026-09-18

## Purpose

Episteme documentation is part of the system's architecture.

Documentation should be readable by humans, useful to automated agents, stable under revision, and easy to navigate.

## File Format

Project documentation uses:

- Markdown (`.md`)
- UTF-8
- Unix line endings
- one blank line between logical sections
- no trailing whitespace

## Naming

Use uppercase filenames for top-level governing documents when the name is an established project concept:

- `README.md`
- `CANON.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`

Use descriptive lowercase or scoped paths for supporting documentation where appropriate.

Do not create multiple documents that serve the same purpose.

## Document Header

Canonical documents begin with:

- document title
- status
- version
- last-updated date

Example:

```markdown
# Document Name

**Status:** Canonical  
**Version:** 0.1  
**Last updated:** YYYY-MM-DD
```

## Headings

Use one H1 title per document.

Use H2 headings for major sections.

Use H3 headings for subsections.

Do not skip heading levels.

## Lists

Use unordered lists for unordered concepts.

Use numbered lists when sequence matters.

Use task lists for tracked work:

```markdown
- [ ] Not complete
- [x] Complete
```

## Code and Technical Terms

Use backticks for:

- filenames
- paths
- commands
- identifiers
- configuration keys
- code symbols

Use fenced code blocks for multi-line examples.

## Status Language

Prefer precise status terms:

- **Proposed** — suggested but not adopted.
- **Canonical** — currently governing.
- **Implemented** — implemented in code.
- **Verified** — demonstrated by an appropriate test or check.
- **Deprecated** — retained for historical or compatibility reasons but no longer preferred.
- **Superseded** — replaced by a newer documented decision.

Do not describe something as complete merely because it exists.

## Terminology

Use the vocabulary established by `CANON.md`.

If a new term is necessary:

1. search for an existing equivalent;
2. define the new term in the appropriate source of truth;
3. use it consistently afterward.

Avoid synonyms when they could blur an architectural distinction.

## Cross-References

Prefer repository-relative links.

Example:

`[Architecture](ARCHITECTURE.md)`

Cross-references should point to the authoritative document rather than duplicate its content.

## Decision Recording

Architectural decisions should be recorded in the document that governs the affected concept unless the decision history becomes large enough to justify a dedicated decision record.

Do not create an ADR or decision file merely because the format exists.

## Documentation Before Implementation

When a change introduces a new architectural concept:

1. inspect existing documentation;
2. determine whether the concept already exists;
3. update the authoritative document;
4. implement the change;
5. update verification and status.

## Visual Standard

Documentation should be:

- concise
- deliberate
- easy to scan
- consistent
- free of decorative clutter
- explicit about status and uncertainty

A document should explain a thing once and link to it elsewhere.

## Quality Gate

Before committing documentation, check:

- Is this the correct source of truth?
- Does another document already cover this?
- Does the document agree with canon?
- Does it introduce an undefined term?
- Does it accidentally promise an unimplemented capability?
- Does it duplicate another document?
- Does it preserve the distinction between fact, interpretation, proposal, and unknown?

## Guiding Rule

> **Sharp documentation is not decoration. It is drift control.**
