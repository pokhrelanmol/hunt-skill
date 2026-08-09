# Graph And Audit Schema

SQLite at `.audit/graph/audit.db` is the operational source of truth. Source text remains in the repository; the database stores coordinates and hashes.

## Identity

Use stable semantic IDs:

```text
contract:src/Vault.sol:Vault
function:src/Vault.sol:Vault.redeem(uint256,address,address)
storage:src/Vault.sol:Vault.totalDebt
role:keeper
asset:USDC
external:morpho-blue
invariant:vault-shares-track-economic-assets
impact:vault-withdrawal-shortfall
HYP-001
```

Do not use line numbers as identity. Put line ranges in evidence.

## Core Records

| Record | Purpose |
|---|---|
| `snapshots`, `files` | Pin commit, dirty state, exact scope, and SHA-256 freshness. |
| `nodes` | Contracts, functions, storage, roles, assets, external systems, lifecycle states. |
| `relations` | Directed typed edges between nodes. |
| `evidence` | Source, documentation, test, audit, or on-chain support for any record. |
| `facts` | Verified observations, inferences, and unresolved assumptions. |
| `invariants` | Protocol properties that should remain true. |
| `impact_goals` | Protocol-specific bad states and attacker objectives linked to invariants. |
| `hypotheses` | Leads and their disposition, root cause, impact, blockers, and next check. |
| `hypothesis_links` | Evidence graph for each hypothesis. |
| `known_findings`, `novelty_checks` | Historical precedents and duplicate screening. |
| `live_evidence` | Chain/block/address-bound configuration, simulation, and trace observations. |
| `manual_approvals` | Human approval records binding PoC work to a claim and source snapshot. |

## Statuses

Evidence status:

- `VERIFIED`: mechanically extracted or directly checked against cited evidence.
- `INFERRED`: reasoned from evidence but not mechanically guaranteed.
- `UNKNOWN`: intentionally unresolved.
- `STALE`: backing source changed after the record was checked.

Hypothesis lifecycle:

```text
LEAD -> INVESTIGATING -> CODE_VALIDATED -> MANUAL_VALIDATED -> CONFIRMED
                         |                |
                         |                +-> POC_BLOCKED when approval is stale/missing
                         +-> BLOCKED
Any nonterminal state -> REJECTED
```

Only the user can authorize `MANUAL_VALIDATED`. A PoC gate checks the approval, claim hash, and current source scope every time.

Impact lifecycle:

- `DRAFT`: generic seed or missing protocol fields; never use as a complete hunt target.
- `READY`: invariant, protocol case, decision point, bad state, attacker goal, and candidate primitives are concrete.
- `COVERED`: all promising flows were investigated or explicitly rejected.

## Relationship Vocabulary

Prefer these controlled types; add a namespaced extension only when none fits:

```text
DECLARES, INHERITS, OVERRIDES, CALLS, DELEGATECALLS, CALLBACKS_TO
READS, WRITES, DERIVES_FROM, INVALIDATES, CHECKPOINTS
GUARDED_BY, AUTHORIZES, GRANTS_ROLE, REVOKES_ROLE, TRUSTS
TRANSFERS, MINTS, BURNS, DEPOSITS, WITHDRAWS, BORROWS, REPAYS
LIFECYCLE_NEXT, CANCELS, SETTLES, LIQUIDATES, CLAIMS
ENFORCES, RELIES_ON, CONFLICTS_WITH, CONSUMES, PRODUCES
EXTERNALIZES_TO, CONFIGURED_BY, PRICES, BACKS, BREAKS
```

Every relation needs endpoints, status, confidence, and evidence or an explicit `UNKNOWN` note. Name similarity alone never proves an edge.

## Query Bounds

- Search: 20 rows by default.
- Neighbor expansion: one hop by default, maximum three.
- Path: maximum depth three unless the user approves a larger search.
- Context: return IDs, summaries, unresolved assumptions, and source coordinates before source text.
- Do not print or load the entire graph by default.
