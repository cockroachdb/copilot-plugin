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

The skills, agents, and hooks work without any setup. Each of the plugin's MCP servers needs its own:

- **`cockroachdb-toolbox`** (any self-hosted or Cloud cluster) needs [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox) v1.0.0 or later on your `PATH`, and a running CockroachDB cluster it can reach. Toolbox connects when the session starts, so without a reachable cluster this server fails to start. If you don't run a cluster, [turn the server off](#turn-off-a-server-you-dont-use).
- **`cockroachdb-cloud`** (CockroachDB Cloud) needs a CockroachDB Cloud account, and signs in with OAuth through your browser.

#### Install MCP Toolbox

macOS or Linux:

```bash
brew install mcp-toolbox
```

Windows: download `toolbox.exe` into a folder on your `PATH`. In PowerShell, set the version to the latest one on the [Toolbox releases page](https://github.com/googleapis/mcp-toolbox/releases), and use `windows/arm64` in the URL on Arm devices:

```powershell
$VERSION = "1.14.0"
curl.exe -o toolbox.exe "https://storage.googleapis.com/mcp-toolbox-for-databases/v$VERSION/windows/amd64/toolbox.exe"
```

Restart VS Code or your terminal after changing your `PATH`, then confirm the install with `toolbox --version`. For other platforms, the container image, and building from source, see [Install Toolbox](https://github.com/googleapis/mcp-toolbox#install-toolbox).

## Configuration

### Self-hosted clusters (MCP Toolbox)

The `cockroachdb-toolbox` server reads its connection settings from environment variables, which Copilot passes through to it. Each one is optional, and an unset variable falls back to the default in [`tools.yaml`](tools.yaml):

| Variable               | Default     | Notes                                                                        |
|------------------------|-------------|------------------------------------------------------------------------------|
| `COCKROACHDB_HOST`     | `localhost` |                                                                              |
| `COCKROACHDB_PORT`     | `26257`     |                                                                              |
| `COCKROACHDB_USER`     | `root`      |                                                                              |
| `COCKROACHDB_PASSWORD` | (empty)     |                                                                              |
| `COCKROACHDB_DATABASE` | `defaultdb` |                                                                              |
| `COCKROACHDB_SSLMODE`  | `require`   | Use `disable` for a local `--insecure` cluster, `verify-full` for production |

Set them in the environment Copilot starts from. On macOS or Linux, add them to your shell profile:

```bash
export COCKROACHDB_HOST="your-cluster-host"
export COCKROACHDB_PORT="26257"
export COCKROACHDB_USER="your-user"
export COCKROACHDB_PASSWORD="your-password"
export COCKROACHDB_DATABASE="your-database"
export COCKROACHDB_SSLMODE="verify-full"
```

On Windows, set them as user environment variables, for example `setx COCKROACHDB_HOST "your-cluster-host"`, then restart VS Code or your terminal.

For a CockroachDB Cloud cluster, find the connection details in the [Cloud Console](https://cockroachlabs.cloud/).

Toolbox runs in read-only mode: `SELECT`, `SHOW`, and `EXPLAIN` work, and writes and schema changes are rejected. To allow writes, run Toolbox with your own copy of [`tools.yaml`](tools.yaml) that sets `enableWriteMode: true`, configured as your own MCP server, and turn off the plugin's `cockroachdb-toolbox` server.

### CockroachDB Cloud

The `cockroachdb-cloud` server connects to the [managed MCP server](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server) that Cockroach Labs hosts. The consent screen asks you to grant read access, write access, or both. The connection can reach every cluster your CockroachDB Cloud role allows.

To limit a connection to one cluster, add your own server entry with an `mcp-cluster-id` header, as shown under [Alternative MCP Backends](#alternative-mcp-backends). When you open this repository as a workspace, `.vscode/mcp.json` sends the header with `COCKROACHDB_CLUSTER_ID` if you set it.

### Turn off a server you don't use

Copilot starts both MCP servers in every session. If you only use one of them, turn off the other:

- **Copilot CLI:** run `/mcp disable cockroachdb-toolbox` (or `cockroachdb-cloud`) in a session, and the choice persists across sessions. To skip a server for a single session, start Copilot with `--disable-mcp-server cockroachdb-toolbox`.
- **VS Code:** in the Extensions view, right-click the server under **MCP SERVERS - INSTALLED** and select **Disable**.

### MCP configuration files

The plugin ships two MCP configs, because Copilot uses different keys in each context:

- `.mcp.json` (top-level `mcpServers`) is read when the plugin is installed from a marketplace.
- `.vscode/mcp.json` (top-level `servers`) is read when the repository is opened as a workspace.

The default backend is the **MCP Toolbox** over stdio. The managed **CockroachDB Cloud MCP Server** is also configured.

### Alternative MCP Backends

<details>
<summary><strong>CockroachDB Cloud MCP Server</strong> (OAuth/API key)</summary>

The official [managed MCP server](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/) is hosted by Cockroach Labs and requires no infrastructure setup. The plugin already includes it as `cockroachdb-cloud`; add your own entry to limit it to one cluster or to use a service account API key. With OAuth 2.1 (PKCE), the consent screen asks you to grant read access, write access, or both (scopes `mcp:read` and `mcp:write`).

Give your entry its own name, such as `cockroachdb-cloud-cluster`, so it doesn't clash with the plugin's `cockroachdb-cloud` server, and turn the plugin's server off. In VS Code (`mcp.json`):

```json
{
  "servers": {
    "cockroachdb-cloud-cluster": {
      "type": "http",
      "url": "https://cockroachlabs.cloud/mcp",
      "headers": {
        "mcp-cluster-id": "{your-cluster-id}"
      }
    }
  }
}
```

With the Copilot CLI:

```bash
copilot mcp add --transport http cockroachdb-cloud-cluster https://cockroachlabs.cloud/mcp --header "mcp-cluster-id: {your-cluster-id}"
```

Leave out the `mcp-cluster-id` header to reach every cluster your user or service account can access. For headless or autonomous agents, add an `Authorization: Bearer {your-service-account-api-key}` header. See the [quickstart guide](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server) for detailed setup.
</details>

<details>
<summary><strong>CockroachDB MCP Server</strong> (first-party, self-hosted)</summary>

[CockroachDB MCP Server](https://github.com/cockroachdb/cockroachdb-mcp-server) is Cockroach Labs' own MCP server for clusters you run yourself. By default it registers only read-only tools, such as `list_databases`, `list_tables`, `get_table_schema`, `select_query`, `explain_query`, `show_statement`, and `show_running_queries`. Setting `CRDB_MCP_ENABLE_WRITE_QUERIES=true` adds `create_database`, `create_table`, `insert_rows`, `update_rows`, and `delete_rows`, and the server refuses an `UPDATE` or `DELETE` without a `WHERE` clause.

**Install:** `go install github.com/cockroachdb/cockroachdb-mcp-server@latest` (Go 1.26+). Linux and Windows binaries and a Docker image are listed on the [releases page](https://github.com/cockroachdb/cockroachdb-mcp-server/releases). There are no prebuilt macOS binaries, so on macOS use `go install` or Docker.

**Configure** with certificate authentication (recommended). In VS Code (`mcp.json`):

```json
{
  "servers": {
    "cockroachdb-mcp-server": {
      "command": "cockroachdb-mcp-server",
      "env": {
        "CRDB_HOST": "your-cluster-host",
        "CRDB_USERNAME": "ai_agent",
        "CRDB_SSL_MODE": "verify-full",
        "CRDB_SSL_CA_PATH": "/certs/ca.crt",
        "CRDB_SSL_CERTFILE": "/certs/client.ai_agent.crt",
        "CRDB_SSL_KEYFILE": "/certs/client.ai_agent.key"
      }
    }
  }
}
```

For a local `--insecure` development cluster with the Copilot CLI:

```bash
copilot mcp add cockroachdb-mcp-server --env CRDB_DATABASE_URL="postgresql://root@localhost:26257/defaultdb?sslmode=disable" --env CRDB_MCP_ALLOW_INSECURE_DB=true -- cockroachdb-mcp-server
```

Password authentication is off unless you set `CRDB_MCP_ALLOW_PASSWORD_AUTH=true`. If the server doesn't start, give the binary's absolute path as the `command`, since apps launched outside a terminal may not search `~/go/bin`. The plugin's SQL safety hook applies to the bundled Toolbox server; this server enforces its own guardrails. See the [server's README](https://github.com/cockroachdb/cockroachdb-mcp-server#configuration) for every setting.
</details>

<details>
<summary><strong>ccloud CLI</strong> (cluster lifecycle, backups, DR, networking)</summary>

The [`ccloud` CLI](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-cli-database-automation/) is an agent-ready command-line tool for full cluster lifecycle management. Agents call ccloud directly via shell commands (not MCP protocol); every command supports `-o json` for structured output.

**Install:** `brew install cockroachdb/tap/ccloud`

See the [ccloud reference](https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-reference) for the full command list.
</details>

## What's Included

### MCP Backends

| Backend                  | Status    | Transport       | Use Case                                                                                                                              |
|--------------------------|-----------|-----------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `cockroachdb-toolbox`    | Active    | stdio           | Any CockroachDB cluster via [MCP Toolbox](https://github.com/googleapis/mcp-toolbox)                                                  |
| `cockroachdb-cloud`      | Active    | Streamable HTTP | [Managed MCP Server](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/), CockroachDB Cloud (OAuth/API key) |
| `cockroachdb-mcp-server` | Available | stdio, HTTPS    | First-party server for self-hosted clusters (not shipped; add it yourself, see Alternative MCP Backends)                              |

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
