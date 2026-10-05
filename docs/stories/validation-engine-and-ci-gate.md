---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: Validation engine and CI gate
tags:
  - engine
summary: The shared parse, lint and truth engine and the CI gate proven both ways.
tasks:
  - dski-5
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:50.404Z
lore_task_status: in-progress
---

# Validation engine and CI gate

## Goal

Give every skill, and CI, one way to prove a diagram parses under the Mermaid version GitHub renders, and that it follows the profile and level rules.

## Acceptance criteria

- `mermaid-check.mjs`, pinned to mermaid 11.17.2, fails every broken fixture and passes every valid one.
- `diagram_lint.py` enforces quoted labels, banned ids, `accTitle`/`accDescr`, the level node cap and an explanation next to the fence.
- CI runs the parse check, the self-test, the lint, pytest and `lore check` on every pull request.
- The gate is shown red on a broken diagram and green after the fix, on a real pull request.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-5](../../.quest/tasks/DSKI-5.json) | Validation engine and CI gate for Mermaid diagrams | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
