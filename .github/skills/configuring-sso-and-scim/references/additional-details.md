# Additional details

## Rollback

### Disable Cloud Console SSO Enforcement

1. Log in with the break-glass admin account
2. Navigate to **Organization Settings > Authentication**
3. Disable **Require SSO** to re-enable password login

### Disable DB Console SSO (OIDC)

```sql
SET CLUSTER SETTING server.oidc_authentication.enabled = false;
```

### Disable SQL/Cluster SSO (JWT)

```sql
SET CLUSTER SETTING server.jwt_authentication.enabled = false;
```

### Disable LDAP/AD Authentication

```sql
-- Revert HBA to password-only authentication
SET CLUSTER SETTING server.host_based_authentication.configuration = '
host all all all password
';
```

### Disable Auto User Provisioning

```sql
-- Disable JWT auto-provisioning
SET CLUSTER SETTING security.provisioning.jwt.enabled = false;

-- Disable LDAP auto-provisioning
SET CLUSTER SETTING security.provisioning.ldap.enabled = false;
```

### Disable SCIM

1. Navigate to **Organization Settings > Authentication > SCIM**
2. Disable the SCIM endpoint
3. Remove the SCIM integration from your IdP

### Remove Identity Mapping

```sql
SET CLUSTER SETTING server.identity_map.configuration = '';
```

## References

**Skill references:**
- [IdP configuration steps](references/configuration-steps.md)

**Related skills:**
- [auditing-cloud-cluster-security](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/auditing-cloud-cluster-security/SKILL.md) — Run a full security posture audit
- [enforcing-password-policies](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/enforcing-password-policies/SKILL.md) — Strengthen password policies as an alternative to SSO
- [managing-tls-certificates](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-security-and-governance/managing-tls-certificates/SKILL.md) — Certificate-based authentication as an alternative to SSO

**Official CockroachDB Documentation:**
- [Cloud Console SSO](https://www.cockroachlabs.com/docs/cockroachcloud/cloud-org-sso.html)
- [DB Console SSO](https://www.cockroachlabs.com/docs/stable/sso-db-console.html)
- [Cluster SSO (JWT)](https://www.cockroachlabs.com/docs/stable/sso-sql.html)
- [SCIM Provisioning](https://www.cockroachlabs.com/docs/cockroachcloud/configure-scim-provisioning)
- [Cluster Settings](https://www.cockroachlabs.com/docs/stable/cluster-settings.html)
- [HBA Configuration](https://www.cockroachlabs.com/docs/stable/security-reference/authentication.html)
- [JWT Authentication](https://www.cockroachlabs.com/docs/stable/sso-sql.html)
- [LDAP Authentication](https://www.cockroachlabs.com/docs/stable/ldap-authentication)
- [Authentication Reference](https://www.cockroachlabs.com/docs/stable/security-reference/authentication)
