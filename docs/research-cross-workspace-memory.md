# Research: DSH cross-workspace memory & viz (2026-11)

## References

1. **bowenliang123/dsh-context（上下文）** — Context Insights sidebar, Context tab/panel, `/context`; composition/evolution visibility. Not a long-term fact store; UX lesson: **make injected context visible**.
2. **Built-in Trajectory + TangRj-Git/trajectory-graph** — Chat | Trajectory | Graph; LTR execution DAG; turn navigator; pan/zoom/filter; local-only; conservative edges. Lesson: **keep execution graph ≠ memory graph**.
3. **dsh-cross-workspace-memory / jelee0145/dsh-mem** — `$DSH_HOME/memory/`; save/recall tools; session-start compact index; project tags; workspace-preferring retrieval.
4. **qwert702/dsh-memory** — project + global JSON under `~/.dsh/memory/`; Memory tab list + force graph; auto extract/inject/consolidate; Cordis `dsh.bundle` + `conversation.view` seat.
5. **adoresever/graph-memory** — graph as **navigation**, evidence stays Q/A; SQLite; cross-session recall.
6. **wr-web/dsh-context-tree** — cross-session forest / checkpoints; bounded recall.

## Our alignment

- Plugin pack + skill + file graph store under `~/.dsh/global-memory/`
- Memory tab List/Graph/Timeline; inject bar; dual store with local override
- Upsert-by-id, pin, compact budgets — no unbounded MEMORY.md append
- Install: `dsh plugin --profile web add …` like other Cordis plugins
