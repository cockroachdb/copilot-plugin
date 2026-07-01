# Additional details

## Findings

### Network Security
- [PASS|WARN|FAIL|N/A] IP allowlist: <details>
- [PASS|WARN|INFO|N/A] Private endpoints: <details>
- [PASS|WARN|N/A] HBA configuration: <details>

### Authentication & SSO
- [PASS|FAIL|N/A] Cloud Console SSO: <details>
- [PASS|FAIL] Database SSO (OIDC): <details>
- [PASS|INFO] Database SSO (LDAP/AD): <details>
- [PASS|FAIL|N/A] SCIM 2.0 provisioning: <details>
- [PASS|FAIL] Auto user provisioning: <details>

### Authorization
- [PASS|WARN|FAIL] Admin user count: X users with admin role
- [PASS|FAIL] PUBLIC role privileges: <details>

### Encryption
- [PASS|FAIL|INFO|N/A] CMEK: <details>
- [PASS|FAIL|WARN|N/A] Enterprise Encryption: <details>
- [PASS|FAIL|N/A] TLS: <details>
- [INFO] Cryptographic posture: TLS version, PQC support, key size

### Audit Logging
- [PASS|WARN|FAIL] Audit log configuration: <details>

### Backup & Recovery
- [PASS|INFO|N/A] Managed backups: <details>
- [PASS|WARN|FAIL|N/A] Self-managed backups: <details>

### Cluster Configuration
- [INFO] Version: vXX.X.X
- [INFO] Plan: Standard | Advanced | Self-hosted
- [INFO] Regions: <list>
```

**Status markers:** `[PASS]`, `[WARN]`, `[FAIL]`, `[INFO]`, `[N/A]`. Use `[N/A]` for checks that don't apply to the deployment model. Append severity adjustment annotations when applicable (see Severity Adjustments).

## Remediation

For each finding, the corresponding remediation skill can be used independently:

| Finding | Remediation Skill |
|---------|------------------|
| Open IP allowlist | [configuring-ip-allowlists](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-ip-allowlists/SKILL.md) |
| SSO not configured / SCIM not enabled | [configuring-sso-and-scim](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-sso-and-scim/SKILL.md) |
| CMEK not enabled | [enabling-cmek-encryption](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/enabling-cmek-encryption/SKILL.md) |
| Audit logging disabled | [configuring-audit-logging](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-audit-logging/SKILL.md) |
| Excessive admin privileges | [hardening-user-privileges](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/hardening-user-privileges/SKILL.md) |
| Weak password policy | [enforcing-password-policies](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/enforcing-password-policies/SKILL.md) |
| TLS/certificate issues | [managing-tls-certificates](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/managing-tls-certificates/SKILL.md) |
| No private connectivity | [configuring-private-connectivity](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-private-connectivity/SKILL.md) |
| Log export not configured | [configuring-log-export](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-log-export/SKILL.md) |
| Compliance gaps | [preparing-compliance-documentation](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/preparing-compliance-documentation/SKILL.md) |

For each FAIL finding, offer: **"Explain how to fix this"** (step-by-step guidance) or **"Help me fix this now"** (interactive remediation).

## Safety Considerations

- **All operations are read-only.** No cluster settings, users, roles, or network configurations are modified during the audit.
- **SQL queries use SHOW and SELECT only.** No DDL or DML statements are executed.
- **ccloud commands are read-only.** Only `list`, `info`, and `auth` subcommands are used.
- **No secrets are logged.** Connection strings and tokens are not included in the report output.
- **Privilege check:** The audit may produce incomplete results if the executing user lacks admin or VIEWACTIVITY privilege. The report notes any permission gaps.

## References

**Skill references:**
- [Sample audit report](references/sample-report.md) — Example report with findings and remediation links
- [SQL queries for security auditing](references/sql-queries.md)
- [ccloud CLI commands](references/ccloud-commands.md)
- [RBAC and privileges setup](references/permissions.md)

**Remediation skills:**
- [configuring-ip-allowlists](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-ip-allowlists/SKILL.md) — Network access hardening
- [enabling-cmek-encryption](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/enabling-cmek-encryption/SKILL.md) — Customer-managed encryption keys
- [configuring-audit-logging](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-audit-logging/SKILL.md) — SQL audit logging
- [hardening-user-privileges](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/hardening-user-privileges/SKILL.md) — RBAC tightening
- [enforcing-password-policies](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/enforcing-password-policies/SKILL.md) — Password strength enforcement
- [configuring-sso-and-scim](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-sso-and-scim/SKILL.md) — SSO and SCIM provisioning
- [managing-tls-certificates](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/managing-tls-certificates/SKILL.md) — TLS certificate management
- [configuring-private-connectivity](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-private-connectivity/SKILL.md) — Private endpoints and VPC peering
- [configuring-log-export](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/configuring-log-export/SKILL.md) — Log and metric export
- [preparing-compliance-documentation](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/preparing-compliance-documentation/SKILL.md) — Compliance readiness and documentation

**Official CockroachDB Documentation:**
- [CockroachDB Cloud Security Overview](https://www.cockroachlabs.com/docs/cockroachcloud/security-overview.html)
- [Managing IP Allowlists](https://www.cockroachlabs.com/docs/cockroachcloud/network-authorization.html)
- [Cloud Console SSO](https://www.cockroachlabs.com/docs/cockroachcloud/cloud-org-sso.html)
- [Cluster SSO (Database SSO)](https://www.cockroachlabs.com/docs/stable/sso-sql.html)
- [SCIM Provisioning](https://www.cockroachlabs.com/docs/cockroachcloud/configure-scim-provisioning)
- [CMEK Overview](https://www.cockroachlabs.com/docs/cockroachcloud/cmek.html)
- [Audit Logging](https://www.cockroachlabs.com/docs/stable/sql-audit-logging.html)
- [Security Reference: Authorization](https://www.cockroachlabs.com/docs/stable/security-reference/authorization.html)
