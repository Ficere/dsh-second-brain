/**
 * dsh-second-brain-memory client — Memory / 全局记忆 tab.
 * Separate from Trajectory execution DAG. Views: List | Graph | Timeline.
 * Data: GET /api/second-brain-memory/{graph,timeline,index} or file protocol via viewer.
 */
(function boot(global) {
  const css = `
.sbm-root{display:flex;flex-direction:column;gap:10px;height:100%;min-height:0;padding:12px 16px;box-sizing:border-box;font-size:13px;color:var(--dsw-alias-label-primary,#e6e6e6);background:transparent}
.sbm-bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.sbm-seg{display:inline-flex;border:1px solid rgba(128,128,128,.35);border-radius:8px;overflow:hidden}
.sbm-seg button{border:0;background:transparent;color:#9a9a9a;padding:4px 12px;cursor:pointer;font-size:12px}
.sbm-seg button.on{background:rgba(128,128,128,.28);color:#e6e6e6}
.sbm-search{flex:1;min-width:140px;background:transparent;border:1px solid rgba(128,128,128,.35);border-radius:8px;padding:4px 10px;color:inherit}
.sbm-inject{font-size:11.5px;color:#9b59f0;border:1px dashed #9b59f0;border-radius:8px;padding:6px 10px;white-space:pre-wrap;max-height:72px;overflow:auto}
.sbm-main{flex:1;min-height:0;display:flex;gap:10px}
.sbm-list{flex:1;overflow:auto;display:flex;flex-direction:column;gap:6px}
.sbm-row{border:1px solid rgba(128,128,128,.25);border-radius:10px;padding:8px 10px;cursor:pointer}
.sbm-row.sel{border-color:#4f8ef7}
.sbm-meta{font-size:11px;color:#9a9a9a;margin-top:4px}
.sbm-graphwrap,.sbm-timewrap{flex:1;min-height:240px;border:1px solid rgba(128,128,128,.25);border-radius:10px;position:relative;overflow:hidden}
.sbm-canvas{position:absolute;inset:0;width:100%;height:100%}
.sbm-detail{width:min(300px,36%);overflow:auto;border:1px solid rgba(128,128,128,.35);border-radius:10px;padding:10px;background:rgba(20,20,20,.9)}
.sbm-tl{list-style:none;margin:0;padding:8px 12px;overflow:auto;height:100%}
.sbm-tl li{padding:8px 0 8px 14px;border-left:2px solid #4f8ef7;margin-left:6px}
.sbm-tl .t{font-size:11px;color:#9a9a9a}
.sbm-empty{opacity:.6;padding:24px;text-align:center}
`
  function ensureCss() {
    if (document.getElementById('sbm-css')) return
    const s = document.createElement('style')
    s.id = 'sbm-css'
    s.textContent = css
    document.head.appendChild(s)
  }

  const TYPE_COLOR = {
    fact: '#4f8ef7', preference: '#9b59f0', person: '#2ecc71',
    decision: '#f0b429', summary: '#95a5a6', ephemeral: '#e67e22',
  }

  async function fetchJSON(url, fallback) {
    try {
      const r = await fetch(url)
      if (!r.ok) throw new Error(String(r.status))
      return await r.json()
    } catch {
      return fallback
    }
  }

  function MemoryApp(rootEl, opts = {}) {
    ensureCss()
    const apiBase = opts.apiBase || '/api/second-brain-memory'
    const state = { view: 'list', q: '', graph: { nodes: {}, edges: [] }, timeline: [], inject: '', selected: null }

    rootEl.className = 'sbm-root'
    rootEl.innerHTML = `
      <div class="sbm-bar">
        <div class="sbm-seg" data-seg>
          <button data-v="list" class="on">列表 List</button>
          <button data-v="graph">图谱 Graph</button>
          <button data-v="timeline">时间线 Timeline</button>
        </div>
        <input class="sbm-search" placeholder="搜索 id / tag / 正文…" />
        <button type="button" data-refresh>刷新</button>
      </div>
      <div class="sbm-inject" data-inject title="本回合可注入的紧凑索引（类 dsh-context 可见条）">加载索引…</div>
      <div class="sbm-main">
        <div data-pane style="flex:1;min-width:0;min-height:0;display:flex;flex-direction:column"></div>
        <div class="sbm-detail" data-detail><em>选择一条记忆</em></div>
      </div>`

    const pane = rootEl.querySelector('[data-pane]')
    const detail = rootEl.querySelector('[data-detail]')
    const injectEl = rootEl.querySelector('[data-inject]')
    const search = rootEl.querySelector('.sbm-search')

    rootEl.querySelector('[data-seg]').onclick = (e) => {
      const b = e.target.closest('button[data-v]')
      if (!b) return
      state.view = b.dataset.v
      rootEl.querySelectorAll('[data-seg] button').forEach((x) => x.classList.toggle('on', x === b))
      render()
    }
    rootEl.querySelector('[data-refresh]').onclick = () => load()
    search.oninput = () => { state.q = search.value.trim().toLowerCase(); render() }

    function filteredNodes() {
      const all = Object.values(state.graph.nodes || {})
      if (!state.q) return all
      return all.filter((n) => {
        const blob = [n.id, n.type, ...(n.tags || []), n.preview || ''].join(' ').toLowerCase()
        return blob.includes(state.q)
      })
    }

    function showDetail(n) {
      state.selected = n?.id || null
      if (!n) { detail.innerHTML = '<em>选择一条记忆</em>'; return }
      detail.innerHTML = `<h4 style="margin:0 0 6px">${n.pinned ? '📌 ' : ''}${n.id}</h4>
        <div class="sbm-meta">${n.type} · imp ${n.importance} · ${n.updated_at || ''}</div>
        <p style="white-space:pre-wrap;margin:8px 0 0">${(n.preview || '').replace(/</g, '&lt;')}</p>
        <div class="sbm-meta">tags: ${(n.tags || []).join(', ') || '—'}</div>
        <div class="sbm-meta">path: ${n.path || 'nodes/' + n.id + '.md'}</div>`
    }

    function renderList() {
      const nodes = filteredNodes().sort((a, b) => (b.importance || 0) - (a.importance || 0))
      if (!nodes.length) {
        pane.innerHTML = '<div class="sbm-empty">暂无全局记忆。在 Web 对话说「记到全局 …」或运行 scripts/global_memory.py upsert</div>'
        return
      }
      const list = document.createElement('div')
      list.className = 'sbm-list'
      for (const n of nodes) {
        const row = document.createElement('div')
        row.className = 'sbm-row' + (state.selected === n.id ? ' sel' : '')
        row.innerHTML = `<div>${n.pinned ? '📌 ' : ''}<b>${n.id}</b></div>
          <div>${(n.preview || '').slice(0, 120)}</div>
          <div class="sbm-meta"><span style="color:${TYPE_COLOR[n.type] || '#aaa'}">●</span> ${n.type} · imp${n.importance} · ${n.updated_at || ''}</div>`
        row.onclick = () => { showDetail(n); render() }
        list.appendChild(row)
      }
      pane.innerHTML = ''
      pane.appendChild(list)
    }

    function renderGraph() {
      pane.innerHTML = '<div class="sbm-graphwrap"><canvas class="sbm-canvas"></canvas></div>'
      const canvas = pane.querySelector('canvas')
      const wrap = pane.querySelector('.sbm-graphwrap')
      const dpr = window.devicePixelRatio || 1
      const W = wrap.clientWidth || 640
      const H = wrap.clientHeight || 360
      canvas.width = W * dpr
      canvas.height = H * dpr
      canvas.style.width = W + 'px'
      canvas.style.height = H + 'px'
      const ctx = canvas.getContext('2d')
      ctx.scale(dpr, dpr)

      const nodes = filteredNodes()
      const pos = {}
      const R = Math.min(W, H) * 0.36
      nodes.forEach((n, i) => {
        const a = (i / Math.max(nodes.length, 1)) * Math.PI * 2
        pos[n.id] = {
          x: W / 2 + Math.cos(a) * R * (0.55 + (n.importance || 3) / 10),
          y: H / 2 + Math.sin(a) * R * (0.55 + (n.importance || 3) / 10),
          n,
        }
      })
      // simple force relaxation
      for (let iter = 0; iter < 40; iter++) {
        for (const a of Object.values(pos)) {
          for (const b of Object.values(pos)) {
            if (a === b) continue
            let dx = a.x - b.x, dy = a.y - b.y
            let dist = Math.hypot(dx, dy) || 1
            const push = 800 / (dist * dist)
            a.x += (dx / dist) * push
            a.y += (dy / dist) * push
          }
          a.x += (W / 2 - a.x) * 0.02
          a.y += (H / 2 - a.y) * 0.02
        }
        for (const e of state.graph.edges || []) {
          const a = pos[e.from], b = pos[e.to]
          if (!a || !b) continue
          const dx = b.x - a.x, dy = b.y - a.y
          a.x += dx * 0.01; a.y += dy * 0.01
          b.x -= dx * 0.01; b.y -= dy * 0.01
        }
      }

      ctx.clearRect(0, 0, W, H)
      ctx.strokeStyle = 'rgba(128,128,128,.35)'
      for (const e of state.graph.edges || []) {
        const a = pos[e.from], b = pos[e.to]
        if (!a || !b) continue
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
      }
      for (const p of Object.values(pos)) {
        const r = 6 + (p.n.importance || 3)
        ctx.fillStyle = TYPE_COLOR[p.n.type] || '#888'
        ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.fill()
        ctx.fillStyle = '#ccc'
        ctx.font = '11px sans-serif'
        ctx.fillText(p.n.id.slice(0, 18), p.x + r + 2, p.y + 3)
      }
      canvas.onclick = (ev) => {
        const rect = canvas.getBoundingClientRect()
        const x = ev.clientX - rect.left, y = ev.clientY - rect.top
        let hit = null, best = 999
        for (const p of Object.values(pos)) {
          const d = Math.hypot(p.x - x, p.y - y)
          if (d < 16 && d < best) { best = d; hit = p.n }
        }
        if (hit) showDetail(hit)
      }
    }

    function renderTimeline() {
      let evs = state.timeline.length
        ? state.timeline
        : filteredNodes().map((n) => ({ id: n.id, at: n.updated_at || n.created_at, type: n.type, importance: n.importance, pinned: n.pinned, preview: n.preview }))
      if (state.q) evs = evs.filter((e) => JSON.stringify(e).toLowerCase().includes(state.q))
      evs = [...evs].sort((a, b) => String(b.at).localeCompare(String(a.at)))
      const ul = document.createElement('ul')
      ul.className = 'sbm-tl'
      if (!evs.length) {
        pane.innerHTML = '<div class="sbm-empty">时间线为空</div>'
        return
      }
      for (const e of evs) {
        const li = document.createElement('li')
        li.innerHTML = `<div class="t">${e.at || ''} · ${e.type || ''} · imp${e.importance ?? ''}</div>
          <div><b>${e.pinned ? '📌 ' : ''}${e.id}</b> — ${(e.preview || '').slice(0, 100)}</div>`
        li.onclick = () => showDetail(state.graph.nodes[e.id] || e)
        ul.appendChild(li)
      }
      const wrap = document.createElement('div')
      wrap.className = 'sbm-timewrap'
      wrap.appendChild(ul)
      pane.innerHTML = ''
      pane.appendChild(wrap)
    }

    function render() {
      if (state.view === 'graph') renderGraph()
      else if (state.view === 'timeline') renderTimeline()
      else renderList()
    }

    async function load() {
      const g = await fetchJSON(`${apiBase}/graph`, { nodes: {}, edges: [], ok: false })
      state.graph = { nodes: g.nodes || {}, edges: g.edges || [] }
      const tl = await fetchJSON(`${apiBase}/timeline`, { events: [] })
      state.timeline = tl.events || []
      try {
        const r = await fetch(`${apiBase}/index`)
        injectEl.textContent = r.ok ? await r.text() : '（无注入索引 — 尚未 init 或插件 API 未挂上）'
      } catch {
        injectEl.textContent = '（离线 / 无 API）'
      }
      // offline: allow opts.initialGraph
      if (!Object.keys(state.graph.nodes).length && opts.initialGraph) {
        state.graph = opts.initialGraph
        state.timeline = Object.values(state.graph.nodes).map((n) => ({
          id: n.id, at: n.updated_at, type: n.type, importance: n.importance, pinned: n.pinned, preview: n.preview,
        }))
      }
      render()
    }

    load()
    return { reload: load, getState: () => state }
  }

  // Expose for standalone viewer / tests
  global.DshSecondBrainMemory = { MemoryApp }

  // Cordis ModuleLoader registration (when running inside dsh web)
  if (global.__ModuleLoader__ && typeof global.__ModuleLoader__.load === 'function') {
    global.__ModuleLoader__.load({
      id: 'dsh-second-brain-memory',
      factory: (require) => {
        const React = require('react')
        const { jsx, jsxs } = require('react/jsx-runtime')
        function MemoryView() {
          const ref = React.useRef(null)
          React.useEffect(() => {
            if (ref.current) MemoryApp(ref.current)
          }, [])
          return jsx('div', { ref, style: { height: '100%', minHeight: 320 } })
        }
        // Best-effort: register conversation.view seat like dsh-memory
        try {
          const slots = require('@deepseek-ai/dsh-client-ui-conversation')
          slots?.registerView?.({
            id: 'second-brain-memory',
            title: 'Memory / 全局记忆',
            order: 50,
            render: () => jsx(MemoryView, {}),
          })
        } catch {
          /* seat API may differ by harness version — viewer still works standalone */
        }
        return { MemoryView, MemoryApp }
      },
    })
  }
})(typeof window !== 'undefined' ? window : globalThis);
