---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: Six focused diagram skills sharing one engine
tags:
  - suite
  - dec-2
summary: The suite ships six skills, one per reader question, with the parse, lint and truth engine owned by diagram-review.
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:41:41.649Z
---

# Six focused diagram skills sharing one engine

## Status

Accepted (2026-10-05). The owner chose the fuller option over the
recommended lean one. Tracked by Quest task DSKI-3 and mirrored as Quest
decision DEC-2.

## Context

The [suite design](../specs/diagram-skill-suite-design.md) offered two
shapes. Both share one engine: the parse check, the lint, the truth check
and the Quest and lore graph generators.

- **Lean, four skills (recommended):** `diagram` (process and data),
  `diagram-architecture`, `diagram-plan` (plans and decisions) and
  `diagram-review`. Fewer triggers and eval sets, at the cost of one broad
  generalist skill.
- **Fuller, six skills:** `diagram-architecture`, `diagram-process`,
  `diagram-decision`, `diagram-plan`, `diagram-data` and `diagram-review`.
  Narrower skills with sharper triggers, at the cost of six eval sets and
  overlap between process, data and architecture.

## Decision

We will ship six skills, one per reader question:

| Skill | Reader question | Source of truth |
|---|---|---|
| `diagram-architecture` | What is this system and what are its parts? | Repository tree, manifests, lore docs |
| `diagram-process` | What happens, in what order, and who does it? | Code, runbooks, specs |
| `diagram-decision` | What was decided, against which options? | ADRs, Quest decisions |
| `diagram-plan` | What blocks what, and where are we? | Quest tasks and milestones |
| `diagram-data` | What is the shape of the data? | Schema files, models |
| `diagram-review` | Are these diagrams valid, legible and true? | The engine |

`diagram-review` owns the engine and the shared references. The other
five reach them through `${CLAUDE_SKILL_DIR}/../diagram-review/`, as
proof-skills' siblings reach into `formal-verify`.

## Consequences

- There are six eval sets and six trigger descriptions. The first eval
  round is 6 skills × 2 cases × 2 arms, and its size is put to the owner
  before it runs.
- Overlap is handled in the descriptions, not by a router. Each skill's
  description names its question and routes the near misses: structure
  goes to architecture, behaviour to process, schema to data.
- Shared guidance (profile, levels, accessibility) lives once, in
  `diagram-review/references/`. A skill never copies it.
- `diagram-decision` and `diagram-plan` share `quest_graph.py` and
  `lore_graph.py`.
