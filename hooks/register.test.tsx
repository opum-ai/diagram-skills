/**
 * Tests for the diagram pane mod, one block per acceptance criterion of DSKI-18.
 *
 * The bundled helper runs through `$.process.run`, which the kit does not run, so
 * each test answers the `process.run` event itself with a counting stub: that is
 * how "no helper call is retried" and "a redraw does not re-run the helper" are
 * measured, as a count of calls. The real helper is exercised once, separately,
 * by running renderer/render.mjs on the same fixtures (see RENDERER-PROVENANCE.md).
 *
 * Bad fixtures (gantt, malformed, over-long) are inline strings, not .md files, so the
 * repository's own diagram gate (which parses every Mermaid fence under docs/ and
 * skills/) never sees them.
 */
import { describe, expect, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { Decision } from './register'
import { htmlPage } from './page'
import type { On } from 'claude-code'
import {
  altFor, decide, hasMermaidHeader, isEmptyDrawing, MAX_DIAGRAMS, MAX_SOURCE, resetCaches, scanFences,
  sourcesOf, widest,
} from './register'

const VALID = { ok: true as const, validated: true }
const FLOW = 'flowchart TD\n  A --> B'
const OK = { ok: true as const, kind: 'flowchart', unicode: '┌───┐\n│ A │\n└───┘', svg: '<svg viewBox="0 0 10 10"/>' }
const SURFACES = ['terminal', 'desktop'] as const
const DOC = `# Spec\n\n\`\`\`mermaid\n${FLOW}\n\`\`\`\n\nThe end.\n`

type Run = { argv: readonly string[]; stdin: string | undefined; env: Readonly<Record<string, string>> | undefined }

type StubOptions = {
  runtimes?: boolean
  render?: (source: string) => unknown
  /** What validate.mjs says (the strict gate); validated by default. */
  validate?: (source: string) => unknown
  /** What `uname -s` says. */
  system?: string
}

/**
 * Answer `process.run`: node/bun `--version` succeed unless `runtimes` is false, the render helper
 * answers `render(source)`, validate.mjs answers `validate(source)`, `uname` answers `system`, and `open`
 * succeeds. Returns the calls, in order.
 */
function stubProcess (on: On, options: StubOptions = {}): Run[] {
  const runs: Run[] = []
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('process.run', ($, e) => {
    runs.push({ argv: e.argv, stdin: e.init?.stdin, env: e.init?.env })
    const [command, arg] = e.argv
    const done = (stdout: string) => ({ value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
    if (arg === '--version') {
      if (options.runtimes === false) throw new Error(`${String(command)}: not found`)
      return done('v1')
    }
    if (command === 'uname') return done(`${options.system ?? 'Darwin'}\n`)
    if (command === 'open') return done('')
    if (String(arg).endsWith('validate.mjs')) return done(JSON.stringify((options.validate ?? (() => VALID))(e.init?.stdin ?? '')))
    return done(JSON.stringify((options.render ?? (() => OK))(e.init?.stdin ?? '')))
  })
  return runs
}

type Link = { exists: boolean; isLink: boolean }

/** Answer `fs.read` (a map of path to text), `fs.exists` and `fs.stat` (the cache dir may be a symlink), and record `fs.write`. */
function stubFs (on: On, files: Record<string, string>, cacheDir: Link = { exists: false, isLink: false }): { writes: { path: string; text: string }[] } {
  const writes: { path: string; text: string }[] = []
  on('fs.read', ($, e) => {
    const key = Object.keys(files).find(name => e.path === name || e.path.endsWith(`/${name}`))
    const text = (key === undefined ? undefined : files[key]) ?? (e.path.endsWith('/renderer/vendor/mermaid.min.js') ? '/*MERMAID-JS*/' : undefined)
    if (text === undefined) throw new Error(`ENOENT: ${e.path}`)
    return { value: text }
  })
  on('fs.exists', ($, e) => ({ value: cacheDir.exists && e.path.endsWith('/.cache/diagram-pane') }))
  on('fs.stat', ($, e) => ({ value: { kind: 'dir' as const, size: 0, mtimeMs: 0, isLink: cacheDir.isLink && e.path.endsWith('/.cache/diagram-pane') } }))
  on('fs.write', ($, e) => { writes.push({ path: e.path, text: e.text }); return { value: undefined } })
  return { writes }
}

/** Run `/diagram <args>` as the person typed it. */
function runDiagram ($: Engine, args: string) {
  return $.command.run({ command: 'diagram', args, origin: { kind: 'composer' }, presentation: { isFullscreen: true, columns: 80 } })
}

/** The reason of a fallback decision, else an empty string. */
const whyOf = (decision: Decision): string => decision.drawing === 'fallback' ? decision.why : ''

const helperCalls = (runs: Run[]): Run[] => runs.filter(run => String(run.argv[1]).endsWith('render.mjs'))

function paneTarget (surface: 'terminal' | 'desktop', columns = 80, bodyRows = 24) {
  return {
    plugin: 'diagram-skills',
    surface,
    component: 'Pane' as const,
    props: {
      title: 'Diagram',
      isFocused: false,
      bodyColumns: columns,
      placement: 'dock' as const,
      scroll: { offset: 0, bodyRows, contentRows: bodyRows, maxOffset: 0 },
      view: {},
    },
    requestId: 'diagram',
    viewport: { columns, rows: bodyRows },
  }
}

describe('pure helpers', () => {
  test('scanFences finds closed mermaid fences only, in order', () => {
    expect(scanFences(DOC)).toEqual([FLOW])
    expect(scanFences('```js\nx\n```')).toEqual([])
    expect(scanFences('```mermaid\nflowchart TD\n  A --> B')).toEqual([]) // still open
    expect(scanFences('```mermaid\na\n```\n```mermaid\nb\n```')).toEqual(['a', 'b'])
  })
  test('sourcesOf takes a whole .mmd file and the fences of anything else', () => {
    expect(sourcesOf('x.mmd', FLOW)).toEqual([FLOW])
    expect(sourcesOf('x.mermaid', '  \n')).toEqual([])
    expect(sourcesOf('x.md', DOC)).toEqual([FLOW])
  })
  test('hasMermaidHeader accepts real headers, comments and frontmatter, and refuses prose', () => {
    expect(hasMermaidHeader(FLOW)).toBe(true)
    expect(hasMermaidHeader('%% note\n\nsequenceDiagram\n A->>B: hi')).toBe(true)
    expect(hasMermaidHeader('---\ntitle: t\n---\nstateDiagram-v2\n [*] --> S')).toBe(true)
    expect(hasMermaidHeader('pie title Pets\n "Dogs" : 3')).toBe(true)
    expect(hasMermaidHeader('hello world')).toBe(false)
    expect(hasMermaidHeader('')).toBe(false)
  })
  test('isEmptyDrawing catches the helper lenient empty output', () => {
    expect(isEmptyDrawing({ ...OK, unicode: '  ' })).toBe(true)
    expect(isEmptyDrawing({ ...OK, svg: '<svg viewBox="0 0 0 0"/>' })).toBe(true)
    expect(isEmptyDrawing(OK)).toBe(false)
  })
  test('widest and altFor', () => {
    expect(widest('a\nbbb')).toBe(3)
    expect(altFor('flowchart')).toBe('Mermaid flowchart diagram')
    expect(altFor('flowchart', 'Two boxes')).toBe('Two boxes')
  })
  test('decide: art fits, wide and tall fall back, svg on remote surfaces, limits and reasons', () => {
    expect(decide(FLOW, OK, 'terminal', 80, 24, 'node', VALID)).toEqual({ drawing: 'art', isUnvalidated: false })
    expect(whyOf(decide(FLOW, OK, 'terminal', 4, 24, 'node', VALID))).toMatch(/wider/)
    expect(whyOf(decide(FLOW, OK, 'terminal', 80, 2, 'node', VALID))).toMatch(/taller/)
    expect(decide(FLOW, OK, 'desktop', 80, 24, 'node', VALID)).toEqual({ drawing: 'svg', isUnvalidated: false })
    expect(decide(FLOW, { ...OK, svg: 'x'.repeat(131073) }, 'desktop', 80, 24, 'node', VALID)).toMatchObject({ drawing: 'fallback' })
    expect(whyOf(decide(FLOW, { ok: false, reason: 'unsupported-type', kind: 'gantt' }, 'desktop', 80, 24, 'node', VALID)))
      .toMatch(/browser view/)
    expect(whyOf(decide('x'.repeat(MAX_SOURCE + 1), undefined, 'desktop', 80, 24, 'node', VALID))).toMatch(/20,000/)
    expect(whyOf(decide(FLOW, OK, 'terminal', 80, 24, null, VALID))).toMatch(/bun or node/)
    // the strict gate: a refused source never draws, in mermaid's own words; an unchecked one draws labelled
    expect(whyOf(decide(FLOW, OK, 'terminal', 80, 24, 'node', { ok: false, reason: 'syntax', message: 'Parse error on line 2:\nboom' })))
      .toMatch(/syntax error: Parse error on line 2/)
    expect(decide(FLOW, OK, 'desktop', 80, 24, 'node', { ok: true, validated: false })).toEqual({ drawing: 'svg', isUnvalidated: true })
    expect(whyOf(decide(FLOW, OK, 'desktop', 80, 24, 'node', undefined))).toBe('Drawing…')
  })
  test('htmlPage is self-contained, strict and network-free', () => {
    const html = htmlPage('graph TD\n A-->B', '/*MERMAID*/', 'A <diagram>')
    expect(html).toContain("default-src 'none'")
    expect(html).toContain("securityLevel: 'strict'")
    expect(html).toContain('/*MERMAID*/')
    expect(html).toContain('<title>A &lt;diagram&gt;</title>')
    expect(html).not.toMatch(/https?:\/\//)
  })
})

describe('AC1: a file draws in the pane', () => {
  test('/diagram <path> draws the first closed fence: art on the terminal, Svg on desktop', async ($, on) => {
    resetCaches()
    stubProcess(on)
    stubFs(on, { 'docs/specs/foo.md': DOC })
    const { text } = await runDiagram($, 'docs/specs/foo.md')
    expect(text).toContain('Drew the diagram')
    for (const surface of SURFACES) {
      const ui = await $.ui.mount(paneTarget(surface))
      if (surface === 'terminal') {
        expect(await ui.find({ type: 'Text', text: /│ A │/ })).toBeDefined()
        expect(await ui.find({ type: 'Svg' })).toBeUndefined()
      } else {
        expect(await ui.find({ type: 'Svg' })).toBeDefined()
        expect(await ui.find({ type: 'Text', text: /│ A │/ })).toBeUndefined()
      }
      expect(await ui.find({ type: 'Button', text: /Open diagram/ })).toBeUndefined()
      await ui.unmount()
    }
  })
})

describe('AC2: fallback works both ways', () => {
  test('a gantt fence keeps its source, gives a reason and a button that writes a network-free page and opens it', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on, { render: () => ({ ok: false, reason: 'unsupported-type', kind: 'gantt' }) })
    const { writes } = stubFs(on, { 'g.mmd': 'gantt\n  title Plan\n  section A\n  Task :a1, 2026-01-01, 3d' })
    await runDiagram($, 'g.mmd')
    for (const surface of SURFACES) {
      const ui = await $.ui.mount(paneTarget(surface))
      expect(await ui.find({ type: 'Code', text: /gantt/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /browser view/ })).toBeDefined()
      await ui.press({ key: await buttonKey(ui, /Open diagram/) })
      await ui.unmount()
    }
    expect(writes.length).toBeGreaterThan(0)
    const page = writes[0]?.text ?? ''
    expect(page).toContain('/*MERMAID-JS*/')
    expect(page).toContain("default-src 'none'")
    expect(page).not.toMatch(/https?:\/\//)
    expect(runs.some(run => run.argv[0] === 'open' && String(run.argv[1]).endsWith('.html'))).toBe(true)
  })

  test('a flowchart wider than bodyColumns falls back with a button; a fitting one shows none', async ($, on) => {
    resetCaches()
    stubProcess(on)
    stubFs(on, { 'f.mmd': FLOW })
    await runDiagram($, 'f.mmd')
    const narrow = await $.ui.mount(paneTarget('terminal', 4))
    expect(await narrow.find({ type: 'Text', text: /wider than the pane/ })).toBeDefined()
    expect(await narrow.find({ type: 'Button', text: /Open diagram/ })).toBeDefined()
    await narrow.unmount()
    const fits = await $.ui.mount(paneTarget('terminal', 80))
    expect(await fits.find({ type: 'Button', text: /Open diagram/ })).toBeUndefined()
    await fits.unmount()
  })

  test('art taller than bodyRows falls back', async ($, on) => {
    resetCaches()
    stubProcess(on)
    stubFs(on, { 'f.mmd': FLOW })
    await runDiagram($, 'f.mmd')
    const ui = await $.ui.mount(paneTarget('terminal', 80, 2))
    expect(await ui.find({ type: 'Text', text: /taller than the pane/ })).toBeDefined()
    await ui.unmount()
  })
})

describe('AC3: the model can push a diagram', () => {
  test('show_diagram draws the source in the same pane', async ($, on) => {
    resetCaches()
    stubProcess(on)
    const ran = await $.tool.call({ tool: 'mcp__diagram-skills__show_diagram', source: FLOW, title: 'Pushed', alt: 'Two boxes' })
    expect(ran.deny).toBeUndefined()
    const ui = await $.ui.mount(paneTarget('desktop'))
    expect(await ui.find({ type: 'Text', text: /Pushed/ })).toBeDefined()
    expect(await ui.find({ type: 'Svg' })).toBeDefined()
    await ui.unmount()
  })

  test('with the strict gate, a malformed source is refused in mermaid own words and the pane keeps the previous drawing', async ($, on) => {
    resetCaches()
    const gate = (source: string) => /^(flowchart|sequenceDiagram|classDiagram)/.test(source) && !/(-->\s*$|->>\s*$|\{\s*$)/m.test(source)
      ? VALID
      : { ok: false, reason: 'syntax', message: `Parse error on line 2: ${JSON.stringify(source.slice(0, 12))}` }
    stubProcess(on, { validate: gate })
    const first = await $.tool.call({ tool: 'mcp__diagram-skills__show_diagram', source: FLOW, title: 'First' })
    expect(JSON.stringify(first.result)).toBe('{"ok":true,"validated":true}')
    for (const bad of ['hello world', '', 'sequenceDiagram\n  A->>', 'classDiagram\n  class Animal {\n    +int age']) {
      const ran = await $.tool.call({ tool: 'mcp__diagram-skills__show_diagram', source: bad, title: 'Bad' })
      expect(JSON.stringify(ran.result)).toContain('"ok":false')
      expect(JSON.stringify(ran.result)).toContain('reason')
    }
    const refused = await $.tool.call({ tool: 'mcp__diagram-skills__show_diagram', source: 'classDiagram\n  class Animal {', title: 'Bad' })
    expect(JSON.stringify(refused.result)).toContain('syntax: Parse error on line 2')
    const ui = await $.ui.mount(paneTarget('terminal'))
    expect(await ui.find({ type: 'Text', text: /First/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Bad/ })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /│ A │/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Unvalidated preview/ })).toBeUndefined()
    await ui.unmount()
  })

  test('without jsdom the source still draws, labelled unvalidated, and the result says validated: false', async ($, on) => {
    resetCaches()
    stubProcess(on, {
      validate: () => ({ ok: true, validated: false, reason: 'no-jsdom' }),
      render: source => source.startsWith('sequenceDiagram') ? { ...OK, kind: 'sequence', unicode: '' } : OK,
    })
    const ran = await $.tool.call({ tool: 'mcp__diagram-skills__show_diagram', source: FLOW, title: 'Unchecked' })
    expect(JSON.stringify(ran.result)).toBe('{"ok":true,"validated":false}')
    for (const surface of SURFACES) {
      const ui = await $.ui.mount(paneTarget(surface))
      expect(await ui.find({ type: surface === 'terminal' ? 'Text' : 'Svg', text: surface === 'terminal' ? /│ A │/ : undefined })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /Unvalidated preview.*Open diagram to check/ })).toBeDefined()
      expect(await ui.find({ type: 'Button', text: /Open diagram/ })).toBeDefined()
      await ui.unmount()
    }
    // the cheap guards still hold when nothing parsed the source
    for (const bad of ['hello world', 'sequenceDiagram\n  A->>']) {
      const refused = await $.tool.call({ tool: 'mcp__diagram-skills__show_diagram', source: bad, title: 'Bad' })
      expect(JSON.stringify(refused.result)).toContain('"ok":false')
    }
  })
})

describe('AC4: a missing runtime is stated', () => {
  test('with neither bun nor node, the pane shows the source and the line naming what is missing, with no retry loop', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on, { runtimes: false })
    stubFs(on, { 'f.mmd': FLOW })
    await runDiagram($, 'f.mmd')
    const ui = await $.ui.mount(paneTarget('terminal'))
    expect(await ui.find({ type: 'Code', text: /flowchart TD/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /bun or node/ })).toBeDefined()
    await ui.unmount()
    const again = await $.ui.mount(paneTarget('desktop'))
    expect(await again.find({ type: 'Text', text: /bun or node/ })).toBeDefined()
    await again.unmount()
    expect(helperCalls(runs).length).toBe(0)
    expect(runs.filter(run => run.argv[1] === '--version').length).toBe(2) // bun, node: asked once each, never again
  })
})

describe('AC5: limits hold', () => {
  test('a source over 20,000 characters is not rendered and says why', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on)
    stubFs(on, { 'big.mmd': `flowchart TD\n${'  A --> B\n'.repeat(3000)}` })
    await runDiagram($, 'big.mmd')
    const ui = await $.ui.mount(paneTarget('terminal'))
    expect(await ui.find({ type: 'Text', text: /over 20,000 characters/ })).toBeDefined()
    await ui.unmount()
    expect(helperCalls(runs).length).toBe(0)
  })

  test('more than 8 fences draws 8 and states how many are hidden', async ($, on) => {
    resetCaches()
    stubProcess(on)
    const fences = Array.from({ length: 11 }, (_, i) => `\`\`\`mermaid\nflowchart TD\n  N${i} --> M${i}\n\`\`\``).join('\n\n')
    stubFs(on, { 'many.md': fences })
    const { text } = await runDiagram($, 'many.md')
    expect(text).toContain(`${11 - MAX_DIAGRAMS} more`)
    const ui = await $.ui.mount(paneTarget('terminal'))
    expect(await ui.find({ type: 'Text', text: new RegExp(`1 of ${MAX_DIAGRAMS}`) })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /3 more diagrams in the file not shown/ })).toBeDefined()
    await ui.unmount()
  })

  test('an unsupported type and a render error are cached: a redraw does not re-run the helper', async ($, on) => {
    resetCaches()
    let mode: 'unsupported' | 'error' = 'unsupported'
    const runs = stubProcess(on, {
      render: () => mode === 'unsupported'
        ? { ok: false, reason: 'unsupported-type', kind: 'gantt' }
        : { ok: false, reason: 'render-error', kind: 'flowchart', message: 'bad edge' },
    })
    stubFs(on, { 'a.mmd': 'gantt\n  title A', 'b.mmd': FLOW })
    for (const [file, why] of [['a.mmd', 'unsupported'], ['b.mmd', 'error']] as const) {
      mode = why
      await runDiagram($, file)
      const first = await $.ui.mount(paneTarget('terminal'))
      await first.unmount()
      const before = helperCalls(runs).length
      for (let i = 0; i < 3; i++) {
        const again = await $.ui.mount(paneTarget('desktop'))
        await again.unmount()
      }
      expect(helperCalls(runs).length).toBe(before)
    }
    expect(helperCalls(runs).length).toBe(2) // one run per distinct source, failures included
  })
})

describe('AC6: packaging and loading', () => {
  test('session.start registers the /diagram command and the show_diagram tool', async ($, on) => {
    resetCaches()
    const commands: string[] = []
    const tools: string[] = []
    on('command.register', ($, e) => { commands.push(e.name); return { value: { command: e.name } } })
    on('tool.register', ($, e) => { tools.push(e.name); return { value: { tool: `mcp__diagram-skills__${e.name}` } } })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    await $.session.start({ cwd: '/work', surface: 'terminal', isInteractive: true })
    expect(commands).toEqual(['diagram'])
    expect(tools).toEqual(['show_diagram'])
  })
})

describe('review fixes (DEC-221 a1): helper env, open, cache dir', () => {
  test('the render helper is started with PES10_STDIN=1 (a plugin path with a space, # or % breaks its entry test)', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on)
    stubFs(on, { 'f.mmd': FLOW })
    await runDiagram($, 'f.mmd')
    const ui = await $.ui.mount(paneTarget('terminal'))
    await ui.unmount()
    const helper = helperCalls(runs)
    expect(helper.length).toBe(1)
    expect(helper[0]?.env?.PES10_STDIN).toBe('1')
  })

  test('on macOS the button runs open on exactly the file it wrote', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on, { render: () => ({ ok: false, reason: 'unsupported-type', kind: 'gantt' }) })
    const { writes } = stubFs(on, { 'g.mmd': 'gantt\n  title Plan' })
    await runDiagram($, 'g.mmd')
    const ui = await $.ui.mount(paneTarget('terminal'))
    await ui.press({ key: await buttonKey(ui, /Open diagram/) })
    await ui.unmount()
    expect(writes.length).toBe(1)
    expect(writes[0]?.path).toMatch(/\/\.cache\/diagram-pane\/[0-9a-f]{64}\.html$/)
    const opens = runs.filter(run => run.argv[0] === 'open')
    expect(opens.length).toBe(1)
    expect(opens[0]?.argv).toEqual(['open', writes[0]?.path])
  })

  test('off macOS the button writes the page, runs no open, and shows the path', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on, { system: 'Linux', render: () => ({ ok: false, reason: 'unsupported-type', kind: 'gantt' }) })
    const { writes } = stubFs(on, { 'g.mmd': 'gantt\n  title Plan' })
    await runDiagram($, 'g.mmd')
    const ui = await $.ui.mount(paneTarget('terminal'))
    await ui.press({ key: await buttonKey(ui, /Open diagram/) })
    expect(writes.length).toBe(1)
    expect(runs.some(run => run.argv[0] === 'open')).toBe(false)
    expect(await ui.find({ type: 'Text', text: new RegExp(`Open this file in a browser: ${(writes[0]?.path ?? '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`) })).toBeDefined()
    await ui.unmount()
  })

  test('a symlinked cache directory is refused: nothing is written and the pane says so', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on, { render: () => ({ ok: false, reason: 'unsupported-type', kind: 'gantt' }) })
    const { writes } = stubFs(on, { 'g.mmd': 'gantt\n  title Plan' }, { exists: true, isLink: true })
    await runDiagram($, 'g.mmd')
    const ui = await $.ui.mount(paneTarget('terminal'))
    await ui.press({ key: await buttonKey(ui, /Open diagram/) })
    expect(writes.length).toBe(0)
    expect(runs.some(run => run.argv[0] === 'open')).toBe(false)
    expect(await ui.find({ type: 'Text', text: /symbolic link/ })).toBeDefined()
    await ui.unmount()
  })

  test('the strict gate and the renderer each run once per source, and node is preferred over bun', async ($, on) => {
    resetCaches()
    const runs = stubProcess(on)
    stubFs(on, { 'f.mmd': FLOW })
    await runDiagram($, 'f.mmd')
    for (let i = 0; i < 3; i++) {
      const ui = await $.ui.mount(paneTarget(i % 2 === 0 ? 'terminal' : 'desktop'))
      await ui.unmount()
    }
    expect(runs.filter(run => String(run.argv[1]).endsWith('validate.mjs')).length).toBe(1)
    expect(helperCalls(runs).length).toBe(1)
    expect(runs.filter(run => run.argv[1] === '--version').map(run => run.argv[0])).toEqual(['node'])
  })
})

/** The key of the first Button whose label matches. */
async function buttonKey (ui: { find: (query: { type: 'Button'; text: RegExp }) => Promise<{ key?: string } | undefined> }, label: RegExp): Promise<string> {
  const found = await ui.find({ type: 'Button', text: label })
  if (found?.key === undefined) throw new Error('no such button')
  return found.key
}
