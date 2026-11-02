---
name: global-memory
description: >-
  Machine-global cross-workspace memory for DSH (GUI-first): upsert/query/pin/compact
  under ~/.dsh/global-memory with a graph store; use with plugin Memory tab or scripts/global_memory.py.
  跨工作区全局记忆：图结构、可控体积、重要留存、边缘合并。DSH Web 会话开场加载；「记到全局」写入。
user-invocable: true
---

# Global memory · 全局记忆

Primary surface is **DSH Web GUI** (`dsh web`: pick workspace → chat). Headless is for smoke tests only.

This skill is the agent protocol. Prefer the Cordis plugin `dsh-second-brain-memory` (Memory tab: List / Graph / Timeline) when installed; otherwise use `scripts/global_memory.py` and the files under `~/.dsh/global-memory/`.

## Dual store

| Store | Path | Scope |
| --- | --- | --- |
| Workspace | `<cwd>/.memory/MEMORY.md`, `notes/` | This project only |
| Global | `~/.dsh/global-memory/` | All workspaces on this machine |

**Priority:** workspace overrides global unless the user says「记到全局」/ promote.

## Layout (`~/.dsh/global-memory/`)

```text
config.yaml    # budgets, retention, enabled
graph.json     # nodes + edges (query index)
nodes/*.md     # one node per stable id (upsert, not append-forever)
INDEX.md       # human skim + size stats
archive/       # compacted leftovers
logs/          # audit lines
```

## GUI session protocol (`dsh web`)

1. **Session start** (after workspace is selected): if global enabled, read `INDEX.md` (or `stats` + top query hits). Inject a **compact index only** (≤ ~2–4 KiB): id · type · imp · one-line preview. Do not paste full node bodies into the system prompt.
2. **When answering** needs detail: `python3 scripts/global_memory.py query --q "…"` or open the node file; cite disk paths.
3. **「记住」** → write workspace `.memory/` or `notes/` (default).
4. **「记到全局」「更新记忆」「更新全局」** → `upsert` by stable id (slug). Rewrite body, bump `updated_at`; never unbounded append to one MEMORY.md.
5. **「重要」/ pin** → importance 5 + pinned so compact will not drop it.
6. Confirm writes by reading the file / plugin UI; chat “已记住” alone is not enough.
7. **Memory tab ≠ Trajectory:** Trajectory/Graph plugins show *execution* DAGs. This Memory tab shows *durable facts/preferences* graph + timeline.

## CLI helper

```bash
python3 scripts/global_memory.py init
python3 scripts/global_memory.py upsert --id coffee-pref --type preference --importance 4 --tags drink --text "美式咖啡，无糖"
python3 scripts/global_memory.py query --q 咖啡
python3 scripts/global_memory.py pin coffee-pref
python3 scripts/global_memory.py compact
python3 scripts/global_memory.py stats
```

Override root: `--root /tmp/gm-test`.

## Compaction / size control

From `config.yaml` budgets (`max_total_bytes`, `max_nodes`, `max_node_bytes`):
- Over budget → merge nodes with importance ≤ `peripheral_importance_max` and older than `peripheral_max_age_days` (unless pinned) into a `summary-*` node; move raw md to `archive/`; drop edges to archived ids (keep `archived` edge to summary).
- Important (imp ≥ 4 or pinned) retained.

## Graph query

Nodes: `{id, type, importance 1-5, tags, text, created_at, updated_at, pinned}`.  
Edges: `{from, to, rel}`.  
Query by keyword / tag / type over `graph.json` (+ body scan).

## Plugin

Install into web profile (when published / from path):

```bash
dsh plugin --profile web add <path-or-package-of-dsh-second-brain-memory>
dsh web
```

Then open **Memory / 全局记忆** beside Chat / Trajectory.

## Done checks

- Two workspaces: write global fact in A GUI chat → readable in B.
- Upsert same id updates body, does not duplicate forever.
- Tiny budget + compact merges peripherals; pinned survives.
