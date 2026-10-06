---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: diagram-decision skill
tags:
  - skill
summary: ADR and Quest decision diagrams showing options, trade-offs and the chosen path.
tasks:
  - dski-10
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:56.000Z
lore_task_status: todo
---

# diagram-decision skill

## Goal

Show what was decided, against which options, and why, for ADRs and Quest decisions.

## Acceptance criteria

- `skills/diagram-decision/SKILL.md` has `name` and a trigger-rich description, and ends with a Reference files section.
- The chosen path in the diagram matches the ADR's Decision section and the Quest decision's outcome.
- `skills/diagram-decision/examples/` holds at least one worked example whose diagrams pass the parse check and the lint.
- Two eval cases are in `evals/evals.json`, with iteration-1 with-skill and baseline results committed.
- `lore check` exits 0.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-10](../../.quest/tasks/DSKI-10.json) | Skill: diagram-decision (ADR and Quest decision diagrams) | To Do |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
