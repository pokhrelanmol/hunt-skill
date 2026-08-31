# Hunt Skill

Hunt Skill is a graph-based bug hunting skill for adversarial smart-contract audits.

It installs into a target audit repository and builds a project-local SQLite graph of contracts, functions, call sites, storage, effects, observations, hypotheses, evidence, and research jobs. Codex then uses that graph to hunt from impact backward to reachable attacker paths instead of reading the whole codebase as one giant notebook.

Graph building is a real gate, not setup theater. Hunt is supposed to create a detailed, queryable graph for the active impact before hunting: attacker entrypoints, sensitive consumers, state roots, call edges, read/write/effect edges, external dependencies, and evidence anchors. If the graph cannot explain how the impact could be reached, the agent should keep mapping instead of guessing from source-reading memory.

The skill is designed to be installed into each audit repository under `.agents/skills/hunt-skill`. Every project keeps its own `.audit/graph/audit.db`, scope snapshot, hypotheses, evidence, novelty checks, observations, and proof handoff state.

For installation, upgrades, scope setup, and troubleshooting, use [docs/SETUP.md](docs/SETUP.md). This README explains what the skill is and how the hunting loop works.

## What It Enforces

- Code and pinned configuration remain the primary evidence.
- After basic code-led RECON, the agent derives protocol-specific invariants and candidate impacts from current code, then uses applicable checklist questions and real edge cases only to challenge or expand those ideas before selecting one graph-anchored job.
- Cross-function, cross-contract, cross-transaction, and external-protocol relationships are queryable without loading a large Markdown notebook.
- Every active Job maintains a compact attacker-lifecycle model: capability -> transient influence -> durable output -> unwind -> consumer -> impact -> reset/repeat -> full-cycle economics. Unsolved stages remain explicit subgoals instead of premature rejection reasons.
- Edge-case leads come from reachable intersections: Hunt checks whether distinct identities, modes, lifecycle stages, or domains collapse into the same key, resource, proof, callback, cache, or accepted condition before a sensitive consumer acts.
- Checklist and historical patterns are used in a bounded post-RECON idea pass, then again to validate novelty and known-issue status.
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

Follow [docs/SETUP.md](docs/SETUP.md) once, open Codex in the target protocol repository, and say:

```text
Use Hunt Skill on this repo.
```

## Primary Workflow

1. Complete installation and scope setup using [docs/SETUP.md](docs/SETUP.md).
2. Open Codex inside the target protocol repository.
3. Say: `Use Hunt Skill on this repo.`
4. Provide scope, docs, deployment context, or protocol explanations only when asked.

Hunt handles `auditctl`, SQLite, graph retrieval, State Probes, Solodit research, chain detection, Tenderly, `cast`, RPC selection, and PoC handoff internally.

## Interactive Hunt

Hunt is a human + AI collaborative research workflow:

```text
one ACTIVE job
-> deep investigation with Hunt methodology
-> conclusion
-> recommend next direction
-> stop for human steering
```

Before selecting that Job, Hunt reviews prior Job and impact coverage, derives lightweight candidates from current code, and chooses the direction with the strongest combination of plausible impact, reachability, local signal, composition potential, and a cheap discriminating check. The Job narrows the security question, not the causal surface: any function or integration that produces a trusted input or consumes an attacker-influenced output remains in scope for its graph.

Job ideation only sketches the attack lifecycle and marks missing stages `UNKNOWN`; it does not require a solved exploit before research begins. During HUNT, that sketch becomes one `JOB_ATTACK_MODEL` fact backed by graph nodes and evidence. Price/value closure, coupled-state singularities, typed-proof mismatches, reset/replay paths, and economic-trust boundaries are activated only when the mapped code contains the corresponding signal.

When the surface-level Jobs are already hunted, Hunt expands the coverage frontier. It may continue an unresolved Job, reopen one because new evidence changed an assumption, create a `VARIANT_OF` Job for a materially different producer/consumer/lifecycle/prerequisite/integration path, or rotate to a new family. Variants inherit the parent graph and killed paths, then map only the new delta. Once the supported frontiers are exhausted, the family is marked saturated and cannot receive another cosmetic variant without an explicit new-evidence reason.

Requests like `hunt`, `look for bugs`, `check this flow`, `investigate this`, or `go deeper` use this workflow. Hunt works autonomously inside the current research question, then recommends the next direction and waits for human steering before changing research direction.

## Built-In Methodology vs External Capabilities

Hunt does not depend on a pile of reasoning agents. The core methodology is built into this skill:

- first-principles questioning;
- state consistency analysis;
- economic and accounting analysis;
- lifecycle and ordering analysis;
- boundary, actor, and permission reasoning;
- external reachability reasoning;
- State Probes;
- falsification and skeptical validation.

External tools are capability providers. Use them only when the current ACTIVE JOB needs evidence that local code, graph context, probes, and reasoning cannot provide efficiently:

- historical finding retrieval with Solodit or similar sources;
- live-chain reads with `cast`;
- fork, trace, simulation, or state override with Tenderly;
- executable proof through the configured dedicated PoC skill;
- a specialized external analyzer only when it returns unique evidence for the active job.

If local code and the SQLite graph answer the question, Hunt should not load another reasoning skill just to think harder.

## Invoke The Skill

Examples:

```text
Use $hunt-skill to map this protocol's asset and state relationships.
Use $hunt-skill to investigate whether cancellation can desynchronize debt.
Use $hunt-skill to continue HYP-003 and try to falsify it.
```

The default interaction is collaborative `CHAT`; concrete research proceeds as one bounded `ACTIVE` job at a time.

## How The Graph-Based Hunt Works

Hunt keeps one active research question at a time:

```text
protocol brain
-> protocol-specific invariant
-> niche forbidden state
-> one ACTIVE job
-> backward trace from impact + forward trace from attacker
-> attacker lifecycle closure with explicit UNKNOWN subgoals
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

For example, if a consumer reads a price, rate, reserve ratio, NAV, share price, exchange rate, or cached valuation, Hunt expands that local graph into a value lifecycle: what value is consumed, where it comes from, which underlying state can move it, whether the attacker can influence it in the relevant window, what durable action is committed before the value normalizes, and whether the entire round trip is profitable. A price move without a durable consumer or viable economics is killed; a temporary price that creates a lasting entitlement is not dismissed merely because the market later recovers.

State Probes deliberately poke underexplored reachable behavior: `1 wei`, dust, threshold +/- 1, partial operations, repeated operations, equivalent paths such as `deposit(100)` versus `deposit(40); deposit(60)`, operation reordering, different actors, time boundaries, and realistic external-state changes. When locally triggered, they also test sequences such as influence value -> commit durable action -> restore value, execute -> unwind -> consume output, execute -> reset -> execute again, or primary state reaches zero while coupled state remains nonzero. Unexpected results become `OBSERVATION`, not automatically a bug.

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

For optional keys and live-state setup details, read [docs/SETUP.md](docs/SETUP.md). The installed skill's [CLI reference](skill/hunt-skill/references/cli.md) contains operational command examples.

## Update An Installed Project

Use the update procedure in [docs/SETUP.md](docs/SETUP.md). Project audit state remains in `.audit/` and is not replaced.

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
