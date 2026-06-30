# Contributing to CockroachDB Plugin for GitHub Copilot

Thank you for your interest in contributing. This guide covers the plugin itself: agents, hooks, MCP configuration, and tooling. For contributing **skills**, see the [cockroachdb-skills CONTRIBUTING.md](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/CONTRIBUTING.md) instead; skills are maintained upstream and synced here automatically.

## Getting Started

### Prerequisites

- VS Code with [GitHub Copilot](https://github.com/features/copilot) (agent mode), or the Copilot CLI
- [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox) v1.0.0+ (`brew install mcp-toolbox`)
- Python 3 (for hook scripts, no external dependencies)
- A running CockroachDB instance (local or cloud)

### Setup

```bash
git clone --recurse-submodules https://github.com/cockroachdb/copilot-plugin.git
cd copilot-plugin
```

Set your connection environment variables:

```bash
export COCKROACHDB_HOST=localhost
export COCKROACHDB_PORT=26257
export COCKROACHDB_USER=root
export COCKROACHDB_PASSWORD=
export COCKROACHDB_DATABASE=defaultdb
export COCKROACHDB_SSLMODE=disable
```

Test the plugin locally by opening the repo in VS Code (Copilot reads `.github/skills`, `.github/agents`, `.github/hooks`, and `.vscode/mcp.json` directly), or install it from source with `Chat: Install Plugin From Source`.

## Project Structure

```
plugin.json                # Plugin manifest (version managed by Release Please)
.mcp.json                  # MCP server definitions for plugin installs (mcpServers)
.vscode/mcp.json           # MCP server definitions for workspace use (servers)
tools.yaml                 # MCP Toolbox source and tool definitions
.github/
  plugin/marketplace.json  # Marketplace catalog entry
  agents/                  # Agent files (*.agent.md)
  hooks/cockroachdb.json   # Hook triggers
  skills/                  # Flattened from cockroachdb-skills submodule (do not edit directly)
scripts/
  validate-sql.py          # PreToolUse: blocks dangerous SQL patterns
  check-sql-files.py       # PostToolUse: lints files for anti-patterns
  sync-skills.sh           # Flattens skills into the Copilot layout
submodules/
  cockroachdb-skills/      # Upstream skills submodule
```

## What You Can Contribute

| Area | Examples |
|------|----------|
| **Agents** | New agent personas, improved prompts |
| **Hooks** | New safety checks, additional SQL anti-pattern detection |
| **MCP config** | New backend integrations, connection improvements |
| **Tools** | New tool definitions in `tools.yaml` |
| **Bug fixes** | Path handling, env var defaults, config issues |
| **Documentation** | README improvements, inline comments |

### What belongs elsewhere

- **New skills** go to the [cockroachdb-skills](https://github.com/cockroachlabs/cockroachdb-skills) repo
- **Toolbox bugs** go to the [MCP Toolbox](https://github.com/googleapis/mcp-toolbox) repo

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b fix/describe-your-change
   ```

2. **Make your changes**, matching the existing code style.

3. **Test hook scripts** (if modified). VS Code passes camelCase tool inputs while Claude Code uses snake_case, so test both:
   ```bash
   echo '{"tool_input":{"sql":"SELECT 1"}}' | python3 scripts/validate-sql.py
   echo '{"tool_input":{"file_path":"test.sql"}}' | python3 scripts/check-sql-files.py
   echo '{"tool_input":{"filePath":"test.sql"}}' | python3 scripts/check-sql-files.py
   ```

4. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/) and open a Pull Request against `main`.

## Commit Conventions

This repo uses [Release Please](https://github.com/googleapis/release-please) for automated versioning and changelogs.

| Prefix | Effect | Example |
|--------|--------|---------|
| `fix:` | Patch release (0.1.x) | `fix: handle empty SQL in validate hook` |
| `feat:` | Minor release (0.x.0) | `feat: add index validation hook` |
| `docs:` | No release | `docs: update README with new backend` |
| `chore:` | No release | `chore: update submodule reference` |

Never bump the version in `plugin.json` or `.release-please-manifest.json` manually; Release Please owns these files.

## Guidelines

### Agents

- Agent files live in `.github/agents/` and use the `.agent.md` extension.
- Use YAML frontmatter with `name` and `description`; Copilot selects an agent based on its description and task context.
- Avoid pinning a Claude-only `model` value so the user's selected Copilot model applies.

### Hooks

- Hook scripts must be Python 3 with **no external dependencies** (stdlib only).
- Read JSON from stdin, write JSON to stdout. PreToolUse blocks a tool with `hookSpecificOutput.permissionDecision` set to `deny`.
- VS Code ignores hook matchers (hooks run on every tool invocation), so scripts must exit early when the input is not relevant. VS Code also passes camelCase tool inputs (`filePath`) where Claude uses snake_case (`file_path`); accept both.
- Load hook scripts through the long-path-safe bootstrap below instead of passing the script path straight to `python3`. The plugin root can resolve to a deeply nested cache path that exceeds the 260-character `MAX_PATH` limit on Windows; passing the path directly makes Python fail to open the script. The bootstrap loads the script with `runpy`, prefixes the path with the `\\?\` long-path escape on Windows, keeps it inside single quotes so paths with spaces still work, and uses `; exit 0` so a failed bootstrap never disrupts editing:
  ```json
  "command": "python3 -c 'import sys, os, runpy; p = os.path.normpath(r\"${CLAUDE_PLUGIN_ROOT}/scripts/your-script.py\"); p = (\"\\\\?\\\\\" + p) if os.name == \"nt\" else p; runpy.run_path(p, run_name=\"__main__\")'; exit 0"
  ```

### MCP Configuration

- `.mcp.json` (top-level `mcpServers`) is used by plugin installs; `.vscode/mcp.json` (top-level `servers`) is used in workspaces. Keep both in sync when adding a backend.
- Use `${ENV_VAR}` syntax for environment variable references.
- The `tools.yaml` file uses Toolbox v1.1.0 map-based format with `${VAR:default}` syntax for defaults.

### Skills

Skills are synced from the upstream [cockroachdb-skills](https://github.com/cockroachlabs/cockroachdb-skills) submodule by a [weekly CI workflow](.github/workflows/update-skills.yml), then flattened into `.github/skills/` by `scripts/sync-skills.sh`. Do not edit files under `.github/skills/` directly; contribute new skills to the upstream repo instead.

## Reporting Issues

- Use [GitHub Issues](https://github.com/cockroachdb/copilot-plugin/issues) for bugs and feature requests.
- Include your plugin version (`plugin.json` -> `version`), VS Code and Copilot versions, and OS.
- For connection issues, include the MCP backend you are using (Toolbox or Cloud MCP).

## License

By contributing, you agree that your contributions will be licensed under the [Apache-2.0 License](LICENSE).
