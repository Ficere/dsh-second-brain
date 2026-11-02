#!/usr/bin/env python3
"""DSH global memory helper — machine-wide graph store under ~/.dsh/global-memory/.

Stdlib only. Used by agents (esp. DSH GUI / dsh web sessions) and for smoke tests.
Commands: init | upsert | get | query | link | pin | compact | stats | rebuild-index
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(os.path.expanduser("~/.dsh/global-memory"))

DEFAULT_CONFIG = {
    "enabled": True,
    "root": str(DEFAULT_ROOT),
    "budgets": {
        "max_total_bytes": 512_000,
        "max_nodes": 200,
        "max_node_bytes": 4_000,
        "index_preview_chars": 160,
    },
    "retention": {
        "peripheral_max_age_days": 30,
        "peripheral_importance_max": 2,
        "keep_pinned": True,
        "archive_on_compact": True,
    },
    "defaults": {
        "importance": 3,
        "type": "fact",
    },
    "priority": {
        "workspace_over_global": True,
        "promote_phrase": "记到全局",
    },
}

NODE_TYPES = ("fact", "preference", "person", "decision", "summary", "ephemeral")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str, maxlen: int = 48) -> str:
    s = text.strip().lower()
    s = re.sub(r"[\s_/]+", "-", s)
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff\-]+", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "mem-" + hashlib.sha1(text.encode()).hexdigest()[:10]
    return s[:maxlen]


def dump_simple_yaml(data: dict, indent: int = 0) -> str:
    """Minimal YAML emitter for our config shape (dicts/lists/scalars)."""
    lines: list[str] = []
    sp = "  " * indent

    def emit(key: str, val: Any, level: int) -> None:
        pad = "  " * level
        if isinstance(val, dict):
            lines.append(f"{pad}{key}:")
            for k, v in val.items():
                emit(str(k), v, level + 1)
        elif isinstance(val, list):
            lines.append(f"{pad}{key}:")
            for item in val:
                if isinstance(item, (dict, list)):
                    lines.append(f"{pad}-")
                    # rare; skip nested lists in config
                else:
                    lines.append(f"{pad}- {json.dumps(item) if isinstance(item, str) else item}")
        elif isinstance(val, bool):
            lines.append(f"{pad}{key}: {'true' if val else 'false'}")
        elif val is None:
            lines.append(f"{pad}{key}: null")
        elif isinstance(val, (int, float)):
            lines.append(f"{pad}{key}: {val}")
        else:
            s = str(val)
            if any(c in s for c in ":#{}[]&*!|>%@`'\"\n"):
                lines.append(f'{pad}{key}: {json.dumps(s, ensure_ascii=False)}')
            else:
                lines.append(f"{pad}{key}: {s}")

    for k, v in data.items():
        emit(str(k), v, indent)
    return "\n".join(lines) + "\n"


def load_simple_yaml(text: str) -> dict:
    """Minimal indented YAML loader for config.yaml (dicts + scalars only)."""
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if rest == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(rest)
    return root


def _parse_scalar(s: str) -> Any:
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s in ("null", "Null", "~"):
        return None
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        try:
            return json.loads(s if s.startswith('"') else '"' + s[1:-1].replace('"', '\\"') + '"')
        except json.JSONDecodeError:
            return s[1:-1]
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class GlobalMemory:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else DEFAULT_ROOT
        self.config_path = self.root / "config.yaml"
        self.graph_path = self.root / "graph.json"
        self.nodes_dir = self.root / "nodes"
        self.archive_dir = self.root / "archive"
        self.logs_dir = self.root / "logs"
        self.index_path = self.root / "INDEX.md"
        self._in_compact = False
        self._ensured = False

    def _ensure_store(self, force_config: bool = False) -> None:
        """Create dirs/config/graph once; no log spam, no index rebuild."""
        if self._ensured and not force_config:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self.nodes_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        if force_config or not self.config_path.exists():
            self.config_path.write_text(dump_simple_yaml(DEFAULT_CONFIG), encoding="utf-8")
        if not self.graph_path.exists():
            self._write_graph({"version": 1, "nodes": {}, "edges": []})
        self._ensured = True

    def init(self, force_config: bool = False) -> None:
        self._ensure_store(force_config=force_config)
        self.rebuild_index()
        self._log("init", f"root={self.root}")

    def load_config(self) -> dict:
        if not self.config_path.exists():
            return dict(DEFAULT_CONFIG)
        loaded = load_simple_yaml(self.config_path.read_text(encoding="utf-8"))
        return deep_merge(DEFAULT_CONFIG, loaded)

    def _read_graph(self) -> dict:
        if not self.graph_path.exists():
            return {"version": 1, "nodes": {}, "edges": []}
        return json.loads(self.graph_path.read_text(encoding="utf-8"))

    def _write_graph(self, g: dict) -> None:
        self.graph_path.write_text(
            json.dumps(g, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def _log(self, action: str, detail: str) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        line = f"{utc_now()} | {action} | {detail}\n"
        with (self.logs_dir / f"{day}.log").open("a", encoding="utf-8") as f:
            f.write(line)

    def _node_path(self, node_id: str) -> Path:
        return self.nodes_dir / f"{node_id}.md"

    def _render_node_md(self, meta: dict, body: str) -> str:
        tags = meta.get("tags") or []
        tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
        lines = [
            "---",
            f"id: {meta['id']}",
            f"type: {meta.get('type', 'fact')}",
            f"importance: {meta.get('importance', 3)}",
            f"pinned: {'true' if meta.get('pinned') else 'false'}",
            f"tags: [{tag_str}]",
            f"created_at: {meta.get('created_at', utc_now())}",
            f"updated_at: {meta.get('updated_at', utc_now())}",
            "---",
            "",
            body.strip(),
            "",
        ]
        return "\n".join(lines)

    def _parse_node_md(self, text: str) -> tuple[dict, str]:
        if not text.startswith("---"):
            return {}, text
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}, text
        meta_raw = parts[1]
        body = parts[2].lstrip("\n")
        meta = load_simple_yaml(meta_raw)
        if "tags" in meta and isinstance(meta["tags"], str):
            inner = meta["tags"].strip()
            if inner.startswith("[") and inner.endswith("]"):
                inner = inner[1:-1]
            meta["tags"] = [t.strip() for t in inner.split(",") if t.strip()]
        return meta, body

    def upsert(
        self,
        text: str,
        node_id: str | None = None,
        ntype: str = "fact",
        importance: int | None = None,
        tags: list[str] | None = None,
        pinned: bool = False,
        link_to: str | None = None,
        rel: str = "related",
    ) -> dict:
        self._ensure_store()
        cfg = self.load_config()
        if not cfg.get("enabled", True):
            raise SystemExit("global memory disabled in config.yaml (enabled: false)")

        node_id = slugify(node_id or text[:40])
        ntype = ntype if ntype in NODE_TYPES else cfg["defaults"]["type"]
        importance = int(importance if importance is not None else cfg["defaults"]["importance"])
        importance = max(1, min(5, importance))
        tags = tags or []
        max_body = int(cfg["budgets"]["max_node_bytes"])
        body = text.strip()
        if len(body.encode("utf-8")) > max_body:
            body = body.encode("utf-8")[: max_body - 20].decode("utf-8", errors="ignore") + "…"

        path = self._node_path(node_id)
        now = utc_now()
        created = now
        if path.exists():
            old_meta, _ = self._parse_node_md(path.read_text(encoding="utf-8"))
            created = old_meta.get("created_at", now)
            if old_meta.get("pinned"):
                pinned = True

        meta = {
            "id": node_id,
            "type": ntype,
            "importance": importance,
            "pinned": pinned,
            "tags": tags,
            "created_at": created,
            "updated_at": now,
            "bytes": len(body.encode("utf-8")),
        }
        path.write_text(self._render_node_md(meta, body), encoding="utf-8")

        g = self._read_graph()
        g["nodes"][node_id] = {
            "id": node_id,
            "type": ntype,
            "importance": importance,
            "pinned": pinned,
            "tags": tags,
            "created_at": created,
            "updated_at": now,
            "preview": body[: int(cfg["budgets"]["index_preview_chars"])],
            "path": f"nodes/{node_id}.md",
        }
        if link_to:
            edge = {"from": node_id, "to": link_to, "rel": rel}
            if edge not in g["edges"]:
                g["edges"].append(edge)
        self._write_graph(g)
        self.rebuild_index()
        self._log("upsert", node_id)
        # Size control is explicit: run `compact` (CLI/skill). No auto-recurse here.
        return meta

    def get(self, node_id: str) -> str:
        path = self._node_path(slugify(node_id))
        if not path.exists():
            raise SystemExit(f"node not found: {node_id}")
        return path.read_text(encoding="utf-8")

    def query(
        self,
        q: str | None = None,
        tag: str | None = None,
        ntype: str | None = None,
        min_importance: int = 1,
        limit: int = 20,
    ) -> list[dict]:
        g = self._read_graph()
        hits = []
        q_l = (q or "").lower()
        for nid, n in g.get("nodes", {}).items():
            if n.get("importance", 0) < min_importance:
                continue
            if ntype and n.get("type") != ntype:
                continue
            tags = n.get("tags") or []
            if tag and tag not in tags:
                continue
            blob = " ".join(
                [
                    nid,
                    n.get("type", ""),
                    n.get("preview", ""),
                    " ".join(tags),
                ]
            ).lower()
            if q_l and q_l not in blob:
                # also search full body
                path = self.root / n.get("path", f"nodes/{nid}.md")
                if path.exists():
                    blob += " " + path.read_text(encoding="utf-8").lower()
                if q_l not in blob:
                    continue
            hits.append(n)
        hits.sort(key=lambda x: (-int(x.get("importance", 0)), x.get("updated_at", "")), reverse=False)
        hits.sort(key=lambda x: (-int(x.get("importance", 0)), x.get("updated_at", "")), reverse=True)
        # fix: want high importance first, then recent
        hits = sorted(
            hits,
            key=lambda x: (-int(x.get("importance", 0)), x.get("updated_at", "")),
        )
        hits = sorted(hits, key=lambda x: int(x.get("importance", 0)), reverse=True)
        # stable: importance desc, updated_at desc
        hits = sorted(
            hits,
            key=lambda x: (int(x.get("importance", 0)), x.get("updated_at", "")),
            reverse=True,
        )
        return hits[:limit]

    def link(self, src: str, dst: str, rel: str = "related") -> None:
        self.init()
        g = self._read_graph()
        src, dst = slugify(src), slugify(dst)
        edge = {"from": src, "to": dst, "rel": rel}
        if edge not in g["edges"]:
            g["edges"].append(edge)
            self._write_graph(g)
            self._log("link", f"{src} -[{rel}]-> {dst}")
        self.rebuild_index()

    def pin(self, node_id: str, pinned: bool = True) -> None:
        node_id = slugify(node_id)
        path = self._node_path(node_id)
        if not path.exists():
            raise SystemExit(f"node not found: {node_id}")
        meta, body = self._parse_node_md(path.read_text(encoding="utf-8"))
        meta["pinned"] = pinned
        meta["updated_at"] = utc_now()
        meta["id"] = node_id
        path.write_text(self._render_node_md(meta, body), encoding="utf-8")
        g = self._read_graph()
        if node_id in g["nodes"]:
            g["nodes"][node_id]["pinned"] = pinned
            g["nodes"][node_id]["updated_at"] = meta["updated_at"]
            self._write_graph(g)
        self.rebuild_index()
        self._log("pin" if pinned else "unpin", node_id)

    def compact(self, dry_run: bool = False) -> dict:
        if self._in_compact:
            return {
                "merged": [],
                "archived": [],
                "summary_id": None,
                "dry_run": dry_run,
                "skipped": "reentrant",
            }
        self._ensure_store()
        cfg = self.load_config()
        ret = cfg["retention"]
        budgets = cfg["budgets"]
        g = self._read_graph()
        now = datetime.now(timezone.utc)
        max_age = timedelta(days=int(ret["peripheral_max_age_days"]))
        imp_max = int(ret["peripheral_importance_max"])

        peripherals: list[str] = []
        for nid, n in list(g.get("nodes", {}).items()):
            if n.get("type") == "summary":
                continue
            if n.get("pinned") and ret.get("keep_pinned", True):
                continue
            if int(n.get("importance", 3)) > imp_max:
                continue
            try:
                updated = datetime.strptime(
                    n.get("updated_at", ""), "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                updated = now - max_age - timedelta(days=1)
            over_budget = (
                len(g["nodes"]) > budgets["max_nodes"]
                or self._total_bytes() > budgets["max_total_bytes"]
            )
            if now - updated < max_age and not over_budget:
                continue
            peripherals.append(nid)

        if len(g["nodes"]) - len(peripherals) > budgets["max_nodes"]:
            ranked = sorted(
                [
                    (nid, n)
                    for nid, n in g["nodes"].items()
                    if nid not in peripherals
                    and n.get("type") != "summary"
                    and not (n.get("pinned") and ret.get("keep_pinned"))
                ],
                key=lambda x: (int(x[1].get("importance", 3)), x[1].get("updated_at", "")),
            )
            need = len(g["nodes"]) - len(peripherals) - budgets["max_nodes"]
            for nid, _ in ranked[: max(0, need)]:
                peripherals.append(nid)

        report = {"merged": [], "archived": [], "summary_id": None, "dry_run": dry_run}
        if not peripherals:
            self._log("compact", "nothing_to_do")
            return report

        snippets = []
        for nid in peripherals:
            npath = self._node_path(nid)
            if npath.exists():
                snippets.append(f"## {nid}\n\n" + npath.read_text(encoding="utf-8")[:800])
        summary_id = f"summary-peripheral-{now.strftime('%Y%m%d')}"
        summary_body = (
            "# Merged peripheral memories\n\n"
            f"Compacted {len(peripherals)} low-importance nodes on {utc_now()}.\n\n"
            + "\n\n".join(snippets[:40])
        )
        report["summary_id"] = summary_id
        report["merged"] = list(peripherals)
        if dry_run:
            return report

        self._in_compact = True
        try:
            now_s = utc_now()
            smeta = {
                "id": summary_id,
                "type": "summary",
                "importance": 3,
                "pinned": False,
                "tags": ["compact", "peripheral"],
                "created_at": now_s,
                "updated_at": now_s,
            }
            self._node_path(summary_id).write_text(
                self._render_node_md(smeta, summary_body), encoding="utf-8"
            )
            stamp = now.strftime("%Y%m%dT%H%M%SZ")
            dest = self.archive_dir / stamp
            dest.mkdir(parents=True, exist_ok=True)
            g = self._read_graph()
            g.setdefault("nodes", {})[summary_id] = {
                "id": summary_id,
                "type": "summary",
                "importance": 3,
                "pinned": False,
                "tags": ["compact", "peripheral"],
                "created_at": now_s,
                "updated_at": now_s,
                "preview": summary_body[: int(cfg["budgets"]["index_preview_chars"])],
                "path": f"nodes/{summary_id}.md",
            }
            for nid in peripherals:
                npath = self._node_path(nid)
                if npath.exists() and ret.get("archive_on_compact", True):
                    shutil.move(str(npath), str(dest / npath.name))
                    report["archived"].append(nid)
                elif npath.exists():
                    npath.unlink()
                g["nodes"].pop(nid, None)
                g["edges"] = [
                    e
                    for e in g.get("edges", [])
                    if e.get("from") != nid and e.get("to") != nid
                ]
                g["edges"].append({"from": summary_id, "to": nid, "rel": "archived"})
            self._write_graph(g)
            self.rebuild_index()
            self._log("compact", f"merged={len(peripherals)} -> {summary_id}")
        finally:
            self._in_compact = False
        return report

    def _total_bytes(self) -> int:
        total = 0
        if self.nodes_dir.exists():
            for p in self.nodes_dir.glob("*.md"):
                total += p.stat().st_size
        if self.graph_path.exists():
            total += self.graph_path.stat().st_size
        if self.index_path.exists():
            total += self.index_path.stat().st_size
        return total

    def stats(self, quiet: bool = False) -> dict:
        g = self._read_graph() if self.graph_path.exists() else {"nodes": {}, "edges": []}
        by_type: dict[str, int] = {}
        by_imp: dict[int, int] = {}
        for n in g.get("nodes", {}).values():
            by_type[n.get("type", "?")] = by_type.get(n.get("type", "?"), 0) + 1
            imp = int(n.get("importance", 0))
            by_imp[imp] = by_imp.get(imp, 0) + 1
        s = {
            "root": str(self.root),
            "node_count": len(g.get("nodes", {})),
            "edge_count": len(g.get("edges", [])),
            "total_bytes": self._total_bytes(),
            "by_type": by_type,
            "by_importance": by_imp,
        }
        if not quiet:
            print(json.dumps(s, ensure_ascii=False, indent=2))
        return s

    def rebuild_index(self) -> None:
        g = self._read_graph() if self.graph_path.exists() else {"nodes": {}, "edges": []}
        cfg = self.load_config() if self.config_path.exists() else DEFAULT_CONFIG
        lines = [
            "# Global memory INDEX",
            "",
            f"Updated: {utc_now()}",
            f"Root: `{self.root}`",
            f"Nodes: {len(g.get('nodes', {}))} · Edges: {len(g.get('edges', []))} · Bytes: {self._total_bytes()}",
            f"Budgets: max_nodes={cfg['budgets']['max_nodes']} max_total_bytes={cfg['budgets']['max_total_bytes']}",
            "",
            "## Nodes (importance ↓)",
            "",
            "| id | type | imp | pinned | tags | updated | preview |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        nodes = sorted(
            g.get("nodes", {}).values(),
            key=lambda x: (int(x.get("importance", 0)), x.get("updated_at", "")),
            reverse=True,
        )
        for n in nodes:
            tags = ",".join(n.get("tags") or [])
            prev = (n.get("preview") or "").replace("|", "/").replace("\n", " ")
            lines.append(
                f"| `{n['id']}` | {n.get('type')} | {n.get('importance')} | "
                f"{'Y' if n.get('pinned') else ''} | {tags} | {n.get('updated_at', '')} | {prev[:80]} |"
            )
        lines += ["", "## Edges", ""]
        for e in g.get("edges", [])[:200]:
            lines.append(f"- `{e.get('from')}` —{e.get('rel')}→ `{e.get('to')}`")
        lines.append("")
        self.index_path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DSH global memory (graph store under ~/.dsh/global-memory)")
    p.add_argument("--root", default=None, help="Override store root (default ~/.dsh/global-memory)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create store + default config")

    up = sub.add_parser("upsert", help="Create or update a node by id")
    up.add_argument("--id", required=False, help="Stable node id / slug")
    up.add_argument("--text", required=True, help="Memory body")
    up.add_argument("--type", default="fact", choices=NODE_TYPES)
    up.add_argument("--importance", type=int, default=None)
    up.add_argument("--tags", default="", help="Comma-separated tags")
    up.add_argument("--pin", action="store_true")
    up.add_argument("--link-to", default=None)
    up.add_argument("--rel", default="related")

    g = sub.add_parser("get", help="Print one node markdown")
    g.add_argument("id")

    q = sub.add_parser("query", help="Query graph by keyword/tag/type")
    q.add_argument("--q", default=None)
    q.add_argument("--tag", default=None)
    q.add_argument("--type", default=None, choices=NODE_TYPES)
    q.add_argument("--min-importance", type=int, default=1)
    q.add_argument("--limit", type=int, default=20)

    lk = sub.add_parser("link", help="Add edge between nodes")
    lk.add_argument("src")
    lk.add_argument("dst")
    lk.add_argument("--rel", default="related")

    pn = sub.add_parser("pin", help="Pin a node (survives compact)")
    pn.add_argument("id")
    pn.add_argument("--off", action="store_true", help="Unpin")

    cp = sub.add_parser("compact", help="Merge/archive peripheral nodes under budget")
    cp.add_argument("--dry-run", action="store_true")

    sub.add_parser("stats", help="Print size / counts")
    sub.add_parser("rebuild-index", help="Rewrite INDEX.md from graph.json")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    gm = GlobalMemory(Path(args.root) if args.root else None)

    if args.cmd == "init":
        gm.init(force_config=False)
        print(f"initialized: {gm.root}")
        return 0
    if args.cmd == "upsert":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        meta = gm.upsert(
            text=args.text,
            node_id=args.id,
            ntype=args.type,
            importance=args.importance,
            tags=tags,
            pinned=args.pin,
            link_to=args.link_to,
            rel=args.rel,
        )
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "get":
        sys.stdout.write(gm.get(args.id))
        return 0
    if args.cmd == "query":
        hits = gm.query(
            q=args.q, tag=args.tag, ntype=args.type, min_importance=args.min_importance, limit=args.limit
        )
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "link":
        gm.link(args.src, args.dst, args.rel)
        print("ok")
        return 0
    if args.cmd == "pin":
        gm.pin(args.id, pinned=not args.off)
        print("ok")
        return 0
    if args.cmd == "compact":
        report = gm.compact(dry_run=args.dry_run)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "stats":
        gm.stats()
        return 0
    if args.cmd == "rebuild-index":
        gm.rebuild_index()
        print(f"wrote {gm.index_path}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
