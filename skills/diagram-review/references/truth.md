# Drawing true diagrams

Models get the boxes roughly right and the arrows mostly wrong, and they
draw the architecture they expect instead of the one in front of them. In
the R2ABench study, node F1 was about 0.5–0.67 against an edge F1 of about
0.09–0.18. This file is the countermeasure: read before drawing, cite
every node, and check that the prose and the picture agree.

## 1. Read the source first

| Diagram | Read | Command |
|---|---|---|
| Architecture | Repository tree, manifests, compose files, lore docs | `python3 <engine>/repo_inventory.py --root .`, then `lore query "<system>" --limit 5` and `lore read <id>` |
| Process | The code or runbook that defines each step | Read the handler, state enum or runbook; note `file#symbol` for each step |
| Decision | The ADR and the Quest decision | `lore read adr/<id>`, `quest decision view DEC-N --json` |
| Plan | Quest tasks and milestones | `python3 <engine>/quest_graph.py deps ...` generates the diagram |
| Data | DDL, migrations or model files | `python3 <engine>/schema_er.py db/migrations` generates the diagram |

`<engine>` is `${CLAUDE_SKILL_DIR}/../diagram-review/scripts`.

If a source cannot be read (no repository access, no Quest workspace), say
so in the explanation and draw only what the user told you. Do not fill
the gap from what systems like this usually contain.

## 2. Cite every node

Add one comment line per node. Renderers ignore it, and `diagram_truth.py`
checks it:

```text
%% ref <node id> = <kind>:<target>
```

| Kind | Target | Resolves when |
|---|---|---|
| `path` | `services/api` or `src/orders.py#place_order` | The path exists, and the symbol after `#` appears in it |
| `schema` | `db/migrations/001_init.sql#orders` | The file defines the table, model, class, type or interface |
| `quest` | `DSKI-5`, `DEC-1`, `M-2` | `quest task/decision/milestone view` finds it |
| `lore` | `adr/0001-use-mermaid-in-markdown-as-the-diagram-notation` | `docs/<id>.md` exists |
| `ext` | free text, e.g. `ext:Customers paying by card` | Always; it is listed as an assertion for a reviewer to judge |

Use `ext` only for people and for systems outside the repository. A box for
something inside the repository that cannot be cited is a sign it was
invented. Remove it, or name it in the prose as an assumption.

For plan diagrams, add `%% edges: quest-dependencies`. The check then
requires the drawn edges to equal Quest's `dependencies` exactly: nothing
missing, nothing extra.

## 3. Check

```bash
python3 <engine>/diagram_truth.py --root . <doc.md>
```

Errors are untraced nodes (no `%% ref`), unresolved refs (the target is
missing) and, for plans, edge mismatches. Fix the diagram, not the ref.

## 4. Make the prose agree with the diagram

A script cannot fully judge this, so walk the checklist before publishing:

1. Every component, step or state the explanation names is in the diagram,
   under the same name.
2. The explanation describes no relationship the diagram does not draw.
   "A calls B" needs an edge from A to B.
3. The direction of every arrow matches the sentence that describes it.
4. If the diagram marks something (chosen, in progress, failed), the prose
   says the same thing about it.
5. Numbers in the prose (counts of services, tasks or tables) match the
   diagram.

When the prose and the diagram disagree, the source decides which one to
fix.
