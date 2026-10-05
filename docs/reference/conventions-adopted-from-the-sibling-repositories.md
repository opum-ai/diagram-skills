---
# yaml-language-server: $schema=../../.lore/schemas/reference.schema.json
type: Reference
title: Conventions adopted from the sibling repositories
tags:
  - conventions
  - ecosystem
summary: Every convention diagram-skills adopts, the sibling it came from, and the deliberate deviations.
generated:
  by: lore/0.12.0
  at: 2026-10-05T19:30:29.810Z
---

# Conventions adopted from the sibling repositories

Reviewed 2026-10-05, read-only, under Quest task DSKI-2. Siblings live
under `/Volumes/external/repos`. Paths below are relative to each
sibling's root. Nothing in any sibling was modified.

**Which sibling sets the pattern.** test-skills and housekeeping-skills
(both last committed 2026-09-27) are the most mature. proof-skills is the
oldest (2026-09-25). profile-skills has no commits yet, so it is used only
where it confirms the others.

## 1. Adopted conventions

### Packaging

| Convention | Source |
|---|---|
| The repository root is the plugin root; `.claude-plugin/plugin.json` sits at the top | proof-skills `README.md` "Repository layout" (moved there in 0.1.1); housekeeping-skills |
| `plugin.json` has nine fields: `name`, `displayName`, `description`, `version`, `author{name: "Opum AI", url: "https://github.com/opum-ai"}`, `homepage`, `repository`, `license: "MIT"`, lowercase `keywords` | proof-skills and housekeeping-skills `.claude-plugin/plugin.json` (test-skills omits `homepage`/`repository`; we follow the fuller two) |
| `LICENSE` is MIT, `Copyright (c) 2026 Opum AI` | all four siblings |
| No marketplace file in the repository; distribution is an entry in `opum-marketplace` pinned to a release tag | `opum-marketplace/.claude-plugin/marketplace.json` |
| Local development through `.claude/skills/<name>` symlinks to `../../skills/<name>` | proof-skills, test-skills, profile-skills |

### Skills

| Convention | Source |
|---|---|
| `skills/<name>/SKILL.md` frontmatter holds only `name` and a long, trigger-rich `description` (about 700–1,100 characters) that says when to fire and routes to sibling skills | all 21 sibling SKILL.md files, e.g. proof-skills `skills/formal-verify/SKILL.md:3` |
| Body: `# <name>`, a short framing intro, a workflow section, a rules section, and last a `## Reference files` list; about 110–150 lines | proof-skills `skills/formal-verify/SKILL.md:145-153`; test-skills |
| `references/`, `scripts/`, `assets/` under each skill; scripts are reached through `${CLAUDE_SKILL_DIR}`, and shared ones through `${CLAUDE_SKILL_DIR}/../<owner>/scripts/` | test-skills `skills/test-plan/SKILL.md:53`; proof-skills `skills/formal-verify/SKILL.md:20-21` |
| One skill owns shared references and scripts; its siblings reach into it | proof-skills `formal-verify`; test-skills |
| Focused skills; a router skill only where users need one entry point | proof-skills ADR-0001; housekeeping-skills ADR-0001 |
| Engines are Python standard library only | test-skills ADR-0005; housekeeping-skills ADR-0003 |
| Diagram rules already in the family: one claim per figure, every arrow labelled, draw the system the problem lives in | proof-skills `skills/formal-verify/references/report-artifact.md:49-70` |

### Evaluation and tests

| Convention | Source |
|---|---|
| `evals/evals.json`: `{skill_name, evals: [{id, name, fixture, expected_skill, prompt, expected_output, assertions, files}]}` | test-skills `evals/evals.json`; housekeeping-skills adds `preamble` |
| Fixtures under `evals/fixtures/<name>/`, built per run; run workspaces git-ignored | housekeeping-skills `.gitignore`; proof-skills `docs/runbooks/run-skill-evals.md` |
| An objective grader `evals/grade.py` that re-derives the truth and never trusts the agent's own claims; writes `grading.json` as `{expectations: [{text, passed, evidence}], summary}` | test-skills `evals/grade.py:1-8`; housekeeping-skills `evals/grade.py:1-8` |
| With-skill vs without-skill results committed as `evals/benchmarks/iteration-N/benchmark.{json,md}`, 3 runs per arm, mean ± sd and delta | test-skills `evals/benchmarks/iteration-1/`; housekeeping-skills `iteration-2/benchmark.md` |
| Trigger sets per skill: about 5 should-fire and 3 near-miss queries | housekeeping-skills `evals/trigger_sets/`; `docs/stories/skill-evaluation-suite.md` |
| pytest in `tests/` with a `conftest.py` that puts the scripts on `sys.path` | housekeeping-skills `tests/conftest.py`; test-skills `pytest.ini` |
| CI on pull requests runs pytest plus the suite's own gate; evals stay out of CI because of cost | test-skills `.github/workflows/ci.yml`; proof-skills `README.md` (trigger suite about $25) |

### Docs, tracker and governance

| Convention | Source |
|---|---|
| CLAUDE.md is managed blocks only; a suite that governs agent behaviour adds its own namespaced block `<!-- <plugin>:<topic>:begin -->` | test-skills `CLAUDE.md:22-43` |
| README sections: pitch, Why, The skills (table), the concept, Install, Usage, Evaluation, Repository layout, Development, Known limitations, License | test-skills, proof-skills and housekeeping-skills `README.md` |
| lore bundle: one Epic; one Story per skill plus an evaluation-suite Story; Specs for contracts; `docs/reference/state-of-the-art-in-<topic>.md` research | test-skills, housekeeping-skills, proof-skills `docs/` |
| ADRs through `lore new adr`, numbered `docs/adr/NNNN-slug.md`, with Status, Context, Decision, Consequences; Status reads "Accepted (date)" | test-skills `docs/adr/0004-*.md`; lore-cli `src/commands/new.ts:296-323` |
| An ADR that mirrors a Quest decision carries a `dec-N` tag and names `DEC-N` | lore-cli `docs/adr/0028-*.md` |
| Story ↔ Task coupling through `lore link`, which owns the `<!-- lore:tasks:begin -->` block | lore-cli `src/commands/link.ts`; housekeeping-skills stories |
| Governance is a prose spec plus a machine-checked TOML, enforced by a gate in CI, changed only by commit to both | test-skills `TEST-CONSTITUTION.md`, `test-policy.toml`, ADR-0004 |
| Named levels with the middle as default | test-skills R1–R5; housekeeping-skills Minimal–Immaculate |

## 2. Deliberate deviations

- **The parse checker is Node, not Python.** Mermaid's grammars exist only
  as JavaScript, and the checker that was proven both ways is
  `mermaid.parse()` under jsdom (see ADR-0001). Everything else (source
  extraction, linting, graders) stays standard-library Python, as the
  siblings do.
- **Governance is lighter than test-skills'.** There is no constitution.
  A diagram policy (node caps per level, required accessibility fields)
  ships as a Spec plus a TOML only because the suite ships the checker
  that enforces it. R1–R5 rigor profiles are not imported; the reader
  levels below are the density axis instead.
- **proof-skills' `graph_svg.py` is not reused for now.** It draws SVG for
  Artifacts and plain HTML files. This suite writes Mermaid into Markdown
  (ADR-0001), where GitHub and the IDEs render it natively.

## 3. What lore and Quest give a diagram skill

### lore does not check Mermaid

`lore check` and `lore validate` never parse a Mermaid fence. There are
no "mermaid" hits anywhere in lore-cli's `src`, `test` or `types`. A fence
is an ordinary code node: link extraction skips it
(`src/core/bundle.ts:999-1029`), and so do the portability and heading
scans (`src/core/check.ts:1237`, `:1327-1333`). **A broken diagram passes
`lore check`,** so this suite must ship its own parse gate.

lore-cli's own `docs/reference/architecture.md:31-88` shows the house
pattern: one sentence stating the claim, then the diagram, then a table
naming every box.

### Read commands for true diagrams

| To draw | Read | Fields |
|---|---|---|
| Task dependency graph | `quest task list --json` | `data[].{id, title, status, dependencies[], parentId}` — no `blockedBy` or `subtasks`; invert `parentId` for children |
| Status colouring | `quest task status-flow --json` | `terminalStatuses`, `pausedStatus`, `closedStatus` |
| Milestone view | `quest milestone list --json` | `data[].{id, title, status, taskIds[], archived}`, joined with each task's `milestoneId`; the two can disagree, so take the union and flag mismatches |
| Decision view | `quest decision list --json` | `data[].{id, title, context, outcome, status}`; no task links, so join to ADRs by the `dec-N` tag |
| Doc relationships | `lore graph --json` | `nodes[]{id, type, title}`, `edges[]{from, to, kind}` with kinds `link`, `supersedes`, `superseded_by`, `requires`, `alternative`, `refutes` |
| Epic → Story → Task | `lore export` (JSONL) | `concept`, `task` and `edge` records, including task `dependency` edges |
| One doc | `lore query "<words>"`, then `lore read <id> --json` | `id, path, type, frontmatter, body` |

Two cautions. `quest manifest` lists `task list` fields without
`dependencies`, `parentId` or `milestoneId`, but real output carries them
when they are set; unset fields are omitted. And lore's Quest adapter reads
`task.milestone` (lore-cli `src/adapters/quest.ts:924`) while Quest writes
`milestoneId`, so milestones come out null in `lore export`. Read
milestones from Quest directly. That mismatch is worth reporting to
lore-cli.

## 4. How diagrams pair with the explanation levels

plain-english-styles defines three readers
(`docs/specs/style-contracts-by-audience-level.md:45-77`):

- **beginner:** a smart executive who does not write code; about 80 words.
- **intermediate:** a product owner; about 100 words.
- **advanced:** a staff-engineer-level reader; under 120 words.

The styles never mention diagrams. Their harness counts a Mermaid fence as
a code block (`harness/src/checks.mjs:333`). That cap is lifted when the
reader asks for code, and a request for a diagram is such an ask. So the
rule is: **draw when asked or when the answer has a shape, keep the fence
out of the word count, and never let the diagram replace the
explanation.**

| | Beginner | Intermediate | Advanced |
|---|---|---|---|
| Diagrams per answer | At most one, only when the answer has a shape | One | More than one if each answers a different question |
| Node cap | 7 | 12 | 20, then split |
| Labels | Plain words; no ids, acronyms or jargon | Real names, glossed on first use | Ids and precise terms |
| Structure | `flowchart LR`, no subgraphs, at most one highlight | One level of grouping; verbs on edges; a legend if colour or line style means anything | Subgraphs, several edge kinds, critical path |
| Prose | The conclusion first, then the diagram, then one line per unclear box | Context and how it was verified, then the diagram, then the one thing to act on | The claim, the mechanism and the action; prose may be shorter than the diagram |

The caps come from the research, not from plain-english-styles. The
evidence supports about 9 nodes as a target and 20 as a hard split; the
beginner cap sits below that target because that reader has no codebase
to hang the boxes on. The pairing is measured the way plain-english-styles
measures its styles: deterministic checks blended with a judge. The
checks are that the diagram parses, its node count is within the level's
cap, accessibility fields are present, and every node exists in the
source. The judge asks whether the diagram makes the claim faster to
grasp than the prose alone.
