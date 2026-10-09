#!/usr/bin/env python3
"""Post-edit check for CockroachDB anti-patterns in SQL and code files.
Receives JSON on stdin from a PostToolUse hook.

The advisory message is emitted under both ``systemMessage`` (VS Code Copilot /
Claude Code, user-visible) and ``additionalContext`` (GitHub Copilot CLI,
model-visible), so the lint surfaces regardless of which tool runs the hook.

OpenAI Codex and Copilot edit files with ``apply_patch``, whose input is patch
text (in ``tool_input.command`` for Codex, as the whole ``tool_input`` string
for Copilot) with no file path key, so the paths come from the patch headers.
Codex also rejects unknown top-level output keys, so the Codex hooks.json
passes ``--codex``.
"""

import json
import os
import re
import sys


SQL_EXTENSIONS = {".sql", ".go", ".py", ".js", ".ts", ".java", ".rb"}
CODEX = "--codex" in sys.argv[1:]
# apply_patch file headers (codex-rs/apply-patch/src/parser.rs).
PATCH_FILE_MARKERS = ("*** Add File: ", "*** Update File: ", "*** Move to: ")


def patch_file_paths(patch_text, base_dir):
    paths = []
    for line in patch_text.splitlines():
        for marker in PATCH_FILE_MARKERS:
            if line.startswith(marker):
                path = line[len(marker):].strip()
                if path and base_dir and not os.path.isabs(path):
                    path = os.path.join(base_dir, path)
                if path:
                    paths.append(path)
    return paths


def candidate_files(data):
    # tool_input/toolInput (Codex / VS Code / Claude) or toolArgs (Copilot CLI).
    # File path key varies by tool: file_path (Claude), filePath / path (others).
    tool_input = (
        data.get("tool_input")
        or data.get("toolInput")
        or data.get("toolArgs")
        or {}
    )
    base_dir = data.get("cwd") or ""
    # Copilot passes apply_patch input as the raw patch text, and its camelCase
    # format can pass other arguments as a JSON string.
    if isinstance(tool_input, str):
        if "*** Begin Patch" in tool_input:
            return patch_file_paths(tool_input, base_dir)
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            return []
    if not isinstance(tool_input, dict):
        return []
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or ""
    )
    if file_path:
        return [file_path]
    command = tool_input.get("command")
    if isinstance(command, str) and "*** Begin Patch" in command:
        return patch_file_paths(command, base_dir)
    return []


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)
    if not isinstance(data, dict):
        sys.exit(0)

    findings = []
    for file_path in dict.fromkeys(candidate_files(data)):
        warnings = lint(file_path)
        if warnings:
            findings.append((file_path, warnings))
    if not findings:
        sys.exit(0)

    if len(findings) == 1:
        message = "CockroachDB lint: " + " ".join(findings[0][1])
    else:
        message = "CockroachDB lint: " + " ".join(
            f"{os.path.basename(path)}: {' '.join(warnings)}"
            for path, warnings in findings
        )
    if CODEX:
        payload = {
            "systemMessage": message,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": message,
            },
        }
    else:
        payload = {"systemMessage": message, "additionalContext": message}
    json.dump(payload, sys.stdout)
    sys.exit(0)


def lint(file_path):
    ext = os.path.splitext(file_path)[1]
    if ext not in SQL_EXTENSIONS:
        return []

    if not os.path.isfile(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return []

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

    return warnings


if __name__ == "__main__":
    main()
