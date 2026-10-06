# Example: the architecture of diagram-skills, at two levels

A worked example of diagram-architecture on this repository. The same system
is drawn twice: as a context view for a beginner and as a container view for
an intermediate reader. Every box is traced to the repository with
`%% ref`, and the inventory came from `repo_inventory.py --root .`.

## Beginner: what is it for?

What does diagram-skills do, and who does it work with?

```mermaid
flowchart LR
  accTitle: What diagram-skills does
  accDescr: A person asks Claude for a diagram; Claude uses the diagram skills, which read the project's docs and task list and write a checked diagram back into the docs that GitHub shows.
  %% level: beginner
  you(["You"])
  claude["Claude"]
  skills["Diagram skills"]
  docs["Project docs"]
  tasks["Task list"]
  github["GitHub"]
  you -- "asks for a diagram" --> claude
  claude -- "follows" --> skills
  skills -- "read" --> tasks
  skills -- "read and write" --> docs
  github -- "shows" --> docs
  %% ref you = ext:A person working in the repository
  %% ref claude = ext:Claude Code, the agent harness the skills run in
  %% ref skills = path:skills
  %% ref docs = path:docs
  %% ref tasks = path:.quest
  %% ref github = ext:GitHub.com, which displays the docs
```

You ask Claude for a picture of your project. Claude follows the diagram
skills, which look at the project's real documents and task list instead of
guessing. The finished picture goes back into the documents, where GitHub
displays it. "Task list" is where the team records what is planned and
done.

## Intermediate: what are the parts?

What runs where, and how do the parts talk to each other?

```mermaid
flowchart LR
  accTitle: Container view of diagram-skills
  accDescr: Claude Code loads six skills; the skills call one engine that parses, lints and traces diagrams, reading Quest tasks and the lore docs bundle. CI runs the same engine and lore check on every pull request, and GitHub renders the Mermaid.
  %% level: intermediate
  user(["Developer"])
  claude["Claude Code: agent harness"]
  subgraph repo["diagram-skills repository"]
    skills["Six skills: SKILL.md + references"]
    engine["Engine: Node parse check, Python lint, truth, generators"]
    docs[("Docs bundle: lore Markdown")]
    tracker[("Tracker records: Quest JSON")]
    ci["CI gate: GitHub Actions"]
  end
  quest["Quest CLI"]
  lore["lore CLI"]
  github["GitHub: renders Mermaid"]
  user -- "asks" --> claude
  claude -- "loads" --> skills
  skills -- "run" --> engine
  engine -- "parses, lints, traces" --> docs
  engine -- "reads tasks via" --> quest
  quest -- "reads, writes" --> tracker
  ci -- "runs" --> engine
  ci -- "runs lore check with" --> lore
  lore -- "validates" --> docs
  github -- "renders" --> docs
  classDef person fill:#08427b,stroke:#dbe7f3,color:#ffffff
  classDef container fill:#2f6fb5,stroke:#dbe7f3,color:#ffffff
  classDef datastore fill:#1d5c8f,stroke:#dbe7f3,color:#ffffff
  classDef external fill:#686868,stroke:#e0e0e0,color:#ffffff
  class user person
  class skills,engine,ci container
  class docs,tracker datastore
  class claude,quest,lore,github external
  %% ref user = ext:A developer using Claude Code in a repository
  %% ref claude = ext:Claude Code, which loads skills from the plugin
  %% ref skills = path:skills
  %% ref engine = path:skills/diagram-review/scripts
  %% ref docs = path:docs
  %% ref tracker = path:.quest
  %% ref ci = path:.github/workflows/ci.yml
  %% ref quest = path:skills/diagram-review/scripts/diagram_truth.py#quest
  %% ref lore = path:.github/workflows/ci.yml#lore
  %% ref github = ext:GitHub.com
```

A developer asks Claude Code for a diagram. Claude Code loads one of the six
skills, and each skill calls the same engine. The engine parses the diagram
with the Mermaid version GitHub uses, lints it, and traces every box to a
file or record. For plans it reads tasks through the Quest CLI. Every pull
request runs that engine again in CI, together with `lore check` on the docs
bundle, and GitHub renders the result. We verified each box against the
repository with `diagram_truth.py`. The Quest CLI, the lore CLI and GitHub
are tools we call, not parts we ship.

Legend: dark blue rounded box is a person; mid-blue boxes are parts this
repository ships; cylinders hold data; grey boxes are outside tools and
services. The type is also written in each label.
