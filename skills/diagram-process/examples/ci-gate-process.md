# Example: what happens when a pull request is checked

A worked example of diagram-process on this repository's own CI gate,
traced to `.github/workflows/ci.yml`. It shows a flowchart with one lane per
CI job, at intermediate level, followed by a beginner version of the same
answer.

## Intermediate: the gate, step by step

What does CI do to a pull request before it can merge?

```mermaid
flowchart TD
  accTitle: The diagram-skills CI gate
  accDescr: A push to a pull request starts two jobs in parallel. The diagram gate installs the pinned Mermaid parser, parses every diagram, self-tests the gate, lints and runs pytest. The lore check job installs lore and Quest and runs lore check. The pull request can merge only if both jobs pass.
  %% level: intermediate
  push(["Push to a pull request"])
  subgraph gate["Job: diagram gate"]
    install["Install pinned Mermaid parser"]
    parse{"Every diagram parses?"}
    selftest{"Gate self-test passes?"}
    lint{"Lint and pytest pass?"}
  end
  subgraph lorejob["Job: lore check"]
    tools["Install lore and Quest at declared versions"]
    check{"lore check and managed instructions pass?"}
  end
  merge(["Mergeable"])
  blocked(["Blocked: fix and push again"])
  push --> install
  push --> tools
  install --> parse
  parse -- "yes" --> selftest
  selftest -- "yes" --> lint
  tools --> check
  lint -- "yes" --> merge
  check -- "yes" --> merge
  parse -- "no" --> blocked
  selftest -- "no" --> blocked
  lint -- "no" --> blocked
  check -- "no" --> blocked
  %% ref push = path:.github/workflows/ci.yml#pull_request
  %% ref install = path:.github/workflows/ci.yml#Install the pinned Mermaid parser
  %% ref parse = path:.github/workflows/ci.yml#Parse every Mermaid diagram
  %% ref selftest = path:tests/mermaid_selftest.sh
  %% ref lint = path:.github/workflows/ci.yml#Lint diagrams
  %% ref tools = path:.github/workflows/ci.yml#Install lore and quest
  %% ref check = path:.github/workflows/ci.yml#lore check
  %% ref merge = ext:GitHub branch protection allows the merge
  %% ref blocked = ext:GitHub marks the pull request as failing
```

Two jobs start together on every push. The left lane checks diagrams. It
installs the exact Mermaid version GitHub renders, parses every diagram,
then proves the checker still fails broken diagrams before trusting its
passes. Then it lints and runs the tests. The right lane checks the docs
bundle with `lore check`. Any "no" blocks the pull request; only two
"yes" paths reach merge. The self-test step is the one people skip: it is
what stops a broken checker from passing everything.

## Beginner: the same answer

Why can't a broken diagram reach the main docs?

```mermaid
flowchart LR
  accTitle: Why a broken diagram cannot merge
  accDescr: A change is checked automatically; if any diagram is broken or the docs are inconsistent, it is sent back; otherwise it can be merged.
  %% level: beginner
  change(["A change is proposed"])
  checks{"Automatic checks pass?"}
  back(["Sent back to fix"])
  merged(["Can be merged"])
  change --> checks
  checks -- "no" --> back
  checks -- "yes" --> merged
  %% ref change = path:.github/workflows/ci.yml#pull_request
  %% ref checks = path:.github/workflows/ci.yml
  %% ref back = ext:GitHub marks the change as failing
  %% ref merged = ext:GitHub allows the merge
```

Every proposed change is checked by a robot before anyone can merge it. If a
diagram would not display, or the documents disagree with each other, the
change goes back to its author. Only a change that passes every check can be
merged, so readers never see a broken picture.
