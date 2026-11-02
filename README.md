# DSH Second Brain

English: A second-brain scaffold whose workflows live as Agent Skills under `.agents/skills/` (DSH, Cursor, and Claude-compatible).

## 一句话定位

第二脑脚手架：短全局地图 + 知识目录 + 按需加载的工作流。技能放在 `.agents/skills/`，与 DSH、Cursor、Claude 的 Agent Skills 发现路径兼容。

## 目录一览

| 路径 | 职责 |
| --- | --- |
| `README.md` | 本说明 |
| `LICENSE` | MIT |
| `CONTRIBUTING.md` | 新增 skill 的约定 |
| `AGENTS.md` | 常驻全局地图（宜短） |
| `decisions.md` | 只追加的决策日志：`date \| decision \| why \| alternatives` |
| `notes/` | 一个主题一个文件 |
| `people/` | 一个人或组织一个文件 |
| `projects/` | 一个项目一个文件（status / last stopped / next） |
| `drafts/` | 写作草稿 |
| `.memory/` | 可选**工作区**文件记忆：会话开始读 `MEMORY.md`；「记住」默认写这里 |
| `~/.dsh/global-memory/` | **本机全局**图记忆（跨工作区）；见 `docs/global-memory.md` |
| `plugins/dsh-second-brain-memory/` | DSH Web Cordis 插件：Memory 页（列表/图谱/时间线） |
| `.agents/skills/global-memory/` | 全局记忆 agent 协议 |
| `scripts/global_memory.py` | upsert / query / pin / compact / stats |
| `SKILL.md` | 安装用的 setup skill：在目标项目里搭布局，并确保三个工作流在 `.agents/skills/` |
| `.agents/skills/` | 三个工作流 skill（DSH / Cursor 发现路径） |

知识目录（`notes/`、`people/`、`projects/`、`drafts/`、`.memory/`）是第二脑的数据层，不是 skill 包。

## 技能索引表

`description` 与各 skill frontmatter 一致。

| name | description | 何时用 | 依赖 |
| --- | --- | --- | --- |
| `weekly-review` | Weekly review — summarize projects/ progress, blockers, next steps; append new decisions; write drafts/weekly-YYYY-MM-DD.md | 做周回顾：汇总进展、标出阻塞和久未联系的人；确认后再追加决策 | `projects/`、`people/`、`decisions.md`、`drafts/`；若有 `.memory/` 则追加一行日志 |
| `people-notes` | Create or update people/ notes — one person or company per file; keep last-contact and open threads current | 新建或更新某人或某组织的笔记 | `people/`（可从 `people/_template.md` 起稿） |
| `draft-writing` | Draft writing into drafts/ using project voice from AGENTS.md and relevant notes/projects; leave publish to the user | 按项目语气起草，留给用户自己发布 | `AGENTS.md`，以及点名的 `notes/` 或 `projects/`、`drafts/` |
| `global-memory` | Machine-global cross-workspace memory for DSH (GUI-first): upsert/query/pin/compact under ~/.dsh/global-memory with a graph store; use with plugin Memory tab or scripts/global_memory.py. | Web 会话跨工作区记忆；「记到全局」；Memory 页 | `~/.dsh/global-memory/`；可选插件 |
| `dsh-second-brain` | Use when setting up or extending a second-brain layout: scaffold AGENTS.md and knowledge dirs, and install or ensure weekly-review, people-notes, and draft-writing under .agents/skills/. | 把这套布局装进一个项目：写短 `AGENTS.md`、建知识目录、放上三个工作流 | 目标项目根目录；技能写入 `.agents/skills/` |

## 安装与发现路径

克隆本仓库，或把文件拷进已有项目根目录：

```bash
git clone https://github.com/Ficere/dsh-second-brain.git
```

DSH 本地发现顺序：`.dsh/skills` → `.agents/skills` → 自定义路径 → `~/.dsh/skills` → `~/.agents/skills`。本仓库的三个技能在 `.agents/skills/`。Cursor 也会扫描 `.agents/skills`，以及 `.cursor/skills`，并兼容 `.claude/skills`。

## 全局记忆插件（Web）

```bash
dsh plugin --profile web add ./plugins/dsh-second-brain-memory
python3 scripts/global_memory.py init
dsh web
```

会话视图中打开 **Memory / 全局记忆**（与 Trajectory 执行图谱分开）。机制说明：`docs/global-memory.md`。

## 如何调用

- **weekly-review**：「做一次周回顾：读 projects，标出阻塞，确认后再写入 decisions.md。」
- **people-notes**：「为这个人建一条 people 笔记，记下最近联系和未完话题。」
- **draft-writing**：「按 AGENTS.md 的语气，根据我点名的笔记在 drafts/ 起草，不要发布。」

## 如何新增 skill

在 `.agents/skills/<name>/SKILL.md` 新增。文件夹用 kebab-case，且与 frontmatter `name` 相同。

```markdown
---
name: my-skill
description: What it does, and when to use it.
user-invocable: true
---
```

正文保持短。只有 `SKILL.md` 将超过约 500 行时，再拆出 `references/`。不要空建 `scripts/` 或 `assets/`。

## 指令预算与硬约束

DSH 指令文件合计约 **64 KB**。`AGENTS.md` 只放常驻地图；长流程放进 skill。

「不要改写 `decisions.md` 旧行」是软规则。删除、强推、改写历史这类硬限制靠 approval policy，不靠提示词单独成立。

## Setup skill

仓库根目录的 `SKILL.md`（`dsh-second-brain`）用来把这套布局装进目标项目：短 `AGENTS.md`、知识目录，以及 `.agents/skills/` 下的三个工作流。它不包含这三个工作流的正文。

## License / 贡献

MIT。Copyright (c) 2026 Lvjun Guo / Ficere。贡献约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。
