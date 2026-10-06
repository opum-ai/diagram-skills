---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: diagram-plan skill
tags:
  - skill
summary: Quest dependency and milestone views generated from quest JSON.
tasks:
  - dski-11
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:56.079Z
lore_task_status: todo
---

# diagram-plan skill

## Goal

Show what blocks what and where the work stands, generated from Quest records rather than memory.

## Acceptance criteria

- `skills/diagram-plan/SKILL.md` has `name` and a trigger-rich description, and ends with a Reference files section.
- `quest_graph.py` turns `quest task list --json` into a dependency diagram whose edges equal Quest's `dependencies`.
- `skills/diagram-plan/examples/` holds at least one worked example whose diagrams pass the parse check and the lint.
- Two eval cases are in `evals/evals.json`, with iteration-1 with-skill and baseline results committed.
- `lore check` exits 0.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-11](../../.quest/tasks/DSKI-11.json) | Skill: diagram-plan (Quest dependency and milestone views) | To Do |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
