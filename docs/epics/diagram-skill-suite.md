---
# yaml-language-server: $schema=../../.lore/schemas/epic.schema.json
type: Epic
title: Diagram skill suite
tags:
  - suite
summary: Six skills that make Claude explain and diagram architectures, processes, decisions, plans and data, checked for syntax and truth.
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:57:50.318Z
---

# Diagram skill suite

## Goal

Make Claude consistently explain and diagram architectures, processes,
decisions, data and plans. Each diagram answers one question, is pitched to
the reader's level, is drawn from real records, and is checked for syntax
and truth before it ships.

## Scope

In scope: six skills ([ADR-0002](../adr/0002-six-focused-diagram-skills-sharing-one-engine.md)),
Mermaid in Markdown ([ADR-0001](../adr/0001-use-mermaid-in-markdown-as-the-diagram-notation.md)),
the shared engine, the CI gate, evals and packaging. Out of scope: rendering
to images, non-Mermaid notations, and diagrams outside Markdown docs and replies.

## Stories

- [Validation engine and CI gate](../stories/validation-engine-and-ci-gate.md)
- [Evaluation suite](../stories/evaluation-suite.md)
- [diagram-review skill](../stories/diagram-review-skill.md)
- [diagram-architecture skill](../stories/diagram-architecture-skill.md)
- [diagram-process skill](../stories/diagram-process-skill.md)
- [diagram-decision skill](../stories/diagram-decision-skill.md)
- [diagram-plan skill](../stories/diagram-plan-skill.md)
- [diagram-data skill](../stories/diagram-data-skill.md)
- [Plugin packaging and README](../stories/plugin-packaging-and-readme.md)
