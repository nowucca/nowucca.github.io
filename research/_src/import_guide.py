#!/usr/bin/env python3
"""Turn a field guide's Claude Docs HTML export into a guide body for /research/guides/.

    python3 import_guide.py <export.html> <slug> [--rules rules.json]

Writes guides/<slug>.html. The guide must already be listed in guides.json (which happens only
after the site owner approves it). Stricter than import_doc.py, because a guide cites many entries:
  - claude.ai artifact links to public entries point at the entry page here; any other
    claude.ai link is unlinked
  - claim ids such as R147-f1 keep their text and link to the entry page
  - it FAILS (writes nothing) if the cleaned text mentions an entry that is not public, or a
    private term from --terms (a JSON list kept OUTSIDE this repo, like the rules file)
--rules uses the same file as import_doc.py, keyed by "guide:<slug>".
"""
import json, re, sys, argparse
from pathlib import Path
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("slug")
    ap.add_argument("--rules")
    ap.add_argument("--terms", required=True, help="JSON list of private terms, kept outside the repo")
    a = ap.parse_args()
    PRIVATE = re.compile(r"\b(" + "|".join(map(re.escape, json.loads(Path(a.terms).read_text()))) + r")\b", re.I)
    cfg = json.loads((HERE / "entries.json").read_text())
    guides = {g["slug"]: g for g in json.loads((HERE / "guides.json").read_text())["guides"]}
    if a.slug not in guides:
        sys.exit(f"{a.slug} is not in guides.json; add it only after it is approved")
    by_artifact = {e["artifact"].rsplit("/", 1)[-1]: e for e in cfg["entries"]}
    public = {e["id"] for e in cfg["entries"]}
    by_id = {e["id"]: e for e in cfg["entries"]}

    soup = BeautifulSoup(Path(a.export).read_text(), "html.parser")
    h1 = soup.find("h1")
    if h1:
        h1.decompose()
    for p in soup.find_all("p"):
        if p.find(attrs={"data-atom": "mention"}) or (p.find("time") and len(p.get_text(strip=True)) < 60):
            p.decompose()
            break
    for link in soup.find_all("a", href=True):
        m = re.match(r"https://claude\.ai/(?:code/)?artifact/([A-Za-z0-9_-]+)", link["href"])
        if not m:
            continue
        t = by_artifact.get(m.group(1))
        cid = re.match(r"\s*(R\d{3})-[fc]\d+\s*$", link.get_text())
        if cid and cid.group(1) in by_id:
            t = by_id[cid.group(1)]  # one doc can hold several entries; the claim id names the right one
        if t:
            link["href"] = f"/research/{t['slug']}/"
        else:
            link.unwrap()
    html = str(soup).strip()
    if a.rules:
        for old, new in json.loads(Path(a.rules).read_text()).get(f"guide:{a.slug}", []):
            if html.count(old) != 1:
                sys.exit(f"rule matched {html.count(old)} times: {old[:80]!r}")
            html = html.replace(old, new)
    text = BeautifulSoup(html, "html.parser").get_text(" ")
    bad = sorted({r for r in re.findall(r"\bR\d{3}\b", text) if r not in public})
    terms = sorted({m.group(0) for m in PRIVATE.finditer(text)})
    if bad or terms:
        sys.exit(f"not written: non-public entries {bad} private terms {terms}")
    out = HERE / "guides" / f"{a.slug}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html + "\n")
    print(f"wrote {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()
