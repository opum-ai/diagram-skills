---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: diagram-architecture skill
tags:
  - skill
summary: C4 context, container and component views drawn from the real repository and lore docs.
tasks:
  - dski-8
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:55.843Z
lore_task_status: done
---

# diagram-architecture skill

## Goal

Draw C4 context, container and component views of the real system, never a template one.

## Acceptance criteria

- `skills/diagram-architecture/SKILL.md` has `name` and a trigger-rich description, and ends with a Reference files section.
- Every container and component node carries a `%% ref` to a path or lore doc that exists.
- `skills/diagram-architecture/examples/` holds at least one worked example whose diagrams pass the parse check and the lint.
- Two eval cases are in `evals/evals.json`, with iteration-1 with-skill and baseline results committed.
- `lore check` exits 0.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-8](../../.quest/completed/DSKI-8.json) | Skill: diagram-architecture (C4 views from the real repository) | Done |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
