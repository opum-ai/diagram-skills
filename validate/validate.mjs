#!/usr/bin/env node
// The diagram pane's syntax gate (DSKI-18, DEC-221 (a1)). Reads one Mermaid source on
// stdin and prints one JSON line:
//   {"ok":true,"validated":true,"diagramType":"flowchart"}   mermaid.parse() accepted it
//   {"ok":false,"reason":"syntax","message":"..."}           mermaid.parse() refused it, in mermaid's own words
//   {"ok":true,"validated":false,"reason":"no-jsdom"}        no jsdom to parse with: nothing was checked
//
// mermaid.parse() needs a DOM. The pinned jsdom and mermaid are the ones the repository's own
// parse gate installs (`npm ci --prefix skills/diagram-review/scripts`), so a plugin install
// without that step has no jsdom and answers "validated":false; the pane then draws the source's
// preview labelled as unvalidated. DIAGRAM_VALIDATE_ROOT points at another directory whose
// node_modules holds jsdom and mermaid (the tests use an empty one to prove the other way).
//
// Without a DOM, valid and invalid sources both throw, so an exception that is not a syntax
// error is reported as "unvalidated", never as a pass.
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const SYNTAX = /Parse error|Lexer error|Lexical error|Parsing failed|Unknown diagram|No diagram type detected|Expecting/i

const here = dirname(fileURLToPath(import.meta.url))
const base = process.env.DIAGRAM_VALIDATE_ROOT ?? join(here, '..', 'skills', 'diagram-review', 'scripts')

function say (value) {
  process.stdout.write(JSON.stringify(value))
}

async function main () {
  const source = readFileSync(0, 'utf8')
  const require = createRequire(join(base, 'resolve.cjs'))
  let JSDOM
  let entry
  try {
    ;({ JSDOM } = require('jsdom'))
    const manifest = require('mermaid/package.json')
    entry = join(dirname(require.resolve('mermaid/package.json')), manifest.module ?? manifest.main)
  } catch {
    return say({ ok: true, validated: false, reason: 'no-jsdom' })
  }
  try {
    const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true })
    globalThis.window = dom.window
    globalThis.document = dom.window.document
    for (const key of ['DOMParser', 'Element', 'HTMLElement', 'Node', 'navigator']) {
      if (!(key in globalThis)) globalThis[key] = dom.window[key]
    }
    const { default: mermaid } = await import(pathToFileURL(entry).href)
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' })
    try {
      const parsed = await mermaid.parse(source)
      return say({ ok: true, validated: true, diagramType: parsed?.diagramType ?? '' })
    } catch (error) {
      const message = String(error && error.message ? error.message : error)
      if (SYNTAX.test(message)) return say({ ok: false, reason: 'syntax', message })
      return say({ ok: true, validated: false, reason: 'environment', message })
    }
  } catch (error) {
    return say({ ok: true, validated: false, reason: 'environment', message: String(error && error.message ? error.message : error) })
  }
}

await main()
