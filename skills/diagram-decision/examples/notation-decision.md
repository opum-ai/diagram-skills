# Example: the notation decision (ADR-0001, DEC-1)

A worked example of diagram-decision on this repository's first ADR. The
options and the outcome come from
`docs/adr/0001-use-mermaid-in-markdown-as-the-diagram-notation.md` and from
`quest decision view DEC-1 --json`, which agree: Option A, accepted on
2026-10-05.

## Intermediate: the options view

Which notation did we choose for diagrams, and what did we give up?

```mermaid
flowchart TD
  accTitle: Diagram notation decision, ADR-0001
  accDescr: The question was which notation to write diagrams in. Mermaid in Markdown was chosen because GitHub renders it natively; D2 with committed renders was rejected because nothing renders D2 where the docs are read.
  %% level: intermediate
  q{"Which notation for diagrams? (DEC-1, accepted)"}
  a["Option A: Mermaid in Markdown (chosen)<br/>renders on GitHub; weaker C4"]
  b["Option B: D2 + committed SVG (rejected)<br/>better layout; renders nowhere natively"]
  q -- "chosen" --> a
  q -- "rejected" --> b
  classDef chosen fill:#e6f4ea,stroke:#1e6b34,stroke-width:3px,color:#111111
  classDef rejected fill:#ffffff,stroke:#8a1c1c,stroke-dasharray:2 2,color:#111111
  class a chosen
  class b rejected
  %% ref q = quest:DEC-1
  %% ref a = lore:adr/0001-use-mermaid-in-markdown-as-the-diagram-notation
  %% ref b = lore:adr/0001-use-mermaid-in-markdown-as-the-diagram-notation
```

We chose Mermaid inside Markdown because GitHub, VS Code and JetBrains show
it without any build step, and models write it fluently. The cost is
weaker C4 support and a version pin to maintain. D2 lays diagrams out
better, but nothing renders it where our docs are read. Every diagram would
become a source file plus a generated image that can drift apart. The
decision is accepted (DEC-1) and was made by the repository owner.

Legend: the thick green border marks the chosen option; the dotted red
border marks the rejected one. Each label also says "chosen" or
"rejected".

## Beginner: the same decision

What did we pick, and why?

```mermaid
flowchart LR
  accTitle: Which drawing format we picked
  accDescr: We picked the format GitHub shows on its own, over a tidier format that would need extra picture files.
  %% level: beginner
  q{"Which drawing format?"}
  a["The one GitHub shows by itself (picked)"]
  b["A tidier one needing extra picture files (not picked)"]
  q --> a
  q --> b
  %% ref q = quest:DEC-1
  %% ref a = lore:adr/0001-use-mermaid-in-markdown-as-the-diagram-notation
  %% ref b = lore:adr/0001-use-mermaid-in-markdown-as-the-diagram-notation
```

We picked the drawing format that GitHub displays on its own. The other
format draws tidier pictures, but every picture would need a second,
generated image file kept in step with it, which is easy to forget. Showing
up correctly everywhere mattered more than tidier layout.
