---
name: people-notes
description: Create or update people/ notes — one person or company per file; keep last-contact and open threads current
user-invocable: true
---
1. Identify the person/org from the user message; resolve to `people/<kebab-name>.md`.
2. If missing, create from the people template: who, context, last contact (ISO date), open threads, preferences.
3. Update only facts the user stated or that appear in provided material; set last contact when a touch happened.
4. Do not invent contact history. End with a short diff of what changed.
