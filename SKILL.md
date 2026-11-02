---
name: dsh-second-brain
description: >-
  Use when setting up or extending a second-brain layout: scaffold AGENTS.md
  and knowledge dirs, and install or ensure weekly-review, people-notes, and
  draft-writing under .agents/skills/.
---
# Second brain setup

Scaffold a layered second brain in a project: a short global map, on-demand workflow skills, and file-backed memory. This file is the setup skill. The three workflows stay in `.agents/skills/` and are not copied here.

Layout follows [Agent Skills](https://agentskills.io/specification): each skill is `<name>/SKILL.md`. Prefer `.agents/skills/` so DSH and Cursor can discover them. Do not add a parallel root `skills/` tree unless the user asks for marketplace packaging.

Public reference pack: https://github.com/Ficere/dsh-second-brain

## When to load

- User wants a second brain, or an `AGENTS.md` plus skills layout
- User asks to scaffold, migrate from `CLAUDE.md` / `.claude/skills`, or add weekly review, people notes, or draft workflows
- User mentions the DSH instruction budget (64 KB), `.agents/skills`, or `.dsh/skills`

## Goals

1. Scaffold a lean project map and knowledge folders.
2. Install the three workflow skills as `<name>/SKILL.md` (kebab-case; frontmatter `name` + `description`).
3. Wire optional cross-session memory as files the user chose. Do not invent a fake auto-memory layer.
4. For a shareable pack, ship a README whose skill-index descriptions match frontmatter exactly.

Keep paths and tone generic. Put person-specific focus, repo paths, and approval policies in the target project, not in this recipe.

## Layer map

| Layer | Claude Code | This layout |
| --- | --- | --- |
| Global map | `CLAUDE.md` | Root `AGENTS.md` (keep short; DSH instruction files ≤ ~64 KB) |
| Local rules | `.claude/rules/` + paths | Encode as skills, or a nested `AGENTS.md` only if that loader is verified |
| Workflows | `.claude/skills/` | `.agents/skills/<name>/SKILL.md` (Cursor and DSH). `.dsh/skills/` ranks higher for DSH-only |
| Memory | Auto memory | Workspace `.memory/` + optional machine-global `~/.dsh/global-memory/` (skill/plugin) |

DSH local discovery order: `.dsh/skills` → `.agents/skills` → custom paths → `~/.dsh/skills` → `~/.agents/skills`. Bundles are one level (`name/SKILL.md`). Skills reload each step.

## Preference check

Ask one question only if the answer is missing:

1. Target root: existing git project, or a new `second-brain/` folder.
2. Skill root: `.agents/skills` (default) or `.dsh/skills` (DSH-first).
3. Memory: (A) `.memory/` plus a line in `AGENTS.md`, (B) another memory skill the user names, or (C) global graph skill/plugin for cross-workspace. Do not install third-party skills without an explicit yes.

If they already answered, proceed.

## Part A — Scaffold

### 1. Create layout

```text
<project-root>/
├── README.md
├── CONTRIBUTING.md
├── SKILL.md           # this setup skill, when the pack itself is the project
├── AGENTS.md
├── CLAUDE.md          # optional symlink → AGENTS.md
├── decisions.md
├── notes/
├── people/
├── projects/
├── drafts/
├── .memory/
│   ├── MEMORY.md
│   └── logs/
└── .agents/skills/
    ├── weekly-review/
    ├── people-notes/
    └── draft-writing/
```

Create missing dirs. Do not overwrite a non-empty `AGENTS.md` or `decisions.md` without confirming; offer a merge or diff. Do not empty-create `scripts/`, `assets/`, or `evals/` under skills.

### 2. Write lean `AGENTS.md`

Target about 80 lines, well under the shared 64 KB budget. Include only always-on facts: the directory map, answer style, a placeholder for 1–3 focus items, and the append-only rule for `decisions.md`. Hard blocks (delete, force-push, history rewrite) belong in the host approval policy.

```markdown
# Second brain · global map

## Layout
- `projects/`: one file per project — required fields: status / last stopped / next
- `decisions.md`: append-only — `date | decision | why | alternatives`
- `people/`: one file per person or org
- `notes/`: one topic per file
- `drafts/`: writing drafts
- `.memory/`: cross-session notes (if present); verify on disk, do not trust chat-only “I remembered”

## How to answer
- Match the user’s language; lead with the answer; tables before long prose when comparing
- Unverified claims → mark as 待核实 / unverified

## Current focus
- [fill 1–3 priorities]

## Soft rules
- Append to `decisions.md`; never edit past rows in place
- Prefer loading a skill over stuffing long procedures into this file
- Keep this file short; put workflows in `.agents/skills/*/SKILL.md`
- If `.memory/` exists, read `.memory/MEMORY.md` at session start and append durable prefs when the user asks to remember something
```

Optional: symlink `CLAUDE.md` to `AGENTS.md` when Claude Code should share the same map.

### 3. Seed knowledge files

- `decisions.md` with a one-line header for the append format
- Optional `projects/_template.md` with status / last stopped / next
- Optional `people/_template.md` with a last-contact date field

## Part B — Workflow skills

Write each as `<skill-root>/<name>/SKILL.md`. Frontmatter: `name`, `description`, and `user-invocable: true` when the user should call it by name. Folder name equals frontmatter `name`. Copy the three skills from this pack (`.agents/skills/`) or write them to match it. Do not duplicate them into the setup skill.

- **weekly-review** — Read `projects/*.md` (skip templates). List status, last stopped, and next. Flag blockers and people whose last contact is older than 30 days or missing. On confirm, append new decisions. Write `drafts/weekly-YYYY-MM-DD.md`. If `.memory/` exists, append a log line under `.memory/logs/`.
- **people-notes** — Resolve `people/<kebab-name>.md`. Create from the people template if missing. Update only stated facts. Set last contact when a touch happened. Do not invent history. End with a short diff.
- **draft-writing** — Read `AGENTS.md` and named files under `notes/` or `projects/`. Draft in `drafts/<slug>.md`. Do not publish. Return the path and what is still open.

After writing, list the skill paths. Invoke by skill name; catalogs refresh without a restart. Add `references/` only when a body would exceed about 500 lines.

## Part C — Cross-session memory

There is no automatic chat memory. Use the option the user chose:

- **A — Files only:** `.memory/MEMORY.md` and `.memory/logs/`, plus the `AGENTS.md` bullet to read memory at session start and append when asked to remember.
- **B — Another skill:** install only the memory skill they named, and only after they agree.
- **C — Global graph (recommended for cross-workspace):** install `.agents/skills/global-memory` and optionally the Cordis plugin `plugins/dsh-second-brain-memory` into the **web** profile (`dsh plugin --profile web add …`). Store lives at `~/.dsh/global-memory/` (graph + nodes). GUI session start loads a compact index;「记到全局」upserts. Memory tab (List/Graph/Timeline) is separate from Trajectory. See `docs/global-memory.md`.

Tell them to open the files on disk (or the Memory tab). A claim in chat is not a write.

## Part D — Smoke checks

1. New session: “What is the status of project X?” with a filled `projects/x.md` — answer without re-explaining the layout.
2. Invoke `weekly-review` — a draft under `drafts/`, and no silent rewrite of old `decisions.md` rows.
3. If memory is enabled: a preference saved in session A is visible in files and read in session B.
4. An attempt to rewrite a historical decisions row may warn in prose. A hard block needs the host approval policy.

Report what was created, what was skipped, and any confirmation still needed.

## README outline for a shared pack

1. One-line positioning (EN + ZH is fine)
2. Directory map (path → role), including root `SKILL.md` as the setup skill
3. Skill index: name, description copied from frontmatter, when to use, deps
4. Install and discovery paths (DSH order; Cursor also scans `.agents/skills`)
5. One example invoke per workflow skill
6. How to add a skill
7. Instruction budget and hard constraints
8. License and CONTRIBUTING

## Hard constraints

- Do not bloat `AGENTS.md` with long procedures.
- Do not treat markdown prohibitions as a sandbox. Call out approval policy for deletes, force-pushes, and history edits.
- Do not overwrite user content without confirm.
- Do not install third-party skills without an explicit yes.
- Do not empty-create `scripts/`, `assets/`, or `evals/`.

## Done criteria

- Layout exists and `AGENTS.md` is short and accurate
- The three workflow skills exist under the chosen skill root, with frontmatter `name` matching the folder
- The memory choice is stated, and files match it
- A shared pack has a README skill index aligned with frontmatter
- The handoff names what to fill under Current focus, and which smoke check to run first
