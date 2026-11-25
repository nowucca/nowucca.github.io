"""How each entry was found: the LinkedIn post or newsletter issue that led to it.

The research index (INDEX.md, in the project folder) lists every source of an entry
in its Registry "Sources" column: the original article plus the posts and newsletter
issues that pointed to it. This module copies the public parts of that column into
_src/via.json when the project folder is mounted, so builds elsewhere still work.
"""
import json, re
from pathlib import Path

SRC = Path(__file__).resolve().parent
PROJECT = Path("/mnt/project-files/research")  # present in the publish job; absent elsewhere

# Labels that name a discovery channel rather than the original work.
CHANNEL = re.compile(
    r"^(LinkedIn,|LinkedIn post|TLDR \w+|The Download|How I AI|Lenny|ByteByteGo|JVM Weekly|Tales from the jar side"
    r"|[\w' ]*[Nn]ewsletter)", re.I)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BLOCKED = re.compile(r"claude\.ai/|google\.com/url|mail\.google\.com|/mnt/|file:", re.I)


def parse_sources(cell):
    """[(label, url or '')] for one Sources cell; plain-text items get url ''."""
    out = [(l.strip(), u.strip()) for l, u in LINK.findall(cell) if not BLOCKED.search(u)]
    rest = LINK.sub("", cell)
    for part in re.split(r";\s*", rest):
        part = part.strip(" ;,")
        if part and CHANNEL.match(part):
            out.append((part, ""))
    return out


def refresh_via_snapshot(public_ids):
    out = SRC / "via.json"
    idx = PROJECT / "INDEX.md"
    if not idx.exists():
        return json.loads(out.read_text()) if out.exists() else {}
    snap = {}
    for rid, cell in re.findall(r"^\| (R\d+) \| [^|]* \| [^|]* \| ([^|]*) \|", idx.read_text(), re.M):
        if rid in public_ids:
            snap[rid] = [{"label": l, "url": u} for l, u in parse_sources(cell)]
    out.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
    return snap


def original_url(source):
    """entries.json `source` is normally a URL; some rows hold the Markdown cell instead."""
    if source.startswith("http"):
        return source
    links = [(l, u) for l, u in LINK.findall(source) if not BLOCKED.search(u)]
    for l, u in links:
        if not CHANNEL.match(l):
            return u
    return links[0][1] if links else source


def channels(rid, source, snap):
    """Discovery channels for one entry, minus the original itself."""
    orig = original_url(source)
    return [v for v in snap.get(rid, []) if CHANNEL.match(v["label"]) and v["url"] != orig]
