# Renderer provenance

`renderer/` is a byte-identical copy of the Mermaid renderer in
[plain-english-styles](https://github.com/opum-ai/plain-english-styles), made
under opum-doc DEC-221 (decision: copy now, extract a shared package when a
third consumer appears). The copy is not edited here, so a later sync is a
comparison and not a guess.

| | |
|---|---|
| Source repository | `opum-ai/plain-english-styles` |
| Source commit | `d2abfe3a16cd490b1ea3c259512ff7475ef76600` (its `dev` at copy time, 2026-10-20) |
| Source tree of `renderer/` at that commit | `b7ff0dc707371b5a6c894a652c817fcbaaa119d6` |
| Copied tree of `renderer/` here | `b7ff0dc707371b5a6c894a652c817fcbaaa119d6` (equal: the copy is byte-identical) |
| `renderer/vendor/elk.bundled.js` sha256 | `20dd2114d683ce758b3ce19bcc56e28a504a617b0d280f760407c37314631d0e` (unmodified `elkjs@0.11.1`) |

Check the copy against the source commit:

```bash
git -C <plain-english-styles checkout> rev-parse d2abfe3a16cd490b1ea3c259512ff7475ef76600:renderer
git rev-parse HEAD:renderer   # equal while the copy is unedited
```

## Licences

The plugin manifest declares `MIT AND EPL-2.0 AND BSD-2-Clause`. The texts and
the per-component notice are in `renderer/licenses/` (`THIRD-PARTY-NOTICES.md`,
`beautiful-mermaid.LICENSE`, `elkjs.LICENSE.md`, `entities.LICENSE`,
`mermaid.LICENSE`):

- beautiful-mermaid 1.1.3: MIT.
- entities 7.0.1: BSD-2-Clause.
- elkjs 0.11.1: EPL-2.0, a file-level weak copyleft. It ships unmodified in its
  own file, `renderer/vendor/elk.bundled.js`, imported and never concatenated.
  If it ever needs a change, that goes back to opum-doc (DEC-169).
- mermaid 11.17.2: MIT, vendored for the HTML fallback only.

`renderer/licenses/THIRD-PARTY-NOTICES.md` is the copied file and says "this
plugin"; read it as this plugin too. It is not edited so that the tree above
stays equal. Its component table and the rules above are the whole set.

## Drift

The copy and plain-english-styles' own may diverge. That is allowed: there is
no CI check that they match.
