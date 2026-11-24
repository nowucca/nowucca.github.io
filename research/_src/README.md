# Research section sources

Builds https://nowucca.com/research/ from the AI research summaries. Jekyll skips
this `_src` folder, so only the generated pages are served.

| File | What it is |
| --- | --- |
| `entries.json` | Themes and subtopics, entry metadata, and cross-links (edges with the reason two entries connect) |
| `entries/<slug>.html` | Entry bodies, cleaned by `import_doc.py` |
| `diagrams/<node id>.jsx` | Diagram code exported from the summary doc |
| `diagrams/<node id>.svg` | Static SVG rendered by `render_diagrams.js` |
| `authors.py` | Credits each entry to its authors from the `by` line and scores reputation; `build.py` calls it |
| `authors.json` | Author display names, aliases, short public specialties, per-entry overrides and ignored names |
| `quality.json` | Generated snapshot of Reviewer verdicts (public entries only); refreshed by `build.py` when /mnt/project-files/research is present |

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

## Authors (/research/authors/)

`build.py` builds an Authors page ranked by reputation and a page per author,
and adds an Authors line to each entry page. Credits are parsed from each
entry's `by` line (see the docstring in `authors.py`). The build prints the
entries it could not credit; paper author lists ("Zhang, Gao et al.") are left
uncredited on purpose. When a new poster or organization shows up, it is
credited automatically; add it to `authors.json` `people` only to give it a
specialty, merge aliases, or fix a wrong parse (`overrides`, `ignore`).
Specialties must be public facts; leave them blank rather than guess.

Reputation is the sum of entry quality over an author's public entries
(1 per entry, +0.25 for a first-round Reviewer pass, -0.25 if the Reviewer
asked for a revision, +0.5 if a published field guide cites it). The private
trusted-author list is not used or shown. Weights live in `authors.py` `QUALITY`.
Only guides listed in `guides.json` (approved) count, so private guides never
show up as tags.
