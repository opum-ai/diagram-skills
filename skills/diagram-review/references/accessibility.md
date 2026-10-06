# Accessibility

Three rules, each from WCAG 2.2, and how to meet them in Mermaid.

## 1. A text alternative, short and long (WCAG 1.1.1)

Every diagram starts with:

```text
  accTitle: <names the diagram: what it is of>
  accDescr: <the claim in one or two sentences, as if read aloud>
```

Mermaid turns these into the SVG's `<title>` and `<desc>`, linked with
`aria-labelledby` and `aria-describedby`. They parse in flowchart,
sequence, stateDiagram-v2, erDiagram, classDiagram and gantt. They break
`mindmap`, which is one reason mindmaps are outside the profile.

- `accTitle` names the diagram: "Order lifecycle", not "Diagram".
- `accDescr` states what the diagram shows, not how it looks: "An order is
  placed, paid, then shipped or refunded", not "Five boxes and arrows".
- For long descriptions use the block form `accDescr { ... }`.
- The prose explanation after the fence is the **long description**. W3C's
  complex-images guidance wants it adjacent to the image, which it is.

## 2. Colour is never the only signal (WCAG 1.4.1)

Whenever colour means something, say it a second way:

- in the label text, e.g. "(done)", "(chosen)", "Container: Postgres";
- with a line style: thick for in progress, dashed for to do, dotted for
  rejected or closed;
- with a shape: cylinder `[("...")]` for a datastore, stadium `(["..."])`
  for start and end, diamond `{"..."}` for a decision.

Explain every encoding in a legend sentence after the diagram. The lint
fails a diagram that uses `classDef` without a legend or key.

## 3. Contrast (WCAG 1.4.3 and 1.4.11)

Text needs 4.5:1 against its fill. A shape's boundary needs 3:1 against
whatever is next to it. Diagrams render on both light and dark pages, so
pair each fill with a stroke that covers the other theme:

- **light fill, dark stroke:** the stroke carries the boundary on a white
  page, and the fill carries it on a dark page;
- **dark fill, light stroke:** the reverse.

Measured palette (contrast ratios computed 2026-10-05):

| Class | Fill | Text | Stroke | Text contrast |
|---|---|---|---|---|
| `person` | `#08427b` | `#ffffff` | `#dbe7f3` | 10.1:1 |
| `system` | `#1168bd` | `#ffffff` | `#dbe7f3` | 5.6:1 |
| `container` | `#2f6fb5` | `#ffffff` | `#dbe7f3` | 5.2:1 |
| `component` | `#85bbf0` | `#111111` | `#0b3d6e` | 9.3:1 |
| `external` | `#686868` | `#ffffff` | `#e0e0e0` | 5.6:1 |
| `datastore` | `#1d5c8f` | `#ffffff` | `#dbe7f3` | 7.1:1 |
| `chosen` | `#e6f4ea` | `#111111` | `#1e6b34`, 3px | 16.6:1 |
| `rejected` | `#ffffff` | `#111111` | `#8a1c1c`, dotted | 18.9:1 |

C4's usual container blue `#438dd5` gives white text only 3.5:1, so this
suite uses `#2f6fb5` instead. Copy the `classDef` lines from here rather
than inventing colours:

```text
  classDef person fill:#08427b,stroke:#dbe7f3,color:#ffffff
  classDef system fill:#1168bd,stroke:#dbe7f3,color:#ffffff
  classDef container fill:#2f6fb5,stroke:#dbe7f3,color:#ffffff
  classDef component fill:#85bbf0,stroke:#0b3d6e,color:#111111
  classDef external fill:#686868,stroke:#e0e0e0,color:#ffffff
  classDef datastore fill:#1d5c8f,stroke:#dbe7f3,color:#ffffff
  classDef chosen fill:#e6f4ea,stroke:#1e6b34,stroke-width:3px,color:#111111
  classDef rejected fill:#ffffff,stroke:#8a1c1c,stroke-dasharray:2 2,color:#111111
```

`quest_graph.py` uses its own status classes (done, in progress, to do,
paused), which follow the same light-fill, dark-stroke rule.
