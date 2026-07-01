---
name: designing-application-transactions
description: Guides application developers in designing correct and performant transaction patterns for CockroachDB, covering transaction lifetime, implicit vs explicit transactions, retry handling with exponential backoff, pushing invariants into SQL, selective pessimistic locking, set-based operations, connection pooling, prepared statements, keyset pagination, follower reads, and separating business logic from database logic. Use when building applications on CockroachDB, designing transaction workflows, handling retries, optimizing application-layer database interactions, or configuring connection pools.
compatibility: "CockroachDB >= 22.1. Works with or without a live database connection. With connection, requires appropriate privileges on target tables."
metadata:
  author: cockroachdb
  version: "1.0"
---

# Designing Application Transactions

Guides application developers through the design principles and implementation patterns needed to build correct, performant, and resilient applications on CockroachDB. Covers the full spectrum from transaction scoping and retry logic to connection pooling and observability.

**Complement to SQL skills:** For SQL syntax, schema design, and query optimization, see [cockroachdb-sql](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-query-and-schema-design/cockroachdb-sql/SKILL.md). For benchmarking transaction formulations under contention, see [benchmarking-transaction-patterns](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-application-development/benchmarking-transaction-patterns/SKILL.md).

## When to Use This Skill

- Designing transaction boundaries for a CockroachDB application
- Implementing client-side retry logic with exponential backoff
- Deciding between implicit and explicit transactions
- Choosing between optimistic and pessimistic concurrency control
- Replacing read-modify-write loops with atomic SQL
- Configuring connection pools (HikariCP, pgbouncer, etc.)
- Implementing keyset pagination instead of OFFSET/LIMIT
- Using follower reads for reporting and analytics queries
- Separating business orchestration from database transactions
- Using prepared statements for performance and security
- Selecting explicit column projections instead of SELECT *
- Testing application behavior under concurrency
- Monitoring application-level database performance

## Prerequisites

- Familiarity with CockroachDB's SERIALIZABLE isolation level
- Understanding of ACID transaction semantics
- Access to application source code for transaction design changes
- SQL connection to a CockroachDB cluster (for testing and validation)

## Additional details

Further sections for this skill are in [references/additional-details.md](references/additional-details.md).

## Additional references

- [monitoring-and-concurrency-testing.md](references/monitoring-and-concurrency-testing.md)
