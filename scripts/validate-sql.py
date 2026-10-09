#!/usr/bin/env python3
"""Pre-execution SQL validation for CockroachDB.
Blocks dangerous patterns before they reach the database.
Receives JSON on stdin from a PreToolUse hook.

Output is written so both hook contracts understand it:
- GitHub Copilot CLI reads a top-level ``permissionDecision`` (and
  ``additionalContext`` for guidance).
- VS Code Copilot and Claude Code read ``hookSpecificOutput`` (and
  ``systemMessage``).
Emitting both keeps this one script working across all three surfaces.

OpenAI Codex rejects any top-level key it does not know (its hook output
schema uses deny_unknown_fields), so the Codex hooks.json passes ``--codex``
and this script then emits only the Codex shape.
"""

import json
import re
import sys

CODEX = "--codex" in sys.argv[1:]


def deny(reason):
    hook_output = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
    if CODEX:
        payload = {"hookSpecificOutput": hook_output}
    else:
        payload = {
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "hookSpecificOutput": hook_output,
        }
    json.dump(payload, sys.stdout)
    sys.exit(0)


def warn(message):
    if CODEX:
        payload = {
            "systemMessage": message,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": message,
            },
        }
    else:
        payload = {"systemMessage": message, "additionalContext": message}
    json.dump(payload, sys.stdout)
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if not isinstance(data, dict):
        sys.exit(0)

    # tool_input (Codex / VS Code / Claude) or toolArgs (Copilot CLI camelCase,
    # which can arrive as a JSON string)
    tool_input = (
        data.get("tool_input") or data.get("toolInput") or data.get("toolArgs") or {}
    )
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            sys.exit(0)
    if not isinstance(tool_input, dict):
        sys.exit(0)
    sql = tool_input.get("sql", "") or tool_input.get("statement", "")
    if not sql:
        sys.exit(0)

    sql_upper = sql.upper()

    if re.search(r"DROP\s+DATABASE", sql_upper):
        deny("DROP DATABASE is blocked by CockroachDB plugin safety hook. "
             "Use DROP TABLE for individual tables instead.")

    if re.search(r"^\s*TRUNCATE\s", sql_upper, re.MULTILINE):
        deny("TRUNCATE is blocked by CockroachDB plugin safety hook. "
             "Use DELETE with a WHERE clause for targeted row removal.")

    if re.search(r"\b(SERIAL|BIGSERIAL)\b", sql_upper):
        warn("WARNING: SERIAL/BIGSERIAL creates sequential IDs that cause write "
             "hotspots in CockroachDB. Use UUID with gen_random_uuid() instead: "
             "id UUID PRIMARY KEY DEFAULT gen_random_uuid()")

    ddl_count = len(re.findall(
        r"(CREATE|ALTER|DROP)\s+(TABLE|INDEX|VIEW|SEQUENCE|TYPE|SCHEMA)",
        sql_upper
    ))
    if ddl_count > 1:
        warn("WARNING: Multiple DDL statements detected. CockroachDB supports "
             "only one DDL per transaction. Split into separate statements or "
             "use SET autocommit_before_ddl = true.")

    sys.exit(0)


if __name__ == "__main__":
    main()
