# Hunt Skill

Hunt Skill is a project-local Codex skill for adversarial smart-contract auditing. It combines protocol relationship mapping, impact-first hunting, bounded SQLite context retrieval, historical-pattern research, skeptical validation, human-steered research direction, and automatic PoC handoff for code-validated hypotheses.

The skill is designed to be installed into each audit repository under `.agents/skills/hunt-skill`. Every project keeps its own `.audit/graph/audit.db`, scope snapshot, hypotheses, evidence, novelty checks, research jobs, observations, and legacy manual approvals.

## What It Enforces

- Code and pinned configuration remain the primary evidence.
- Impact catalogs combine protocol archetypes with concrete protocol-specific invariants and bad states.
- Cross-function, cross-contract, cross-transaction, and external-protocol relationships are queryable without loading a large Markdown notebook.
- Pattern matching is used as bounded fallback inspiration when code-led hunting stalls, then again to validate novelty and known-issue status.
- Repository audits, similar audits, Solodit, and the EVM Hack Registry must be checked before reporting.
- Tenderly is preferred for simulations, traces, forks, and state overrides when its skill is available.
- A code-validated hypothesis automatically hands off to a configured dedicated PoC skill; proof still checks current scope and asks the user only when required environment/context is missing.

## Requirements

- Python 3.11 or newer
- SQLite with JSON1 and FTS5, included with normal modern Python distributions
- Git
- Codex project skill discovery through `.agents/skills`
- Optional: Foundry `cast` for narrow live-state reads

No model API key, database server, Python package installation, or global skill symlink is required.

## Optional Environment Setup

Hunt inherits API keys from your shell. Do not put keys in `.audit/`, SQLite, reports, or command examples.

For zsh, add this to `~/.zshrc` and run `source ~/.zshrc`:

```bash
export SOLODIT_API_KEY="..."
export ALCHEMY_API_KEY="..."
```

For bash, add the same exports to `~/.bashrc` and run `source ~/.bashrc`.

`SOLODIT_API_KEY` enables Solodit-backed historical vulnerability research. `ALCHEMY_API_KEY` is optional and lets Hunt prefer authenticated Alchemy RPC for `cast` live-state reads; if absent, Hunt falls back to public RPC for supported chains.

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

## Primary Workflow

1. Install Hunt Skill into the protocol repository.
2. Optionally configure `SOLODIT_API_KEY` and `ALCHEMY_API_KEY`.
3. Open Codex inside the target protocol repository.
4. Say: `Use Hunt Skill on this repo.`
5. Provide scope, docs, deployment context, or protocol explanations only when asked.

Hunt handles `auditctl`, SQLite, graph retrieval, State Probes, Solodit research, chain detection, Tenderly, `cast`, RPC selection, and PoC handoff internally.

## Advanced Setup Commands

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

Configure the dedicated PoC skill once if automatic proof handoff should run:

```bash
python3 "$AUDITCTL" poc-config --repo "$PROJECT" \
  --path /absolute/path/to/poc-skill
```

## Invoke The Skill

Examples:

```text
Use $hunt-skill to map this protocol's asset and state relationships.
Use $hunt-skill to investigate whether cancellation can desynchronize debt.
Use $hunt-skill to continue HYP-003 and try to falsify it.
Use $hunt-skill to run a full audit of the pinned scope.
```

The default mode is collaborative `CHAT`; a full repository audit starts only when explicitly requested.

## How Hunt Skill Hunts

Hunt keeps one active research question at a time:

```text
protocol brain
-> protocol-specific invariant
-> niche forbidden state
-> one ACTIVE job
-> backward trace from impact + forward trace from attacker
-> selected dimensions: local state, accounting, lifecycle/order, boundaries, actors, integrations, live state, historical patterns
-> exploratory State Probe
-> observation
-> hypothesis
-> aggressive falsification
-> CODE_VALIDATED
-> automatic PoC handoff
-> human chooses the next direction
```

It dynamically chooses relevant dimensions for the active impact instead of running every checklist.

State Probes deliberately poke underexplored reachable behavior: `1 wei`, dust, threshold +/- 1, partial operations, repeated operations, equivalent paths such as `deposit(100)` versus `deposit(40); deposit(60)`, operation reordering, different actors, time boundaries, and realistic external-state changes. Unexpected results become `OBSERVATION`, not automatically a bug.

Historical research is impact-driven: derive the needed attack primitive from the active job, query Solodit or historical sources, extract mechanism and prerequisites, then return to current code and verify independently. Historical matches generate attack ideas, not evidence.

## Live-State Reads

When live state matters, Hunt uses this hierarchy:

1. Tenderly for simulations, traces, forks, state overrides, and historical execution when useful and available.
2. `cast` for narrow state reads when Tenderly is unavailable, unsuitable, or unnecessary.
3. Official explorers or deployment sources to cross-check addresses/configuration.

For `cast`, Hunt resolves the chain automatically from audit context or the active job. If `ALCHEMY_API_KEY` is configured and Alchemy supports the chain, it uses the correct Alchemy endpoint. Otherwise it falls back to a public RPC for supported chains. The normal user should not configure RPC URL templates.

Advanced live debugging:

```bash
python3 "$AUDITCTL" rpc-resolve --repo "$PROJECT" --chain base
python3 "$AUDITCTL" cast-read --repo "$PROJECT" --chain base \
  --operation call --address 0x... --signature "totalAssets()(uint256)"
```

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
