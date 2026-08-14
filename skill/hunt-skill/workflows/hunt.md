# HUNT Workflow

HUNT is one meaningful `ACTIVE` job attacking one protocol-specific impact, not a category scan or batch queue. Work autonomously inside the current research question. In normal interactive HUNT, stop before switching to an independent direction; in FULL AUDIT, [full-audit.md](full-audit.md) may feed the next agenda job into this same workflow.

## Entry Gate

For normal interactive hunting, require broad protocol context from RECON: scope, architecture, actors, assets, value flow, integrations, lifecycles, and important invariants. Do not require perfect deterministic coverage for every state-changing entrypoint before the first hunt.

For the `ACTIVE` job, require deep local graph/context coverage for the relevant subsystem, function, state, integration, or impact. If local call/effect/argument coverage is stale or missing, deepen RECON only for that surface.

Do not start from memory of source files alone. Before the Combined Impact Loop, the agent must create and query a useful graph packet for the `ACTIVE` job. The packet should include relevant impact/invariant links, attacker entrypoints or explicit `UNKNOWN`, sensitive consumers, state roots, call edges, read/write/effect edges, external integrations, and source/evidence anchors. If `research-packet`, `neighbors`, or `path` cannot retrieve these relationships, return to RECON and build the missing graph records.

## Active Job Frame

Before tracing, make the job precise:

1. Terminal attacker outcome: what concrete asset, right, avoided liability, victim loss, or protocol-owned value changes at the end of the lifecycle?
2. Niche invariant: what specifically must remain true?
3. Forbidden state: what exact state violates it?
4. Sensitive consumer and irreversible consumer: which decision/function/accounting operation makes that state matter, and what transfer, entitlement, liability change, or accounting commitment becomes hard to unwind?
5. Attacker objective: what must the attacker cause, obtain, avoid, repay, restore, or exploit?
6. Prerequisite graph: list required assets/inventory, permissions/identities, accounting representations, external state, timing/ordering control, repayment/restoration/unwind requirements, and unknown missing edges.
7. Relevant dimensions: select only useful lenses, such as local state, economic/accounting, lifecycle/order, boundary/math, actors/cohorts, permissions, external integration, live state, historical primitive, cross-chain, or State Probe.

## Combined Impact Loop

1. Load the bounded `research-packet` for the `ACTIVE` job. If it is empty, superficial, or not linked to concrete graph records, stop and repair the graph before hunting.
2. Trace backward from impact: sensitive consumer -> bad input -> state representation -> state source -> mutation path -> possible attacker primitive.
3. Trace forward from attacker: callable/actionable primitive -> state mutation -> bad representation -> sensitive consumer -> forbidden state -> impact.
4. For every successful primitive, record the capability fragment it produces even when it is not independently profitable: asset/inventory, entitlement, accounting or cached state, pricing influence, callback access, timing/execution control, identity/permission, reusable economic position, or external-state influence.
5. Search whether each fragment satisfies a prerequisite of another function, subsystem, integration, transaction, identity, or later lifecycle step. After obtaining any asset, right, entitlement, representation, or capability, query graph consumers that accept it as valuable, authoritative, or permissioning.
6. When a required resource appears missing, turn it into a subgoal instead of a rejection. Check temporary sources, protocol-native sources, external sources, iterative/cyclic sources, and outputs from other suspicious primitives. Preserve unresolved sources as `UNKNOWN` prerequisite edges or composition subgoals.
7. Maintain an attacker balance sheet for the whole lifecycle: assets acquired, liabilities created or avoided, temporary capital, protocol-owned value released, claims/entitlements created and consumed, fees, slippage, penalties, repayment, restoration, unwind, final attacker profit, and protocol/victim loss.
8. Identify the earliest irreversible consumer. Temporary or restored state is enough when value, entitlement, liability, or accounting is committed before correction.
9. Search for amplification after any extraction or capability: repetition, multiple actors/identities, reused backing, cross-system conversion, or using extracted value to satisfy another prerequisite.
10. Use selected dimensions together around this same forbidden state:
   - local code/dataflow: origin, cache, normalization, rounding, writers, consumers, sibling paths, guards, callbacks, inverse/cancel paths;
   - economic/accounting: economic reality vs protocol representation, stale or asymmetric updates, double counting, delayed loss, early gain, reset/restoration mismatch;
   - lifecycle/order: partial, repeated, delayed, cancelled, restored, async, reordered, or intermediate states that remain realistically reachable;
   - actor/cohort: first/last/early/late users, attacker/victim/keeper/liquidator/relayer interactions when they affect loss allocation;
   - external/live: exact external state, attacker reachability, local consumption before correction, and only necessary deployment/config facts;
   - historical: search for the primitive required by this impact, extract required conditions, then verify them locally.
11. Read relevant existing tests/harnesses before writing or running a probe.
12. When practical for an important job, run a focused State Probe; compare expected-equivalent before/after state.
13. Store probe results and unexpected behavior as `STATE_PROBE` or `OBSERVATION`. An anomaly is not automatically a hypothesis.
14. Form a hypothesis only when a concrete composed chain connects attacker -> prerequisite sourcing -> one or more capability fragments -> local/external state -> sensitive/irreversible consumer -> forbidden state -> terminal impact. Do not require each fragment to be independently profitable.
15. Falsify serious hypotheses across all material dimensions: reachability, permissions, ordering, sync/correction, external reachability, live config, timing, liquidity/capital sourcing, actual impact, full-lifecycle balance sheet, repayment/restoration/unwind, amplification, victim requirements, intended behavior, and known/duplicate issues.
16. Reject on economics only after recording the exact missing prerequisite, plausible sourcing/composition routes considered, evidence blocking each relevant route, the full-lifecycle balance sheet, and precise reopen conditions. If a meaningful fragment remains but the full chain is unknown, preserve it as `OBSERVATION`, `STATE_PROBE`, `UNKNOWN` prerequisite, or composition subgoal.
17. Conclude the `ACTIVE` job as `DONE`, `BLOCKED`, or with a linked hypothesis.
18. Persist the result, explain what was learned/rejected/uncertain/suspicious, recommend the next highest-value direction, and stop for human steering unless the persisted mode is `FULL_AUDIT`.

## Pattern Fallback

If the active code-led job stalls, run one focused historical search anchored to the same forbidden state, sensitive consumer, integration, or attacker primitive. Convert any match into required conditions and retrace current code. Historical similarity never changes status by itself.
