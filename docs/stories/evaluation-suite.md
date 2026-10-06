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
lore_task_status: done
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
| [DSKI-6](../../.quest/completed/DSKI-6.json) | Eval harness: fixtures, objective grader and benchmark layout | Done |
<!-- lore:tasks:end -->

## Notes

Part of the [diagram skill suite](../epics/diagram-skill-suite.md). Design: [suite design](../specs/diagram-skill-suite-design.md).

### Iteration 1 (2026-10-06)

12 cases, two per skill, each run once with the skill and once without
(24 subagent runs on claude-opus-5-5). Graded by `evals/grade.py` against
the fixture's real code, schema and Quest records. Full results:
[benchmark](../../evals/benchmarks/iteration-1/benchmark.md).

| | With skill | Without skill |
|---|---|---|
| Expectations passed | 77 of 77 (100%) | 60 of 77 (78%) |
| Mean tokens per run | about 39,000 | about 28,000 |
| Mean time per run | about 78 s | about 62 s |

What separated them: 12 of the baseline's 17 failures are missing
`accTitle`/`accDescr`. The rest are plan views that included finished or
out-of-scope tasks, and decision diagrams that did not mark or did not draw
the options. What did not: the truth checks. On this small fixture the
baseline invented nothing either, so the fixture does not yet test what the
truth check is for.

Limits of this round:

- One run per arm, so there is no variance estimate.
- The prose is not graded. One with-skill answer names the wrong
  migration file for a dropped table.
- The grader was fixed twice mid-round, on both arms, before the final
  grading: node classification, and labels containing parentheses.

