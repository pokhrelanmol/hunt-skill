# Graph And Audit Schema

SQLite at `.audit/graph/audit.db` is the operational source of truth. Source text remains in the repository; the database stores coordinates and hashes.

## Identity

Use stable semantic IDs:

```text
contract:src/Vault.sol:Vault
function:src/Vault.sol:Vault.redeem(uint256,address,address)
parameter:function:src/Vault.sol:Vault.redeem(uint256,address,address):0
callsite:function:src/Vault.sol:Vault.redeem(uint256,address,address):ast-431:offset-9210
storage:src/Vault.sol:Vault.totalDebt
effect:callsite:function:src/Vault.sol:Vault.redeem(uint256,address,address):ast-431:offset-9210:0
role:keeper
asset:USDC
external:morpho-blue
invariant:vault-shares-track-economic-assets
impact:vault-withdrawal-shortfall
HYP-001
```

Do not use line numbers as identity. Put line ranges in evidence.

Call-site identity must include the caller plus a compiler/source identity such as AST ID and byte offset. Never collapse repeated calls because they share a caller and callee. Parameter position is canonical and zero-based.

## Core Records

| Record | Purpose |
|---|---|
| `snapshots`, `files` | Pin commit, dirty state, exact scope, and SHA-256 freshness. |
| `nodes` | Contracts, functions, storage, roles, assets, external systems, lifecycle states. |
| `relations` | Directed typed edges between nodes. |
| `evidence` | Source, documentation, test, audit, or on-chain support for any record. |
| `facts` | Verified observations, inferences, unresolved assumptions, user context, observations, and state probes. |
| `invariants` | Protocol properties that should remain true. |
| `impact_goals` | Protocol-specific bad states and attacker objectives linked to invariants. |
| `hypotheses` | Leads and their disposition, root cause, impact, blockers, and next check. |
| `hypothesis_links` | Evidence graph for each hypothesis. |
| `known_findings`, `novelty_checks` | Historical precedents and duplicate screening. |
| `live_evidence` | Chain/block/address-bound configuration, simulation, and trace observations. |
| `investigations` | Research jobs; use mode `JOB` and keep only one `ACTIVE` job at a time. |
| `manual_approvals` | Legacy approval records retained for old databases, not the normal PoC path. |

The current generic records can represent deterministic RECON facts as typed nodes, relations, and evidence. Do not claim that a dedicated normalized dataflow table exists unless the installed tooling actually provides one.

## Required RECON Records

The graph must be query-useful, not ceremonial. Do not create a few placeholder nodes and proceed. For the active job, the graph should let a later agent answer:

- which attacker-accessible entrypoints can touch the selected impact;
- which sensitive consumer makes the bad state matter;
- which state roots, cached values, balances, shares, debts, roles, prices, or lifecycle flags feed that consumer;
- which functions write or derive those values;
- which external systems are trusted;
- which path connects an attacker action to the local/external state and then to the sensitive consumer;
- which logical identities, modes, lifecycle stages, or domains map to each representation, key, resource, proof, receipt, callback, or cached record trusted by the consumer;
- which material context dimensions the producer binds and which dimensions the consumer independently validates;
- which exact source/evidence anchors support or limit each edge.

For every scoped function, retain compact queryable facts for:

- canonical parameters: position, name, type, storage location, source span, and compiler node ID;
- unique call sites: caller, declared callee, callee expression, dispatch, AST ID, byte offset, condition, status, confidence, and baseline;
- argument bindings: call site, canonical parameter, exact expression, expression type, origin kind, and origin node IDs;
- return components: type, binding, and whether assigned, tuple-bound, ignored, returned, or consumed;
- runtime targets: candidate function, resolution kind, evidence, confidence, and separate live narrowing;
- direct effects: local storage, token ledger, external protocol, or unresolved assembly, with operation, target/value expressions, condition, and source span;
- effective effects: entrypoint, leaf, direct effect, shortest ordered call-site path, depth, status, and confidence;
- extraction coverage: explicit complete, incomplete, zero-call, or zero-effect disposition for each scoped function.

If the available deterministic tooling cannot populate a field, store the missing fact as `UNKNOWN` with the exact next check. Never fill a mechanical field from model intuition and label it `VERIFIED`.

## Graph Usefulness Gate

Before HUNT job execution, query the graph. A useful active-job graph has:

- `JOB` linked to the impact/invariant being tested;
- graph nodes for relevant attacker entrypoints, sensitive consumers, state roots, roles/assets, and external dependencies;
- nodes and edges for material logical contexts, shared resources/keys, produced artifacts, mode/default encodings, and consumer validation boundaries;
- `CALLS`/dispatch edges for relevant local paths;
- `READS`, `WRITES`, `DERIVES_FROM`, `TRANSFERS`, `MINTS`, `BURNS`, `DEPOSITS`, `WITHDRAWS`, `BORROWS`, `REPAYS`, `LIQUIDATES`, or namespaced effect edges as applicable;
- evidence on verified graph edges;
- explicit `UNKNOWN` records for unresolved dispatch, missing build artifacts, assembly, dynamic targets, or unverified external behavior.

If the graph cannot support a backward trace from sensitive consumer to trusted state/source and a forward trace from attacker entrypoint to mutation/effect, do not hunt yet. Build the missing graph records first.

## Statuses

Evidence status:

- `VERIFIED`: mechanically extracted or directly checked against cited evidence.
- `INFERRED`: reasoned from evidence but not mechanically guaranteed.
- `UNKNOWN`: intentionally unresolved.
- `STALE`: backing source changed after the record was checked.

Hypothesis lifecycle:

```text
LEAD -> INVESTIGATING -> CODE_VALIDATED -> POC_VALIDATED -> CONFIRMED
                         |                |
                         |                +-> POC_BLOCKED when proof environment/context is missing
                         +-> BLOCKED
Any nonterminal state -> REJECTED
```

`CODE_VALIDATED` automatically runs PoC handoff for the same hypothesis. The handoff checks current source scope and a configured dedicated PoC skill path; the user is asked only when proof is blocked by missing context or environment.

Research job lifecycle:

```text
NEXT -> ACTIVE -> DONE
        |        |
        +-> PARKED
        +-> BLOCKED
```

User context lifecycle:

```text
USER_CONTEXT fact starts UNKNOWN unless independently verified.
New context must be linked to affected jobs, hypotheses, assumptions, or rejected paths before it changes audit state.
```

State probe lifecycle:

```text
STATE_PROBE starts INFERRED unless an executed harness/trace/log supports VERIFIED.
Unexpected probe output becomes OBSERVATION first, not an automatic hypothesis.
```

Impact lifecycle:

- `DRAFT`: generic seed or missing protocol fields; never use as a complete hunt target.
- `READY`: invariant, protocol case, decision point, bad state, attacker goal, and candidate primitives are concrete.
- `COVERED`: all promising flows were investigated or explicitly rejected.

## Relationship Vocabulary

Prefer these controlled types; add a namespaced extension only when none fits:

```text
DECLARES, INHERITS, OVERRIDES, CALLS, DELEGATECALLS, CALLBACKS_TO
BINDS_ARGUMENT, BINDS_RETURN, POSSIBLE_TARGET, LIVE_TARGET
READS, WRITES, DERIVES_FROM, INVALIDATES, CHECKPOINTS
DIRECT_EFFECT, EFFECTIVE_EFFECT, PATH_STEP
GUARDED_BY, AUTHORIZES, GRANTS_ROLE, REVOKES_ROLE, TRUSTS
TRANSFERS, MINTS, BURNS, DEPOSITS, WITHDRAWS, BORROWS, REPAYS
LIFECYCLE_NEXT, CANCELS, SETTLES, LIQUIDATES, CLAIMS
ENFORCES, RELIES_ON, CONFLICTS_WITH, CONSUMES, PRODUCES
EXTERNALIZES_TO, CONFIGURED_BY, PRICES, BACKS, BREAKS
IDENTIFIED_BY, MAPS_TO, SHARES_RESOURCE, BINDS_CONTEXT, VALIDATES_CONTEXT
```

Every relation needs endpoints, status, confidence, and evidence or an explicit `UNKNOWN` note. Name similarity alone never proves an edge.

## Production Path Policy

- Primary scoped contracts and explicitly classified production dependencies may enter default call and effect paths.
- Tests, mocks, handlers, harnesses, deployment scripts, and test-only overrides are supporting context only.
- Compiler candidate targets and live-confirmed targets remain distinguishable.
- Interface, virtual, proxy, beacon, diamond, and dynamic dispatch stay `UNKNOWN` or `INFERRED` until their candidate set or deployment evidence is recorded.
- Persistent storage requires an lvalue rooted in a state variable or proven `storage` alias. A struct-field declaration alone is insufficient.

## Query Bounds

- Search: 20 rows by default.
- Neighbor expansion: one hop by default, maximum three.
- Path: maximum depth three unless the user approves a larger search.
- Context: return IDs, summaries, unresolved assumptions, and source coordinates before source text.
- Do not print or load the entire graph by default.
