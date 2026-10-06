# Persisting diagrams in lore and linking them to Quest

A diagram that explains the system belongs in the repository's lore docs,
next to the prose that explains it, so it is reviewed and kept current like
code. A diagram that answers a passing question can stay in the reply.

Persist it when the user asks, or when the diagram documents something that
will still be true next week: an architecture view, a lifecycle, a decision
or a data model. A plan diagram goes stale as tasks move; regenerate it
rather than committing a snapshot, unless the user wants the snapshot.

## Where it goes

Find an existing home before creating one:

```bash
lore query "<subject words>" --limit 5
lore read <id>
```

| Diagram | Doc type | Home |
|---|---|---|
| Architecture (C4) | Reference | `docs/reference/`, the architecture overview |
| Process, lifecycle | Spec or Runbook | The spec that defines it, or the runbook that operates it |
| Decision | ADR | The ADR's Context or Decision section |
| Data model | Spec or Reference | The spec that owns the schema |
| Plan snapshot | Story or Epic | Under the Story's notes, dated |

To create a doc: `lore new reference "<title>"` (or `spec`, `adr`, `runbook`),
then write the prose and the diagram outside any `<!-- lore:... -->` managed
block. Never edit inside a managed block. `lore sync` owns those blocks.

## The shape inside a doc

~~~text
<lead sentence: the question>

```mermaid
...
  %% level: <level>
  %% ref ...
```

<explanation, then a legend sentence if colour or line style means anything>
~~~

## Link it

- **To the Quest task the diagram serves:** name the task id in the
  surrounding prose (for example "Tracked by DSKI-8"). If the doc is a
  Story, couple it with `lore link <story-id> <task-id>` (set
  `LORE_QUEST_ACTOR`, `LORE_QUEST_ACTOR_KIND` and, for an agent,
  `LORE_QUEST_ACCOUNTABLE_HUMAN` first).
- **To a Quest decision:** an ADR that mirrors decision `DEC-N` carries the
  tag `dec-N` and names `DEC-N` in its Status section.
- Every Quest write needs an actor declaration
  (`--actor ... --actor-kind ...`). Agents are `delegated-agent` with
  `--accountable-human`.

## Close the loop

```bash
lore sync      # regenerate managed blocks after any tracker change
lore check     # must exit 0
```

`lore check` does not look inside Mermaid fences, so run the three checks in
`checks.md` as well.
