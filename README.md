# Hunt Skill

Hunt Skill is a graph-based bug hunting skill for adversarial smart-contract audits.

It installs into a target audit repository and builds a project-local SQLite graph of contracts, functions, call sites, storage, effects, observations, hypotheses, evidence, and research jobs. Codex then uses that graph to hunt from impact backward to reachable attacker paths instead of reading the whole codebase as one giant notebook.

The skill is designed to be installed into each audit repository under `.agents/skills/hunt-skill`. Every project keeps its own `.audit/graph/audit.db`, scope snapshot, hypotheses, evidence, novelty checks, observations, and proof handoff state.

For installation, upgrades, scope setup, and troubleshooting, use [docs/SETUP.md](docs/SETUP.md). This README explains what the skill is and how the hunting loop works.

## What It Enforces

- Code and pinned configuration remain the primary evidence.
- Impact catalogs combine protocol archetypes with concrete protocol-specific invariants and bad states.
- Cross-function, cross-contract, cross-transaction, and external-protocol relationships are queryable without loading a large Markdown notebook.
- Pattern matching is used as bounded fallback inspiration when code-led hunting stalls, then again to validate novelty and known-issue status.
- Repository audits, similar audits, Solodit, and the EVM Hack Registry must be checked before reporting.
- Tenderly is preferred for simulations, traces, forks, and state overrides when its skill is available.
- A code-validated hypothesis automatically hands off to a configured dedicated PoC skill; proof still checks current scope and asks the user only when required environment/context is missing.

## Requirements

- Python 3.11 or newer.
- SQLite with JSON1 and FTS5, included with normal modern Python distributions.
- Git.
- Codex project skill discovery through `.agents/skills`.
- Optional: Foundry `cast` for narrow live-state reads.

No model API key, database server, Python package installation, or global skill symlink is required.

For exact install commands, optional environment variables, updates, and troubleshooting, read [docs/SETUP.md](docs/SETUP.md).

## Quick Start

Clone this repository once:

```bash
git clone git@github.com:pokhrelanmol/hunt-skill.git
cd hunt-skill
```

Install into an audit project:

```bash
./scripts/install.sh /absolute/path/to/audit-project
```

This copies the skill to the audit project:

```text
<audit-project>/.agents/skills/hunt-skill/
```

Restart or open a new Codex task in the project after installation so project skill discovery refreshes.

Then open Codex inside the target protocol repository and say:

```text
Use Hunt Skill on this repo.
```

If you need optional Solodit, Alchemy, update, or scope commands, go to [docs/SETUP.md](docs/SETUP.md).

## Primary Workflow

1. Install Hunt Skill into the protocol repository.
2. Optionally configure Solodit or Alchemy using [docs/SETUP.md](docs/SETUP.md).
3. Open Codex inside the target protocol repository.
4. Say: `Use Hunt Skill on this repo.`
5. Provide scope, docs, deployment context, or protocol explanations only when asked.

Hunt handles `auditctl`, SQLite, graph retrieval, State Probes, Solodit research, chain detection, Tenderly, `cast`, RPC selection, and PoC handoff internally.

## Invoke The Skill

Examples:

```text
Use $hunt-skill to map this protocol's asset and state relationships.
Use $hunt-skill to investigate whether cancellation can desynchronize debt.
Use $hunt-skill to continue HYP-003 and try to falsify it.
Use $hunt-skill to run a full audit of the pinned scope.
```

The default mode is collaborative `CHAT`; a full repository audit starts only when explicitly requested.

## How The Graph-Based Hunt Works

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

The important part is that the graph is not just a call graph. It is a compact audit memory:

- which external functions can be called by which actor;
- which internal functions they reach;
- which state variables, mappings, balances, shares, debts, limits, timestamps, and configuration values they read or write;
- which external protocols, tokens, or oracle values influence the path;
- which observations and hypotheses were already tested, killed, or validated.

That means Codex can ask sharper questions:

- “What functions write `totalDebt` but not `accountDebt[user]`?”
- “What paths update shares before pulling assets?”
- “What functions touch collateral accounting but skip health checks?”
- “Where can an attacker move from a public entry point into this sensitive state transition?”
- “Which previous observations already killed this idea?”

It dynamically chooses relevant dimensions for the active impact instead of running every checklist. The graph narrows the search space; invariant reasoning decides what matters.

State Probes deliberately poke underexplored reachable behavior: `1 wei`, dust, threshold +/- 1, partial operations, repeated operations, equivalent paths such as `deposit(100)` versus `deposit(40); deposit(60)`, operation reordering, different actors, time boundaries, and realistic external-state changes. Unexpected results become `OBSERVATION`, not automatically a bug.

Historical research is impact-driven: derive the needed attack primitive from the active job, query Solodit or historical sources, extract mechanism and prerequisites, then return to current code and verify independently. Historical matches generate attack ideas, not evidence.

## Example: How Hunt Would Find A Bug

Imagine a vault has these simplified paths:

```text
deposit()
  -> mint shares from totalAssets()

withdraw()
  -> burn shares
  -> send assets

donate()
  -> transfer assets into the vault
  -> does not mint shares

claimRewards()
  -> increases accounting balance
```

The protocol invariant might be:

```text
shares should represent a fair claim on vault assets
```

A naive checklist might only ask whether `deposit()` and `withdraw()` have reentrancy guards. Hunt instead builds the relationship graph and notices that multiple paths influence the same economic state:

```text
external asset balance
totalAssets()
share price
shares minted
reward accounting
withdrawable amount
```

Then it creates an ACTIVE job around a concrete forbidden state:

```text
Can an attacker make later depositors mint too few shares, or withdraw more value than their fair share, by changing assets without matching share/accounting updates?
```

From there Hunt traces in two directions:

1. Backward from impact: find every path that changes `totalAssets()`, share price, reward balance, or withdrawable amount.
2. Forward from attacker actions: find every public or permissionless function an attacker can execute before `deposit()`, `withdraw()`, or reward settlement.

It may run State Probes like:

```text
deposit(100)
donate(1)
deposit(100)

deposit(100)
claimRewards()
deposit(100)

deposit(40); deposit(60)
deposit(100)
```

If the outputs differ in a way that violates the invariant, Hunt records an observation, not yet a bug:

```text
OBSERVATION: share minting depends on externally-increased assets that are not matched by shares.
```

Then it tries to kill the idea:

- Is donation impossible because the token cannot be transferred directly?
- Is the behavior accepted ERC-4626 design?
- Is the loss dust-only?
- Is there a minimum-liquidity defense?
- Is the attacker donating more than they can extract?
- Is this already documented or known from prior audits?

Only if the path survives does it become a hypothesis:

```text
HYPOTHESIS: attacker can manipulate share price before victim deposit and extract value through later withdrawal.
```

Then Hunt asks for proof only after code-level validation:

```text
attacker capability
-> reachable path
-> broken invariant
-> measurable asset/accounting impact
-> novelty check
-> CODE_VALIDATED
-> automatic PoC handoff
```

This is the core idea: Hunt does not “find bugs” by spraying prompts at files. It uses the SQLite graph to keep relationships precise, then uses impact-driven probes to look for forbidden states that are actually reachable.

## Live-State Reads

When live state matters, Hunt uses this hierarchy:

1. Tenderly for simulations, traces, forks, state overrides, and historical execution when useful and available.
2. `cast` for narrow state reads when Tenderly is unavailable, unsuitable, or unnecessary.
3. Official explorers or deployment sources to cross-check addresses/configuration.

For `cast`, Hunt resolves the chain automatically from audit context or the active job. If `ALCHEMY_API_KEY` is configured and Alchemy supports the chain, it uses the correct Alchemy endpoint. Otherwise it falls back to a public RPC for supported chains. The normal user should not configure RPC URL templates.

Advanced live debugging:

```bash
PROJECT=/absolute/path/to/audit-project
AUDITCTL="$PROJECT/.agents/skills/hunt-skill/scripts/auditctl.py"

python3 "$AUDITCTL" rpc-resolve --repo "$PROJECT" --chain base
python3 "$AUDITCTL" cast-read --repo "$PROJECT" --chain base \
  --operation call --address 0x... --signature "totalAssets()(uint256)"
```

For live-state setup details, read [docs/SETUP.md](docs/SETUP.md).

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
