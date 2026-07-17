# Agent instructions for copilot-plugin

Guidance for AI coding assistants (and new contributors) working in this repo. It complements [CONTRIBUTING.md](./CONTRIBUTING.md).

## What this repo is

The CockroachDB plugin for GitHub Copilot: plugin manifest (`plugin.json` at the root), MCP configs, agents (`.github/agents/*.agent.md`), skills (`.github/skills/`), and safety hooks (`.github/hooks/cockroachdb.json` + `scripts/`).

## Rules that prevent breakage

- **Never edit `.github/skills/` by hand.** Skills come from the [cockroachdb-skills](https://github.com/cockroachlabs/cockroachdb-skills) submodule via `scripts/sync-skills.sh`, which flattens the domain-grouped upstream tree (Copilot requires `.github/skills/<name>/` with the directory equal to the frontmatter `name:`), dereferences symlinks, and runs `scripts/transform-skills-for-copilot.py`. Edit the sync or transform scripts, or contribute upstream, never the synced output.
- **The transform exists to pass the awesome-copilot marketplace lint** (`@microsoft/vally`), which enforces three things per skill: no file links outside the skill directory, every file under `references/` reachable from SKILL.md, and SKILL.md at most 500 lines. Two subtleties the transform already handles, so keep them intact: link reachability ignores links inside fenced code blocks (an unbalanced fence count hides everything after it), and the over-length split must only cut at `## ` headers outside code fences.
- **Two MCP configs with different top-level keys, both on purpose:** `.mcp.json` (plugin installs) uses `mcpServers`; `.vscode/mcp.json` (workspace use) uses `servers`. Keep them in sync when adding a backend.
- **Hook scripts emit both output contracts** (top-level `permissionDecision`/`additionalContext` for the Copilot CLI, `hookSpecificOutput`/`systemMessage` for VS Code and Claude Code) and accept `tool_input`, `toolInput`, or `toolArgs` with `file_path`, `filePath`, or `path`. VS Code ignores hook matchers and runs hooks on every tool call, so scripts must exit fast and silent on irrelevant input. Keep the `runpy` long-path bootstrap and trailing `; exit 0` in hook commands.
- **Agent frontmatter is `name` and `description` only.** Do not add Claude-only fields like `model:` or `color:`; the user's selected Copilot model should apply.
- **Never bump versions by hand.** Release Please owns `version` in `plugin.json`, `.release-please-manifest.json`, and `CHANGELOG.md`. Conventional commits: `fix:`/`feat:` cut a release, `chore:`/`docs:` do not.
- **No counts in descriptions.** Counts go stale; name the things instead.

## Testing

```bash
bash scripts/test-hooks.sh
```

CI runs this on any PR touching `.github/hooks/` or `scripts/`. After a skills sync, verify the marketplace lint the way the marketplace does: install `@microsoft/vally` and call `runLint({ rootPath })` on the repo root; expect every skill to pass.

## Writing style

Commit messages and PR bodies in a plain human voice: conventional-commit prefixes, no AI attribution trailers, plain punctuation.
