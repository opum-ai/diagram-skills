---
# yaml-language-server: $schema=../../.lore/schemas/reference.schema.json
type: Reference
title: Delivery report for diagram-skills 0.1.0
tags:
  - report
  - delivery
summary: What was decided, built, proven and measured for diagram-skills 0.1.0, with links, and what is still open.
generated:
  by: lore/0.12.0
  at: 2026-10-06T17:20:00.000Z
---

# Delivery report for diagram-skills 0.1.0

Written 2026-10-06 against the brief's definition of done. Every item links
to its evidence.

## Decisions

| Decision | Record | Choice |
|---|---|---|
| Diagram notation | [ADR-0001](../adr/0001-use-mermaid-in-markdown-as-the-diagram-notation.md), DEC-1 | Mermaid in Markdown, conservative profile, parse gate pinned to GitHub's Mermaid 11.17.2 |
| Suite shape | [ADR-0002](../adr/0002-six-focused-diagram-skills-sharing-one-engine.md), DEC-2 | Six focused skills sharing one engine (owner chose this over the recommended four) |
| Repository layout | [Suite design](../specs/diagram-skill-suite-design.md), section 6 | Approved by the owner; engine inside `skills/diagram-review/scripts/` |
| Image export | Quest DSKI-14 | Opt-in, local `mmdc`, approved by the owner after the first build |

The research and the conventions behind them are in
[state of the art](state-of-the-art-in-diagramming-for-agent-written-docs.md)
and [conventions](conventions-adopted-from-the-sibling-repositories.md).

## What shipped

Each skill landed through its own pull request into `dev`, after green
checks on the exact head commit.

| Skill | PR | Iteration-1 evals, with skill vs without |
|---|---|---|
| diagram-review (engine, shared references) | #7, export #13 | 5/5 vs 4/5; 4/4 vs 3/4 |
| diagram-architecture | #8 | 7/7 vs 5/7; 7/7 vs 6/7 |
| diagram-process | #9 | 7/7 vs 6/7; 7/7 vs 6/7 |
| diagram-decision | #10 | 7/7 vs 6/7; 7/7 vs 4/7 |
| diagram-plan | #11 | 7/7 vs 5/7; 7/7 vs 5/7 |
| diagram-data | #12 | 7/7 vs 6/7; 5/5 vs 4/5 |

Each skill has a SKILL.md, worked examples and two eval cases. Every example
diagram passes the parse, lint and truth checks in CI. The foundations
landed as #1 (scaffold), #2–#4 (research, conventions, design), #5 (gate)
and #6 (eval harness).

## The validation gate, proven both ways

On pull request #5, a commit carrying a deliberately broken diagram made run
[37368998996](https://github.com/opum-ai/diagram-skills/actions/runs/37368998996)
fail at "Parse every Mermaid diagram". The fix made run
[37498971774](https://github.com/opum-ai/diagram-skills/actions/runs/37498971774)
pass. CI also proves it on every run: `tests/mermaid_selftest.sh` fails the
build if the checker stops failing broken diagrams.

## Evaluation

Results are in the [benchmark](../../evals/benchmarks/iteration-1/benchmark.md)
and the [evaluation story](../stories/evaluation-suite.md): 77 of 77
expectations passed with the skills and 60 of 77 without, at about 38% more
tokens. Most of the gap is accessibility fields. The truth checks did not
separate the two arms on the small fixture.

## Open

- **Iteration 2 (DSKI-15):** harder fixtures where truth checks
  discriminate, three runs per arm, the gaps the first round found, and
  the owner's viewer feedback.
- **Listing in opum-marketplace:** that changes another repository, so it
  waits for the owner.
- **Release:** `dev` has not been promoted to `main`, and no version tag
  exists.
- **Known limitations:** listed in the README.
