# Research section sources

Builds https://nowucca.com/research/ from the AI research summaries. Jekyll skips
this `_src` folder, so only the generated pages are served.

| File | What it is |
| --- | --- |
| `entries.json` | Themes and subtopics, entry metadata, and cross-links (edges with the reason two entries connect) |
| `entries/<slug>.html` | Entry bodies, cleaned by `import_doc.py` |
| `diagrams/<node id>.jsx` | Diagram code exported from the summary doc |
| `diagrams/<node id>.svg` | Static SVG rendered by `render_diagrams.js` |

## Adding or updating an entry

1. Export the summary doc's tab as HTML (Claude Docs `export`, format `html`).
   Each `<figure data-embed="node/<id>">` in it is a diagram: read that widget's
   code and save it as `diagrams/<id>.jsx`.
2. Add the entry to `entries.json`: metadata in `entries`, its id under a
   subtopic's `primary` (and `also`, with the reason), and its cross-links in
   `edges`. Only entries listed here are public.
3. `python3 import_doc.py <export.html> <id> --rules <redactions.json>`.
   The rules file holds exact text to remove and lives outside this repo.
   Read the result before publishing: it is public.
4. `node render_diagrams.js` (needs the TypeScript compiler: `npm i -g typescript`).
5. `python3 build.py`, then check `/research/`, `/research/map/` and the entry
   page with `python3 -m http.server` from the repo root, at desktop and phone width.
