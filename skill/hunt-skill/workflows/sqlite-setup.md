# SQLite Setup

No database server is required. Python 3.11+ includes the `sqlite3` module and this skill has no runtime package dependencies.

## Phase 1: Diagnose

**Entry:** The target repository is known.

1. Run `python3 <SKILL_ROOT>/scripts/auditctl.py doctor --repo <repo>`.
2. Confirm Python >=3.11, SQLite, JSON1, and FTS5.
3. Note whether the Tenderly integration is visible. This is optional for local code analysis but required for Tenderly-backed live claims.

**Exit:** Required SQLite capabilities pass, or the exact missing capability is reported.

## Phase 2: Initialize

**Entry:** Diagnostics pass.

1. Run `init --repo <repo>`.
2. Inspect the generated `.audit/INDEX.md`, `.audit/CURRENT.md`, and `.audit/SCOPE_FILES.txt` without overwriting existing files.
3. Put exact in-scope file paths in `.audit/SCOPE_FILES.txt`, one path per line. Comments start with `#`.
4. Run `snapshot --scope-file .audit/SCOPE_FILES.txt`.

**Exit:** `.audit/graph/audit.db` exists and a current exact source snapshot is recorded.

## Phase 3: Profile And Seed

**Entry:** A snapshot exists and protocol architecture is understood enough to name archetypes.

1. Run `profile-set` with one or more archetypes and a protocol-specific case summary.
2. Run `impact-seed` to create draft impact goals.
3. Refine only relevant goals; mark them `READY` after all protocol fields are concrete.

**Exit:** The database has a protocol profile and at least one `READY` impact goal for hunting.

## Phase 4: Verify

**Entry:** Initialization and profile seeding are complete.

1. Run `db-info`, `stale`, and `lint`.
2. Optionally inspect manually:

```bash
sqlite3 .audit/graph/audit.db ".tables"
sqlite3 .audit/graph/audit.db "select id,title,status from impact_goals limit 10;"
```

3. Do not open the database as text or paste broad query output into context.

**Exit:** Schema is healthy, scope is fresh, and bounded queries work.

## Troubleshooting

- `python3: command not found`: install Python 3.11+ and rerun `doctor`.
- `FTS5 unavailable`: use a Python build with SQLite FTS5; search cannot operate reliably without it.
- `database is locked`: stop concurrent writers, retry, and inspect lingering `audit.db-wal`/`audit.db-shm`; do not delete them while a process is active.
- stale PoC handoff: capture a fresh source snapshot and rerun `poc-handoff`.
- stale graph rows: refresh their evidence against the current snapshot rather than deleting audit history.
