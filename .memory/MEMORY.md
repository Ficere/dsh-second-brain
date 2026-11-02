# Workspace memory (L2)

File-backed project memory for DeepSeek Harness. DSH does not persist chat on its own. This file is the workspace layer: durable preferences and facts for *this* project, checked on disk.

If `.memory/` is present, read this file at session start. Append here only when the user asks to remember something. Confirm the write by opening the file; a chat claim is not enough.

## Preferences

## Facts

## Open loops
