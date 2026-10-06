---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: diagram-data skill
tags:
  - skill
summary: ER and schema diagrams traced to the schema files that define them.
tasks:
  - dski-12
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:56.155Z
lore_task_status: done
---

# diagram-data skill

## Goal

Show the shape of the data, traced to the schema files that define it.

## Acceptance criteria

- `skills/diagram-data/SKILL.md` has `name` and a trigger-rich description, and ends with a Reference files section.
- Every entity and relationship traces to a table, model or schema definition.
- `skills/diagram-data/examples/` holds at least one worked example whose diagrams pass the parse check and the lint.
- Two eval cases are in `evals/evals.json`, with iteration-1 with-skill and baseline results committed.
- `lore check` exits 0.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-12](../../.quest/completed/DSKI-12.json) | Skill: diagram-data (ER and schema diagrams) | Done |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
