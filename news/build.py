#!/usr/bin/env python3
"""Build the /news/ daily brief.

Inputs (all in this folder):
  topics.json              sections of the brief, in page order (add/remove topics here)
  editions/YYYY-MM-DD.json one file per day: {"date", "generated", "headline", "sections": {topic_id: [story, ...]}}
      story = {"headline", "summary", "source", "url", "date"?, "also"?: [{"name", "url"}]}

Outputs:
  news/YYYY-MM-DD/index.html  each edition
  news/index.html             archive, newest first
  news/latest/index.html      redirect to the newest edition
  _library.json + library/index.html  registers /news/ in the site hub (same markup as nowucca-publish)

Usage: python3 news/build.py   (from the repo root or anywhere; stdlib only)
"""
import datetime as dt
import html
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700'
         '&family=IBM+Plex+Mono:wght@500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">')
SECTION_TITLE = "Daily news brief"
SECTION_LEDE = "A neutral daily roundup — Austin, Texas, the US, Australia, AI, tech, world and a little sport — from well-sourced, low-bias outlets, with every story linked to its source."

e = lambda s: html.escape(str(s), quote=True)


def head(title, extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
{FONTS}
<link rel="stylesheet" href="/library/style.css">
<link rel="stylesheet" href="/news/style.css">
{extra}</head>
<body>
"""


def long_date(d):
    x = dt.date.fromisoformat(d)
    return f"{x:%A} {x.day} {x:%B %Y}"


def load():
    topics = json.loads((HERE / "topics.json").read_text())["topics"]
    eds = []
    for p in sorted((HERE / "editions").glob("*.json")):
        eds.append(json.loads(p.read_text()))
    eds.sort(key=lambda x: x["date"])
    return topics, eds


def story_html(s):
    also = ""
    if s.get("also"):
        also = " · also " + ", ".join(f'<a href="{e(a["url"])}" rel="noopener">{e(a["name"])}</a>' for a in s["also"])
    date = f' · {e(s["date"])}' if s.get("date") else ""
    return f"""<li class="story">
  <h3><a href="{e(s['url'])}" rel="noopener">{e(s['headline'])}</a></h3>
  <p>{e(s['summary'])}</p>
  <p class="src label">{e(s['source'])}{date}{also}</p>
</li>"""


def edition_page(ed, topics, prev_d, next_d):
    secs = ed["sections"]
    present = [t for t in topics if secs.get(t["id"])]
    # any section in the edition that is no longer in topics.json still renders, after the rest
    known = {t["id"] for t in topics}
    present += [{"id": k, "title": k.replace("-", " ").title()} for k in secs if k not in known and secs[k]]
    nav = "".join(f'<a href="#{e(t["id"])}">{e(t["title"])}</a>' for t in present)
    body = []
    for t in present:
        items = "\n".join(story_html(s) for s in secs[t["id"]])
        body.append(f'<section id="{e(t["id"])}" class="topic">\n<h2>{e(t["title"])}</h2>\n<ol class="stories">\n{items}\n</ol>\n</section>')
    n = sum(len(secs[t["id"]]) for t in present)
    pn = []
    pn.append(f'<a href="/news/{prev_d}/">&larr; {e(long_date(prev_d))}</a>' if prev_d else "<span></span>")
    pn.append(f'<a href="/news/{next_d}/">{e(long_date(next_d))} &rarr;</a>' if next_d else "<span></span>")
    gen = ed.get("generated", "")
    return head(f"News brief · {long_date(ed['date'])}") + f"""<main class="wrap">
<nav class="crumbs label"><a href="/news/">&larr; All briefs</a><a href="/library/">Library</a></nav>
<header class="masthead">
  <span class="label">nowucca.com · Daily news brief</span>
  <h1>{e(long_date(ed['date']))}</h1>
  {f'<p class="lede">{e(ed["headline"])}</p>' if ed.get("headline") else ""}
  <div class="meta label"><span>{n} stories</span><span>{len(present)} sections</span>{f"<span>Compiled {e(gen[11:16])} CT</span>" if gen else ""}</div>
</header>
<nav class="jump" aria-label="Sections">{nav}</nav>
{chr(10).join(body)}
<footer class="foot">
  <p><strong>How this is made.</strong> Stories are selected from wire services (AP, via PBS NewsHour syndication), public broadcasters (ABC Australia, KUT/NPR, Euronews) and nonprofit newsrooms (Texas Tribune), plus company primary sources for product announcements. Summaries are written fresh and kept to what the source reports; claims that are unconfirmed are labelled as reported or alleged. Compiled with Claude, an Anthropic model — follow the links for the full reporting.</p>
  <nav class="prevnext label">{pn[0]}{pn[1]}</nav>
</footer>
</main>
</body>
</html>
"""


def archive_page(eds):
    rows = []
    for ed in reversed(eds):
        n = sum(len(v) for v in ed["sections"].values())
        rows.append(f"""<li><a class="row" href="/news/{ed['date']}/">
  <span class="date">{ed['date']}</span>
  <span class="text"><span class="title">{e(long_date(ed['date']))}</span><span class="one">{e(ed.get('headline', ''))}</span><span class="label">{n} stories</span></span>
</a></li>""")
    latest = eds[-1]["date"] if eds else ""
    return head(SECTION_TITLE, '<link rel="alternate" href="/news/latest/">\n') + f"""<main class="wrap">
<a class="back" href="/library/">&larr; All pages</a>
<header class="masthead">
  <span class="label">nowucca.com · Daily news brief</span>
  <h1>{e(SECTION_TITLE)}</h1>
  <p class="lede">{e(SECTION_LEDE)}</p>
  <div class="meta label"><span>{len(eds)} editions</span><span>Updated {latest}</span>{f'<a href="/news/{latest}/">Read today&rsquo;s &rarr;</a>' if latest else ""}</div>
</header>
<ol class="rows">
{chr(10).join(rows)}
</ol>
</main>
</body>
</html>
"""


def redirect_page(d):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=/news/{d}/">
<link rel="canonical" href="/news/{d}/"><title>Latest news brief</title></head>
<body><p><a href="/news/{d}/">Latest brief: {d}</a></p></body></html>
"""


def rebuild_library(latest):
    mf = ROOT / "_library.json"
    lib = json.loads(mf.read_text())
    secs = lib["sections"]
    secs["news"] = {**secs.get("news", {}), "title": SECTION_TITLE, "lede": SECTION_LEDE,
                    "items": [], "external": True, "href": "/news/", "updated": latest}
    mf.write_text(json.dumps(lib, indent=2, ensure_ascii=False) + "\n")

    def upd(s):
        return s.get("updated") or max((i["date"] for i in s.get("items", [])), default="")

    order = sorted(secs.items(), key=lambda kv: upd(kv[1]), reverse=True)  # stable: ties keep manifest order
    rows = []
    for key, s in order:
        href = s.get("href") or f"/{key}/"
        if s.get("external"):
            label = href
        else:
            n = len(s.get("items", []))
            label = f"{n} page{'s' if n != 1 else ''} · /{key}/"
        rows.append(f"""<li><a class="row" href="{e(href)}">
  <span class="date">{upd(s)}</span>
  <span class="text"><span class="title">{e(s['title'])}</span><span class="one">{e(s.get('lede', ''))}</span><span class="label">{e(label)}</span></span>
</a></li>""")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(lib['title'])}</title>
{FONTS}
<link rel="stylesheet" href="/library/style.css">
</head>
<body>
<main class="wrap">
<a class="back" href="/">&larr; nowucca.com</a>
<header class="masthead">
  <span class="label">nowucca.com</span>
  <h1>{e(lib['title'])}</h1>
  <p class="lede">{e(lib['lede'])}</p>
</header>
<ol class="rows">
{chr(10).join(rows)}
</ol>
</main>
</body>
</html>
"""
    (ROOT / "library" / "index.html").write_text(page)


def update_home_card(ed):
    """Refresh the 'Daily news brief' card text in the home page front matter with today's headline."""
    home = ROOT / "index.html"
    lines = home.read_text().split("\n")
    in_card = False
    for i, line in enumerate(lines):
        if line.startswith("  - title:"):
            in_card = line.strip() == "- title: Daily news brief"
        elif in_card and line.startswith("    text:"):
            text = f"Today: {ed['headline']}" if ed.get("headline") else f"Latest brief: {long_date(ed['date'])}"
            lines[i] = "    text: " + json.dumps(text, ensure_ascii=False)
            home.write_text("\n".join(lines))
            return


def main():
    topics, eds = load()
    for i, ed in enumerate(eds):
        prev_d = eds[i - 1]["date"] if i > 0 else None
        next_d = eds[i + 1]["date"] if i + 1 < len(eds) else None
        out = HERE / ed["date"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(edition_page(ed, topics, prev_d, next_d))
    (HERE / "index.html").write_text(archive_page(eds))
    if eds:
        (HERE / "latest").mkdir(exist_ok=True)
        (HERE / "latest" / "index.html").write_text(redirect_page(eds[-1]["date"]))
        rebuild_library(eds[-1]["date"])
        update_home_card(eds[-1])
    print(f"built {len(eds)} edition(s); latest {eds[-1]['date'] if eds else '-'}")


if __name__ == "__main__":
    main()
