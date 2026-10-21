/**
 * The diagram pane mod (DSKI-18; design opum-doc DEC-221, ODOC-494).
 *
 * `/diagram <path>` opens a pane and draws the first closed mermaid fence of a
 * file (the whole file for .mmd and .mermaid). The tool
 * `mcp__diagram-skills__show_diagram` lets the skill push its own diagram into
 * the same pane. Transcript rendering stays plain-english-styles' job.
 *
 * Drawing, per surface:
 * - terminal: Unicode art, when it fits the pane's own `bodyColumns` and
 *   `bodyRows` (art that does not fit does not wrap; it falls back);
 * - desktop, VS Code, mobile: `Svg` (at most 131,072 characters, `alt` required);
 * - every other case: the source plus a one-line reason and an "Open diagram"
 *   Button, which writes a self-contained HTML page (vendored mermaid.js, strict
 *   security level, a CSP that allows no network) and opens it.
 * No PNG and no Chromium.
 *
 * The renderer, `renderer/render.mjs`, is a byte-identical copy of
 * plain-english-styles' (see RENDERER-PROVENANCE.md). The render pass never
 * waits on it: the first draw shows the source, the helper runs off the render
 * path, and its result - a failure too - is cached by the source's SHA-256, so
 * a broken diagram is never re-run on a redraw.
 *
 * Every function that takes `$` is a top-level declaration: the plugin
 * validator accepts `$` only as an argument to one.
 */
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderNode } from 'claude-code'

import type { View } from '../types'
import { htmlPage } from './page'

export const PANE = 'diagram'
export const TOOL = 'show_diagram'
export const MAX_SOURCE = 20000 // a longer source is not rendered
export const MAX_SVG = 131072 // the `Svg` element's own cap
export const MAX_DIAGRAMS = 8 // at most this many fences of one document
const HELPER_TIMEOUT_MS = 5000
const CACHE_LIMIT = 512

export type Rendered =
  | { ok: true; kind: string; unicode: string; svg: string }
  | { ok: false; reason: string; kind?: string; message?: string }

/**
 * What the syntax gate (validate/validate.mjs) said: the source parsed (`validated: true`), it
 * failed with mermaid's own message, or nothing was checked (`validated: false`: no jsdom, or no
 * node to run the gate under).
 */
export type Checked =
  | { ok: true; validated: boolean }
  | { ok: false; reason: 'syntax'; message: string }

/** One drawing of a rendered diagram on a surface. */
export type Drawing = 'art' | 'svg' | 'fallback'

const view = atom({ plugin: 'diagram-skills', key: 'view' } as const, null)

// Module-level, so it survives every redraw of a session (a reload starts it
// over, which costs only a re-render). Bounded so a long session cannot grow it.
const cache = new Map<string, Rendered>()
const checks = new Map<string, Checked>()
const inflight = new Set<string>()
let runtimeChoice: string | null | undefined
let mermaidJsCache: string | undefined
let systemChoice: string | undefined

/** Forget every cached result and the runtime choice (the tests start from a clean module). */
export function resetCaches (): void {
  cache.clear()
  checks.clear()
  inflight.clear()
  runtimeChoice = undefined
  mermaidJsCache = undefined
  systemChoice = undefined
}

/** The SHA-256 of a string, lowercase hex. */
async function sha256 (text: string): Promise<string> {
  const bytes = new TextEncoder().encode(text)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('')
}

/** Remember one result, evicting the oldest when the cache is full. */
function remember (key: string, value: Rendered): void {
  if (cache.size >= CACHE_LIMIT) {
    const oldest = cache.keys().next().value
    if (oldest !== undefined) cache.delete(oldest)
  }
  cache.set(key, value)
}

/** The closed ```mermaid fences of a markdown text, in order (any other fence is skipped whole). */
export function scanFences (text: string): string[] {
  const lines = text.split('\n')
  const isClose = (line: string): boolean => /^[ \t]*```[ \t]*$/.test(line)
  const sources: string[] = []
  for (let i = 0; i < lines.length; i++) {
    const open = /^[ \t]*```[ \t]*([^\s`]*)/.exec(lines[i] as string)
    if (!open) continue
    const info = (open[1] ?? '').toLowerCase()
    let j = i + 1
    while (j < lines.length && !isClose(lines[j] as string)) j++
    if (j >= lines.length) break // still open: nothing after it is a closed fence
    if (info === 'mermaid') sources.push(lines.slice(i + 1, j).join('\n'))
    i = j
  }
  return sources
}

/** The diagram sources of a file: the whole of a .mmd/.mermaid file, else its closed fences. */
export function sourcesOf (path: string, text: string): string[] {
  if (/\.(mmd|mermaid)$/i.test(path)) return text.trim() === '' ? [] : [text]
  return scanFences(text)
}

const HEADERS = [
  'graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 'stateDiagram', 'erDiagram', 'journey', 'gantt', 'pie',
  'quadrantChart', 'requirementDiagram', 'gitGraph', 'C4Context', 'C4Container', 'C4Component', 'C4Dynamic',
  'C4Deployment', 'mindmap', 'timeline', 'zenuml', 'sankey', 'xychart', 'block', 'packet', 'kanban', 'architecture',
  'radar', 'treemap',
]

/**
 * Whether a source opens with a Mermaid diagram header. A leading frontmatter
 * block, `%%` comment lines and blank lines are skipped. The bundled helper is
 * lenient (it draws an empty or partial picture for some malformed sources and
 * reports every unknown header as "unsupported"), so the tool checks this first
 * to tell text that is not Mermaid from a type the browser view handles.
 */
export function hasMermaidHeader (source: string): boolean {
  const lines = source.split('\n')
  let i = 0
  if ((lines[0] ?? '').trim() === '---') {
    i = 1
    while (i < lines.length && (lines[i] ?? '').trim() !== '---') i++
    i++
  }
  for (; i < lines.length; i++) {
    const line = (lines[i] as string).trim()
    if (line === '' || line.startsWith('%%')) continue
    const word = /^[A-Za-z0-9-]+/.exec(line)?.[0] ?? ''
    return HEADERS.some(header => word === header || word.startsWith(`${header}-`))
  }
  return false
}

/** True when a successful render drew nothing a reader could use (the helper's lenient output). */
export function isEmptyDrawing (result: Rendered): boolean {
  if (!result.ok) return false
  return result.unicode.trim() === '' || /viewBox="0 0 0 0"/.test(result.svg)
}

/** The widest line of a string, in characters. */
export function widest (text: string): number {
  let max = 0
  for (const line of text.split('\n')) max = Math.max(max, [...line].length)
  return max
}

/** The rows of a string. */
export function rows (text: string): number {
  return text.split('\n').length
}

/** The one-line text equivalent of a diagram, for `Svg`'s alt. */
export function altFor (kind: string, alt?: string): string {
  return alt !== undefined && alt.trim() !== '' ? alt : `Mermaid ${kind} diagram`
}

/** The drawing and, for a fallback, the one-line reason. */
export type Decision = { drawing: 'art' | 'svg'; isUnvalidated: boolean } | { drawing: 'fallback'; why: string }

/**
 * Which drawing one source gets on a surface. Unicode art on the terminal when
 * it fits `bodyColumns` x `bodyRows`; `Svg` on every other surface when it is
 * within the element's cap; the source-plus-button fallback otherwise.
 * `runtime` is what the helper runs under, `null` when neither bun nor node is on PATH.
 */
export function decide (
  source: string,
  result: Rendered | undefined,
  surface: string,
  columns: number,
  bodyRows: number,
  runtime: string | null,
  checked: Checked | undefined,
): Decision {
  if (source.length > MAX_SOURCE) {
    return { drawing: 'fallback', why: `This diagram is over ${MAX_SOURCE.toLocaleString('en-US')} characters, so it is not drawn here; open it in the browser.` }
  }
  if (runtime === null) return { drawing: 'fallback', why: 'Diagrams need bun or node on PATH; neither was found.' }
  if (checked !== undefined && !checked.ok) {
    return { drawing: 'fallback', why: `This diagram has a syntax error: ${checked.message.split('\n')[0] ?? ''}; open it in the browser.` }
  }
  if (result === undefined || checked === undefined) return { drawing: 'fallback', why: 'Drawing…' }
  if (!result.ok) {
    return {
      drawing: 'fallback',
      why: result.reason === 'unsupported-type'
        ? 'This diagram type needs the browser view.'
        : result.reason === 'too-large'
          ? 'This diagram is too large; open it in the browser.'
          : `This diagram could not be drawn${result.message !== undefined ? `: ${result.message}` : ''}; open it in the browser.`,
    }
  }
  if (isEmptyDrawing(result)) {
    return { drawing: 'fallback', why: 'This diagram drew nothing; check its source or open it in the browser.' }
  }
  if (surface === 'terminal') {
    if (columns > 0 && widest(result.unicode) > columns) {
      return { drawing: 'fallback', why: 'This diagram is wider than the pane; open it in the browser.' }
    }
    if (bodyRows > 0 && rows(result.unicode) > bodyRows) {
      return { drawing: 'fallback', why: 'This diagram is taller than the pane; open it in the browser.' }
    }
    return { drawing: 'art', isUnvalidated: !checked.validated }
  }
  return result.svg.length <= MAX_SVG ? { drawing: 'svg', isUnvalidated: !checked.validated } : { drawing: 'fallback', why: 'This diagram is too large to draw here; open it in the browser.' }
}

/** The runtime to run the helper with: `node`, then `bun`, else null. */
async function chooseRuntime ($: EngineInterface): Promise<string | null> {
  if (runtimeChoice !== undefined) return runtimeChoice
  for (const runtime of ['node', 'bun']) {
    try {
      const { exitCode } = await $.process.run([runtime, '--version'], { timeoutMs: 2000 })
      if (exitCode === 0) { runtimeChoice = runtime; return runtime }
    } catch { /* not on PATH */ }
  }
  runtimeChoice = null
  return null
}

/** Run the bundled helper on one source. Never throws. */
async function renderSource ($: EngineInterface, runtime: string, source: string): Promise<Rendered> {
  try {
    const { exitCode, stdout } = await $.process.run(
      [runtime, `${$.plugin.root}/renderer/render.mjs`],
      // PES10_STDIN makes the helper run: its own "am I the entry point" test compares
      // import.meta.url with the path and fails on a plugin path holding a space, # or %.
      { stdin: source, timeoutMs: HELPER_TIMEOUT_MS, env: { PES10_STDIN: '1' } },
    )
    if (exitCode !== 0) return { ok: false, reason: 'helper-exit', message: `exit ${exitCode}` }
    return JSON.parse(stdout) as Rendered
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    return { ok: false, reason: 'helper-error', message }
  }
}

/** Render one source once: a cached result (a failure too) is never re-run. */
async function renderOnce ($: EngineInterface, runtime: string, source: string): Promise<Rendered> {
  const key = await sha256(source)
  const hit = cache.get(key)
  if (hit !== undefined) return hit
  const result = await renderSource($, runtime, source)
  remember(key, result)
  return result
}

/**
 * Run the syntax gate on one source. Only `node` runs it: bun resolves a package it cannot
 * find by installing it from the network, which a gate must never do. Never throws.
 */
async function checkSource ($: EngineInterface, runtime: string, source: string): Promise<Checked> {
  if (runtime !== 'node') return { ok: true, validated: false }
  try {
    const { exitCode, stdout } = await $.process.run(
      [runtime, `${$.plugin.root}/validate/validate.mjs`],
      { stdin: source, timeoutMs: HELPER_TIMEOUT_MS },
    )
    if (exitCode !== 0) return { ok: true, validated: false }
    const parsed = JSON.parse(stdout) as { ok: boolean; validated?: boolean; message?: string }
    if (parsed.ok) return { ok: true, validated: parsed.validated === true }
    return { ok: false, reason: 'syntax', message: parsed.message ?? 'syntax error' }
  } catch {
    return { ok: true, validated: false }
  }
}

/** The gate's answer for a source, asked once: a cached answer (a failure too) is never re-run. */
async function checkOnce ($: EngineInterface, runtime: string, source: string): Promise<Checked> {
  const key = await sha256(source)
  const hit = checks.get(key)
  if (hit !== undefined) return hit
  const result = await checkSource($, runtime, source)
  if (checks.size >= CACHE_LIMIT) {
    const oldest = checks.keys().next().value
    if (oldest !== undefined) checks.delete(oldest)
  }
  checks.set(key, result)
  return result
}

/** Say something in the pane, under the drawing. */
async function note ($: EngineInterface, text: string): Promise<void> {
  await update($, view, current => (current === null ? current : { ...current, note: text }))
}

/** The operating system's name (`uname -s`), asked once; empty when it cannot be read. */
async function systemName ($: EngineInterface): Promise<string> {
  if (systemChoice !== undefined) return systemChoice
  try {
    const { stdout } = await $.process.run(['uname', '-s'], { timeoutMs: 2000 })
    systemChoice = stdout.trim()
  } catch {
    systemChoice = ''
  }
  return systemChoice
}

/**
 * Write the self-contained HTML page and open it in the browser. A symbolic link at the cache
 * directory is refused (a write through it would land somewhere the plugin did not choose).
 * Only macOS has `open`; anywhere else the pane says where the page is and runs nothing.
 */
async function openInBrowser ($: EngineInterface, source: string, title: string): Promise<void> {
  const key = await sha256(source)
  const base = `${$.plugin.root}/.cache`
  const dir = `${base}/diagram-pane`
  for (const part of [base, dir]) {
    if (await $.fs.exists(part) && (await $.fs.stat(part)).isLink) {
      await note($, `Not written: ${part} is a symbolic link.`)
      return
    }
  }
  const path = `${dir}/${key}.html`
  let js = mermaidJsCache
  if (js === undefined) {
    const text = await $.fs.read(`${$.plugin.root}/renderer/vendor/mermaid.min.js`)
    js = typeof text === 'string' ? text : new TextDecoder().decode(text)
    mermaidJsCache = js
  }
  await $.fs.write(path, htmlPage(source, js, title))
  if ((await systemName($)) === 'Darwin') {
    await $.process.run(['open', path], { timeoutMs: HELPER_TIMEOUT_MS })
  } else {
    await note($, `Open this file in a browser: ${path}`)
  }
}

/** Open the pane. */
async function openPane ($: EngineInterface): Promise<void> {
  await $.ui.open({ id: PANE, title: 'Diagram' })
}

/** Show these sources in the pane, the first drawn. */
async function show ($: EngineInterface, sources: string[], title: string, alt: string | undefined): Promise<View> {
  const next: View = {
    title,
    alt,
    sources: sources.slice(0, MAX_DIAGRAMS),
    hidden: Math.max(0, sources.length - MAX_DIAGRAMS),
    index: 0,
  }
  await update($, view, () => next)
  await openPane($)
  return next
}

/** Move to another fence of the shown document. */
async function step ($: EngineInterface, by: number): Promise<void> {
  await update($, view, current => {
    if (current === null) return current
    const index = Math.min(current.sources.length - 1, Math.max(0, current.index + by))
    return { ...current, index }
  })
}

/** Start the helper for a source off the render path and redraw when it is done. */
function schedule ($: EngineInterface, runtime: string, source: string, key: string): void {
  if ((cache.has(key) && checks.has(key)) || inflight.has(key) || source.length > MAX_SOURCE) return
  inflight.add(key)
  void Promise.all([renderSource($, runtime, source), checkOnce($, runtime, source)])
    .then(([result]) => { remember(key, result) })
    .catch(() => { remember(key, { ok: false, reason: 'helper-error' }) })
    .finally(() => { inflight.delete(key); $.ui.invalidate('ui.render') })
}

export const register: Register = (on, options) => {
  void options

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'diagram',
      description: 'Draw a Mermaid diagram from a file in a pane',
      argumentHint: '<path>',
    })
    await $.tool.register({
      name: TOOL,
      description:
        'Draw a Mermaid diagram in the diagram pane. Give the Mermaid source (without the code fence), '
        + 'an optional title and an optional one-sentence alt text. Where the syntax gate can run (it needs node on PATH as well as the installed jsdom), a source that does not '
        + 'parse is refused with Mermaid\'s own message and the pane keeps what it showed; where it cannot, the diagram is drawn as an '
        + 'unvalidated preview and the result says validated: false.',
      inputSchema: {
        type: 'object',
        properties: {
          source: { type: 'string', description: 'The Mermaid source, without the ```mermaid fence.' },
          title: { type: 'string', description: 'A short title for the pane.' },
          alt: { type: 'string', description: 'A one-sentence text equivalent of the diagram.' },
        },
        required: ['source'],
      },
    })
    return next(e)
  })

  on('command.run', { command: 'diagram' }, async ($, e) => {
    const path = e.args.trim()
    if (path === '') return { text: 'Usage: /diagram <path to a .md, .mmd or .mermaid file>' }
    let text: string
    try {
      const read = await $.fs.read(path)
      text = typeof read === 'string' ? read : new TextDecoder().decode(read)
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      return { text: `Could not read ${path}: ${message}` }
    }
    const sources = sourcesOf(path, text)
    if (sources.length === 0) return { text: `No closed mermaid fence found in ${path}.` }
    await show($, sources, path, undefined)
    const hidden = sources.length - Math.min(sources.length, MAX_DIAGRAMS)
    return {
      text: hidden > 0
        ? `Drew diagram 1 of ${MAX_DIAGRAMS} from ${path}; ${hidden} more in the file are not shown.`
        : `Drew ${sources.length === 1 ? 'the diagram' : `diagram 1 of ${sources.length}`} from ${path}.`,
    }
  })

  on('tool.call', { tool: `mcp__diagram-skills__${TOOL}` }, async ($, e) => {
    const input = e as unknown as { source?: unknown; title?: unknown; alt?: unknown }
    const source = typeof input.source === 'string' ? input.source : ''
    const title = typeof input.title === 'string' && input.title.trim() !== '' ? input.title : 'Diagram'
    const alt = typeof input.alt === 'string' ? input.alt : undefined
    const refuse = (reason: string): { result: { ok: false; reason: string } } => ({ result: { ok: false, reason } })

    if (source.trim() === '') return refuse('empty-source')
    if (source.length > MAX_SOURCE) return refuse(`too-large: over ${MAX_SOURCE} characters`)

    // The strict gate runs when jsdom resolves (under node); a source it refuses is refused here
    // with mermaid's own message. Without it nothing was parsed, so the source is drawn labelled
    // unvalidated and the result says `validated: false`; the header check is the only guard then.
    const runtime = await chooseRuntime($)
    let validated = false
    if (runtime !== null) {
      const checked = await checkOnce($, runtime, source)
      if (!checked.ok) return refuse(`syntax: ${checked.message}`)
      validated = checked.validated
    }
    if (!validated && !hasMermaidHeader(source)) return refuse('not-mermaid: the source does not start with a Mermaid diagram header')

    if (runtime !== null) {
      const result = await renderOnce($, runtime, source)
      if (!result.ok && (result.reason === 'render-error' || result.reason === 'helper-error' || result.reason === 'helper-exit')) {
        return refuse(`${result.reason}${result.message !== undefined ? `: ${result.message}` : ''}`)
      }
      if (isEmptyDrawing(result)) return refuse('render-error: the diagram drew nothing')
    }
    await show($, [source], title, alt)
    return { result: { ok: true, validated } }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Code, Button } = $.ui.resolve(e)
    const elements = $.ui.resolve(e)
    const SvgEl = 'Svg' in elements ? elements.Svg : undefined
    const current = await read($, view)

    if (current === null) {
      return <Box flexDirection="column"><Text dimColor>No diagram yet. Run /diagram {'<path>'} to draw one.</Text></Box>
    }

    const source = current.sources[current.index] as string
    const runtime = await chooseRuntime($)
    const key = await sha256(source)
    if (runtime !== null) schedule($, runtime, source, key)

    const columns = e.props.bodyColumns
    const bodyRows = e.props.scroll?.bodyRows ?? 0
    const checked: Checked | undefined = runtime === null
      ? undefined
      : runtime === 'node' ? checks.get(key) : { ok: true, validated: false }
    const decision = decide(source, cache.get(key), e.surface, columns, bodyRows, runtime, checked)
    const result = cache.get(key)

    const nodes: RenderNode[] = []
    if (current.title !== '') nodes.push(<Text key="title" bold>{current.title}</Text>)
    if (current.sources.length > 1) {
      nodes.push(
        <Box key="nav" flexDirection="row">
          <Button key="prev" label="Previous" onPress={() => step($, -1)} />
          <Text> {current.index + 1} of {current.sources.length} </Text>
          <Button key="next" label="Next" onPress={() => step($, 1)} />
        </Box>,
      )
    }
    if (current.hidden > 0) nodes.push(<Text key="hidden" dimColor>{current.hidden} more diagram{current.hidden === 1 ? '' : 's'} in the file not shown (the pane draws {MAX_DIAGRAMS}).</Text>)

    const unvalidated = (
      <Box key="unvalidated" flexDirection="column">
        <Text dimColor>Unvalidated preview: nothing parsed this source. Open diagram to check.</Text>
        <Button key="open" label="Open diagram" onPress={() => openInBrowser($, source, current.title)} />
      </Box>
    )
    if (decision.drawing === 'art' && result !== undefined && result.ok) {
      nodes.push(<Text key="art">{result.unicode}</Text>)
      if (decision.isUnvalidated) nodes.push(unvalidated)
    } else if (decision.drawing === 'svg' && result !== undefined && result.ok && SvgEl !== undefined) {
      nodes.push(<SvgEl key="svg" source={result.svg} alt={altFor(result.kind, current.alt)} />)
      if (decision.isUnvalidated) nodes.push(unvalidated)
    } else {
      nodes.push(
        <Box key="fallback" flexDirection="column">
          <Code source={source} language="mermaid" />
          <Text dimColor>{decision.drawing === 'fallback' ? decision.why : 'This diagram could not be drawn here; open it in the browser.'}</Text>
          {decision.drawing === 'fallback' && decision.why === 'Drawing…'
            ? null
            : <Button key="open" label="Open diagram" onPress={() => openInBrowser($, source, current.title)} />}
        </Box>,
      )
    }
    if (current.note !== undefined) nodes.push(<Text key="note" dimColor>{current.note}</Text>)
    return <Box flexDirection="column">{nodes}</Box>
  })
}
