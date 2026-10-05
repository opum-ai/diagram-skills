---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: diagram-process skill
tags:
  - skill
summary: Flowcharts, lanes, sequence and state diagrams for workflows and lifecycles.
tasks:
  - dski-9
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:55.921Z
lore_task_status: todo
---

# diagram-process skill

## Goal

Show what happens, in what order and who does it, with flowcharts, lanes, sequence and state diagrams.

## Acceptance criteria

- `skills/diagram-process/SKILL.md` has `name` and a trigger-rich description, and ends with a Reference files section.
- Each step or state traces to the code, runbook or spec that defines it.
- `skills/diagram-process/examples/` holds at least one worked example whose diagrams pass the parse check and the lint.
- Two eval cases are in `evals/evals.json`, with iteration-1 with-skill and baseline results committed.
- `lore check` exits 0.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-9](../../.quest/tasks/DSKI-9.json) | Skill: diagram-process (flows, sequences, state machines) | To Do |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
