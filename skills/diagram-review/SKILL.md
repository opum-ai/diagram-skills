---
name: diagram-review
description: Validate and critique Mermaid diagrams in Markdown docs, ADRs, READMEs, PR descriptions or a reply. Checks that each diagram parses under the Mermaid version GitHub renders, follows the accessible profile (accTitle/accDescr, quoted labels, legend, colour never the only signal), stays within the reader's node cap, and is true - every node traced to a real file, Quest record or lore doc, with prose that says what the picture shows. Use this skill whenever someone asks to check, review, lint, validate, fix or audit a diagram, when a Mermaid diagram fails to render on GitHub, when a docs PR adds or changes diagrams, or before publishing any diagram another diagram-* skill drew, even if they only say "does this look right". Also owns the shared engine and references the other diagram skills use. To draw a new diagram, use diagram-architecture, diagram-process, diagram-decision, diagram-plan or diagram-data instead.
---

# diagram-review

Checks diagrams the way a careful reviewer would. The first two questions are
cheap and mechanical: does it render, and does it follow the rules? The third
is the one that matters: is it true? The other five diagram skills draw;
this one judges, and it owns the engine they all call.

| Skill | Draws |
|---|---|
| diagram-architecture | C4 context, container and component views |
| diagram-process | Flows, lanes, sequences and state machines |
| diagram-decision | ADR and Quest decision diagrams |
| diagram-plan | Quest dependency and milestone views |
| diagram-data | ER and schema diagrams |

`<engine>` below is `${CLAUDE_SKILL_DIR}/scripts`. Sibling skills reach it at
`${CLAUDE_SKILL_DIR}/../diagram-review/scripts`.

## Workflow

### 1. Find the diagrams

Take the files the user names. With none named, take the Markdown files
changed on the branch (`git diff --name-only origin/dev...HEAD -- '*.md'`), or
ask. A diagram pasted into chat goes into a scratch `.md` file with the prose
around it.

### 2. Run the three checks

Set up once with `npm ci --prefix <engine> --no-audit --no-fund`. Then:

```bash
node    <engine>/mermaid-check.mjs <paths>
python3 <engine>/diagram_lint.py   <paths> [--level beginner|intermediate|advanced]
python3 <engine>/diagram_truth.py  --root <repo root> <paths>
```

Exit 2 from the parse check is an install problem, not a verdict. Fix the
install or report that the parse check could not run; never call an
unchecked diagram valid. `references/checks.md` explains every exit code and
rule.

### 3. Read each diagram as a reviewer

The scripts cannot judge everything. For each diagram, answer:

1. **One question.** Does the sentence before it say what it answers, and
   does every node serve that question? Two questions means two diagrams.
2. **Labels.** Does every edge have a verb? Can a reader name every box
   without opening the code?
3. **Prose agreement.** Walk the checklist in `references/truth.md`,
   section 4. Every component the explanation names is drawn, every
   relationship it claims has an edge in the right direction, and every
   count matches.
4. **Truth beyond refs.** A `%% ref` proves the node exists, not that the
   edge is right. Spot-check the two or three edges the claim depends on
   against the code or records.
5. **Level.** Do the node count, the labels and the explanation fit the
   reader (`references/levels.md`)?
6. **External assertions.** List every `ext:` ref. Each should be a person
   or a system outside the repository.

### 4. Report

Lead with the verdict per diagram: **pass**, **fix** or **redraw**. Then list
the findings, most serious first: false before broken, broken before
unclear. Each finding names the location (`file:line`), what is wrong, and
the exact fix. Quote the corrected Mermaid lines for syntax and labelling
fixes. Keep it at the user's level; a beginner gets the verdict and the one
fix that matters, not the rule names.

### 5. Fix, if asked

Change only what the findings name, then re-run all three checks and show
that they pass. A diagram that cannot be traced to a source gets its
invented nodes removed, or named in the prose as assumptions. It does not
get an `ext:` ref to make the check pass.

## In CI

`.github/workflows/ci.yml` runs the parse check over `docs/` and `skills/`,
self-tests the gate (`tests/mermaid_selftest.sh` proves broken diagrams fail
and fixed ones pass), lints, and runs `lore check`. `lore check` never looks
inside a Mermaid fence, so this gate is the only one on diagram syntax.

## Honesty rules

- A check that did not run is reported as not run, not as passed.
- A pass on all three checks means "renders, follows the rules, every node
  exists". It does not mean every arrow is right. Say so when it matters.
- Do not soften a finding that the diagram contradicts its source; that is
  the finding the user most needs.

## Reference files

- `references/checks.md`: the three checks, exit codes, repair loop and limits.
- `references/mermaid-profile.md`: allowed types, parse traps, safe templates, comment conventions.
- `references/accessibility.md`: accTitle/accDescr, colour and legends, the measured palette.
- `references/levels.md`: beginner, intermediate and advanced caps and explanations.
- `references/truth.md`: reading the source, `%% ref` kinds, the prose-agreement checklist.
- `references/persisting.md`: where diagrams live in lore and how they link to Quest.
- `scripts/`: `mermaid-check.mjs`, `diagram_lint.py`, `diagram_truth.py`, and the generators `quest_graph.py`, `schema_er.py`, `repo_inventory.py`.
