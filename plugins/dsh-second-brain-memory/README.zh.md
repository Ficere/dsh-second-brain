# dsh-second-brain-memory

DSH Web **全局记忆**插件（与 Trajectory 执行图谱分离）。

## 安装

```bash
# 从本仓库路径（开发）
dsh plugin --profile web add ./plugins/dsh-second-brain-memory

# 或发布后
dsh plugin --profile web add dsh-second-brain-memory
dsh web
```

打开会话视图环：**对话 | 轨迹 | Memory / 全局记忆**。

## 能力

- 双存储：`~/.dsh/global-memory`（全局图）+ 工作区 `.memory/`（本地优先）
- 会话只注入紧凑索引；「记到全局」按 id upsert
- 页内 **列表 / 力导向图谱 / 时间线**；顶栏显示本回合可注入索引（对齐 dsh-context 可见性）
- 体积预算 + pin + compact 合并边缘记忆

数据与协议见仓库 `docs/global-memory.md` 与 skill `global-memory`。
