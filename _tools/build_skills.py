#!/usr/bin/env python3
"""Build the /skills/ section of nowucca.com from local skill folders.

Each skill is a folder with a SKILL.md (Agent Skills format), so the same
folder works in Claude Code (~/.claude/skills), Codex ($HOME/.agents/skills)
and pi (~/.pi/agent/skills or ~/.agents/skills).

For every skill this writes:
  skills/<name>/index.html   the page: description, install steps, files, source
  skills/<name>/<name>.zip   the skill folder, ready to unzip into a skills dir
and then skills/index.html (the catalog) and skills/skills.json (machine-readable).

Before writing anything it checks each skill and refuses to publish on errors:
frontmatter (name/description rules shared by Claude, Codex and pi), every
relative scripts/ references/ assets/ path mentioned in a text file must exist,
and nothing that looks like a secret.

Usage (stdlib only):
  python3 _tools/build_skills.py --src ~/Work/skills --src ~/skills-playground \
      --only nowucca-publish,company-research [--date 2026-11-09] [--check]

Skills already published but not named this run are kept (their entry in
skills/skills.json is reused), so you can rebuild one skill at a time.
Register the section on /library/ with nowucca-publish's `publish.py link`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import zipfile
from pathlib import Path

SITE = "https://nowucca.com"
SKIP_NAMES = {".DS_Store", "__pycache__", ".git", "node_modules", ".venv", "venv",
              ".pytest_cache", ".mypy_cache", ".ruff_cache", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".js", ".mjs", ".ts", ".json", ".yaml",
                 ".yml", ".toml", ".css", ".html", ".csv", ".tsv", ".xml", ".svg", ""}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Relative paths into the skill's own folders, as written in SKILL.md and friends.
REF_RE = re.compile(r"(?<![\w./~-])((?:scripts|references|assets|agents|templates|examples)/[\w.\-/]*[\w\-])")
SECRET_RES = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[abpr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


# ---------------------------------------------------------------- reading

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Minimal YAML frontmatter reader: top-level `key: value` lines only."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    meta: dict = {}
    key = None
    for line in text[3:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            key, val = m.group(1), m.group(2).strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
                q = val[0]
                val = val[1:-1]
                val = val.replace("''", "'") if q == "'" else val.replace('\\"', '"')
            meta[key] = val
        elif key and isinstance(meta.get(key), str) and line.startswith((" ", "\t")):
            # folded continuation of a plain scalar, or nested map (kept as text)
            meta[key] = (meta[key] + " " + line.strip()).strip()
    body = text[end + 4:].lstrip("\n")
    return meta, body


def skill_files(root: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_NAMES)
        for f in sorted(filenames):
            p = Path(dirpath) / f
            if f in SKIP_NAMES or p.suffix in SKIP_SUFFIXES or p.is_symlink() and not p.exists():
                continue
            out.append(p)
    return out


def is_text(p: Path) -> bool:
    if p.suffix.lower() not in TEXT_SUFFIXES:
        return False
    try:
        p.read_text(encoding="utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def find_skills(srcs: list[Path]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for src in srcs:
        src = src.expanduser()
        candidates = [src] if (src / "SKILL.md").is_file() else sorted(
            p.parent for p in src.glob("*/SKILL.md"))
        for d in candidates:
            found.setdefault(d.name, d)
    return found


# ---------------------------------------------------------------- checks

def check_skill(d: Path) -> tuple[dict, list[str], list[str]]:
    errors, warnings = [], []
    text = (d / "SKILL.md").read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(text)
    name, desc = meta.get("name", ""), meta.get("description", "")
    if not name:
        errors.append("SKILL.md frontmatter has no name (Codex requires it)")
    elif not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"name {name!r} must be lowercase letters, digits and single hyphens, at most 64 chars")
    elif name != d.name:
        errors.append(f"name {name!r} differs from folder {d.name!r} (Claude and some harnesses require a match)")
    if not desc:
        errors.append("SKILL.md frontmatter has no description (pi will not load it)")
    elif len(desc) > 1024:
        errors.append(f"description is {len(desc)} chars; pi and Claude cap it at 1024")
    if "<" in desc or ">" in desc:
        warnings.append("description contains angle brackets, which claude.ai rejects")

    files = skill_files(d)
    rels = {p.relative_to(d).as_posix() for p in files}
    reldirs = {str(Path(r).parent.as_posix()) for r in rels} | {
        "/".join(r.split("/")[:i]) for r in rels for i in range(1, r.count("/") + 1)}
    for p in files:
        rel = p.relative_to(d).as_posix()
        if p.stat().st_size > 15 * 1024 * 1024:
            errors.append(f"{rel} is over 15MB")
        if not is_text(p):
            continue
        t = p.read_text(encoding="utf-8")
        for rx in SECRET_RES:
            if rx.search(t):
                errors.append(f"{rel} looks like it contains a secret ({rx.pattern[:16]}...)")
        if p.suffix.lower() in {".md", ".txt", ""} or p.name == "SKILL.md":
            for m in REF_RE.finditer(t):
                ref = m.group(1).rstrip(".")
                # resolve relative to the skill root, and to the file's own folder
                local = (p.parent.relative_to(d) / ref).as_posix() if p.parent != d else ref
                if ref in rels or ref in reldirs or local in rels or local in reldirs:
                    continue
                if any(ch in ref for ch in "*{<"):
                    continue
                errors.append(f"{rel} mentions {ref}, which is not in the skill folder")
        for m in re.finditer(r"(~/(?:Work|Documents|Desktop|Downloads|skills-playground)[\w./-]*|/Users/[\w./-]+)", t):
            warnings.append(f"{rel} uses a machine-specific path {m.group(1)}; other people won't have it")
    return ({"name": name or d.name, "description": desc, "meta": meta},
            list(dict.fromkeys(errors)), sorted(set(warnings)))


# ---------------------------------------------------------------- writing

def esc(s: str) -> str:
    return html.escape(s, quote=True)


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def requirements(files: list[Path], d: Path) -> list[str]:
    req = set()
    for p in files:
        s = p.suffix.lower()
        if s == ".py":
            req.add("python3")
        elif s in {".js", ".mjs", ".ts"}:
            req.add("node")
        elif s == ".sh":
            req.add("bash")
    return sorted(req)


def write_zip(d: Path, name: str, files: list[Path], out: Path) -> str:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = p.relative_to(d).as_posix()
            info = zipfile.ZipInfo(f"{name}/{rel}", date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = ((0o755 if os.access(p, os.X_OK) else 0o644) | 0o100000) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    return hashlib.sha256(out.read_bytes()).hexdigest()


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=IBM+Plex+Mono:wght@500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<link rel="stylesheet" href="/library/style.css">
<link rel="stylesheet" href="/skills/style.css">
</head>
<body>
<main class="wrap">
"""
TAIL = "</main>\n{scripts}</body>\n</html>\n"
def install_snippet(name: str) -> str:
    url = f"{SITE}/skills/{name}/{name}.zip"
    return (f"curl -fsSL {url} -o /tmp/{name}.zip\n"
            f"mkdir -p ~/.agents/skills ~/.claude/skills\n"
            f"unzip -oq /tmp/{name}.zip -d ~/.agents/skills\n"
            f"ln -sfn ~/.agents/skills/{name} ~/.claude/skills/{name}")


VENDOR = ('<script src="/skills/vendor/highlight-11.9.0.min.js"></script>\n'
          '<script src="/skills/vendor/marked-12.0.2.min.js"></script>\n'
          '<script src="/skills/explorer.js"></script>\n')
LANG = {".py": "python", ".sh": "bash", ".bash": "bash", ".zsh": "bash", ".js": "javascript",
        ".mjs": "javascript", ".ts": "typescript", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        ".toml": "ini", ".css": "css", ".html": "xml", ".xml": "xml", ".svg": "xml", ".md": "markdown",
        ".csv": "plaintext", ".tsv": "plaintext", ".txt": "plaintext", "": "plaintext"}
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
               ".webp": "image/webp"}


def file_records(d: Path, files: list[Path]) -> list[dict]:
    import base64
    recs = []
    for p in files:
        rel = p.relative_to(d).as_posix()
        size = p.stat().st_size
        rec = {"path": rel, "size": human_size(size)}
        if is_text(p):
            rec["lang"] = LANG.get(p.suffix.lower(), "plaintext")
            rec["text"] = p.read_text(encoding="utf-8")
        elif p.suffix.lower() in IMAGE_TYPES and size < 512 * 1024:
            rec["image"] = f"data:{IMAGE_TYPES[p.suffix.lower()]};base64," + base64.b64encode(p.read_bytes()).decode()
        recs.append(rec)
    # SKILL.md first, then folders after root files, alphabetical
    recs.sort(key=lambda r: (r["path"] != "SKILL.md", "/" in r["path"], r["path"].lower()))
    return recs


def skill_page(entry: dict, d: Path, files: list[Path]) -> str:
    name = entry["name"]
    out = [HEAD.format(title=esc(name), desc=esc(entry["description"][:300])).replace(
        '<main class="wrap">', '<main class="wrap wide">')]
    out.append('<nav class="crumbs"><a class="back" href="/skills/">&larr; Skills</a>'
               '<a class="back" href="/library/">Library</a></nav>\n')
    out.append('<header class="masthead">\n  <span class="label">Agent skill · Claude · Codex · pi</span>\n'
               f'  <h1>{esc(name)}</h1>\n  <p class="lede">{esc(entry["description"])}</p>\n'
               f'  <p class="meta label"><span>Updated {esc(entry["date"])}</span>'
               f'<span>{len(files)} files</span><span>{esc(entry["zip_size"])} zip</span>'
               + (f'<span>Needs {esc(", ".join(entry["requires"]))}</span>' if entry["requires"] else "")
               + '</p>\n</header>\n')
    if entry.get("note"):
        out.append(f'<p class="note">{esc(entry["note"])}</p>\n')

    recs = file_records(d, files)
    data = json.dumps({"name": name, "files": recs}, ensure_ascii=False).replace("</", "<\\/")
    out.append('<section class="block">\n<h2>Files</h2>\n'
               f'<div class="explorer" data-skill="{esc(name)}">\n'
               '  <nav class="tree" aria-label="Files"><ul>\n')
    # no-JS fallback: plain list of anchors; explorer.js replaces this tree
    for r in recs:
        out.append(f'    <li><a href="#file={esc(r["path"])}">{esc(r["path"])}</a></li>\n')
    out.append('  </ul></nav>\n'
               '  <div class="pane">\n'
               '    <div class="pane-bar"><span class="path label"></span>'
               '<span class="pane-tools"><button type="button" class="mode" hidden>Rendered</button>'
               '<button type="button" class="copy">Copy</button></span></div>\n'
               '    <div class="pane-body"><noscript><p>Turn on JavaScript to browse the files, or download the zip.</p></noscript></div>\n'
               '  </div>\n</div>\n'
               f'<script type="application/json" id="skill-files">{data}</script>\n</section>\n')

    snippet = install_snippet(name)
    out.append('<section class="block">\n<h2>Install</h2>\n'
               f'<p><a class="button" href="/skills/{esc(name)}/{esc(name)}.zip" download>Download {esc(name)}.zip</a></p>\n'
               '<p>The zip holds one folder, <code>' + esc(name) + '/</code>. These four lines install it for all three '
               'harnesses at once: Codex and pi read <code>~/.agents/skills</code>, and Claude Code gets a link '
               'in <code>~/.claude/skills</code>.</p>\n'
               f'<div class="code"><button class="copy" type="button" data-for="install-{esc(name)}">Copy</button>'
               f'<pre id="install-{esc(name)}"><code class="language-bash">{esc(snippet)}</code></pre></div>\n'
               '<table class="where"><thead><tr><th>Harness</th><th>Personal</th><th>Per project</th></tr></thead><tbody>\n'
               '<tr><td>Claude Code</td><td><code>~/.claude/skills/</code></td><td><code>.claude/skills/</code></td></tr>\n'
               '<tr><td>Codex</td><td><code>~/.agents/skills/</code></td><td><code>.agents/skills/</code></td></tr>\n'
               '<tr><td>pi</td><td><code>~/.pi/agent/skills/</code> or <code>~/.agents/skills/</code></td><td><code>.pi/skills/</code> or <code>.agents/skills/</code></td></tr>\n'
               '<tr><td>claude.ai</td><td colspan="2">Settings &rarr; Capabilities &rarr; Skills, then upload the zip</td></tr>\n'
               '</tbody></table>\n'
               f'<p class="label hash">sha256 {esc(entry["sha256"])}</p>\n</section>\n')
    out.append(TAIL.format(scripts=VENDOR))
    return "".join(out)


EXPLORER_JS = r"""/* /skills/ file explorer: tree on the left, highlighted preview on the right. */
(function () {
  var root = document.querySelector(".explorer");
  var dataEl = document.getElementById("skill-files");
  wireCopyButtons();
  if (!root || !dataEl) return;
  var data = JSON.parse(dataEl.textContent);
  var files = data.files;
  var byPath = {};
  files.forEach(function (f) { byPath[f.path] = f; });
  var treeEl = root.querySelector(".tree");
  var body = root.querySelector(".pane-body");
  var pathEl = root.querySelector(".pane-bar .path");
  var modeBtn = root.querySelector(".pane-bar .mode");
  var copyBtn = root.querySelector(".pane-bar .copy");
  var current = null, rendered = false;

  // Build a nested tree from the flat path list.
  var tree = { dirs: {}, files: [] };
  files.forEach(function (f) {
    var parts = f.path.split("/"), node = tree;
    for (var i = 0; i < parts.length - 1; i++) {
      node = node.dirs[parts[i]] = node.dirs[parts[i]] || { dirs: {}, files: [] };
    }
    node.files.push(f);
  });
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function renderNode(node, prefix) {
    var ul = el("ul");
    node.files.forEach(function (f) {
      var li = el("li"), b = el("button", "file", f.path.split("/").pop());
      b.type = "button"; b.dataset.path = f.path;
      b.addEventListener("click", function () { show(f.path, true); });
      li.appendChild(b); ul.appendChild(li);
    });
    Object.keys(node.dirs).sort().forEach(function (name) {
      var li = el("li", "dir"), b = el("button", "folder", name + "/");
      b.type = "button"; b.setAttribute("aria-expanded", "true");
      var child = renderNode(node.dirs[name], prefix + name + "/");
      b.addEventListener("click", function () {
        var open = b.getAttribute("aria-expanded") === "true";
        b.setAttribute("aria-expanded", String(!open));
        child.hidden = open;
      });
      li.appendChild(b); li.appendChild(child); ul.appendChild(li);
    });
    return ul;
  }
  treeEl.innerHTML = "";
  treeEl.appendChild(renderNode(tree, ""));

  function show(path, push) {
    var f = byPath[path];
    if (!f) return;
    current = f;
    treeEl.querySelectorAll("button.file").forEach(function (b) {
      b.setAttribute("aria-current", b.dataset.path === path ? "true" : "false");
    });
    pathEl.textContent = f.path + "  ·  " + f.size;
    modeBtn.hidden = f.lang !== "markdown" || !window.marked;
    copyBtn.hidden = f.text == null;
    draw();
    if (push) history.replaceState(null, "", "#file=" + encodeURIComponent(path));
  }
  function stripFrontmatter(t) {
    var m = /^---\n[\s\S]*?\n---\n?/.exec(t);
    return m ? t.slice(m[0].length) : t;
  }
  function draw() {
    var f = current;
    body.innerHTML = "";
    if (f.text != null && rendered && f.lang === "markdown" && window.marked) {
      var art = el("article", "prose");
      art.innerHTML = window.marked.parse(stripFrontmatter(f.text));
      art.querySelectorAll("pre code").forEach(function (c) { if (window.hljs) hljs.highlightElement(c); });
      body.appendChild(art);
      modeBtn.textContent = "Source";
    } else if (f.text != null) {
      var wrap = f.lang === "markdown" || f.lang === "plaintext";
      var pre = el("pre", wrap ? "src wrap" : "src"), code = el("code");
      if (window.hljs && f.lang !== "plaintext" && hljs.getLanguage(f.lang)) {
        var fm = f.lang === "markdown" ? /^---\n[\s\S]*?\n---\n?/.exec(f.text) : null;
        if (fm) {
          var inner = fm[0].replace(/^---\n/, "").replace(/\n---\n?$/, "");
          code.innerHTML = '<span class="hljs-meta">---</span>\n' +
            hljs.highlight(inner, { language: "yaml", ignoreIllegals: true }).value +
            '\n<span class="hljs-meta">---</span>\n' +
            hljs.highlight(f.text.slice(fm[0].length), { language: "markdown", ignoreIllegals: true }).value;
        } else {
          code.innerHTML = hljs.highlight(f.text, { language: f.lang, ignoreIllegals: true }).value;
        }
      } else {
        code.textContent = f.text;
      }
      var lines = f.text.replace(/\n$/, "").split("\n").length, gutter = el("span", "gutter");
      gutter.setAttribute("aria-hidden", "true");
      gutter.textContent = Array.from({ length: lines }, function (_, i) { return i + 1; }).join("\n");
      if (!wrap) pre.appendChild(gutter);
      pre.appendChild(code);
      body.appendChild(pre);
      modeBtn.textContent = "Rendered";
    } else if (f.image) {
      var img = el("img"); img.src = f.image; img.alt = f.path;
      body.appendChild(img);
    } else {
      body.appendChild(el("p", "binary", "Binary file (" + f.size + "). It's in the zip."));
    }
  }
  modeBtn.addEventListener("click", function () { rendered = !rendered; draw(); });
  copyBtn.addEventListener("click", function () {
    if (!current || current.text == null) return;
    copy(current.text, copyBtn);
  });
  var fromHash = /^#file=(.+)$/.exec(location.hash);
  show(fromHash && byPath[decodeURIComponent(fromHash[1])] ? decodeURIComponent(fromHash[1]) : files[0].path, false);

  function copy(text, btn) {
    navigator.clipboard.writeText(text).then(function () {
      btn.textContent = "Copied";
      setTimeout(function () { btn.textContent = "Copy"; }, 1500);
    });
  }
  function wireCopyButtons() {
    document.querySelectorAll("button.copy[data-for]").forEach(function (b) {
      b.addEventListener("click", function () {
        navigator.clipboard.writeText(document.getElementById(b.dataset.for).textContent).then(function () {
          b.textContent = "Copied";
          setTimeout(function () { b.textContent = "Copy"; }, 1500);
        });
      });
    });
    if (window.hljs) document.querySelectorAll(".code pre code[class*=language-]").forEach(function (c) { hljs.highlightElement(c); });
  }
})();
"""


def index_page(entries: list[dict], title: str, lede: str) -> str:
    out = [HEAD.format(title=esc(title), desc=esc(lede))]
    out.append('<a class="back" href="/library/">&larr; Library</a>\n')
    out.append(f'<header class="masthead">\n  <span class="label">nowucca.com</span>\n  <h1>{esc(title)}</h1>\n'
               f'  <p class="lede">{esc(lede)}</p>\n'
               '  <p class="meta label"><span>Works in Claude Code, Codex and pi</span>'
               '<span><a href="/skills/skills.json">skills.json</a></span></p>\n</header>\n')
    out.append('<ol class="rows">\n')
    for e in sorted(entries, key=lambda e: (e["date"], e["name"]), reverse=True):
        out.append(f'<li><a class="row" href="/skills/{esc(e["name"])}/">\n'
                   f'  <span class="date">{esc(e["date"])}</span>\n'
                   f'  <span class="text"><span class="title">{esc(e["name"])}</span>'
                   f'<span class="one">{esc(e["description"])}</span>'
                   f'<span class="label">{e["files"]} files · {esc(e["zip_size"])}'
                   + (f' · needs {esc(", ".join(e["requires"]))}' if e["requires"] else "")
                   + '</span></span>\n</a></li>\n')
    out.append('</ol>\n')
    out.append('<section class="block">\n<h2>Installing</h2>\n<p>Every skill here is a folder with a '
               '<code>SKILL.md</code> in the open Agent Skills format. Each page has a zip and a one-step install '
               'that sets it up for Claude Code, Codex and pi together.</p>\n</section>\n')
    out.append(TAIL.format(scripts=""))
    return "".join(out)


STYLE = """/* /skills/ pages, on top of /library/style.css. Built by _tools/build_skills.py. */
.crumbs { display: flex; gap: 1.25rem; }
.block { display: flex; flex-direction: column; gap: 0.9rem; min-width: 0; }
.note { border-left: 3px solid var(--accent); padding: 0.5rem 0 0.5rem 1rem; color: var(--muted); }
code { font: 500 0.88em/1.5 var(--mono); }
p code, td code, li code { background: var(--accent-soft); padding: 0.05rem 0.3rem; border-radius: 3px; overflow-wrap: anywhere; }
pre { margin: 0; overflow-x: auto; padding: 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: 6px; font-size: 0.85rem; line-height: 1.55; }
pre code { font-size: inherit; background: none; padding: 0; }
.code { position: relative; }
.code pre { padding-right: 5rem; }
button.copy { position: absolute; top: 0.5rem; right: 0.5rem; font: 500 0.75rem/1 var(--mono); padding: 0.45rem 0.65rem; border-radius: 4px; border: 1px solid var(--line); background: var(--bg); color: var(--fg); cursor: pointer; }
button.copy:hover { border-color: var(--accent); color: var(--accent); }
.button { display: inline-block; font: 600 1rem/1 var(--display); padding: 0.8rem 1.1rem; border-radius: 6px; background: var(--accent); color: var(--bg); text-decoration: none; }
.button:hover { filter: brightness(1.08); }
table.where { border-collapse: collapse; width: 100%; font-size: 0.92rem; table-layout: fixed; }
.where td { overflow-wrap: anywhere; }
.hash { overflow-wrap: anywhere; text-transform: none; }
.where th, .where td { text-align: left; padding: 0.5rem 0.6rem 0.5rem 0; border-bottom: 1px solid var(--line); vertical-align: top; }
.where th { font: 500 0.75rem/1.4 var(--mono); text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }
.tree { list-style: none; margin: 0; padding: 0; font: 500 0.88rem/1.9 var(--mono); }
.tree li { padding-left: calc(var(--depth, 0) * 1.25rem); overflow-wrap: anywhere; }
details { border: 1px solid var(--line); border-radius: 6px; background: var(--surface); }
details > summary { cursor: pointer; padding: 0.7rem 1rem; }
details[open] > summary { border-bottom: 1px solid var(--line); }
details pre { border: 0; border-radius: 0 0 6px 6px; }
.prose { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 1.25rem 1.25rem 1.5rem; min-width: 0; overflow-wrap: anywhere; }
.prose > * + * { margin-top: 0.9rem; }
.prose h1, .prose h2, .prose h3 { margin-top: 1.6rem; text-transform: none; letter-spacing: -0.01em; color: var(--fg); }
.prose h1 { font-size: 1.6rem; } .prose h2 { font-size: 1.3rem; } .prose h3 { font-size: 1.1rem; }
.prose ul, .prose ol { padding-left: 1.4rem; margin-bottom: 0; }
.prose table { border-collapse: collapse; display: block; overflow-x: auto; font-size: 0.9rem; }
.prose th, .prose td { border: 1px solid var(--line); padding: 0.4rem 0.6rem; text-align: left; }
.prose pre { background: var(--bg); }
@media (max-width: 480px) { .where { font-size: 0.85rem; } }

/* Wider layout for skill pages so the explorer has room */
.wrap.wide { max-width: 76rem; }
.wrap.wide > .masthead, .wrap.wide > .crumbs, .wrap.wide > .note { max-width: 44rem; }
.wrap.wide > .block:last-of-type { max-width: 52rem; }

/* Explorer: tree left, preview right */
.explorer { display: grid; grid-template-columns: minmax(12rem, 17rem) minmax(0, 1fr); border: 1px solid var(--line); border-radius: 8px; background: var(--surface); height: min(78vh, 52rem); overflow: hidden; }
.explorer .tree { border-right: 1px solid var(--line); overflow: auto; padding: 0.6rem 0.4rem; font: 500 0.86rem/1.5 var(--mono); }
.explorer .tree ul { list-style: none; margin: 0; padding: 0; }
.explorer .tree ul ul { padding-left: 0.9rem; border-left: 1px solid var(--line); margin-left: 0.55rem; }
.explorer .tree button { all: unset; box-sizing: border-box; display: block; width: 100%; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; overflow-wrap: anywhere; }
.explorer .tree button:hover { background: var(--accent-soft); }
.explorer .tree button:focus-visible { outline: 2px solid var(--accent); }
.explorer .tree button.folder { color: var(--muted); }
.explorer .tree button.folder::before { content: "▾ "; }
.explorer .tree button.folder[aria-expanded="false"]::before { content: "▸ "; }
.explorer .tree button[aria-current="true"] { background: var(--accent-soft); color: var(--accent); }
.explorer .pane { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
.pane-bar { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--line); }
.pane-bar .path { text-transform: none; overflow-wrap: anywhere; }
.pane-tools { display: flex; gap: 0.4rem; flex-shrink: 0; }
.pane-tools button, button.copy { font: 500 0.75rem/1 var(--mono); padding: 0.45rem 0.65rem; border-radius: 4px; border: 1px solid var(--line); background: var(--bg); color: var(--fg); cursor: pointer; }
.pane-tools button:hover { border-color: var(--accent); color: var(--accent); }
.pane-body { flex: 1; overflow: auto; min-height: 0; }
.pane-body pre.src { border: 0; border-radius: 0; margin: 0; padding: 1rem 1.1rem; display: grid; grid-template-columns: auto 1fr; gap: 0 1rem; background: none; overflow: visible; min-width: max-content; }
.pane-body pre.src.wrap { display: block; white-space: pre-wrap; overflow-wrap: anywhere; min-width: 0; }
.pane-body .gutter { color: var(--muted); text-align: right; user-select: none; opacity: 0.7; }
.pane-body .prose { border: 0; border-radius: 0; }
.pane-body img { max-width: 100%; display: block; margin: 1rem auto; }
.pane-body .binary { padding: 1rem; color: var(--muted); }
.code .copy { position: absolute; top: 0.5rem; right: 0.5rem; }
@media (max-width: 760px) {
  .explorer { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto minmax(0, 1fr); height: 85vh; }
  .explorer .tree { border-right: 0; border-bottom: 1px solid var(--line); max-height: 12rem; }
}

/* Syntax colors (highlight.js classes), themed with the site tokens */
:root { --hl-kw: #8a3ffc; --hl-str: #2e7d32; --hl-com: #6b7785; --hl-num: #b5531b; --hl-fn: #1d5c88; --hl-attr: #a1356b; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --hl-kw: #c59dff; --hl-str: #8fd19e; --hl-com: #7f8b97; --hl-num: #f0a36b; --hl-fn: #7fb6de; --hl-attr: #ef9ac4; } }
:root[data-theme="dark"] { --hl-kw: #c59dff; --hl-str: #8fd19e; --hl-com: #7f8b97; --hl-num: #f0a36b; --hl-fn: #7fb6de; --hl-attr: #ef9ac4; }
.hljs-keyword, .hljs-selector-tag, .hljs-literal, .hljs-doctag, .hljs-meta .hljs-keyword { color: var(--hl-kw); }
.hljs-string, .hljs-regexp, .hljs-addition, .hljs-meta .hljs-string { color: var(--hl-str); }
.hljs-comment, .hljs-quote, .hljs-meta { color: var(--hl-com); font-style: italic; }
.hljs-number, .hljs-symbol, .hljs-variable, .hljs-template-variable, .hljs-deletion { color: var(--hl-num); }
.hljs-title, .hljs-title.function_, .hljs-title.class_, .hljs-built_in, .hljs-section, .hljs-name { color: var(--hl-fn); }
.hljs-attr, .hljs-attribute, .hljs-property, .hljs-params, .hljs-selector-class, .hljs-type, .hljs-bullet, .hljs-link { color: var(--hl-attr); }
.hljs-section, .hljs-strong { font-weight: 600; }
.hljs-emphasis { font-style: italic; }
.hljs-code { color: var(--hl-str); }
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", action="append", default=[], help="a skills folder, or one skill folder (repeatable)")
    ap.add_argument("--only", default="", help="comma-separated skill names to build (default: all found)")
    ap.add_argument("--note", action="append", default=[], help="name=text, a short note shown on that skill's page")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent), help="site checkout")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--title", default="Skills")
    ap.add_argument("--lede", default="Agent skills I've written and use every day, with source and a one-step install for Claude Code, Codex and pi.")
    ap.add_argument("--check", action="store_true", help="check only; write nothing")
    ap.add_argument("--force", action="store_true", help="build despite errors (local preview only; never publish this)")
    args = ap.parse_args()

    repo = Path(args.repo).expanduser()
    out_root = repo / "skills"
    found = find_skills([Path(s) for s in args.src])
    only = [s.strip() for s in args.only.split(",") if s.strip()]
    missing = [s for s in only if s not in found]
    if missing:
        print("not found in --src: " + ", ".join(missing), file=sys.stderr)
        return 2
    names = only or sorted(found)
    notes = dict(n.split("=", 1) for n in args.note)

    manifest_path = out_root / "skills.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"skills": []}
    by_name = {e["name"]: e for e in manifest["skills"]}

    failed = False
    built = []
    for n in names:
        d = found[n]
        info, errors, warnings = check_skill(d)
        for w in warnings:
            print(f"  warning {n}: {w}")
        for e in errors:
            print(f"  ERROR   {n}: {e}")
        if errors:
            failed = True
            continue
        print(f"  ok      {n} ({d})")
        built.append((n, d, info))
    if failed and args.force:
        print("  --force: building anyway for preview; do not publish", file=sys.stderr)
        built = [(n, found[n], check_skill(found[n])[0]) for n in names]
    elif failed:
        print("refusing to build: fix the errors above", file=sys.stderr)
        return 1
    if args.check:
        return 0

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "style.css").write_text(STYLE)
    (out_root / "explorer.js").write_text(EXPLORER_JS)
    import shutil
    vendor = out_root / "vendor"
    vendor.mkdir(exist_ok=True)
    for f in (Path(__file__).resolve().parent / "vendor").iterdir():
        shutil.copy2(f, vendor / f.name)
    for n, d, info in built:
        files = skill_files(d)
        sdir = out_root / n
        sdir.mkdir(exist_ok=True)
        sha = write_zip(d, n, files, sdir / f"{n}.zip")
        prev = by_name.get(n, {})
        entry = {
            "name": n,
            "description": info["description"],
            "date": args.date if prev.get("sha256") != sha else prev.get("date", args.date),
            "files": len(files),
            "requires": requirements(files, d),
            "zip": f"{SITE}/skills/{n}/{n}.zip",
            "page": f"{SITE}/skills/{n}/",
            "zip_size": human_size((sdir / f"{n}.zip").stat().st_size),
            "sha256": sha,
            "note": notes.get(n, prev.get("note", "")),
        }
        (sdir / "index.html").write_text(skill_page(entry, d, files))
        by_name[n] = entry
        print(f"  wrote   skills/{n}/ ({entry['files']} files, {entry['zip_size']})")

    entries = sorted(by_name.values(), key=lambda e: e["name"])
    manifest = {"title": args.title, "lede": args.lede, "site": SITE,
                "harnesses": {"claude-code": "~/.claude/skills", "codex": "~/.agents/skills",
                              "pi": "~/.pi/agent/skills or ~/.agents/skills"},
                "skills": entries}
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    (out_root / "index.html").write_text(index_page(entries, args.title, args.lede))
    print(f"  wrote   skills/index.html ({len(entries)} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
