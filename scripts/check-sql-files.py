#!/usr/bin/env python3
"""Post-edit check for CockroachDB anti-patterns in SQL and code files.
Receives JSON on stdin from a PostToolUse hook.

The advisory message is emitted under both ``systemMessage`` (VS Code Copilot /
Claude Code, user-visible) and ``additionalContext`` (GitHub Copilot CLI,
model-visible), so the lint surfaces regardless of which tool runs the hook.
"""

import json
import os
import re
import sys


SQL_EXTENSIONS = {".sql", ".go", ".py", ".js", ".ts", ".java", ".rb"}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # tool_input/toolInput (VS Code / Claude) or toolArgs (Copilot CLI). File
    # path key varies by tool: file_path (Claude), filePath / path (others).
    tool_input = (
        data.get("tool_input")
        or data.get("toolInput")
        or data.get("toolArgs")
        or {}
    )
    if not isinstance(tool_input, dict):
        sys.exit(0)
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or ""
    )
    if not file_path:
        sys.exit(0)

    ext = os.path.splitext(file_path)[1]
    if ext not in SQL_EXTENSIONS:
        sys.exit(0)

    if not os.path.isfile(file_path):
        sys.exit(0)

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        sys.exit(0)

    warnings = []

    if re.search(r"\b(SERIAL|BIGSERIAL)\b", content, re.IGNORECASE):
        warnings.append(
            "SERIAL/BIGSERIAL detected: causes write hotspots in CockroachDB, "
            "use UUID with gen_random_uuid() instead."
        )

    if re.search(r"SELECT\s+\*\s+FROM", content, re.IGNORECASE):
        warnings.append(
            "SELECT * detected: enumerate columns explicitly for CockroachDB "
            "to enable covering index optimizations."
        )

    # Check for missing transaction retry logic in Go files
    if ext == ".go":
        if re.search(r"\bBEGIN\b|sql\.Tx", content):
            if not re.search(r"crdb\.ExecuteTx|retry|40001", content, re.IGNORECASE):
                warnings.append(
                    "Transaction without retry logic detected: CockroachDB requires "
                    "retry on SQLSTATE 40001 (serialization_failure). "
                    "Use crdb.ExecuteTx from cockroach-go."
                )

    # Check for missing retry in Java files
    if ext == ".java":
        if re.search(r"\bBEGIN\b|connection\.setAutoCommit", content):
            if not re.search(r"retry|40001|RetryableExecutor", content, re.IGNORECASE):
                warnings.append(
                    "Transaction without retry logic detected: CockroachDB requires "
                    "retry on SQLSTATE 40001. "
                    "Use cockroachdb-jdbc-wrapper RetryableExecutor."
                )

    if warnings:
        message = "CockroachDB lint: " + " ".join(warnings)
        json.dump({
            "systemMessage": message,
            "additionalContext": message,
        }, sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
