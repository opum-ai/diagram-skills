---
name: diagram-architecture
description: Explain and diagram a software system's architecture as C4 views - system context, containers, components - drawn from the actual repository, manifests, compose files and lore docs, never from a generic template. Produces a Mermaid diagram plus a plain-English explanation pitched to the reader (beginner, intermediate or advanced), with every box traced to a real path. Use this skill whenever someone asks how a system or repo is structured, what talks to what, for an architecture overview or C4 diagram, to onboard someone to a codebase, to document services for an arc42 or lore reference doc, or says "draw the architecture", "show me the big picture" or "what are the moving parts" - even if they never say C4 or diagram. For step-by-step flows or lifecycles use diagram-process; for database tables use diagram-data; for task plans use diagram-plan.
---

# diagram-architecture

Answers "what is this system, and what are its parts?" with C4 views that
are true to the repository in front of you. The usual failure is the
template: a model draws the architecture it expects (a load balancer, a
cache, an auth service) instead of the one that exists. Every box here
comes from evidence in the repository, and the checks prove it.

`<engine>` is `${CLAUDE_SKILL_DIR}/../diagram-review/scripts`; shared rules
live in `${CLAUDE_SKILL_DIR}/../diagram-review/references/`.

## Workflow

### 1. Pick the view and the reader

| The reader wants to know | C4 view | Typical size |
|---|---|---|
| What the system is for and who or what it talks to | **Context** | The system, 2–5 people or external systems |
| What runs, where data lives, how the parts talk | **Container** | 4–10 apps, services, datastores |
| What is inside one container | **Component** | 5–12 modules in one container |

Context and container views are enough for most questions (c4model.com). Go
to component level only for one container, on request. Pick the reader's
level as in `levels.md`; it caps nodes at 7, 12 or 20.

### 2. Inventory before drawing

```bash
python3 <engine>/repo_inventory.py --root <repo>
lore query "architecture" --limit 5      # if the repo has a lore bundle
```

The inventory lists deployable units (manifests, Dockerfiles, compose
services), datastores and external services, each with the file that proves
it. Read the README and any architecture doc, and skim each unit's entry
point to learn what it does and how it calls the others: HTTP clients,
queue producers, database drivers. **Only draw what you found.** If the
repository says nothing about how two parts talk, leave the edge out and
say so, rather than guessing a protocol.

### 3. Draw it as a flowchart with C4 classes

Use `flowchart LR` with C4 classes, not `C4Context`, whose parser accepts
malformed input. Name each box the way the reader would, and put the type
and technology in the label:

An illustrative shop (the paths stand in for real ones):

```text
flowchart LR
  accTitle: Container view of the shop
  accDescr: Customers use the web app, which calls the orders API; the API stores orders in Postgres and charges cards through Stripe.
  %% level: intermediate
  customer(["Customer"])
  subgraph shop["Shop (our system)"]
    web["Web app: Next.js"]
    api["Orders API: Python, FastAPI"]
    db[("Orders database: Postgres")]
  end
  stripe["Stripe: card payments"]
  customer -- "browses, orders" --> web
  web -- "calls, JSON over HTTPS" --> api
  api -- "reads and writes, SQL" --> db
  api -- "charges cards, HTTPS" --> stripe
  classDef person fill:#08427b,stroke:#dbe7f3,color:#ffffff
  classDef container fill:#2f6fb5,stroke:#dbe7f3,color:#ffffff
  classDef datastore fill:#1d5c8f,stroke:#dbe7f3,color:#ffffff
  classDef external fill:#686868,stroke:#e0e0e0,color:#ffffff
  class customer person
  class web,api container
  class db datastore
  class stripe external
  %% ref customer = ext:Shoppers using a browser
  %% ref web = path:apps/web
  %% ref api = path:services/orders
  %% ref db = path:docker-compose.yml#postgres
  %% ref stripe = path:services/orders/pyproject.toml#stripe
```

- **People:** stadium `(["..."])`. **Datastores:** cylinder `[("...")]`.
  **External systems:** class `external`. The system boundary is a
  `subgraph`. Copy the palette from `accessibility.md`.
- An outside service the code calls is traced to the code or manifest that
  calls it (`path:...#stripe`), not to `ext:`. `ext:` is for people and for
  systems with no footprint in the repository.
- **Every edge** is one-way and labelled with a verb, plus the protocol
  between containers when you know it ("reads, HTTPS", "publishes to").
- **Every node** gets a `%% ref`: `path:` for anything in the repository,
  `lore:` for a documented concept, `ext:` only for people and outside
  systems. Group units the reader thinks of as one thing. The ref points
  at the directory that holds them.

### 4. Check

Run the three checks in `checks.md` on a scratch `.md` that holds the lead
sentence, the diagram and the explanation. Repair from the error lines until
all three pass.

### 5. Explain

Lead with one sentence saying what the system is. After the diagram, walk
it in the order a request travels, at the reader's level. A beginner gets
plain words and no technology names. An advanced reader gets protocols,
datastores and where the risk sits. End with a legend sentence for the
shapes and colours, for example: "Legend: dark blue boxes are people,
mid-blue are parts we run, grey are outside services, cylinders store
data."

### 6. Persist, when it documents the system

Put it in the architecture Reference doc (`lore query`, then edit, or
`lore new reference "Architecture overview"`), and link the Quest task it
serves (`persisting.md`). Run `lore check`.

## What not to do

- Do not add boxes that the repository does not show: gateways, caches,
  queues, monitoring. If the reader needs to know one is missing, say it
  in the prose.
- Do not mix levels: no classes or functions on a container view.
- Do not draw more than the cap. Split by question instead, for example
  one container view and one component view of the API.

## Reference files

From `${CLAUDE_SKILL_DIR}/../diagram-review/references/`:

- `levels.md`: caps and explanation patterns per reader.
- `mermaid-profile.md`: syntax rules and traps.
- `accessibility.md`: the C4 palette, legends, accTitle/accDescr.
- `truth.md`: `%% ref` kinds and the prose-agreement checklist.
- `checks.md`: the parse, lint and truth loop.
- `persisting.md`: where the doc lives and how to link it.

In this skill: `examples/` holds a worked container view of this repository.
