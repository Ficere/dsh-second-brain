# Second brain · global map

## Layout
- `projects/`: one file per project — required fields: status / last stopped / next
- `decisions.md`: append-only — `date | decision | why | alternatives`
- `people/`: one file per person or org
- `notes/`: one topic per file
- `drafts/`: writing drafts
- `.memory/`: **workspace** cross-session notes (if present); verify on disk, do not trust chat-only “I remembered”
- `~/.dsh/global-memory/`: **machine-global** graph memory (cross-workspace). Managed by skill `global-memory` and/or plugin `dsh-second-brain-memory`. Not inside the project tree.

## How to answer
- Match the user’s language; lead with the answer; tables before long prose when comparing
- Unverified claims → mark as 待核实 / unverified

## Current focus
- [fill 1–3 priorities]

## Soft rules
- Append to `decisions.md`; never edit past rows in place
- Prefer loading a skill over stuffing long procedures into this file
- Keep this file short; put workflows in `.agents/skills/*/SKILL.md`
- If `.memory/` exists, read `.memory/MEMORY.md` at session start and append durable prefs to disk when the user asks to remember something
- **Global memory (GUI primary — `dsh web`)**: when the web/GUI session starts in a workspace, if `~/.dsh/global-memory/config.yaml` has `enabled: true` (or the Memory plugin is installed), load `INDEX.md` + query relevant nodes from `graph.json`; do **not** dump every node into the prompt. On「记住」default-write **workspace** `.memory/` (or `notes/`); on「记到全局 / 更新全局记忆 / 重要」upsert into `~/.dsh/global-memory/nodes/` via `scripts/global_memory.py` or the plugin API. **Local overrides global** unless the user explicitly promotes. Pin high-importance; run compact when over budget. Browse history in the Web **Memory / 全局记忆** tab (graph + timeline) — separate from Trajectory execution DAG.
