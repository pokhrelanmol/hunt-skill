# Project Setup Guide

This is the canonical installation, update, scope, and troubleshooting guide for Hunt Skill.

## 1. Clone Or Update The Skill Repository

First installation:

```bash
git clone git@github.com:pokhrelanmol/hunt-skill.git
cd hunt-skill
```

Existing checkout:

```bash
git pull --ff-only
```

## 2. Install Into The Audit Project

```bash
./scripts/install.sh /absolute/path/to/audit-project
```

The installer:

1. Checks Python and SQLite capabilities.
2. Copies only `skill/hunt-skill` into `<project>/.agents/skills/hunt-skill`.
3. Initializes missing `.audit/` control files and `.audit/graph/audit.db`.
4. Preserves existing `.audit` files and production source.
5. Refuses to replace an existing installed skill unless `--update` is supplied.

Options:

```text
--update    Back up and replace an existing project skill.
--no-init   Install the skill without initializing .audit/.
--help      Show installer usage.
```

An update backup is written beside the installed skill as `.hunt-skill.backup-<UTC timestamp>`.

## 3. Refresh Codex Discovery

Open a new Codex task from the audit project after installation. The skill should appear as `hunt-skill` from:

```text
<project>/.agents/skills/hunt-skill/SKILL.md
```

The repository intentionally does not install a global symlink. Each project controls its own skill version.

## 4. Lock The Audit Scope

Edit:

```text
<project>/.audit/SCOPE_FILES.txt
```

Use one repository-relative file or directory per line. Prefer exact files for contests and bounties:

```text
src/Vault.sol
src/Facility.sol
src/libraries/Accounting.sol
```

Capture the snapshot:

```bash
PROJECT=/absolute/path/to/audit-project
AUDITCTL="$PROJECT/.agents/skills/hunt-skill/scripts/auditctl.py"

python3 "$AUDITCTL" snapshot --repo "$PROJECT" \
  --scope-file .audit/SCOPE_FILES.txt
```

The snapshot stores exact paths and SHA-256 hashes. Graph evidence and PoC handoff readiness become stale when scoped source changes.

Protocol family selection and impact seeding are not setup steps. After code-led RECON, the agent derives protocol-specific invariants and candidate Jobs from current code and uses checklist questions or real edge cases only as bounded reasoning lenses.

## 5. Optional Integrations

Tenderly, Solodit, Alchemy, and a dedicated PoC skill are optional during installation. Configure them only when the active investigation needs them.

Optional shell keys:

```bash
export SOLODIT_API_KEY="..."
export ALCHEMY_API_KEY="..."
```

`SOLODIT_API_KEY` enables Solodit-backed historical research. `ALCHEMY_API_KEY` selects authenticated RPC where supported; otherwise Hunt may use a public RPC for narrow reads.

Configure the dedicated proof skill once:

```bash
python3 "$AUDITCTL" poc-config --repo "$PROJECT" \
  --path /absolute/path/to/poc-skill
```

At `CODE_VALIDATED`, Hunt runs `poc-handoff`. It checks source freshness and the configured skill before returning the proof packet.

## 6. Update Or Remove

Update:

```bash
./scripts/install.sh --update /absolute/path/to/audit-project
```

Remove only the installed skill:

```bash
rm -rf /absolute/path/to/audit-project/.agents/skills/hunt-skill
```

The project's `.audit/` database and notebooks remain intact unless removed separately.

## Troubleshooting

Do not run diagnostics at every task start. The installer already checks Python and SQLite. Use the following commands only when installation, database access, search, or optional tooling fails:

```bash
PROJECT=/absolute/path/to/audit-project
AUDITCTL="$PROJECT/.agents/skills/hunt-skill/scripts/auditctl.py"

python3 "$AUDITCTL" doctor --repo "$PROJECT"
python3 "$AUDITCTL" db-info --repo "$PROJECT"
```

### Skill is not listed

- Confirm `.agents/skills/hunt-skill/SKILL.md` exists in the project.
- Open a new Codex task rooted at the project.
- Run `python3 scripts/validate_repo.py` in the Hunt Skill checkout.

### FTS5 or JSON1 fails

Use a modern Python distribution built with SQLite JSON1 and FTS5. No separate SQLite server is needed.

### Database is locked

Stop concurrent writers and retry. Do not delete `audit.db-wal` or `audit.db-shm` while a process is active.

### PoC handoff is stale

Review the changed source, capture a fresh scope snapshot, and rerun `poc-handoff`.
