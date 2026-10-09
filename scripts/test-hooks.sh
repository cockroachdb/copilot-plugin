#!/usr/bin/env bash
# Regression tests for the CockroachDB safety hooks (Copilot plugin).
#
# Runs the real commands from .github/hooks/cockroachdb.json (with
# ${CLAUDE_PLUGIN_ROOT} substituted) and asserts the output satisfies BOTH
# hook output contracts, so the hooks work across every Copilot surface:
#   - VS Code Copilot / Claude Code: hookSpecificOutput + systemMessage
#   - GitHub Copilot CLI:            top-level permissionDecision + additionalContext
#
# Also asserts fail-open (exit 0, no block) when the plugin root cannot be
# resolved (issues #20 MAX_PATH and #23 unsubstituted token).
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS="$ROOT/.github/hooks/cockroachdb.json"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

hook_cmd() { # $1=event  $2=root
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hooks"][sys.argv[2]][0]["hooks"][0]["command"].replace("${CLAUDE_PLUGIN_ROOT}", sys.argv[3]))' "$HOOKS" "$1" "$2"
}

# check: desc, event, root, stdin, want_rc, mode(empty|all), space-separated tokens
# The command runs with no plugin-root variables set unless ENV_ROOT is set, in
# which case ENV_NAME (default CLAUDE_PLUGIN_ROOT) is exported with that value,
# the way hosts export the plugin root to hook processes.
check() {
  local desc="$1" event="$2" root="$3" stdin="$4" want_rc="$5" mode="$6" tokens="${7:-}"
  local cmd out rc ok=1
  cmd="$(hook_cmd "$event" "$root")"
  if [ -n "${ENV_ROOT:-}" ]; then
    out="$(printf '%s' "$stdin" | env -u CLAUDE_PLUGIN_ROOT -u COPILOT_PLUGIN_ROOT -u PLUGIN_ROOT "${ENV_NAME:-CLAUDE_PLUGIN_ROOT}=$ENV_ROOT" sh -c "$cmd" 2>/dev/null)"; rc=$?
  else
    out="$(printf '%s' "$stdin" | env -u CLAUDE_PLUGIN_ROOT -u COPILOT_PLUGIN_ROOT -u PLUGIN_ROOT sh -c "$cmd" 2>/dev/null)"; rc=$?
  fi
  [ "$rc" = "$want_rc" ] || ok=0
  if [ "$mode" = "empty" ]; then
    [ -z "$out" ] || ok=0
  else
    for t in $tokens; do printf '%s' "$out" | grep -q "$t" || ok=0; done
  fi
  if [ "$ok" = 1 ]; then echo "ok   - $desc"; else echo "FAIL - $desc (rc=$rc, out=${out:-<empty>})"; fails=$((fails + 1)); fi
}

printf 'CREATE TABLE t (id SERIAL PRIMARY KEY);\n' > "$TMP/a.sql"
printf '# markdown, not sql\n' > "$TMP/a.md"

# PreToolUse: deny must appear in BOTH shapes
check "DROP DATABASE deny (both shapes)" PreToolUse "$ROOT" '{"tool_input":{"sql":"DROP DATABASE x"}}'        0 all "permissionDecision hookSpecificOutput"
check "TRUNCATE deny (both shapes)"       PreToolUse "$ROOT" '{"tool_input":{"sql":"TRUNCATE TABLE t"}}'       0 all "permissionDecision hookSpecificOutput"
check "toolArgs container deny (CLI)"     PreToolUse "$ROOT" '{"toolArgs":{"sql":"DROP DATABASE x"}}'          0 all "permissionDecision"
check "SERIAL warn (both shapes)"         PreToolUse "$ROOT" '{"tool_input":{"sql":"CREATE TABLE t (id SERIAL)"}}' 0 all "systemMessage additionalContext"
check "safe SQL: no output"               PreToolUse "$ROOT" '{"tool_input":{"sql":"SELECT 1"}}'               0 empty

# PostToolUse: lint in BOTH shapes; all path-key aliases; CLI container
check "lint .sql via file_path (both)"    PostToolUse "$ROOT" "{\"tool_input\":{\"file_path\":\"$TMP/a.sql\"}}" 0 all "systemMessage additionalContext"
check "lint via filePath key"             PostToolUse "$ROOT" "{\"tool_input\":{\"filePath\":\"$TMP/a.sql\"}}"  0 all "systemMessage"
check "lint via path key"                 PostToolUse "$ROOT" "{\"tool_input\":{\"path\":\"$TMP/a.sql\"}}"      0 all "systemMessage"
check "lint via toolArgs container (CLI)" PostToolUse "$ROOT" "{\"toolArgs\":{\"filePath\":\"$TMP/a.sql\"}}"    0 all "additionalContext"
check "non-SQL edit: no output"           PostToolUse "$ROOT" "{\"tool_input\":{\"file_path\":\"$TMP/a.md\"}}"  0 empty

# apply_patch edits (GPT models): the input is patch text, so paths come from
# the patch headers, resolved against the payload's cwd.
PATCH='*** Begin Patch\n*** Add File: a.sql\n+CREATE TABLE t (id SERIAL PRIMARY KEY);\n*** End Patch\n'
check "lint apply_patch string input"     PostToolUse "$ROOT" "{\"cwd\":\"$TMP\",\"tool_name\":\"apply_patch\",\"tool_input\":\"$PATCH\"}"          0 all "systemMessage additionalContext"
check "lint apply_patch command input"    PostToolUse "$ROOT" "{\"cwd\":\"$TMP\",\"tool_name\":\"apply_patch\",\"tool_input\":{\"command\":\"$PATCH\"}}" 0 all "systemMessage"

# fail-open when plugin root is missing / unsubstituted (issues #20, #23)
check "PreToolUse fail-open on bad root"  PreToolUse  '${CLAUDE_PLUGIN_ROOT}' '{"tool_input":{"sql":"DROP DATABASE x"}}'                0 empty
check "PostToolUse fail-open on bad root" PostToolUse '${CLAUDE_PLUGIN_ROOT}' "{\"tool_input\":{\"file_path\":\"$TMP/a.sql\"}}"        0 empty

# placeholder left unsubstituted, plugin root exported (Claude Code today; Copilot
# CLI exports CLAUDE_PLUGIN_ROOT, COPILOT_PLUGIN_ROOT, and PLUGIN_ROOT to hooks).
# Single quotes keep the shell from expanding the placeholder, so the bootstrap
# must read the exported variable. PowerShell hosts rewrite the placeholder to
# ${env:NAME}, which single quotes also leave alone.
ENV_ROOT="$ROOT"                           check "PreToolUse uses exported CLAUDE_PLUGIN_ROOT"   PreToolUse  '${CLAUDE_PLUGIN_ROOT}'     '{"tool_input":{"sql":"DROP DATABASE x"}}'         0 all "permissionDecision hookSpecificOutput"
ENV_ROOT="$ROOT" ENV_NAME=COPILOT_PLUGIN_ROOT check "PreToolUse uses exported COPILOT_PLUGIN_ROOT" PreToolUse  '${CLAUDE_PLUGIN_ROOT}'     '{"toolArgs":{"sql":"DROP DATABASE x"}}'           0 all "permissionDecision"
ENV_ROOT="$ROOT" ENV_NAME=PLUGIN_ROOT      check "PreToolUse uses exported PLUGIN_ROOT"          PreToolUse  '${CLAUDE_PLUGIN_ROOT}'     '{"toolArgs":{"sql":"DROP DATABASE x"}}'           0 all "permissionDecision"
ENV_ROOT="$ROOT"                           check "PostToolUse uses exported CLAUDE_PLUGIN_ROOT"  PostToolUse '${CLAUDE_PLUGIN_ROOT}'     "{\"tool_input\":{\"file_path\":\"$TMP/a.sql\"}}" 0 all "systemMessage additionalContext"
ENV_ROOT="$ROOT"                           check "PreToolUse uses exported root in PowerShell form" PreToolUse '${env:CLAUDE_PLUGIN_ROOT}' '{"tool_input":{"sql":"DROP DATABASE x"}}'      0 all "permissionDecision hookSpecificOutput"
ENV_ROOT="$TMP/missing"                    check "PreToolUse fail-open when exported root has no script" PreToolUse '${CLAUDE_PLUGIN_ROOT}' '{"tool_input":{"sql":"DROP DATABASE x"}}'    0 empty

# The SQL hook must match the name Copilot CLI gives the Toolbox tool:
# <server>-<tool>, with no mcp__ prefix.
if python3 -c 'import json,sys; m=json.load(open(sys.argv[1]))["hooks"]["PreToolUse"][0]["matcher"]; sys.exit(0 if "cockroachdb-toolbox-cockroachdb-execute-sql" in m.split("|") else 1)' "$HOOKS"; then
  echo "ok   - PreToolUse matcher includes the Copilot CLI tool name"
else
  echo "FAIL - PreToolUse matcher includes the Copilot CLI tool name"; fails=$((fails + 1))
fi

echo
if [ "$fails" -eq 0 ]; then
  echo "All hook regression tests passed."
else
  echo "$fails test(s) failed."
  exit 1
fi
