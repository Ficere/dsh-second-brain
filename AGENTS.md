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
- If `.memory/` exists, read `.memory/MEMORY.md` at session start and append durable prefs to disk when the user asks to remember something
