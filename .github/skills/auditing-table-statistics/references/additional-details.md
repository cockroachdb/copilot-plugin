# Additional details

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| **SHOW STATISTICS returns empty** | No statistics ever collected | Run `CREATE STATISTICS __auto__ FROM table_name;` |
| **row_count shows 0 for non-empty table** | Statistics out of sync | Refresh: `CREATE STATISTICS __auto__ FROM table_name;` |
| **Permission denied error** | No privileges on table | Grant any privilege: `GRANT SELECT ON table_name TO user;` |
| **CREATE STATISTICS job stuck** | Large table with high write volume | Check `SHOW JOBS` status; consider `CANCEL JOB` and retry during low-traffic period |
| **Automatic collection not triggering** | Setting disabled or threshold not met | Verify `sql.stats.automatic_collection.enabled = true` and check row count drift |
| **Statistics exist but query plans still poor** | Stale statistics or missing multi-column stats | Refresh existing; create multi-column for correlated columns (see Query 6) |
| **High drift but recent created timestamp** | Extreme write volume between collections | Lower automatic collection threshold or increase manual refresh frequency |

### Defensive Query Patterns

**Handle missing statistics:**
```sql
-- Use COALESCE for NULL created timestamps
SELECT COALESCE(created, '1970-01-01'::TIMESTAMP) AS stats_created_at
FROM [SHOW STATISTICS FOR TABLE table_name]
WHERE column_names = '{}';
```

**Avoid division by zero in drift calculations:**
```sql
-- Use NULLIF to prevent divide-by-zero errors
SELECT
  ABS(actual - stats)::NUMERIC / NULLIF(stats, 0) * 100 AS drift_pct
FROM ...;
```

## Key Considerations

- **Auto vs manual:** Keep automatic collection enabled for baseline; use manual `CREATE STATISTICS` for ad-hoc post-bulk-load refresh and critical tables
- **Multi-column statistics:** Auto-collection covers index column groups; manual `CREATE STATISTICS` is needed for correlated non-indexed columns queried together (e.g., `CREATE STATISTICS city_state_stats ON city, state FROM addresses;`)
- **Large tables (>10M rows):** Schedule `CREATE STATISTICS` during maintenance windows; monitor with `SHOW JOBS WHERE job_type = 'CREATE STATS'`
- **Staleness tuning:** OLTP: 3-7 days, OLAP: 14-30 days, hybrid: critical tables 3-7 days, archive 30+ days
- **Privilege:** Any table privilege (SELECT, INSERT, etc.) grants statistics visibility

See [references/create-statistics-examples.md](references/create-statistics-examples.md) and [references/statistics-thresholds.md](references/statistics-thresholds.md) for detailed guidance.

## References

**Official CockroachDB Documentation:**
- [SHOW STATISTICS](https://www.cockroachlabs.com/docs/stable/show-statistics.html) - Complete syntax and output schema
- [CREATE STATISTICS](https://www.cockroachlabs.com/docs/stable/create-statistics.html) - Manual statistics collection guide
- [Cost-Based Optimizer](https://www.cockroachlabs.com/docs/stable/cost-based-optimizer.html) - How optimizer uses statistics
- [Table Statistics](https://www.cockroachlabs.com/docs/stable/cost-based-optimizer.html#table-statistics) - Statistics impact on query planning
- [SHOW JOBS](https://www.cockroachlabs.com/docs/stable/show-jobs.html) - Job monitoring and management

**Related Skills:**
- [profiling-statement-fingerprints](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-observability-and-diagnostics/profiling-statement-fingerprints/SKILL.md) - Identify slow query patterns
- [triaging-live-sql-activity](https://github.com/cockroachlabs/cockroachdb-skills/blob/main/skills/cockroachdb-observability-and-diagnostics/triaging-live-sql-activity/SKILL.md) - Real-time query triage

**Supplementary References:**
- [Statistics Thresholds Guide](references/statistics-thresholds.md) - Workload-specific staleness and drift thresholds
- [CREATE STATISTICS Examples](references/create-statistics-examples.md) - Comprehensive collection patterns and batch strategies
