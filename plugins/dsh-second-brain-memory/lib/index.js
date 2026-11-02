/**
 * dsh-second-brain-memory — host side (Cordis).
 * Reads/writes ~/.dsh/global-memory (or $DSH_HOME/global-memory).
 * Provides HTTP JSON for the Memory tab and a compact index string for session inject.
 *
 * Note: full Cordis apply() wiring follows harness 0.2 Config+apply channel when
 * installed via `dsh plugin --profile web add`. Standalone Node can still import
 * { loadStore, compactIndex, upsertNode } for tests.
 */
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export const Config = {
  enabled: true,
  root: '', // default: $DSH_HOME/global-memory or ~/.dsh/global-memory
  injectMaxChars: 2400,
  injectTopK: 12,
  scriptPath: '', // optional absolute path to scripts/global_memory.py
}

function dshHome() {
  return process.env.DSH_HOME || path.join(os.homedir(), '.dsh')
}

export function resolveRoot(config = {}) {
  if (config.root) return config.root.replace(/^~(?=$|\/|\\)/, os.homedir())
  return path.join(dshHome(), 'global-memory')
}

export function loadStore(root) {
  const graphPath = path.join(root, 'graph.json')
  const indexPath = path.join(root, 'INDEX.md')
  const configPath = path.join(root, 'config.yaml')
  let graph = { version: 1, nodes: {}, edges: [] }
  if (fs.existsSync(graphPath)) {
    try { graph = JSON.parse(fs.readFileSync(graphPath, 'utf8')) } catch { /* keep empty */ }
  }
  const index = fs.existsSync(indexPath) ? fs.readFileSync(indexPath, 'utf8') : ''
  const enabled = !fs.existsSync(configPath)
    ? true
    : !/^\s*enabled:\s*false\s*$/m.test(fs.readFileSync(configPath, 'utf8'))
  return { root, graph, index, enabled, graphPath, indexPath }
}

export function compactIndex(store, { topK = 12, maxChars = 2400 } = {}) {
  if (!store.enabled) return ''
  const nodes = Object.values(store.graph.nodes || {})
    .sort((a, b) => (b.importance || 0) - (a.importance || 0) || String(b.updated_at).localeCompare(String(a.updated_at)))
    .slice(0, topK)
  const lines = [
    '<memory 全局记忆 · 本机跨工作区 · 仅索引摘要>',
    '细节请用 Memory 页或 global_memory.py query；本地 .memory/ 优先于全局。',
  ]
  for (const n of nodes) {
    const pin = n.pinned ? '📌' : ''
    const prev = (n.preview || '').replace(/\s+/g, ' ').slice(0, 80)
    lines.push(`- [${n.type}|imp${n.importance}] ${pin}${n.id} · ${prev}`)
  }
  lines.push('</memory>')
  let text = lines.join('\n')
  if (text.length > maxChars) text = text.slice(0, maxChars - 1) + '…'
  return text
}

export function runPy(scriptPath, args, root) {
  const script = scriptPath || path.resolve(__dirname, '../../../scripts/global_memory.py')
  const cmd = ['python3', script, '--root', root, ...args]
  const r = spawnSync(cmd[0], cmd.slice(1), { encoding: 'utf8' })
  return { code: r.status ?? 1, stdout: r.stdout || '', stderr: r.stderr || '' }
}

/**
 * Cordis entry. Safe no-op if seats missing (older harness).
 */
export function apply(ctx, config = {}) {
  const cfg = { ...Config, ...config }
  const root = resolveRoot(cfg)

  // Ensure store exists when plugin loads
  try {
    runPy(cfg.scriptPath, ['init'], root)
  } catch { /* ignore */ }

  // Optional HTTP for Memory tab (harness-dependent)
  try {
    ctx.http?.get?.('/api/second-brain-memory/graph', (_req, res) => {
      const store = loadStore(root)
      res.json({ ok: true, ...store.graph, root: store.root, enabled: store.enabled })
    })
    ctx.http?.get?.('/api/second-brain-memory/index', (_req, res) => {
      const store = loadStore(root)
      res.type('text/plain').send(compactIndex(store, { topK: cfg.injectTopK, maxChars: cfg.injectMaxChars }))
    })
    ctx.http?.get?.('/api/second-brain-memory/timeline', (_req, res) => {
      const store = loadStore(root)
      const events = Object.values(store.graph.nodes || {})
        .map((n) => ({
          id: n.id,
          at: n.updated_at || n.created_at,
          created_at: n.created_at,
          type: n.type,
          importance: n.importance,
          pinned: !!n.pinned,
          preview: n.preview,
        }))
        .sort((a, b) => String(b.at).localeCompare(String(a.at)))
      res.json({ ok: true, events, root: store.root })
    })
  } catch { /* host without http */ }

  // Session inject: compact index only (waterfall if available)
  try {
    ctx.on?.('system-prompt/assemble', (ev) => {
      const store = loadStore(root)
      const block = compactIndex(store, { topK: cfg.injectTopK, maxChars: cfg.injectMaxChars })
      if (block && ev?.append) ev.append(block)
      else if (block && typeof ev === 'object') ev.globalMemoryIndex = block
    })
  } catch { /* optional */ }

  ctx.logger?.info?.(`[dsh-second-brain-memory] root=${root}`)
}

export default { Config, apply, name: 'dsh-second-brain-memory' }
