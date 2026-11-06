#!/usr/bin/env node
// Render Claude Docs diagram widgets (diagrams/<id>.jsx) to static SVG (diagrams/<id>.svg).
//
// A widget is one JSX module: `export default () => <svg>…</svg>`. It draws with
// --cds-* colour tokens, which research/style.css defines for light and dark.
// Presentation attributes can't hold var(), so colour attributes move into style.
//
// Needs Node and the TypeScript compiler (used only to turn JSX into calls):
//   npm i -g typescript    (or set NODE_PATH to a folder that has it)
'use strict';
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function loadTs() {
  try { return require('typescript'); } catch (_) {}
  const root = execSync('npm root -g').toString().trim();
  return require(path.join(root, 'typescript'));
}
const ts = loadTs();

const FRAGMENT = Symbol('fragment');
const VOID = new Set();
const KEEP_CASE = new Set(['viewBox', 'refX', 'refY', 'markerWidth', 'markerHeight', 'preserveAspectRatio', 'gradientUnits', 'patternUnits']);
const STYLE_PROPS = new Set(['fill', 'stroke', 'stop-color', 'color']);

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escAttr = s => esc(s).replace(/"/g, '&quot;');
const attrName = k => (KEEP_CASE.has(k) || k.startsWith('data-') || k.startsWith('aria-')) ? k
  : k === 'className' ? 'class' : k.replace(/[A-Z]/g, c => '-' + c.toLowerCase());

function h(tag, props, ...children) {
  if (typeof tag === 'function') return tag({ ...(props || {}), children: children.length === 1 ? children[0] : children });
  return { tag, props: props || {}, children };
}

function render(node) {
  if (node === null || node === undefined || node === false || node === true) return '';
  if (Array.isArray(node)) return node.map(render).join('');
  if (typeof node !== 'object') return esc(node);
  if (node.tag === FRAGMENT) return render(node.children);
  const attrs = [];
  const style = [];
  for (const [k, v] of Object.entries(node.props)) {
    if (k === 'key' || k === 'children' || v === undefined || v === null || v === false) continue;
    const name = attrName(k);
    if (STYLE_PROPS.has(name) && String(v).includes('var(')) style.push(`${name}:${v}`);
    else attrs.push(`${name}="${escAttr(v)}"`);
  }
  if (node.tag === 'svg' && !node.props.xmlns) attrs.unshift('xmlns="http://www.w3.org/2000/svg"');
  if (style.length) attrs.push(`style="${escAttr(style.join(';'))}"`);
  const open = `<${node.tag}${attrs.length ? ' ' + attrs.join(' ') : ''}`;
  const inner = render(node.children);
  return inner ? `${open}>${inner}</${node.tag}>` : `${open}/>`;
}

// claude.Visualize: hand the rows to the render function; datum() stamps nothing here.
const claude = {
  Visualize: ({ sources, children }) => {
    const rows = sources && sources.rows && sources.rows.data || [];
    const fn = Array.isArray(children) ? children[0] : children;
    return fn({ rows, datum: () => ({}) });
  },
};

function renderFile(file) {
  const src = fs.readFileSync(file, 'utf8');
  const js = ts.transpileModule(src, {
    compilerOptions: { jsx: ts.JsxEmit.React, jsxFactory: 'h', jsxFragmentFactory: 'Fragment', module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const mod = { exports: {} };
  new Function('module', 'exports', 'h', 'Fragment', 'claude', js)(mod, mod.exports, h, FRAGMENT, claude);
  const fn = mod.exports.default;
  if (typeof fn !== 'function') throw new Error(`${file}: no default export`);
  return render(fn());
}

const dir = path.join(__dirname, 'diagrams');
let n = 0;
for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.jsx')).sort()) {
  const svg = renderFile(path.join(dir, f));
  fs.writeFileSync(path.join(dir, f.replace(/\.jsx$/, '.svg')), svg + '\n');
  n++;
}
console.log(`rendered ${n} diagram(s)`);
