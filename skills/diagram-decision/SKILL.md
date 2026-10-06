---
name: diagram-decision
description: Explain and diagram a technical decision - the question, the options considered, the trade-off of each and the path chosen - for an architecture decision record (ADR), a Quest decision (DEC-N) or a design discussion, plus how decisions relate over time (supersedes, requires). Reads the real ADR and Quest decision, so the chosen path in the picture always matches the record, and pairs the diagram with a plain-English explanation at the reader's level. Use this skill whenever someone asks to visualise or explain an ADR or design decision, compare options with a diagram, show why we chose X over Y, write up a decision for stakeholders, show which decisions superseded which, or add a diagram to an ADR - even if they just say "make the trade-off clear". For the system the decision is about use diagram-architecture; for task plans use diagram-plan.
---

# diagram-decision

Answers "what did we decide, against which options, and why?" A decision
diagram earns its place when a reader must see the alternatives side by side
and see which branch was taken. The record is the authority. The diagram
draws the ADR's options and its Decision exactly, and the checks fail if it
marks a different path as chosen.

`<engine>` is `${CLAUDE_SKILL_DIR}/../diagram-review/scripts`; shared rules
live in `${CLAUDE_SKILL_DIR}/../diagram-review/references/`.

## Workflow

### 1. Read the record

```bash
lore query "<decision topic>" --type ADR --limit 5
lore read adr/<id>
quest decision list --json            # or: quest decision view DEC-N --json
```

Take the options from the ADR's Context (or MADR's Considered Options), the
outcome from its Decision section, and the status from its Status section.
A Quest decision gives `title`, `context`, `outcome` and `status`
(proposed, accepted or superseded). An ADR that mirrors a Quest decision
carries a `dec-N` tag. If the ADR and the Quest decision disagree, report
the disagreement; do not draw either side.

If there is no record yet, as in a live design discussion, draw from what
the user stated. Mark the decision **proposed**, and offer to record it
(`lore new adr`, `quest decision create`).

### 2. Pick the form

| The reader needs | Form |
|---|---|
| The options and the chosen one, with trade-offs | **Options view:** `flowchart TD`, question → options → outcome |
| A choice that depends on conditions | **Decision tree:** `flowchart TD` with diamond conditions |
| How decisions replaced or depend on each other | **History view:** `flowchart LR` of ADRs with `supersedes` and `requires` edges, from `lore graph --json` |

### 3. Draw the options view

```text
flowchart TD
  accTitle: Diagram notation decision
  accDescr: We needed one notation for diagrams; Mermaid was chosen over D2 because GitHub renders it natively.
  %% level: intermediate
  q{"Which diagram notation?"}
  a["Mermaid in Markdown (chosen)<br/>renders on GitHub; weaker C4"]
  b["D2 with committed renders (rejected)<br/>better layout; renders nowhere natively"]
  q -- "option A" --> a
  q -- "option B" --> b
  classDef chosen fill:#e6f4ea,stroke:#1e6b34,stroke-width:3px,color:#111111
  classDef rejected fill:#ffffff,stroke:#8a1c1c,stroke-dasharray:2 2,color:#111111
  class a chosen
  class b rejected
  %% ref q = quest:DEC-1
  %% ref a = lore:adr/0001-use-mermaid-in-markdown-as-the-diagram-notation
  %% ref b = lore:adr/0001-use-mermaid-in-markdown-as-the-diagram-notation
```

- Write "(chosen)", "(rejected)" or "(proposed)" in the label. The colour
  and border repeat it, never replace it.
- Put each option's deciding trade-off in its label, in the ADR's words,
  shortened.
- Cite the question to the Quest decision and the options to the ADR.

### 4. Check, including the chosen path

Run the three checks in `checks.md`. Then confirm by reading: the node
marked chosen is the option the ADR's Decision section names, and the status
in the prose matches the ADR's Status. This is the one error this skill
exists to prevent.

### 5. Explain

Lead with the decision in one sentence, then why, in one or two. After the
diagram, give each option's trade-off in plain words and what the choice
costs us. A beginner gets "we picked the one GitHub shows without extra
work"; an advanced reader gets the version pin and what would reopen it.

### 6. Persist

A decision diagram belongs inside its ADR, under Context or Decision
(`persisting.md`). Keep the ADR's required sections intact. Run `lore check`.

## What not to do

- Do not add options the record does not mention, or drop one it does.
- Do not draw a decision as accepted when the record says proposed.
- Do not draw pros and cons as a wall of boxes; one deciding trade-off per
  option, and the rest in the prose.

## Reference files

From `${CLAUDE_SKILL_DIR}/../diagram-review/references/`:

- `accessibility.md`: the `chosen` and `rejected` classes; legends.
- `levels.md`: caps and explanation patterns per reader.
- `truth.md`: `quest:` and `lore:` refs; the prose-agreement checklist.
- `mermaid-profile.md`: parse traps (quote every label).
- `checks.md`: the parse, lint and truth loop.
- `persisting.md`: diagrams inside ADRs; `dec-N` tags.

In this skill: `examples/` holds a worked options view of a real ADR.
