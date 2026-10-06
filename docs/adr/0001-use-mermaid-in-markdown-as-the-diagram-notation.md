---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: Use Mermaid in Markdown as the diagram notation
tags:
  - notation
  - mermaid
  - dec-1
summary: Mermaid fences in Markdown, written to a conservative syntax profile pinned to GitHub's renderer and gated by a headless parse check; D2 considered as the alternative.
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:14:54.006Z
---

# Use Mermaid in Markdown as the diagram notation

## Status

Accepted (2026-10-05). The owner chose Option A. Tracked by Quest task
DSKI-1 and mirrored as Quest decision DEC-1.

## Context

Every skill in this suite writes diagrams into the lore docs bundle and
into replies. The diagrams are read in three places: on GitHub, in the
terminal, and in an IDE. The owner's starting preference was Mermaid
inside Markdown, and the brief asked for that preference to be tested,
not assumed.

The evidence is in
[State of the art in diagramming](../reference/state-of-the-art-in-diagramming-for-agent-written-docs.md).
Five notations were compared: Mermaid, PlantUML, D2, Structurizr DSL and
Graphviz DOT. The facts that decide it:

- **Where it renders.** GitHub renders only Mermaid from a fenced block.
  VS Code 1.121 and JetBrains also render Mermaid without an extension.
  None of the others renders on GitHub.
- **How reliably a model writes it.** Mermaid has about 2.6 million
  Markdown fences on GitHub, about 45 times PlantUML's count and about 470
  times D2's. Grammar traps exist, but a parse-and-repair loop lifts
  validity from 68.7% to 93.9%.
- **Whether CI can check it.** `mermaid.parse()` under jsdom, pinned to
  GitHub's Mermaid 11.17.2, needs no browser and takes about 40 ms per
  diagram. Locally it passed 28 of 28 valid diagrams and failed 12 of 12
  broken ones. `mmdc` was 640 MB and exited 0 on one broken diagram.
- **What it cannot do well.** Mermaid's C4 support is experimental and its
  parser accepts some malformed C4. Structurizr and C4-PlantUML model C4
  properly, but neither renders on GitHub.
- **What no notation solves.** Models get the boxes roughly right and the
  arrows mostly wrong, and they invent template components. A parser
  cannot catch that. A fidelity check against the source of truth is
  needed whichever notation is chosen.

PlantUML, Structurizr and Graphviz were set aside. PlantUML and Structurizr
need Java and render nowhere the docs are read. Graphviz has no sequence,
state or C4 forms. That leaves two real options.

### Option A (recommended): Mermaid fences in Markdown, guard-railed

Diagrams are ` ```mermaid ` fences inside the lore doc that explains them.
They follow a conservative syntax profile:

- `flowchart` rather than `graph`;
- `stateDiagram-v2`;
- quoted labels;
- no lowercase `end` as an id, and no id starting with `o` or `x`
  directly after an arrow;
- no `@{ shape: }` and no `-beta` types;
- `accTitle` and `accDescr` on every diagram.

C4 views are flowcharts with subgraph boundaries and a fixed set of
C4 classes; `C4Context` is used only for the smallest context view. A
headless parse check, pinned to GitHub's Mermaid version, runs in every
skill's repair loop and as a CI gate.

**Trade-off.** It renders where readers already are and models write it
fluently. The cost is weaker C4 semantics: no model behind the views and
manual layout. The version pin also has to be bumped by hand when GitHub
moves. And Mermaid's layout degrades past about 15 nodes.

### Option B: D2 source with committed SVG and ASCII renders

Diagrams are `.d2` files next to the doc. CI compiles each one with the
pinned `d2` binary. The doc embeds the committed SVG for GitHub and IDEs,
and an ASCII render for the terminal.

**Trade-off.** D2 has better layout and a 17 MB single-binary toolchain.
It compiles in about 30 ms and has built-in terminal output. The costs:

- nothing renders D2 natively, so every diagram becomes two artefacts that
  can drift apart, and every PR diff carries generated SVG;
- the model corpus is thin (about 5.6 thousand Markdown fences), so
  syntax errors will be more frequent;
- the project is pre-1.0 and backed by one company.

## Decision

We will write diagrams as Mermaid fences in Markdown, to the
conservative profile in Option A. A headless parse check, pinned to
GitHub's Mermaid version (11.17.2 on 2026-10-05), will run in each skill's
repair loop and in CI. D2 (Option B) was rejected because nothing renders
it where these docs are read.

## Consequences

Whatever the notation:

- A parse gate catches grammar errors only. Fidelity to the source of
  truth and agreement with the prose need a separate check.
- `lore check` does not look inside diagram source, so the parse gate is
  the only thing that catches a broken diagram before review.

Of this choice:

- The parse checker's Mermaid version is pinned to GitHub's renderer.
  Bumping it is a deliberate change, made after confirming GitHub's
  version with an `info` block.
- C4 views lose model-backed consistency. If one model ever has to feed
  many views, revisit Structurizr, which can export to Mermaid.
