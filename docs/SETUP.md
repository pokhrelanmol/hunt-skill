# Project Setup Guide

This guide installs Hunt Skill into one audit project and initializes its project-local SQLite workflow.

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

## 4. Verify SQLite

```bash
PROJECT=/absolute/path/to/audit-project
AUDITCTL="$PROJECT/.agents/skills/hunt-skill/scripts/auditctl.py"

python3 "$AUDITCTL" doctor --repo "$PROJECT"
python3 "$AUDITCTL" db-info --repo "$PROJECT"
```

Expected requirements:

- Python `>=3.11`
- SQLite JSON1: `true`
- SQLite FTS5: `true`
- Runtime dependencies: empty

Tenderly is optional for local code analysis. When live state matters, Hunt prefers Tenderly for simulations/traces/forks and falls back to `cast` plus Alchemy/public RPC for narrow reads.

Optional shell keys:

```bash
export SOLODIT_API_KEY="..."
export ALCHEMY_API_KEY="..."
```

`SOLODIT_API_KEY` enables Solodit-backed historical research. `ALCHEMY_API_KEY` is optional for preferred authenticated RPC; supported chains can fall back to public RPC.

## 5. Lock The Audit Scope

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
python3 "$AUDITCTL" snapshot --repo "$PROJECT" \
  --scope-file .audit/SCOPE_FILES.txt
```

The snapshot stores exact paths and SHA-256 hashes. Graph evidence and PoC handoff readiness become stale when scoped source changes.

## 6. Create The Protocol Profile

Choose every applicable archetype. Hybrid protocols may use several:

Available seed archetypes are `generic`, `vault`, `lending`, `bridge`, `dex`, `stablecoin`, `perps`, `liquid-staking`, and `governance`.

```bash
python3 "$AUDITCTL" profile-set --repo "$PROJECT" \
  --name "Protocol Name" \
  --archetype vault \
  --archetype lending \
  --asset USDC \
  --integration "External ERC4626 collateral" \
  --case "Describe how shares, collateral, debt, liquidation, settlement, and external state interact."

python3 "$AUDITCTL" impact-seed --repo "$PROJECT"
python3 "$AUDITCTL" impact-list --repo "$PROJECT" --status DRAFT
```

Do not hunt directly from generic templates. Refine the relevant impacts until they are protocol-specific and `READY`.

## 7. Use Bounded Retrieval

```bash
python3 "$AUDITCTL" search --repo "$PROJECT" "cancel debt"
python3 "$AUDITCTL" neighbors --repo "$PROJECT" function:... \
  --types CALLS,READS,WRITES --depth 1 --limit 30
python3 "$AUDITCTL" context --repo "$PROJECT" \
  --goal "Can cancellation desynchronize facility debt?" --limit 20
```

Do not open the SQLite file as text or dump the entire graph into model context.

## 8. Pattern Research Order

1. Hunt from current code, protocol invariants, and state relationships.
2. When a bounded local pass produces no useful lead, run one focused historical search for inspiration.
3. Convert a matched pattern into a current-protocol question and trace it independently.
4. After a hypothesis survives validation, search historical sources again for duplicates and novelty.

Similarity never proves vulnerability.

## 9. Automatic PoC Handoff

Configure the dedicated proof skill once:

```bash
python3 "$AUDITCTL" poc-config --repo "$PROJECT" \
  --path /absolute/path/to/poc-skill
```

When a hypothesis reaches `CODE_VALIDATED`, Codex runs:

```bash
python3 "$AUDITCTL" poc-handoff --repo "$PROJECT" HYP-001
```

The handoff checks that the scope is fresh and the configured PoC skill contains `SKILL.md`. Hunt resolves normal supported RPCs automatically; Codex asks only for genuinely missing proof inputs such as deployed addresses, historical blocks, archive-only capability, or unavailable fixtures.

## 10. Update Or Remove

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
