#!/usr/bin/env node
// Render mermaid sources (diagrams/mmd-<hash>.mmd, written by import_doc.py) to
// static SVG (diagrams/mmd-<hash>.svg), drawn with the same --cds-* colour
// tokens as the widget diagrams so they follow light and dark mode.
//
// Mermaid needs a browser, so this uses Playwright's Chromium and a local copy
// of mermaid.min.js. Text is measured inside the served research page, so
// serve the repo root first (python3 -m http.server 8765) and run:
//   MERMAID_JS=/path/to/node_modules/mermaid/dist/mermaid.min.js node render_mermaid.js
// (defaults to the global npm root's mermaid; SITE overrides the page URL).
// Add --force to re-render all.
'use strict';
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { chromium } = require('playwright');

const DIR = path.join(__dirname, 'diagrams');
const lib = process.env.MERMAID_JS ||
  path.join(execSync('npm root -g').toString().trim(), 'mermaid', 'dist', 'mermaid.min.js');

// Mermaid does colour maths on its theme variables, so it is given unusual
// sentinel colours that are swapped for tokens in its output.
const SENTINEL = {
  '#010203': 'var(--cds-text-primary)',
  '#7d8a95': 'var(--cds-chart-axis)',
  '#fefdfc': 'var(--surface)',
  '#0b0b0b': 'var(--cds-chart-axis)', // arrowheadPath, fixed by mermaid
};
const FONT = '"Bricolage Grotesque", "Avenir Next", "Segoe UI", system-ui, sans-serif';
const SITE = process.env.SITE || 'http://localhost:8765/research/';
const themeVariables = {
  fontFamily: FONT, fontSize: '13px',
  primaryColor: '#fefdfc', primaryBorderColor: '#7d8a95', primaryTextColor: '#010203',
  secondaryColor: '#fefdfc', tertiaryColor: '#fefdfc',
  lineColor: '#7d8a95', textColor: '#010203', mainBkg: '#fefdfc', nodeBorder: '#7d8a95',
  clusterBkg: '#fefdfc', clusterBorder: '#7d8a95', edgeLabelBackground: '#fefdfc',
};

(async () => {
  const force = process.argv.includes('--force');
  const jobs = fs.readdirSync(DIR).filter(f => f.endsWith('.mmd'))
    .map(f => f.slice(0, -4))
    .filter(id => force || !fs.existsSync(path.join(DIR, id + '.svg')));
  if (!jobs.length) { console.log('rendered 0 mermaid diagram(s)'); return; }
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(SITE, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.addScriptTag({ path: lib });
  await page.evaluate(tv => window.mermaid.initialize({
    startOnLoad: false, theme: 'base', themeVariables: tv, securityLevel: 'strict',
    flowchart: { htmlLabels: false, curve: 'basis' },
  }), themeVariables);
  for (const id of jobs) {
    const src = fs.readFileSync(path.join(DIR, id + '.mmd'), 'utf8');
    let { svg } = await page.evaluate(([id, src]) => window.mermaid.render(id, src), [id, src]);
    for (const [hex, token] of Object.entries(SENTINEL)) svg = svg.split(hex).join(token);
    const left = svg.match(/#[0-9a-fA-F]{6}\b|rgb\(/g);
    if (left) console.warn(`${id}: colours left as is: ${[...new Set(left)].join(' ')}`);
    svg = svg.replace(/ style="max-width: [^"]*"/, '');
    // The site styles .label (mermaid's class for node text) as small caps.
    svg = svg.replace('</style>', `#${id} .label, #${id} text { font: 400 13px ${FONT}; text-transform: none; letter-spacing: normal; }</style>`);
    fs.writeFileSync(path.join(DIR, id + '.svg'), svg + '\n');
  }
  await browser.close();
  console.log(`rendered ${jobs.length} mermaid diagram(s)`);
})().catch(e => { console.error(e); process.exit(1); });
