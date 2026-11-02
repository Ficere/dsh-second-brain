# Contributing

English: Add a skill as `.agents/skills/<name>/SKILL.md`. Keep `name` kebab-case and ≤64 characters. Keep `description` ≤1024 characters and say when to use the skill. Prefer progressive disclosure; do not add empty `scripts/` or `assets/`. Do not put long procedures in `AGENTS.md`. Do not add unrelated frontmatter fields that break portability.

中文：

- 新 skill 放在 `.agents/skills/<name>/SKILL.md`。`name` 用 kebab-case，不超过 64 字符；`description` 不超过 1024 字符，并写明何时使用。
- 优先渐进披露。正文放在 `SKILL.md`；不要空建 `scripts/`、`assets/`。
- 不要把长流程写进 `AGENTS.md`。
- 不要添加会破坏可移植性的无关 frontmatter 字段。可移植的最小集合是 `name` 与 `description`。本仓库的三个技能另设 `user-invocable: true`，以便按名字调用。
