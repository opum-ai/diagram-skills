#!/usr/bin/env node
// Headless Mermaid syntax check: no browser, no Puppeteer. Pinned to the Mermaid version
// GitHub renders (see docs/adr/0001-use-mermaid-in-markdown-as-the-diagram-notation.md).
// Uses the real `mermaid` package's mermaid.parse() (the same grammars the renderer uses)
// under a jsdom window. The shim is REQUIRED: without it, mermaid on Node 24 still
// imports, but any diagram whose text goes through sanitizeText() throws
// "DOMPurify.addHook is not a function", which looks like a parse failure but isn't.
//
// Usage: node mermaid-check.mjs [--expect-fail] <file|dir>...
//   .mmd/.mermaid files are parsed whole; .md/.markdown files have every
//   ```mermaid / ~~~mermaid fenced block extracted and parsed separately.
// Exit codes: 0 = every diagram as expected; 1 = at least one syntax result not as expected;
//             2 = usage or ENVIRONMENT error (a non-syntax exception: broken shim, bad install).
// --expect-fail inverts the check (each diagram must fail with a SYNTAX error), for negative fixtures.
import { readFileSync, statSync, readdirSync } from 'node:fs';
import { join, extname } from 'node:path';
import { createRequire } from 'node:module';
import { JSDOM } from 'jsdom';

const MERMAID_VERSION = createRequire(import.meta.url)('mermaid/package.json').version;

const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
for (const k of ['DOMParser', 'Element', 'HTMLElement', 'Node', 'navigator']) {
  if (!(k in globalThis)) globalThis[k] = dom.window[k];
}
const { default: mermaid } = await import('mermaid');
mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });

// Messages that mean "the diagram text is invalid" (jison, Langium/chevrotain, detector).
const SYNTAX = /Parse error|Lexer error|Lexical error|Parsing failed|Unknown diagram|No diagram type detected|Expecting/i;

const args = process.argv.slice(2);
const expectFail = args.includes('--expect-fail');
const targets = args.filter((a) => a !== '--expect-fail');
if (!targets.length) { console.error('usage: mermaid-check.mjs [--expect-fail] <file|dir>...'); process.exit(2); }

const EXT = new Set(['.mmd', '.mermaid', '.md', '.markdown']);
function walk(p) {
  if (statSync(p).isDirectory()) return readdirSync(p).sort().flatMap((n) => (n === 'node_modules' ? [] : walk(join(p, n))));
  return EXT.has(extname(p)) ? [p] : [];
}
// Fence-aware scan (CommonMark rules): a fence closes only on the same character
// with at least the same length, so a ```mermaid line inside a ~~~text example
// is content, not a diagram. Only fences whose info string is exactly `mermaid`
// (optionally followed by attributes) are checked, so ```mermaid-broken or
// ```text can show a bad example without failing the gate.
function mermaidFences(text) {
  const out = [];
  let open = null;
  text.split('\n').forEach((line, i) => {
    const m = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (open) {
      if (m && m[1][0] === open.ch && m[1].length >= open.len && m[2].trim() === '') {
        if (open.mermaid) out.push({ line: open.line, src: open.body.join('\n') + '\n' });
        open = null;
      } else open.body.push(line);
    } else if (m) {
      open = { ch: m[1][0], len: m[1].length, line: i + 1, mermaid: /^mermaid(\s|$)/.test(m[2].trim()), body: [] };
    }
  });
  return out;
}
function diagramsIn(file) {
  const text = readFileSync(file, 'utf8');
  if (!['.md', '.markdown'].includes(extname(file))) return [{ where: file, src: text }];
  return mermaidFences(text).map(({ line, src }) => ({ where: `${file}:${line}`, src }));
}

let bad = 0, env = 0, total = 0;
for (const file of targets.flatMap(walk)) {
  for (const { where, src } of diagramsIn(file)) {
    total++;
    let status, detail;
    try {
      const r = await mermaid.parse(src); // throws on syntax error
      status = 'parsed'; detail = r?.diagramType ?? '';
    } catch (e) {
      const msg = String(e?.message ?? e);
      status = SYNTAX.test(msg) ? 'syntax-error' : 'env-error';
      detail = msg.split('\n').slice(0, 4).join(' | ').slice(0, 220);
    }
    if (status === 'env-error') { env++; console.log(`ENV  ${where} ${detail}`); continue; }
    const good = expectFail ? status === 'syntax-error' : status === 'parsed';
    if (!good) bad++;
    console.log(`${good ? 'PASS' : 'FAIL'} ${where} [${status}] ${detail}`);
  }
}
console.log(`\n${total - bad - env}/${total} as expected, ${env} environment errors (mermaid ${MERMAID_VERSION}, node ${process.version}${expectFail ? ', --expect-fail' : ''})`);
process.exit(env ? 2 : bad ? 1 : 0);
