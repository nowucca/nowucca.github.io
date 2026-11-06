#!/usr/bin/env python3
"""Turn a Claude Docs HTML export into an entry body for the Research section.

    python3 import_doc.py <export.html> <entry id> [--rules rules.json]

Writes entries/<slug>.html (slug from entries.json). Generic clean-up:
  - drops the doc's byline paragraph (date chip and @mention)
  - points claude.ai artifact links at the entry's page here when that entry is
    public, and unlinks them (keeping the words) when it is not
  - drops list items that are about an entry that is not public
  - turns <figure data-embed="node/<id>"> into a placeholder the build fills
    with diagrams/<id>.svg

--rules names a JSON file of exact replacements per entry id, kept OUTSIDE this
repo because the text it removes is what shouldn't be published:
  {"R005": [["old text", "new text"], ...]}
Each old text must occur exactly once in the cleaned HTML.
"""
import json, re, sys, argparse
from pathlib import Path
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("entry_id")
    ap.add_argument("--rules")
    a = ap.parse_args()

    cfg = json.loads((HERE / "entries.json").read_text())
    by_id = {e["id"]: e for e in cfg["entries"]}
    by_artifact = {e["artifact"].rsplit("/", 1)[-1]: e for e in cfg["entries"]}
    entry = by_id[a.entry_id]
    public = set(by_id)

    soup = BeautifulSoup(Path(a.export).read_text(), "html.parser")

    h1 = soup.find("h1")
    if h1:
        h1.decompose()  # the page template prints the title
    for p in soup.find_all("p"):
        if p.find(attrs={"data-atom": "mention"}) or (p.find("time") and len(p.get_text(strip=True)) < 60):
            p.decompose()
            break

    for link in soup.find_all("a", href=True):
        m = re.match(r"https://claude\.ai/(?:code/)?artifact/([A-Za-z0-9_-]+)", link["href"])
        if not m:
            continue
        target = by_artifact.get(m.group(1))
        if target:
            link["href"] = f"/research/{target['slug']}/"
        else:
            link.unwrap()

    def hidden_lead(text):
        m = re.match(r"\s*(R\d{3})\b", text)
        return bool(m and m.group(1) not in public)

    for li in soup.find_all("li"):
        if hidden_lead(li.get_text()):
            li.decompose()
    for ul in soup.find_all(["ul", "ol"]):
        if not ul.find("li"):
            ul.decompose()

    for fig in soup.find_all("figure", attrs={"data-embed": True}):
        node = fig["data-embed"].split("/", 1)[-1]
        cap = fig.find("figcaption")
        new = soup.new_tag("figure", attrs={"class": "diagram", "data-diagram": node})
        if cap:
            c = soup.new_tag("figcaption")
            c.string = cap.get_text()
            new.append(c)
        fig.replace_with(new)

    html = str(soup).strip()

    if a.rules:
        rules = json.loads(Path(a.rules).read_text()).get(a.entry_id, [])
        for old, new in rules:
            n = html.count(old)
            if n != 1:
                sys.exit(f"{a.entry_id}: rule matched {n} times: {old[:80]!r}")
            html = html.replace(old, new)

    leftovers = sorted({r for r in re.findall(r"\bR\d{3}\b", html) if r not in public})
    if leftovers:
        print(f"warning: {a.entry_id} still mentions non-public entries: {', '.join(leftovers)}", file=sys.stderr)

    out = HERE / entry["file"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html + "\n")
    print(f"wrote {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()
