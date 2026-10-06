# The check loop

Every diagram skill runs these three checks before a diagram leaves the
session, and loops back to the draft on any error. GenAIScript's repair loop
and the VisPlotBench results show why: feeding the exact parser error back
lifts valid Mermaid from about 69% to about 94%.

`<engine>` is `${CLAUDE_SKILL_DIR}/../diagram-review/scripts`.

## One-time setup

The parse check needs the pinned Mermaid and jsdom (about 180 MB, no
browser):

```bash
npm ci --prefix <engine> --no-audit --no-fund
```

If `npm` is unavailable, say the parse check could not run. Do not report
the diagram as validated.

## The three checks

```bash
node    <engine>/mermaid-check.mjs <file.md|file.mmd|dir>       # 1. it parses (GitHub's Mermaid)
python3 <engine>/diagram_lint.py   <file> [--level beginner]    # 2. profile, a11y, size, explanation
python3 <engine>/diagram_truth.py  --root <repo> <file>         # 3. every node traces to a source
```

| Exit | mermaid-check | diagram_lint | diagram_truth |
|---|---|---|---|
| 0 | Every diagram parses | No errors (warnings allowed) | Every node traced |
| 1 | A syntax error; the message names the line | At least one rule failed | Untraced or unresolved node, or edge mismatch |
| 2 | **Environment error:** fix the install; this is not a verdict on the diagram | Usage | Usage |

For a diagram in a reply rather than a file, write it to a scratch `.md`
file with its lead sentence and explanation, and check that.

## Repairing

- Feed the exact error line back and change only what it names. A full
  regeneration tends to introduce a new error elsewhere.
- Parse errors are almost always one of the traps in `mermaid-profile.md`,
  section 2.
- `node-cap` means split the diagram by question; do not drop nodes the
  question needs.
- `untraced` means find the source or remove the node; do not add an `ext:`
  ref to something inside the repository.
- Stop after three rounds on the same error and tell the user what is
  failing, with the error line.

## What a pass does not prove

The parser accepts some wrong diagrams; see `mermaid-profile.md`, section 5.
The truth check proves each node exists, not that each edge is right,
except for generated plan diagrams. Read the diagram against the prose
checklist in `truth.md`, section 4.
