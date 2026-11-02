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
