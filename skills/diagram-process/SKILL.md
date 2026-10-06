---
name: diagram-process
description: Explain and diagram how something happens - a workflow, request path, pipeline, approval process, incident runbook or object lifecycle - as a Mermaid flowchart (with swimlanes for who does what), sequence diagram (who calls whom, in what order, including the error path) or state diagram (the states something moves through). Every step is traced to the code, runbook or spec that defines it, and the diagram ships with a plain-English walkthrough at the reader's level. Use this skill whenever someone asks how a process, flow, request, job, deploy, checkout, login, retry or approval works, what happens when X, what order things run in, what states an order or ticket goes through, or wants a flowchart, sequence diagram, swimlane or state machine - even if they only say "walk me through it". For the static structure of a system use diagram-architecture; for decisions use diagram-decision; for data models use diagram-data.
---

# diagram-process

Answers "what happens, in what order, and who does it?" Processes are where
diagrams beat prose: order, branching and hand-offs are hard to hold in a
paragraph. They are also where models drop the steps that matter. Error
paths and activations are the weakest dimension in MermaidSeqBench, so this
skill makes you look for them.

`<engine>` is `${CLAUDE_SKILL_DIR}/../diagram-review/scripts`; shared rules
live in `${CLAUDE_SKILL_DIR}/../diagram-review/references/`.

## Workflow

### 1. Pick the form from the question

| The question is about | Form | Header |
|---|---|---|
| Steps, decisions and who owns each step | Flowchart, with one lane per owner | `flowchart TD` with a `subgraph` per lane |
| Messages between parts, in time order | Sequence | `sequenceDiagram` |
| The states one thing can be in, and what moves it | State machine | `stateDiagram-v2` |

If the question has two of these, draw two diagrams. A beginner gets one: the
flowchart, in plain words. Set the level as in `levels.md`.

### 2. Read the process where it is defined

- **Code:** follow the entry point (route handler, job, CLI command)
  through the calls it makes. Note `file#symbol` for each step: you will
  cite it.
- **State machines:** find the enum or status field and every place that
  assigns it. The transitions are those assignments, not the ones you
  would expect.
- **Runbooks and specs:** `lore query "<process>" --limit 5`, then
  `lore read <id>`. Each numbered step is a node.
- **Then look for what is easy to miss:** the failure branch (timeouts,
  validation errors, retries), the async hand-off, the step a human does.
  If the source has no error handling, the diagram shows none, and the
  prose says so. That is often the finding.

### 3. Draw

**Flowchart (BPMN-lite):** a start and an end as stadiums `(["..."])`,
steps as boxes, decisions as diamonds `{"..."}` with a labelled edge per
outcome, and one `subgraph` lane per owner. Hand-offs between lanes are
the edges worth labelling.

**Sequence:** declare participants in the order they first act. Use `->>`
for a call and `-->>` for a reply. Show the error path with
`alt` / `else` / `end`. Write a semicolon as `#59;`.

**State:** `[*]` for start and end. Every transition is `a --> b : event`;
a line without `-->` silently becomes two unrelated states.

Quote every flowchart label. Give every node, participant or state a
`%% ref` to the code or doc that defines it (`truth.md`). Start from a
template in `mermaid-profile.md`, section 3.

### 4. Check

Run the three checks in `checks.md` on a scratch `.md` with the lead
sentence, the diagram and the explanation. Repair from the error lines.

### 5. Explain

Lead with the one-line answer ("A refund waits for the warehouse to confirm
the return"). Walk the diagram in the order things happen. Name the branch
that fails and what the user sees then. Say who acts at each hand-off. Keep
to the reader's level: a beginner gets "the payment step checks the card
with the bank", an advanced reader gets `charge()` and the timeout value.

### 6. Persist, when it documents the system

A lifecycle or workflow that will stay true belongs in its Spec or Runbook
(`persisting.md`). Name the Quest task it serves, and run `lore check`.

## What not to do

- Do not draw the happy path alone when the source handles failure. If
  the source does not handle failure, say so.
- Do not invent steps to make the flow look complete ("logs the event",
  "notifies the admin") unless the code does them.
- Do not put two processes in one diagram because they share a step.

## Reference files

From `${CLAUDE_SKILL_DIR}/../diagram-review/references/`:

- `mermaid-profile.md`: templates for flowchart, sequence and state; parse traps.
- `levels.md`: caps and explanation patterns per reader.
- `truth.md`: citing each step with `%% ref`; the prose-agreement checklist.
- `accessibility.md`: accTitle/accDescr, legends, palette.
- `checks.md`: the parse, lint and truth loop.
- `persisting.md`: where process diagrams live in lore.

In this skill: `examples/` holds a worked lifecycle from a real repository.
