# CockroachDB Plugin for GitHub Copilot

[![Release Please](https://github.com/cockroachdb/copilot-plugin/actions/workflows/release-please.yml/badge.svg)](https://github.com/cockroachdb/copilot-plugin/actions/workflows/release-please.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Connect [GitHub Copilot](https://github.com/features/copilot) directly to your CockroachDB clusters for hands-on database work: explore schemas, write optimized SQL, debug queries, and manage distributed database clusters. This plugin provides tools across MCP backends (self-hosted MCP Toolbox and managed CockroachDB Cloud MCP Server), specialized agents (DBA, Developer, Operator), skills across operational domains, and built-in safety hooks.

## Installation

Install from a plugin marketplace. VS Code reads the `copilot-plugins` and `awesome-copilot` marketplaces by default; add this repository with the `chat.plugins.marketplaces` setting, then open the Extensions view, search `@agentPlugins`, and install the `cockroachdb` plugin.

### Install from source

Run `Chat: Install Plugin From Source` from the Command Palette and point it at this repository, or with the Copilot CLI:

```bash
copilot plugin install cockroachdb/copilot-plugin
```

### Use as workspace customizations

Clone the repository into your project. Copilot reads `.github/skills`, `.github/agents`, and `.github/hooks` directly, and `.vscode/mcp.json` provides the cluster connection.

### Prerequisites

This plugin connects to CockroachDB via MCP (Model Context Protocol) using [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox) (v1.0.0+):

```bash
brew install mcp-toolbox
```

## Configuration

Set environment variables for your CockroachDB connection:

```bash
export COCKROACHDB_HOST="your-cluster-host"
export COCKROACHDB_PORT="26257"
export COCKROACHDB_USER="your-user"
export COCKROACHDB_PASSWORD="your-password"
export COCKROACHDB_DATABASE="your-database"
export COCKROACHDB_SSLMODE="verify-full"
```

For CockroachDB Cloud, find connection details in the [Cloud Console](https://cockroachlabs.cloud/).

### MCP configuration files

The plugin ships two MCP configs, because Copilot uses different keys in each context:

- `.mcp.json` (top-level `mcpServers`) is read when the plugin is installed from a marketplace.
- `.vscode/mcp.json` (top-level `servers`) is read when the repository is opened as a workspace.

The default backend is the **MCP Toolbox** over stdio. The managed **CockroachDB Cloud MCP Server** is also configured.

### Alternative MCP Backends

<details>
<summary><strong>CockroachDB Cloud MCP Server</strong> (OAuth/API key)</summary>

The official [managed MCP server](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/) is hosted by Cockroach Labs and requires no infrastructure setup. Authenticate via OAuth 2.1 (PKCE) or a service account API key. Read-only by default; write access requires explicit consent.

```json
{
  "servers": {
    "cockroachdb-cloud": {
      "type": "http",
      "url": "https://cockroachlabs.cloud/mcp",
      "headers": {
        "mcp-cluster-id": "{your-cluster-id}"
      }
    }
  }
}
```

For headless or autonomous agents, add an `Authorization: Bearer {your-service-account-api-key}` header. See the [quickstart guide](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server) for detailed setup.
</details>

<details>
<summary><strong>ccloud CLI</strong> (cluster lifecycle, backups, DR, networking)</summary>

The [`ccloud` CLI](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-cli-database-automation/) is an agent-ready command-line tool for full cluster lifecycle management. Agents call ccloud directly via shell commands (not MCP protocol); every command supports `-o json` for structured output.

**Install:** `brew install cockroachdb/tap/ccloud`

See the [ccloud reference](https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-reference) for the full command list.
</details>

## What's Included

### MCP Backends

| Backend                | Status    | Transport       | Use Case                                                                                                                              |
|------------------------|-----------|-----------------|--------------------------------------------------------------------------------------------------------------------------------------|
| `cockroachdb-toolbox`  | Active    | stdio           | Any CockroachDB cluster via [MCP Toolbox](https://github.com/googleapis/mcp-toolbox)                                                  |
| `cockroachdb-cloud`    | Active    | Streamable HTTP | [Managed MCP Server](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/), CockroachDB Cloud (OAuth/API key) |

### Skills

Skills are sourced from the [`cockroachdb-skills`](https://github.com/cockroachlabs/cockroachdb-skills) submodule, a single source of truth shared across CockroachDB agent integrations. Copilot requires a flat skill layout, so `scripts/sync-skills.sh` flattens the domain-grouped upstream tree into `.github/skills/<skill>/`. A [weekly CI workflow](.github/workflows/update-skills.yml) auto-detects upstream changes and opens a PR to update.

| Domain                          | Examples                                                     |
|---------------------------------|--------------------------------------------------------------|
| **Query & Schema Design**       | cockroachdb-sql                                              |
| **Observability & Diagnostics** | profiling-statement-fingerprints, triaging-live-sql-activity |
| **Security & Governance**       | auditing-cloud-cluster-security, hardening-user-privileges   |
| **Onboarding & Migrations**     | molt-fetch, molt-verify, molt-replicator                     |
| **Operations & Lifecycle**      | managing-cluster-capacity, upgrading-cluster-version         |

### Agents

| Agent                   | Description                                                                       |
|-------------------------|----------------------------------------------------------------------------------|
| `cockroachdb-dba`       | CockroachDB DBA expert: performance tuning, schema review, cluster diagnostics    |
| `cockroachdb-developer` | Application developer expert: ORM config, retry logic, transaction patterns       |
| `cockroachdb-operator`  | Operator/SRE expert: cluster operations, monitoring, backups, scaling, incidents  |

Agents are discovered from `.github/agents/`. Copilot selects them based on task context, or you can pick one from the agent picker in agent mode.

### Hooks

| Hook              | Trigger              | What It Does                                                                          |
|-------------------|----------------------|--------------------------------------------------------------------------------------|
| `validate-sql`    | Before SQL execution | Blocks DROP DATABASE, TRUNCATE; warns on SERIAL, multi-DDL transactions               |
| `check-sql-files` | After a file edit    | Scans SQL/code files for CockroachDB anti-patterns (SERIAL, SELECT *, missing retry)  |

Hooks run as Python scripts (Python 3, no external dependencies) and provide automated safety guardrails. VS Code runs hooks on every tool invocation regardless of the matcher, and the scripts exit early when the input is not relevant.

**Windows note:** the hooks invoke `python3`, so make sure a `python3` is on your `PATH`. The python.org installer creates `python.exe` and the `py` launcher but not `python3.exe`; on those installs the hooks safely no-op (they never block editing, but the safety checks will not run). Installing Python from the Microsoft Store, or adding a `python3` alias, enables them. You do not need to turn on Windows long-path support: the hooks load their scripts through the `\\?\` long-path prefix, so they work no matter how deep the plugin cache path is.

## Development

Clone the repository:

```bash
git clone --recurse-submodules https://github.com/cockroachdb/copilot-plugin.git
cd copilot-plugin
```

Resync skills from the submodule after an update:

```bash
scripts/sync-skills.sh submodules/cockroachdb-skills/skills
```

### Project Structure

```
plugin.json                      # Plugin manifest (Copilot agent plugin)
.mcp.json                        # MCP server config for plugin installs (mcpServers)
.vscode/mcp.json                 # MCP server config for workspace use (servers)
tools.yaml                       # Toolbox source & tool definitions
.github/
  plugin/marketplace.json        # Marketplace catalog for distribution
  agents/
    cockroachdb-dba.agent.md     # DBA agent
    cockroachdb-developer.agent.md
    cockroachdb-operator.agent.md
  hooks/
    cockroachdb.json             # Hook configuration
  skills/                        # Skills flattened from the cockroachdb-skills submodule
  workflows/
    update-skills.yml            # Weekly submodule sync
    release-please.yml           # Automated releases
scripts/
  validate-sql.py                # SQL validation hook
  check-sql-files.py             # Anti-pattern linter hook
  sync-skills.sh                 # Flatten skills into the Copilot layout
submodules/
  cockroachdb-skills/            # Shared skills submodule
assets/
  logo.svg                       # Plugin logo
```

## Releasing

This repo uses [Release Please](https://github.com/googleapis/release-please) for automated releases.

1. Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`) on `main`
2. Release Please opens a Release PR with version bump and changelog
3. Merge the Release PR to publish

## Links

- [CockroachDB Documentation](https://www.cockroachlabs.com/docs/)
- [CockroachDB Cloud Console](https://cockroachlabs.cloud/)
- [Managed MCP Server Blog Post](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/)
- [Cloud MCP Quickstart Guide](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server)
- [Agent Skills in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Agent Plugins in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-plugins)
- [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox)
- [Report Issues](https://github.com/cockroachdb/copilot-plugin/issues)

## License

[Apache-2.0](LICENSE)
