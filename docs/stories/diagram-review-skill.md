---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: diagram-review skill
tags:
  - skill
summary: "Validator and critic: parse, lint, truth and prose agreement for any Mermaid diagram."
tasks:
  - dski-7
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:55.761Z
lore_task_status: done
---

# diagram-review skill

## Goal

Check any Mermaid diagram for syntax, legibility, accessibility and truth, and say exactly what to fix.

## Acceptance criteria

- `skills/diagram-review/SKILL.md` has `name` and a trigger-rich description, and ends with a Reference files section.
- `diagram_truth.py` resolves every `%% ref` line and reports nodes that resolve nowhere.
- `skills/diagram-review/examples/` holds at least one worked example whose diagrams pass the parse check and the lint.
- Two eval cases are in `evals/evals.json`, with iteration-1 with-skill and baseline results committed.
- `lore check` exits 0.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-7](../../.quest/completed/DSKI-7.json) | Skill: diagram-review (validator and critic) | Done |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
