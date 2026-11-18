#!/usr/bin/env python3
"""Build /speeches/: a weekly short motivational speech (about two minutes read aloud).

Inputs (all in this folder):
  themes.json               standards, plus a queue of themes to draw from (Steven adds to it)
  editions/YYYY-MM-DD.json  one file per speech:
      {"date", "title", "theme", "dek", "paragraphs": [str, ...], "takeaway", "generated"?}

Outputs:
  speeches/YYYY-MM-DD/index.html   each speech
  speeches/index.html              archive, newest first
  speeches/latest/index.html       redirect to the newest speech
  _library.json + library/index.html  registers /speeches/ in the site hub

Usage: python3 speeches/build.py   (stdlib only; run from anywhere)
"""
import datetime as dt
import html
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700'
         '&family=IBM+Plex+Mono:wght@500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">')
SECTION_TITLE = "Weekly pep talk"
SECTION_LEDE = "A short motivational speech each week, about two minutes read aloud, with one thing to do this week."

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
<link rel="stylesheet" href="/speeches/style.css">
{extra}</head>
<body>
"""


def long_date(d):
    x = dt.date.fromisoformat(d)
    return f"{x:%A} {x.day} {x:%B %Y}"


def words(sp):
    return sum(len(p.split()) for p in sp["paragraphs"]) + len(sp.get("takeaway", "").split())


def minutes(sp):
    return max(1, round(words(sp) / 150))


def load():
    eds = [json.loads(p.read_text()) for p in sorted((HERE / "editions").glob("*.json"))]
    eds.sort(key=lambda x: x["date"])
    return eds


def speech_page(sp, prev_sp, next_sp):
    paras = "\n".join(f"<p>{e(p)}</p>" for p in sp["paragraphs"])
    pn = [
        f'<a href="/speeches/{prev_sp["date"]}/">&larr; {e(prev_sp["title"])}</a>' if prev_sp else "<span></span>",
        f'<a href="/speeches/{next_sp["date"]}/">{e(next_sp["title"])} &rarr;</a>' if next_sp else "<span></span>",
    ]
    return head(f"{sp['title']} · Weekly pep talk") + f"""<main class="wrap">
<nav class="crumbs label"><a href="/speeches/">&larr; All speeches</a><a href="/library/">Library</a></nav>
<header class="masthead">
  <span class="label">nowucca.com · Weekly pep talk</span>
  <h1>{e(sp['title'])}</h1>
  {f'<p class="lede">{e(sp["dek"])}</p>' if sp.get("dek") else ""}
  <div class="meta label"><span>{e(long_date(sp['date']))}</span><span>{minutes(sp)} min read aloud</span><span>{e(sp.get('theme', ''))}</span></div>
</header>
<article class="speech">
{paras}
</article>
{f'<aside class="takeaway"><span class="label">This week</span><p>{e(sp["takeaway"])}</p></aside>' if sp.get("takeaway") else ""}
<footer class="foot">
  <p>Written with Claude, an Anthropic model, as an original piece. It's general encouragement, not professional advice.</p>
  <nav class="prevnext label">{pn[0]}{pn[1]}</nav>
</footer>
</main>
</body>
</html>
"""


def archive_page(eds):
    rows = []
    for sp in reversed(eds):
        rows.append(f"""<li><a class="row" href="/speeches/{sp['date']}/">
  <span class="date">{sp['date']}</span>
  <span class="text"><span class="title">{e(sp['title'])}</span><span class="one">{e(sp.get('dek', ''))}</span><span class="label">{e(sp.get('theme', ''))} · {minutes(sp)} min</span></span>
</a></li>""")
    latest = eds[-1]["date"] if eds else ""
    return head(SECTION_TITLE) + f"""<main class="wrap">
<a class="back" href="/library/">&larr; All pages</a>
<header class="masthead">
  <span class="label">nowucca.com · Weekly pep talk</span>
  <h1>{e(SECTION_TITLE)}</h1>
  <p class="lede">{e(SECTION_LEDE)}</p>
  <div class="meta label"><span>{len(eds)} speech{'es' if len(eds) != 1 else ''}</span><span>Updated {latest}</span>{f'<a href="/speeches/{latest}/">Read the latest &rarr;</a>' if latest else ""}</div>
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
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=/speeches/{d}/">
<link rel="canonical" href="/speeches/{d}/"><title>Latest pep talk</title></head>
<body><p><a href="/speeches/{d}/">Latest speech: {d}</a></p></body></html>
"""


def rebuild_library(latest):
    """Register /speeches/ in _library.json and regenerate library/index.html (same markup as news/build.py)."""
    mf = ROOT / "_library.json"
    lib = json.loads(mf.read_text())
    secs = lib["sections"]
    secs["speeches"] = {**secs.get("speeches", {}), "title": SECTION_TITLE, "lede": SECTION_LEDE,
                        "items": [], "external": True, "href": "/speeches/", "updated": latest}
    mf.write_text(json.dumps(lib, indent=2, ensure_ascii=False) + "\n")

    def upd(s):
        return s.get("updated") or max((i["date"] for i in s.get("items", [])), default="")

    order = sorted(secs.items(), key=lambda kv: upd(kv[1]), reverse=True)
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


def main():
    eds = load()
    for i, sp in enumerate(eds):
        out = HERE / sp["date"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(speech_page(sp, eds[i - 1] if i > 0 else None, eds[i + 1] if i + 1 < len(eds) else None))
        print(f"{sp['date']}: {words(sp)} words, ~{minutes(sp)} min")
    (HERE / "index.html").write_text(archive_page(eds))
    if eds:
        (HERE / "latest").mkdir(exist_ok=True)
        (HERE / "latest" / "index.html").write_text(redirect_page(eds[-1]["date"]))
        rebuild_library(eds[-1]["date"])
    print(f"built {len(eds)} speech(es); latest {eds[-1]['date'] if eds else '-'}")


if __name__ == "__main__":
    main()
