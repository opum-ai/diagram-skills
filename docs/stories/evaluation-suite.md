---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: Evaluation suite
tags:
  - evals
summary: Fixtures with a known source of truth, an objective grader, and with-skill vs baseline benchmarks.
tasks:
  - dski-6
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:55.680Z
lore_task_status: todo
---

# Evaluation suite

## Goal

Measure each skill against a no-skill baseline with graders that re-derive the truth instead of trusting the agent.

## Acceptance criteria

- `evals/grade.py` writes `grading.json` with `text`, `passed` and `evidence` for each expectation.
- Each fixture declares its source of truth as data.
- pytest covers the grader on a known-good and a known-bad output.

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [DSKI-6](../../.quest/tasks/DSKI-6.json) | Eval harness: fixtures, objective grader and benchmark layout | To Do |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).
