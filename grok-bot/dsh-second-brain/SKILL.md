---
name: dsh-second-brain
description: >-
  Use when setting up or extending a DeepSeek Harness (DSH) second-brain:
  scaffold AGENTS.md + knowledge dirs, or install/run weekly-review /
  people-notes / draft-writing skills that mirror Claude Second Brain 2.0
  layered memory.
---
# DSH Second Brain

Build or extend a Claude Second Brain–style layered memory inside a DeepSeek Harness (DSH) project: short global map, on-demand workflow skills, and file-backed memory (DSH has no built-in auto-memory).

Layout follows [Agent Skills](https://agentskills.io/specification): each skill is `<name>/SKILL.md` (optional `references/` / `scripts/` / `assets/` only when needed). Prefer `.agents/skills/` for DSH + Cursor discovery. Do not invent a parallel root `skills/` tree unless the user asks for Anthropic marketplace packaging.

Public reference pack: https://github.com/Ficere/dsh-second-brain

## When to load

- User wants a DSH “第二大脑” / second brain / AGENTS.md + skills layout
- User asks to scaffold, migrate from Claude Code `CLAUDE.md` / `.claude/skills`, or add weekly review / people notes / draft workflows for DSH
- User mentions DSH instruction budget (64 KB), `.agents/skills`, or `.dsh/skills`

## Goals

1. Scaffold a lean project map and knowledge folders.
2. Install reusable DSH skill bundles (`<name>/SKILL.md`, kebab-case, frontmatter `name` + `description`).
3. Wire optional cross-session memory (file skill or community plugin)—never invent a fake auto-memory layer.
4. Ship a README with a skill index whose descriptions match frontmatter exactly; keep `grok-bot/` (if present) clearly labeled as orchestrator-only.

Keep paths and tone generic. Put person-specific focus items, repo paths, and approval policies in the target project’s files—not hard-coded in this recipe.

## Layer map (Claude → DSH)

| Layer | Claude Code | DSH |
| --- | --- | --- |
| Global map | `CLAUDE.md` | Root `AGENTS.md` (keep short; total instruction files ≤ ~64 KB) |
| Local rules | `.claude/rules/` + paths | No equivalent path loader—encode as skills or a nested `AGENTS.md` only if verified |
| Workflows | `.claude/skills/` | Prefer `.agents/skills/<name>/SKILL.md` (also works for Codex/Cursor); `.dsh/skills/` ranks higher if DSH-only |
| Auto memory | Auto memory | Manual files and/or a memory skill/plugin |

Discovery ranks (local provider): `.dsh/skills` (100) → `.agents/skills` (200) → custom → `~/.dsh/skills` → `~/.agents/skills`. Bundles are one level only (`name/SKILL.md`); no nested recursive discovery. Skills reload each step—no restart needed after edits.

## Preference check (ask only if missing)

Ask **one** question if unclear:

1. Target root (existing git project vs new `second-brain/` folder).
2. Skill root: `.agents/skills` (default, shared) vs `.dsh/skills` (DSH-first).
3. Memory: (A) lightweight `.memory/` + instructions in `AGENTS.md`, (B) install/link [yunyu422/memory-system](https://github.com/yunyu422/memory-system), or (C) `dsh-agent-memory` plugin—user chooses; do not install plugins without explicit yes.

If they already answered, proceed.

## Part A — Scaffold

### 1. Create layout

```text
<project-root>/
├── README.md              # skill index + install paths (see Part E)
├── CONTRIBUTING.md        # optional but preferred for public packs
├── AGENTS.md
├── CLAUDE.md          # optional symlink → AGENTS.md if they also use Claude Code
├── decisions.md
├── notes/
├── people/
├── projects/
├── drafts/
├── .memory/           # if memory option A or B needs it
│   ├── MEMORY.md
│   └── logs/
└── .agents/skills/    # or .dsh/skills/ per preference
    ├── weekly-review/
    ├── people-notes/
    └── draft-writing/
```

Create missing dirs. Do not overwrite non-empty `AGENTS.md` or `decisions.md` without confirming; offer merge/diff instead. Do **not** empty-create `scripts/` / `assets/` / `evals/` under skills.

### 2. Write lean `AGENTS.md`

Target ~80 lines, hard cap well under the shared 64 KB instruction budget. Include only always-on facts:

- Directory map (`projects/`, `decisions.md`, `people/`, `notes/`, `drafts/`, `.memory/` if used)
- Answer style (language, conclusion-first, mark unknowns)
- Current focus: placeholder for 1–3 items the user fills
- Soft “do not rewrite history in `decisions.md`”—note that hard blocks belong in DSH approval policy, not prose alone

Template body (adapt language to the user):

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
```

Optional: `CLAUDE.md` → symlink to `AGENTS.md` so Claude Code and DSH share one map.

### 3. Seed empty knowledge files

- `decisions.md` with a one-line header explaining the append format
- Optional stub `projects/_template.md` with status / last stopped / next
- Optional stub `people/_template.md` with last contact date field

## Part B — Install workflow skills

Write each as `<skill-root>/<name>/SKILL.md`. Frontmatter: `name`, `description`; set `user-invocable: true` when the user should call it by name. Bodies are instructions for the DSH agent, not Grok Bot tool calls. Folder name must equal frontmatter `name`.

### `weekly-review`

```markdown
---
name: weekly-review
description: Weekly review — summarize projects/ progress, blockers, next steps; append new decisions; write drafts/weekly-YYYY-MM-DD.md
user-invocable: true
---
1. Read `projects/*.md` (skip templates). List status, last stopped, next for each.
2. Flag blockers. From `people/`, list anyone with last contact older than 30 days (or missing).
3. Propose new decisions from the review; on user confirm, append to `decisions.md` with date | decision | why | alternatives.
4. Write `drafts/weekly-YYYY-MM-DD.md` with the summary, blockers, people to ping, and next-week focus.
5. If `.memory/` exists, append a short log line under `.memory/logs/YYYY-MM-DD.md` pointing at the weekly draft.
```

### `people-notes`

```markdown
---
name: people-notes
description: Create or update people/ notes — one person or company per file; keep last-contact and open threads current
user-invocable: true
---
1. Identify the person/org from the user message; resolve to `people/<kebab-name>.md`.
2. If missing, create from the people template: who, context, last contact (ISO date), open threads, preferences.
3. Update only facts the user stated or that appear in provided material; set last contact when a touch happened.
4. Do not invent contact history. End with a short diff of what changed.
```

### `draft-writing`

```markdown
---
name: draft-writing
description: Draft writing into drafts/ using project voice from AGENTS.md and relevant notes/projects; leave publish to the user
user-invocable: true
---
1. Read `AGENTS.md` answer style and any topic files the user names under `notes/` or `projects/`.
2. Draft in `drafts/<slug>.md` (or the path they give). Conclusion first; match their language.
3. Do not publish, send, or post. Return the path and a 2–3 line summary of what is still open.
```

After writing, list the skill paths and remind: invoke via DSH skill catalog / `skill({ name })` or user command; catalogs refresh without restart. Only add `references/` when a body would exceed ~500 lines.

## Part C — Cross-session memory

DSH does not auto-persist chat memory. Pick the user’s option:

- **A — Files only:** ensure `.memory/MEMORY.md` + `.memory/logs/`; add one bullet in `AGENTS.md` to read MEMORY at session start and append durable prefs to disk when the user says to remember something.
- **B — memory-system skill:** clone or vendor [yunyu422/memory-system](https://github.com/yunyu422/memory-system) into the chosen skill root only after they agree; follow that repo’s layout (user / workspace / preferences layers).
- **C — Plugin:** point them to install `dsh-agent-memory` themselves; do not claim it is configured until they confirm.

Always tell them to open the files on disk to verify writes—chat claims are not enough.

## Part D — Smoke checks

After scaffold + skills, run or instruct these checks in the target project:

1. New session: “What is the status of project X?” with a filled `projects/x.md` — should answer without re-explaining layout.
2. Invoke `weekly-review` — expect draft under `drafts/` and no silent rewrite of old `decisions.md` rows.
3. Preference save (if memory enabled) in session A → visible in files → session B reads it.
4. Attempt to rewrite a historical decisions row — prose may warn; hard block needs DSH approval policy.

Report what was created, what was skipped, and any confirmation still needed.

## Part E — README for public / shared packs

When scaffolding a shareable repo (or refreshing https://github.com/Ficere/dsh-second-brain), write README with this outline:

1. One-line positioning (EN + ZH ok)
2. Directory map (path → role)
3. Skill index table: name | description (verbatim from frontmatter) | when to use | deps
4. Install + discovery paths (DSH order; Cursor also scans `.agents/skills`)
5. One example invoke per skill
6. How to add a skill (naming, frontmatter, when to split references)
7. Instruction budget + hard constraints
8. If a `grok-bot/` orchestrator copy exists: state clearly it is **not** a duplicate of the three DSH skills
9. License / CONTRIBUTING

## Hard constraints

- Never bloat `AGENTS.md` with long procedures—move them into skills.
- Never treat markdown “禁止 …” as a technical sandbox; call out approval policy for deletes/force-pushes/history edits.
- Never overwrite user content without confirm.
- Never install third-party skills/plugins without an explicit yes.
- Never empty-create `scripts/` / `assets/` / `evals/`.
- Deliverable for the human: concrete paths written + how to invoke each skill in DSH.

## Done criteria

- Layout exists; `AGENTS.md` is short and accurate
- At least the three workflow skills exist under the chosen skill root with valid frontmatter matching folder names
- Memory approach is stated and files/plugin path match the choice
- Shared packs have a README skill index aligned with frontmatter
- User gets a brief handoff: what to fill under Current focus, and which smoke check to run first (prefer memory + decisions integrity)
