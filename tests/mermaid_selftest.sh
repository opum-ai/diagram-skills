#!/usr/bin/env bash
# Prove the Mermaid parse gate both ways on every run: broken diagrams must
# fail, their fixed versions must pass, and a Markdown file with one broken
# fence among valid ones must fail the whole file. A checker that silently
# stops failing (e.g. a broken jsdom shim reporting environment errors) turns
# this red instead of letting the gate pass while comparing nothing.
set -u
cd "$(dirname "$0")/.."
C="node skills/diagram-review/scripts/mermaid-check.mjs"
F=tests/fixtures/mermaid
rc=0
expect() { # expect <exit-code> <label> <args...>
  local want=$1 label=$2; shift 2
  $C "$@" >/tmp/selftest.$$ 2>&1; local got=$?
  if [ "$got" -eq "$want" ]; then echo "ok   $label (exit $got)"; else echo "FAIL $label (exit $got, wanted $want)"; cat /tmp/selftest.$$; rc=1; fi
}
expect 0 "valid diagrams parse"                       "$F/pass"
expect 0 "every broken diagram fails with a syntax error" --expect-fail "$F/fail"
expect 1 "broken diagrams fail the gate"              "$F/fail"
expect 1 "one broken fence fails a Markdown file"     "$F/markdown"
expect 0 "a fence nested in another fence is not a diagram" "$F/nested"
rm -f /tmp/selftest.$$
[ $rc -eq 0 ] && echo "gate self-test OK" || echo "gate self-test FAILED"
exit $rc
