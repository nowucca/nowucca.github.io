#!/usr/bin/env python3
"""Build the Research section of nowucca.com from research/_src/.

    python3 research/_src/build.py

Inputs (all in research/_src/):
  entries.json      themes > subtopics, entries (metadata), edges (cross-links)
  entries/*.html    entry bodies, cleaned by import_doc.py
  diagrams/*.svg    diagrams rendered by render_diagrams.js

Outputs:
  research/index.html          themes, subtopics and entries, plus a registry
  research/map/index.html      interactive knowledge map of entries and links
  research/<slug>/index.html   one page per entry, with its connections

Jekyll skips _src (leading underscore), so only the generated pages are served.
"""
import html, json, math, random, re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
FONTS = "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=IBM+Plex+Mono:wght@500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap"

e = lambda s: html.escape(str(s), quote=True)


def load():
    cfg = json.loads((SRC / "entries.json").read_text())
    entries = {x["id"]: x for x in cfg["entries"]}
    theme_of, sub_of = {}, {}
    for i, t in enumerate(cfg["themes"]):
        t["color"] = f"var(--t{i % 8 + 1})"
        for s in t["subtopics"]:
            for rid in s["primary"]:
                theme_of[rid], sub_of[rid] = t, s
    for rid in entries:
        if rid not in theme_of:
            raise SystemExit(f"{rid} is not filed under any subtopic")
    for ed in cfg["edges"]:
        for k in ("a", "b"):
            if ed[k] not in entries:
                raise SystemExit(f"edge names unknown entry {ed[k]}")
    return cfg, entries, theme_of, sub_of


def page(title, body, desc, wide=False, active=""):
    nav = [("/research/", "Research"), ("/research/map/", "Knowledge map"), ("/library/", "Library")]
    links = " ".join(
        f'<a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{e(t)}</a>' for h, t in nav
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/library/style.css">
<link rel="stylesheet" href="/research/style.css">
</head>
<body>
<main class="wrap{' wide' if wide else ''}">
<nav class="crumbs" aria-label="Section"><a href="/">&larr; nowucca.com</a>{links}</nav>
{body}
</main>
</body>
</html>
"""


def tags(t):
    return '<div class="tags">' + "".join(f'<span class="tag">{e(x)}</span>' for x in t) + "</div>"


def neighbours(cfg, rid):
    out = []
    for ed in cfg["edges"]:
        if rid in (ed["a"], ed["b"]):
            out.append((ed["b"] if ed["a"] == rid else ed["a"], ed))
    return out


# ---------- entry pages ----------

def wrap_tables(body):
    return re.sub(r"(<table>.*?</table>)", r'<div class="table-scroll">\1</div>', body, flags=re.S)


def fill_diagrams(body):
    def sub(m):
        node, rest = m.group(1), m.group(2)
        svg_path = SRC / "diagrams" / f"{node}.svg"
        if not svg_path.exists():
            raise SystemExit(f"missing diagram {svg_path.name}; run render_diagrams.js")
        return f'<figure class="diagram" data-diagram="{node}"><div class="diagram-scroll">{svg_path.read_text().strip()}</div>{rest}</figure>'
    return re.sub(r'<figure class="diagram" data-diagram="([^"]+)">(.*?)</figure>', sub, body, flags=re.S)


def entry_page(cfg, entries, theme_of, sub_of, x):
    t, s = theme_of[x["id"]], sub_of[x["id"]]
    body = (SRC / x["file"]).read_text()
    body = fill_diagrams(wrap_tables(body))
    conns = neighbours(cfg, x["id"])
    items = []
    for other, ed in conns:
        o = entries[other]
        weak = '<span class="weak-tag">weak</span>' if ed["strength"] == "weak" else ""
        items.append(
            f'<li style="--c:{theme_of[other]["color"]}"><a class="to" href="/research/{o["slug"]}/">{e(o["title"])}</a>'
            f'<span class="label">{e(other)} · {e(theme_of[other]["title"])}{weak}</span><span class="why">{e(ed["why"])}</span></li>'
        )
    conn_html = (
        f'<section class="article"><h2>Connections</h2><ul class="links">{"".join(items)}</ul>'
        f'<p><a href="/research/map/#{e(x["id"])}">See {e(x["id"])} on the knowledge map</a></p></section>'
        if items else ""
    )
    head = f"""<header class="masthead">
  <span class="label">{e(x["id"])} · {e(t["title"])} › {e(s["title"])}</span>
  <h1>{e(x["title"])}</h1>
  <div class="entry-meta"><span>{e(x["by"])}</span><span>Published {e(x["published"])}</span><span>Summarized {e(x["added"])}</span></div>
  <p><a href="{e(x["source"])}" rel="noopener">Read the original</a></p>
  {tags(x["tags"])}
</header>"""
    foot = '<p class="foot">Part of the <a href="/research/">Research</a> notes on nowucca.com. Figures and claims are the source\'s own unless the summary says otherwise.</p>'
    html_out = page(f'{x["title"]} · Research', head + f'\n<article class="article">{body}</article>\n' + conn_html + foot, x["summary"])
    d = OUT / x["slug"]
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(html_out)


# ---------- index ----------

def index_page(cfg, entries, theme_of, sub_of, updated):
    parts = [f"""<header class="masthead">
  <span class="label">nowucca.com · research</span>
  <h1>{e(cfg["title"])}</h1>
  <p class="lede">{e(cfg["lede"])}</p>
  <div class="meta label"><span>{len(entries)} entries</span><span>{len(cfg["edges"])} connections</span><span>Updated <time datetime="{updated[0]}">{updated[1]}</time></span></div>
</header>
<a class="cta" href="/research/map/"><span><span class="cta-title">Knowledge map</span><span class="label">Every entry and how the ideas connect</span></span><span class="cta-go">Open the map &rarr;</span></a>"""]
    for t in cfg["themes"]:
        subs = []
        for s in t["subtopics"]:
            rows = []
            for rid in s["primary"]:
                x = entries[rid]
                rows.append(
                    f'<li><a class="row" href="/research/{x["slug"]}/"><span class="date">{e(x["added"])}</span>'
                    f'<span class="text"><span class="id">{e(rid)}</span><span class="title">{e(x["title"])}</span>'
                    f'<span class="one">{e(x["summary"])}</span>{tags(x["tags"])}</span></a></li>'
                )
            also = "".join(
                f'<li><span class="label">Also</span><a href="/research/{entries[a["id"]]["slug"]}/">{e(a["id"])} {e(entries[a["id"]]["title"])}</a>: {e(a["why"])}</li>'
                for a in s["also"]
            )
            subs.append(
                f'<div class="subtopic"><h3><span class="n">{e(s["n"])}</span>{e(s["title"])}</h3>'
                + (f'<ol class="rows">{"".join(rows)}</ol>' if rows else "")
                + (f'<ul class="also">{also}</ul>' if also else "")
                + "</div>"
            )
        parts.append(
            f'<section class="theme" id="theme-{e(t["n"])}" style="--c:{t["color"]}"><header><h2><span class="swatch"></span>{e(t["n"])}. {e(t["title"])}</h2>'
            f'<p class="lede">{e(t["lede"])}</p></header>{"".join(subs)}</section>'
        )
    reg = "".join(
        f'<tr><td>{e(x["id"])}</td><td><a href="/research/{x["slug"]}/">{e(x["title"])}</a></td>'
        f'<td class="hide-sm">{e(sub_of[x["id"]]["n"])} {e(sub_of[x["id"]]["title"])}</td><td class="hide-sm">{e(x["added"])}</td></tr>'
        for x in sorted(entries.values(), key=lambda v: v["id"], reverse=True)
    )
    parts.append(
        '<section class="theme"><header><h2>All entries</h2></header><div class="table-scroll"><table class="registry">'
        '<thead><tr><th>ID</th><th>Title</th><th class="hide-sm">Filed under</th><th class="hide-sm">Added</th></tr></thead>'
        f"<tbody>{reg}</tbody></table></div></section>"
    )
    (OUT / "index.html").write_text(page("Research", "\n".join(parts), cfg["lede"], active="/research/"))


# ---------- map ----------

def layout(ids, edges, w=760, h=520, iters=600):
    """Deterministic force layout: springs on edges, repulsion between nodes."""
    rnd = random.Random(7)
    n = len(ids)
    pos = {rid: [w / 2 + 180 * math.cos(2 * math.pi * i / n) + rnd.uniform(-5, 5),
                 h / 2 + 150 * math.sin(2 * math.pi * i / n) + rnd.uniform(-5, 5)] for i, rid in enumerate(ids)}
    k = math.sqrt(w * h / max(n, 1)) * 0.8
    for step in range(iters):
        temp = 18 * (1 - step / iters) + 0.5
        disp = {rid: [0.0, 0.0] for rid in ids}
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
                d = math.hypot(dx, dy) or 0.01
                f = k * k / d if d < 3 * k else 0.0
                disp[a][0] += dx / d * f; disp[a][1] += dy / d * f
                disp[b][0] -= dx / d * f; disp[b][1] -= dy / d * f
        for ed in edges:
            a, b = ed["a"], ed["b"]
            dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
            d = math.hypot(dx, dy) or 0.01
            f = d * d / k * (0.6 if ed["strength"] == "weak" else 1)
            disp[a][0] -= dx / d * f; disp[a][1] -= dy / d * f
            disp[b][0] += dx / d * f; disp[b][1] += dy / d * f
        for rid in ids:
            dx, dy = disp[rid]
            dx += (w / 2 - pos[rid][0]) * 0.06; dy += (h / 2 - pos[rid][1]) * 0.06
            d = math.hypot(dx, dy) or 0.01
            pos[rid][0] += dx / d * min(d, temp); pos[rid][1] += dy / d * min(d, temp)
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    mx, my = 110, 60
    sx = (w - 2 * mx) / ((max(xs) - min(xs)) or 1); sy = (h - 2 * my - 30) / ((max(ys) - min(ys)) or 1)
    # Fit the frame, but don't stretch one axis more than 1.6x the other.
    sx, sy = min(sx, sy * 1.6), min(sy, sx * 1.6)
    ox = (w - (max(xs) - min(xs)) * sx) / 2; oy = (h - 30 - (max(ys) - min(ys)) * sy) / 2
    return {rid: (round(ox + (p[0] - min(xs)) * sx, 1), round(oy + (p[1] - min(ys)) * sy, 1)) for rid, p in pos.items()}


MAP_JS = r"""
(() => {
  const D = JSON.parse(document.getElementById('map-data').textContent);
  const byId = Object.fromEntries(D.nodes.map(n => [n.id, n]));
  const svg = document.getElementById('map');
  const panel = document.getElementById('panel');
  const NS = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs, parent) => { const x = document.createElementNS(NS, tag); for (const k in attrs) x.setAttribute(k, attrs[k]); parent && parent.appendChild(x); return x; };
  const gEdges = el('g', {}, svg), gNodes = el('g', {}, svg);
  const edgeEls = D.edges.map((ed, i) => {
    const a = byId[ed.a], b = byId[ed.b];
    const line = el('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: 'edge' + (ed.strength === 'weak' ? ' weak' : '') }, gEdges);
    const hit = el('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: 'edge-hit' }, gEdges);
    hit.addEventListener('click', () => selectEdge(i));
    return line;
  });
  const deg = id => D.edges.filter(ed => ed.a === id || ed.b === id).length;
  const nodeEls = {};
  for (const n of D.nodes) {
    const g = el('g', { class: 'node', tabindex: '0', role: 'button', 'aria-label': `${n.id}: ${n.title}` }, gNodes);
    el('circle', { cx: n.x, cy: n.y, r: 9 + 2.5 * deg(n.id), style: `fill:${n.color}` }, g);
    const r = 9 + 2.5 * deg(n.id);
    const t = el('text', { x: n.x, y: n.y + r + 15, 'text-anchor': 'middle' }, g); t.textContent = n.short;
    const s = el('text', { x: n.x, y: n.y + r + 28, 'text-anchor': 'middle', class: 'rid' }, g); s.textContent = n.id;
    g.addEventListener('click', () => selectNode(n.id));
    g.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); selectNode(n.id); } });
    g.addEventListener('mouseenter', () => highlight(n.id));
    g.addEventListener('mouseleave', () => highlight(current));
    nodeEls[n.id] = g;
  }
  let current = null;
  function highlight(id, edgeIdx) {
    const near = new Set();
    D.edges.forEach((ed, i) => {
      const on = edgeIdx !== undefined ? i === edgeIdx : (id && (ed.a === id || ed.b === id));
      edgeEls[i].classList.toggle('hot', !!on);
      edgeEls[i].classList.toggle('dim', (id || edgeIdx !== undefined) && !on);
      if (on) { near.add(ed.a); near.add(ed.b); }
    });
    for (const k in nodeEls) {
      nodeEls[k].classList.toggle('dim', (id || edgeIdx !== undefined) && !near.has(k) && k !== id);
      nodeEls[k].classList.toggle('sel', k === id);
    }
  }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function selectNode(id) {
    current = id; highlight(id);
    history.replaceState(null, '', '#' + id);
    const n = byId[id];
    const links = D.edges.filter(ed => ed.a === id || ed.b === id).map(ed => {
      const o = byId[ed.a === id ? ed.b : ed.a];
      return `<li style="--c:${o.color}"><button class="to" data-go="${o.id}">${esc(o.id)} ${esc(o.title)}</button>${ed.strength === 'weak' ? '<span class="label">weak link</span>' : ''}<span class="why">${esc(ed.why)}</span></li>`;
    }).join('');
    panel.innerHTML = `<span class="label">${esc(n.id)} · ${esc(n.theme)}</span><h2>${esc(n.title)}</h2><p class="one">${esc(n.summary)}</p><p><a href="/research/${n.slug}/">Read the summary &rarr;</a></p>` +
      (links ? `<h3 class="label">Connections</h3><ul class="links">${links}</ul>` : '<p class="one">No connections yet.</p>');
    panel.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click', () => { selectNode(b.dataset.go); nodeEls[b.dataset.go].focus(); }));
  }
  function selectEdge(i) {
    const ed = D.edges[i], a = byId[ed.a], b = byId[ed.b];
    current = null; highlight(null, i);
    panel.innerHTML = `<span class="label">Connection${ed.strength === 'weak' ? ' · weak' : ''}</span><h2>${esc(a.id)} and ${esc(b.id)}</h2><p>${esc(ed.why)}</p>` +
      `<ul class="links"><li style="--c:${a.color}"><button class="to" data-go="${a.id}">${esc(a.title)}</button></li><li style="--c:${b.color}"><button class="to" data-go="${b.id}">${esc(b.title)}</button></li></ul>`;
    panel.querySelectorAll('[data-go]').forEach(x => x.addEventListener('click', () => selectNode(x.dataset.go)));
  }
  svg.addEventListener('click', ev => { if (ev.target === svg) { current = null; highlight(null); } });
  const start = location.hash.slice(1);
  if (byId[start]) selectNode(start);
})();
"""


def short_title(t):
    t = re.split(r"[:(]", t)[0].strip()
    return t if len(t) <= 26 else t[:24].rstrip() + "…"


def map_page(cfg, entries, theme_of, updated):
    ids = sorted(entries)
    pos = layout(ids, cfg["edges"])
    data = {
        "nodes": [dict(id=r, title=entries[r]["title"], short=short_title(entries[r]["title"]), slug=entries[r]["slug"],
                       summary=entries[r]["summary"], theme=theme_of[r]["title"], color=theme_of[r]["color"],
                       x=pos[r][0], y=pos[r][1]) for r in ids],
        "edges": cfg["edges"],
    }
    legend = "".join(
        f'<li><span class="swatch" style="--c:{t["color"]}"></span>{e(t["title"])}</li>'
        for t in cfg["themes"] if any(s["primary"] for s in t["subtopics"])
    ) + '<li><span class="solid"></span>link</li><li><span class="dash"></span>weak link</li>'
    fallback = "".join(
        f'<li><a href="/research/{entries[ed["a"]]["slug"]}/">{e(ed["a"])}</a> and <a href="/research/{entries[ed["b"]]["slug"]}/">{e(ed["b"])}</a>'
        f'{" (weak)" if ed["strength"] == "weak" else ""}: {e(ed["why"])}</li>'
        for ed in cfg["edges"]
    )
    body = f"""<header class="masthead">
  <span class="label">nowucca.com · research</span>
  <h1>Knowledge map</h1>
  <p class="lede">Each dot is a summarized source, coloured by theme and sized by how many others it connects to. Lines are the cross-links: pick a dot or a line to see why two ideas meet.</p>
  <div class="meta label"><span>{len(entries)} entries</span><span>{len(cfg["edges"])} connections</span><span>Updated <time datetime="{updated[0]}">{updated[1]}</time></span></div>
</header>
<ul class="legend">{legend}</ul>
<div class="map-shell">
  <div class="map-stage">
    <svg id="map" viewBox="0 0 760 520" role="group" aria-label="Knowledge map of research entries"></svg>
    <span class="map-hint">Select a dot or a line</span>
  </div>
  <aside class="panel" id="panel" aria-live="polite">
    <span class="label">How to read it</span>
    <h2>Pick an entry</h2>
    <p class="one">Its summary and every connection appear here, each with the reason the two are linked. Dashed lines are weak links: a shared theme more than a shared mechanism.</p>
  </aside>
</div>
<section class="article"><h2>All connections</h2><ul class="all-links">{fallback}</ul></section>
<script type="application/json" id="map-data">{json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>{MAP_JS}</script>"""
    d = OUT / "map"
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("Knowledge map · Research", body, "How the research entries on nowucca.com connect.", wide=True, active="/research/map/"))


def main():
    cfg, entries, theme_of, sub_of = load()
    # Build time in Central (Steven's zone); builds only run when something is published.
    now = datetime.now(ZoneInfo("America/Chicago")).replace(second=0, microsecond=0)
    updated = (now.isoformat(), now.strftime("%b %-d, %Y, %-I:%M %p CT"))
    for x in entries.values():
        entry_page(cfg, entries, theme_of, sub_of, x)
    index_page(cfg, entries, theme_of, sub_of, updated)
    map_page(cfg, entries, theme_of, updated)
    print(f"built {len(entries)} entries, index and map (updated {updated[1]})")


if __name__ == "__main__":
    main()
