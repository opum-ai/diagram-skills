/**
 * The self-contained HTML page the "Open diagram" button writes. Plain TypeScript with no
 * imports, so the engine loads it as part of the mod and Node 24 can import it directly, which
 * is how tests/test_pane_page.py checks the page built around the SHIPPED mermaid.js.
 */

/** Escape the five characters that matter inside the HTML page. */
export function escapeHtml (text: string): string {
  const table: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }
  return text.replace(/[&<>"']/g, c => table[c] ?? c)
}

/** A self-contained HTML page that draws one Mermaid source with the vendored mermaid.js. */
export function htmlPage (source: string, mermaidJs: string, title: string): string {
  const csp = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:"
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="${csp}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(title)}</title>
<style>body{margin:0;padding:24px;background:#fff;color:#18181b;font:14px system-ui,sans-serif}#d{display:flex;justify-content:center}</style>
</head><body><div id="d"></div>
<script>${mermaidJs.replace(/<\/script/gi, '<\\/script')}</script>
<script>
  mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
  mermaid.render('d0', ${JSON.stringify(source).replace(/</g, '\\u003c')}).then(function (r) { document.getElementById('d').innerHTML = r.svg; })
    .catch(function (e) { document.getElementById('d').textContent = 'Could not draw this diagram: ' + e.message; });
</script>
</body></html>
`
}
