---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: Plugin packaging and README
tags:
  - docs
summary: README in the sibling shape, plugin validation and the final report.
tasks:
  - dski-13
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:56.232Z
lore_task_status: todo
---

# Plugin packaging and README

## Goal

Make the suite installable and explain it the way the sibling plugins do.

## Acceptance criteria

- The README follows the sibling section order and reports the iteration-1 results.
- `claude plugin validate .` passes, or its absence is recorded.
- `lore check` exits 0.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-13](../../.quest/tasks/DSKI-13.json) | README, plugin validation and final report | To Do |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
