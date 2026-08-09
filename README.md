# Hunt Skill

Hunt Skill is a project-local Codex skill for adversarial smart-contract auditing. It combines protocol relationship mapping, impact-first hunting, bounded SQLite context retrieval, historical-pattern research, skeptical validation, and human-gated PoC work.

The skill is designed to be installed into each audit repository under `.agents/skills/hunt-skill`. Every project keeps its own `.audit/graph/audit.db`, scope snapshot, hypotheses, evidence, novelty checks, and manual approvals.

## What It Enforces

- Code and pinned configuration remain the primary evidence.
- Impact catalogs combine protocol archetypes with concrete protocol-specific invariants and bad states.
- Cross-function, cross-contract, cross-transaction, and external-protocol relationships are queryable without loading a large Markdown notebook.
- Pattern matching is used as bounded fallback inspiration when code-led hunting stalls, then again to validate novelty and known-issue status.
- Repository audits, similar audits, Solodit, and the EVM Hack Registry must be checked before reporting.
- Tenderly is preferred for simulations, traces, forks, and state overrides when its skill is available.
- PoC work is blocked until the user manually approves a code-validated hypothesis. Approval becomes stale when the claim or scoped source changes.

## Requirements

- Python 3.11 or newer
- SQLite with JSON1 and FTS5, included with normal modern Python distributions
- Git
- Codex project skill discovery through `.agents/skills`

No model API key, database server, Python package installation, or global skill symlink is required.

## Install Into A Project

Clone this repository once:

```bash
git clone git@github.com:pokhrelanmol/hunt-skill.git
cd hunt-skill
```

Install into an audit project:

```bash
./scripts/install.sh /absolute/path/to/audit-project
```

This copies the skill to:

```text
<audit-project>/.agents/skills/hunt-skill/
```

It also runs diagnostics and initializes the project's compact `.audit/` control plane without overwriting existing audit files or modifying production contracts.

Restart or open a new Codex task in the project after installation so project skill discovery refreshes.

For installation options, upgrades, scope setup, and troubleshooting, read [docs/SETUP.md](docs/SETUP.md).

## First Project Setup

Define an exact source scope in `<project>/.audit/SCOPE_FILES.txt`, then run:

```bash
PROJECT=/absolute/path/to/audit-project
AUDITCTL="$PROJECT/.agents/skills/hunt-skill/scripts/auditctl.py"

python3 "$AUDITCTL" snapshot --repo "$PROJECT" \
  --scope-file .audit/SCOPE_FILES.txt

python3 "$AUDITCTL" profile-set --repo "$PROJECT" \
  --name "Protocol Name" \
  --archetype vault \
  --case "Describe the concrete assets, accounting, lifecycle, and integrations."

python3 "$AUDITCTL" impact-seed --repo "$PROJECT"
python3 "$AUDITCTL" db-info --repo "$PROJECT"
```

Template impact rows begin as `DRAFT`. They cannot become `READY` until they identify the protocol-specific invariant, decision point, bad state, attacker objective, and candidate primitives.

## Invoke The Skill

Examples:

```text
Use $hunt-skill to map this protocol's asset and state relationships.
Use $hunt-skill to investigate whether cancellation can desynchronize debt.
Use $hunt-skill to continue HYP-003 and try to falsify it.
Use $hunt-skill to run a full audit of the pinned scope.
```

The default mode is collaborative `CHAT`; a full repository audit starts only when explicitly requested.

## Update An Installed Project

Pull this repository, then reinstall explicitly:

```bash
git pull --ff-only
./scripts/install.sh --update /absolute/path/to/audit-project
```

The installer backs up the previous skill directory before replacing it. Project audit state remains in `.audit/` and is not replaced.

## Repository Layout

```text
hunt-skill/
  README.md
  docs/SETUP.md
  scripts/install.sh
  scripts/validate_repo.py
  skill/hunt-skill/
    SKILL.md
    agents/openai.yaml
    assets/impact-catalogs.json
    references/
    workflows/
    scripts/auditctl.py
    tests/
```

## Validate

```bash
python3 scripts/validate_repo.py
PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s skill/hunt-skill/tests -v
```
