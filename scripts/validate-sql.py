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
"""

import json
import re
import sys


def deny(reason):
    json.dump({
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }, sys.stdout)
    sys.exit(0)


def warn(message):
    json.dump({
        "systemMessage": message,
        "additionalContext": message,
    }, sys.stdout)
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # tool_input (VS Code / Claude) or toolArgs (Copilot CLI camelCase)
    tool_input = data.get("tool_input") or data.get("toolArgs") or {}
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
