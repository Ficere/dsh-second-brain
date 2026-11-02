# 全局记忆机制说明

> 主路径：**DSH Web GUI**（`dsh web` 选工作区再聊天）。`dsh headless` 仅用于冒烟。  
> 插件：`plugins/dsh-second-brain-memory`（Memory 页）。技能：`.agents/skills/global-memory`。脚本：`scripts/global_memory.py`。

## 1. 落盘到哪里

| 层 | 路径 | 作用 |
| --- | --- | --- |
| 工作区 | `<workspace>/.memory/MEMORY.md`、`notes/` 等 | 本项目事实/偏好；**默认「记住」写这里** |
| 全局 | `~/.dsh/global-memory/`（或 `$DSH_HOME/global-memory`） | **跨工作区**共享；「记到全局」写这里 |

全局目录结构：

```text
~/.dsh/global-memory/
  config.yaml     # enabled、预算、保留策略
  graph.json      # 节点 + 边（查询索引）
  nodes/<id>.md   # 每条记忆一个文件（按 id upsert）
  INDEX.md        # 人类速览 + 体积统计
  archive/        # compact 后的原文
  logs/           # 审计
```

没有独立「记忆微服务」：答靠读盘，记住靠写盘；聊天气泡里说记住了不算。

## 2. 读写时机（GUI）

1. **选工作区并开会话** → 若 `enabled: true`（或已装 Memory 插件），加载 `INDEX.md` / `graph.json`，只把 **紧凑索引**（Top-K、约 2–4KB）注入上下文；不把全文塞进 system prompt。
2. **问答需要细节** → `query` 或打开 `nodes/<id>.md`，或在 Memory 页点选。
3. **「记住」** → 默认写工作区 `.memory/` 或 `notes/`。
4. **「记到全局 / 更新（全局）记忆」** → 对稳定 `id`（slug）**upsert**：改写正文、更新 `updated_at`，禁止无限追加单一 MEMORY.md。
5. **「重要」** → `importance=5` 且 `pinned`，compact 不删。
6. 冲突：**本地覆盖全局**，除非用户明确 promote /「记到全局」。

## 3. 跨对话 / 跨工作区

- **同工作区跨对话**：与从前一样——新会话读同一目录磁盘文件。
- **跨工作区**：读同一台机器上的 `~/.dsh/global-memory/`。空工作区也能召回全局事实；工作区私有笔记仍互不自动同步。
- **更新**：同 id 覆盖，文件数与体积受 `config.yaml` 预算约束。

## 4. 图结构与查询

- 节点：`id, type(fact|preference|person|decision|summary|ephemeral), importance(1–5), tags, text, created_at, updated_at, pinned`
- 边：`from, to, rel`
- 查询：关键字 / tag / type，走 `graph.json`（必要时扫正文）

Memory 页的 **图谱** 是「实体/事实关系图」，**不是** Trajectory 的执行 DAG（Turn→Tool→Model）。二者分栏，避免混用。

## 5. 压缩与重要留存

预算：`max_total_bytes` / `max_nodes` / `max_node_bytes`。  
超限时 `compact`：把低重要度（默认 ≤2）且超过 N 天、未 pin 的节点合并进 `summary-peripheral-*`，原文进 `archive/`，高重要与 pinned 保留。

## 6. 可视化（插件）

Memory / 全局记忆 Tab：

- **列表**：过滤、点选详情  
- **图谱**：力导向 / 环形布局，按 type 着色，imp 影响节点大小  
- **时间线**：按 `updated_at` 修订历史  
- 顶栏：**本回合可注入索引**条（对齐 dsh-context「看得见上下文」的思路）

独立预览：`plugins/dsh-second-brain-memory/viewer/index.html`（可配 `?graph=/path/to/graph.json`）。

## 7. 安装

```bash
dsh plugin --profile web add ./plugins/dsh-second-brain-memory
# 或技能-only：保证 AGENTS.md 含全局钩子，并用 scripts/global_memory.py
python3 scripts/global_memory.py init
dsh web
```

## 8. 与主流插件的对齐（摘要）

| 参考 | 对齐点 |
| --- | --- |
| dsh-context（上下文） | 可见性：索引条 / 面板，而不仅是黑盒注入 |
| Trajectory / trajectory-graph | 执行流单独成 Tab；Memory 不占用执行 DAG |
| dsh-cross-workspace-memory / dsh-mem | `~/.dsh` 本机共享；会话只注入摘要；工具/命令读写全文 |
| qwert702/dsh-memory | Memory 页 = 列表 + 图；双 scope；巩固/合并 |
