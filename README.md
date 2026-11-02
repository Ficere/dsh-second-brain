# DSH Second Brain

English: A Claude Second Brain 2.0–style layered memory pack for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (DSH). Short global map in `AGENTS.md`, on-demand workflow skills, and optional file-backed memory. DSH has no built-in auto-memory.

中文：这是一套给 DeepSeek Harness 用的「第二大脑」技能包，分层方式和 Claude Second Brain 2.0 对齐：常驻的全局地图尽量短，具体流程放进按需加载的 skill，跨会话记忆落到文件里。

## 怎么用

克隆本仓库，或把这些文件拷进已有的 DSH 项目根目录：

```bash
git clone https://github.com/Ficere/dsh-second-brain.git
```

技能放在 `.agents/skills/`（Codex 也能发现这一层）。DSH 本地发现顺序是 `.dsh/skills` → `.agents/skills` → 自定义路径 → `~/.dsh/skills` → `~/.agents/skills`。每个技能只一层：`<name>/SKILL.md`。改完即生效，不用重启。

目录：

| 路径 | 作用 |
| --- | --- |
| `AGENTS.md` | 全局地图：布局、回答方式、当前焦点占位、软规则 |
| `decisions.md` | 只追加的决策日志 |
| `projects/` `people/` `notes/` `drafts/` | 项目、人物、笔记、草稿 |
| `.memory/` | 可选的工作区记忆（L2） |
| `.agents/skills/` | `weekly-review`、`people-notes`、`draft-writing` |

先填 `AGENTS.md` 里的 Current focus，再按 `projects/_template.md` 和 `people/_template.md` 建真实条目。

## 如何调用三个技能

在 DSH 里按名字调用（技能目录 / `skill({ name })` / 用户命令均可）。目录每次步骤都会刷新。

- **`weekly-review`**：读 `projects/`（跳过模板），标出阻塞和超过 30 天未联系的人；经你确认后追加 `decisions.md`；写出 `drafts/weekly-YYYY-MM-DD.md`。
- **`people-notes`**：为一个人或组织维护 `people/<kebab-name>.md`，更新最近联系（ISO 日期）和未完话题。只记你说过或材料里有的事实。
- **`draft-writing`**：按 `AGENTS.md` 的语气和你点名的笔记起草到 `drafts/`。不发布、不发送。

## 指令预算与硬约束

DSH 指令文件合计大约 **64 KB**。`AGENTS.md` 保持短；长流程放在 skill 里，不要塞进全局地图。

Markdown 里的「不要改历史」只是软规则。删除、强推、改写 `decisions.md` 旧行这类硬限制，要配 DSH 的 approval policy，不能只靠提示词。

## 可选记忆

默认是文件方案：`.memory/MEMORY.md` 与 `.memory/logs/`。会话开始时读 `MEMORY.md`；只有当你明确说「记住」时，才把持久偏好追加到磁盘。写完请打开文件核对。

不想用文件层时，可以自己安装社区方案（本仓库只放链接，不内置代码）：

- [yunyu422/memory-system](https://github.com/yunyu422/memory-system)
- [dsh-agent-memory](https://github.com/Culeot/dsh-agent-memory)（npm 包 `dsh-agent-memory`）

## Grok Bot

`grok-bot/dsh-second-brain/SKILL.md` 是给 Grok Bot 助手用的编排配方：用来在目标项目里脚手架这份布局、安装上述三个技能，并按你的选择接上记忆。DSH 运行时读的是 `.agents/skills/` 下的三个技能，不是这份编排文件。

## License

MIT. Copyright (c) 2026 Lvjun Guo / Ficere.
