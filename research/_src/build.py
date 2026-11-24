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
  research/authors/            authors ranked by reputation, one page each (authors.py, authors.json)

Jekyll skips _src (leading underscore), so only the generated pages are served.
"""
import html, json, math, random, re
import authors as authors_mod
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
FONTS = "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=IBM+Plex+Mono:wght@500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap"

e = lambda s: html.escape(str(s), quote=True)


def load_guides():
    p = SRC / "guides.json"
    return json.loads(p.read_text())["guides"] if p.exists() else []


GUIDES = load_guides()


def guide_pages(entries, theme_of):
    """Field guides: syntheses across entries, published one at a time after approval."""
    if not GUIDES:
        return
    d = OUT / "guides"
    d.mkdir(exist_ok=True)
    cards = []
    for g in GUIDES:
        for rid in g["entries"]:
            if rid not in entries:
                raise SystemExit(f"guide {g['slug']} draws on non-public entry {rid}")
        body = fill_diagrams(wrap_tables((SRC / "guides" / f"{g['slug']}.html").read_text()))
        srcs = "".join(
            f'<li style="--c:{theme_of[r]["color"]}"><a class="to" href="/research/{entries[r]["slug"]}/">{e(entries[r]["title"])}</a><span class="label">{e(r)}</span></li>'
            for r in g["entries"]
        )
        head = f"""<header class="masthead">
  <span class="label">Field guide · {len(g["entries"])} sources</span>
  <h1>{e(g["title"])}</h1>
  <p class="lede">{e(g["summary"])}</p>
  <div class="entry-meta"><span>Claims read from the full papers</span><span>Updated {e(g["updated"])}</span></div>
</header>"""
        foot = ('<section class="article"><h2>Sources in this guide</h2><ul class="links">' + srcs + '</ul></section>'
                '<p class="foot">A field guide synthesizes the <a href="/research/">Research</a> entries it cites. Each claim id links to the entry it comes from.</p>')
        gd = d / g["slug"]
        gd.mkdir(exist_ok=True)
        (gd / "index.html").write_text(page(f'{g["title"]} · Field guide', head + f'\n<article class="article">{body}</article>\n' + foot, g["summary"], active="/research/guides/"))
        cards.append(f'<li><a class="row" href="/research/guides/{g["slug"]}/"><span class="date">{e(g["updated"])}</span>'
                     f'<span class="text"><span class="title">{e(g["title"])}</span><span class="one">{e(g["summary"])}</span></span></a></li>')
    idx = f"""<header class="masthead"><span class="label">nowucca.com · research</span><h1>Field guides</h1>
<p class="lede">What the research entries add up to, topic by topic: what to decide, what to do, where the evidence disagrees, and the numbers behind it.</p></header>
<ol class="rows">{"".join(cards)}</ol>"""
    (d / "index.html").write_text(page("Field guides · Research", idx, "Field guides built from the research entries on nowucca.com.", active="/research/guides/"))


def guides_block():
    if not GUIDES:
        return ""
    items = "".join(f'<li><a href="/research/guides/{g["slug"]}/">{e(g["title"])}</a></li>' for g in GUIDES)
    return (f'<a class="cta" href="/research/guides/"><span><span class="cta-title">Field guides</span>'
            f'<span class="label">{len(GUIDES)} guide{"s" if len(GUIDES) != 1 else ""} synthesized from the entries</span></span>'
            f'<span class="cta-go">Read the guides &rarr;</span></a>')


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
    nav = [("/research/", "Research"), ("/research/map/", "Knowledge map")]
    if GUIDES:
        nav.append(("/research/guides/", "Field guides"))
    nav.append(("/research/authors/", "Authors"))
    nav.append(("/library/", "Library"))
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


AUTHOR_LINKS = {}  # entry id -> html of credited author links, filled in main()


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
  {AUTHOR_LINKS.get(x["id"], "")}
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
    parts[0] += guides_block() + authors_block()
    toc = []
    for t in cfg["themes"]:
        n_t = sum(len(s["primary"]) for s in t["subtopics"])
        sub_links = "".join(
            f'<li><a href="#sub-{e(s["n"])}"><span class="n">{e(s["n"])}</span>{e(s["title"])}</a></li>'
            for s in t["subtopics"]
        )
        toc.append(
            f'<li style="--c:{t["color"]}"><a class="toc-theme" href="#theme-{e(t["n"])}"><span class="swatch"></span><span>{e(t["n"])}. {e(t["title"])} <span class="count">{n_t}</span></span></a>'
            f'<ol class="toc-subs">{sub_links}</ol></li>'
        )
    parts.append(
        '<nav class="toc" id="contents" aria-label="Contents"><h2 class="label">Contents</h2>'
        f'<ol class="toc-themes">{"".join(toc)}<li><a class="toc-theme" href="#all-entries"><span>All entries <span class="count">{len(entries)}</span></span></a></li></ol></nav>'
    )
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
                f'<div class="subtopic" id="sub-{e(s["n"])}"><h3><span class="n">{e(s["n"])}</span>{e(s["title"])}</h3>'
                + (f'<ol class="rows">{"".join(rows)}</ol>' if rows else "")
                + (f'<ul class="also">{also}</ul>' if also else "")
                + "</div>"
            )
        parts.append(
            f'<section class="theme" id="theme-{e(t["n"])}" style="--c:{t["color"]}"><header><h2><span class="swatch"></span>{e(t["n"])}. {e(t["title"])}</h2>'
            f'<p class="lede">{e(t["lede"])}</p></header>{"".join(subs)}<a class="to-top label" href="#contents">&uarr; Back to contents</a></section>'
        )
    reg = "".join(
        f'<tr><td>{e(x["id"])}</td><td><a href="/research/{x["slug"]}/">{e(x["title"])}</a></td>'
        f'<td class="hide-sm">{e(sub_of[x["id"]]["n"])} {e(sub_of[x["id"]]["title"])}</td><td class="hide-sm">{e(x["added"])}</td></tr>'
        for x in sorted(entries.values(), key=lambda v: v["id"], reverse=True)
    )
    parts.append(
        '<section class="theme" id="all-entries"><header><h2>All entries</h2></header><div class="table-scroll"><table class="registry">'
        '<thead><tr><th>ID</th><th>Title</th><th class="hide-sm">Filed under</th><th class="hide-sm">Added</th></tr></thead>'
        f"<tbody>{reg}</tbody></table></div></section>"
    )
    (OUT / "index.html").write_text(page("Research", "\n".join(parts), cfg["lede"], active="/research/"))


# ---------- authors ----------

AUTHORS = []


def guide_short(g):
    return re.sub(r"^Field guide:\s*", "", g["title"])


def guide_chips(a):
    if not a["guides"]:
        return ""
    return '<div class="tags">' + "".join(
        f'<a class="tag guide-tag" href="/research/guides/{e(g["slug"])}/">{e(guide_short(g))} · {a["guide_count"][g["slug"]]}</a>'
        for g in a["guides"]) + "</div>"


def specialty(a):
    if a["specialty"]:
        return e(a["specialty"])
    subs = [t for (n, t), _ in a["top_subs"]]
    return "Writes most about " + e(", ".join(subs[:-1]) + (" and " if len(subs) > 1 else "") + subs[-1]).lower() + "." if subs else ""


def fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


def authors_block():
    if not AUTHORS:
        return ""
    return (f'<a class="cta" href="/research/authors/"><span><span class="cta-title">Authors</span>'
            f'<span class="label">{len(AUTHORS)} people and organizations, ranked by reputation</span></span>'
            f'<span class="cta-go">See who writes what &rarr;</span></a>')


def scoring_note():
    q = authors_mod.QUALITY
    return (f'<section class="article" id="scoring"><h2>How reputation is scored</h2>'
            f'<p>Each public entry an author wrote or shared counts {fmt(q["base"])}. An entry that passed the research Reviewer on its first round adds {fmt(q["review_first_pass"])}; '
            f'one the Reviewer sent back for revision subtracts {fmt(-q["review_revise"])}. An entry cited by a published field guide adds {fmt(q["in_guide"])}. '
            f'Ties go to the author with more entries. Only published entries and field guides count.</p></section>')


def author_pages(entries, theme_of, sub_of, updated):
    if not AUTHORS:
        return
    d = OUT / "authors"
    d.mkdir(exist_ok=True)
    rows = []
    for a in AUTHORS:
        n = len(a["entries"])
        rows.append(
            f'<tr><td>{a["rank"]}</td><td><a href="/research/authors/{e(a["slug"])}/">{e(a["name"])}</a>'
            f'<span class="spec">{specialty(a)}</span>{guide_chips(a)}</td>'
            f'<td class="num">{n}</td><td class="num">{fmt(a["score"])}</td></tr>')
        ent = []
        for r in a["entries"]:
            x = entries[r["id"]]
            role = '<span class="weak-tag">shared</span>' if r["role"] == "shared" else ""
            ent.append(
                f'<li><a class="row" href="/research/{x["slug"]}/"><span class="date">{e(x["added"])}</span>'
                f'<span class="text"><span class="id">{e(r["id"])}</span>{role}<span class="title">{e(x["title"])}</span>'
                f'<span class="one">{e(x["summary"])}</span>{tags(x["tags"])}</span></a></li>')
        n_auth = sum(r["role"] == "author" for r in a["entries"])
        facts = [f'{n} entr{"y" if n == 1 else "ies"}' + (f' ({n_auth} as author, {n - n_auth} shared)' if 0 < n_auth < n else (" shared" if n_auth == 0 else ""))]
        facts.append(f'Reputation {fmt(a["score"])} · rank {a["rank"]} of {len(AUTHORS)}')
        if a["reviewed"]:
            facts.append(f'{a["first_pass"]} of {a["reviewed"]} reviewed entries passed on the first round')
        guides_html = (f'<section class="article"><h2>Field guides</h2><p>Entries by {e(a["name"])} are sources in these guides:</p>{guide_chips(a)}</section>'
                       if a["guides"] else "")
        head = f"""<header class="masthead">
  <span class="label">Author · {"organization" if a["kind"] == "org" else "person"}</span>
  <h1>{e(a["name"])}</h1>
  <p class="lede">{specialty(a)}</p>
  <div class="entry-meta">{"".join(f"<span>{e(f)}</span>" for f in facts)}</div>
  {tags(a["top_tags"])}
</header>"""
        body = (head + guides_html + f'<section class="article"><h2>Entries</h2></section><ol class="rows">{"".join(ent)}</ol>'
                + '<p class="foot">Credits come from each entry\'s byline. <a href="/research/authors/#scoring">How reputation is scored</a>.</p>')
        ad = d / a["slug"]
        ad.mkdir(exist_ok=True)
        (ad / "index.html").write_text(page(f'{a["name"]} · Authors · Research', body, f'{a["name"]}: {n} research entries on nowucca.com.', active="/research/authors/"))
    idx = f"""<header class="masthead">
  <span class="label">nowucca.com · research</span>
  <h1>Authors</h1>
  <p class="lede">Who wrote or shared the sources behind the Research entries, ranked by reputation: how many entries they account for, weighted by how well those entries held up.</p>
  <div class="meta label"><span>{len(AUTHORS)} authors</span><span>{len(entries)} entries</span><span>Updated <time datetime="{updated[0]}">{updated[1]}</time></span></div>
</header>
<div class="table-scroll"><table class="registry authors">
<thead><tr><th>#</th><th>Author, specialty and field guides</th><th class="num">Entries</th><th class="num">Reputation</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
{scoring_note()}"""
    (d / "index.html").write_text(page("Authors · Research", idx, "Authors behind the research entries on nowucca.com, ranked by reputation.", active="/research/authors/"))


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
    global AUTHORS
    AUTHORS, cred = authors_mod.build_authors(entries, GUIDES, theme_of, sub_of)
    by_slug = {a["slug"]: a for a in AUTHORS}
    for rid, m in cred.items():
        if m:
            links = ", ".join(f'<a href="/research/authors/{e(sl)}/">{e(by_slug[sl]["name"])}</a>' + (" (shared)" if role == "shared" else "")
                              for sl, role in sorted(m.items(), key=lambda kv: kv[1] == "shared") if sl in by_slug)
            AUTHOR_LINKS[rid] = f'<p class="credits"><span class="label">Authors</span> {links}</p>'
    uncredited = [rid for rid, m in cred.items() if not m]
    for x in entries.values():
        entry_page(cfg, entries, theme_of, sub_of, x)
    index_page(cfg, entries, theme_of, sub_of, updated)
    map_page(cfg, entries, theme_of, updated)
    guide_pages(entries, theme_of)
    author_pages(entries, theme_of, sub_of, updated)
    print(f"built {len(entries)} entries, index, map and {len(AUTHORS)} author pages (updated {updated[1]})")
    if uncredited:
        print(f"no author credited for {len(uncredited)} entries (paper author lists are not credited): {' '.join(sorted(uncredited))}")


if __name__ == "__main__":
    main()
