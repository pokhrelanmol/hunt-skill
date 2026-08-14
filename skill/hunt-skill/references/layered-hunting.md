# Layered Impact-First Hunting

Use forward and backward reasoning together around one active job. Critical bugs usually compose several valid functions across time, modules, cohorts, or external protocols.

Start from:

```text
NICHE IMPACT -> FORBIDDEN STATE -> SENSITIVE CONSUMER -> ATTACKER OBJECTIVE
```

Treat the final impact as a prerequisite graph. A missing asset, inventory, capital source, permission, identity, timing control, external state, accounting representation, or unwind path is a subgoal to source or falsify before it becomes a blocker.

Select only dimensions that could materially answer whether that forbidden state is reachable: local state, economic/accounting, lifecycle/order, boundary/math, actor/cohort, permissions, external integration, live state, historical primitive, cross-chain, or State Probe.

## Forward Path: Primitive To Impact

1. Identify a permissionless or attacker-controllable transition.
2. Record exactly what state, balance, rate, cache, role, or lifecycle flag it changes.
3. Query later consumers of that changed value.
4. Treat the transition's output as a capability fragment even when it is illiquid, temporary, costly, or not directly profitable.
5. Ask whether ordering, delay, cancellation, partial failure, callback, external state, or another subsystem lets the fragment satisfy a later prerequisite.
6. Connect the primitive to a `READY` impact goal or preserve the missing edge as a subgoal/unknown before rejecting it as harmless.

## Backward Path: Impact To Trigger

1. Select one meaningful attacker objective from the impact catalog.
2. Define the exact forbidden state and sensitive consumer.
3. Walk backward through the consumer's inputs, reads, guards, calculations, and dependencies.
4. Enumerate local write paths, lifecycle transitions, economic/accounting counterparts, and external systems that can shape those inputs.
5. Identify prerequisites: assets/inventory, permissions/identities, external state, timing/order, temporary capital, repayment/restoration/unwind, and any intermediate representations the consumer accepts.
6. Intersect with attacker capabilities, resource-producing primitives, and composition subgoals to form the shortest viable lifecycle.

## Layer Questions

For each candidate chain, ask:

```text
Layer 1: What final impact does the attacker want?
Layer 2: What forbidden state is required?
Layer 3: Which sensitive consumer makes that state matter?
Layer 4: What local, economic, lifecycle, actor, external, or live facts feed it?
Layer 5: Which reachable flows can shape those inputs?
Layer 6: What fragment does each flow produce, and which later consumer can use it?
Layer 7: Which missing resources become attacker subgoals rather than blockers?
Layer 8: What keeps the bad representation alive until an irreversible consumer commits value, entitlement, or liability?
Layer 9: What capital, timing, liquidity, ordering, repayment, restoration, unwind, and cohort behavior are required?
Layer 10: What is the complete attacker balance sheet after all legs, repetition, amplification, and repayment?
Layer 11: Which check, sync, normalization, external guarantee, or recovery path kills every relevant composition route?
```

## Capability And Prerequisite Composition

Do not require a primitive to be profitable by itself. Preserve what it produces and search for consumers:

- assets, inventory, or reusable economic positions;
- rights, entitlements, permissions, identities, or execution control;
- accounting representations, cached values, prices, rates, shares, debt, or claims;
- temporary external state, callback access, timing/order control, or cross-system influence.

For each fragment, ask:

1. Which function, subsystem, integration, or identity accepts this fragment as valuable, authoritative, permissioning, or state-changing?
2. Which missing prerequisite could this fragment satisfy?
3. Can temporary capital or an earlier extracted value source the next prerequisite?
4. Does an irreversible consumer commit value or accounting before the fragment is corrected, repaid, restored, or unwound?
5. Can repetition, multiple actors, reused backing, or cross-system conversion amplify a small positive edge?

Reject only after the relevant composition routes have concrete blocker evidence. Otherwise store the fragment as an observation, unknown prerequisite, or parked subgoal.

## Composition Targets

Prioritize interactions among:

- request, fulfill, cancel, settle, claim, withdraw, liquidate;
- cached and live balances or exchange rates;
- inverse operations implemented on different paths;
- cross-contract role and authorization propagation;
- callbacks and state writes before/after external calls;
- external vaults, lending markets, AMMs, bridges, oracles, and tokens;
- delayed checkpoints, epochs, finality, and governance/config changes.

## Pattern-Inspiration Fallback

Use this only when the bounded forward/backward pass cannot produce a useful lead or discriminating next check.

1. Choose the highest-value unresolved impact goal or external integration.
2. Search historical findings for the same invariant, decision point, bad state, and attacker primitive.
3. Extract required conditions and ask whether each condition exists here.
4. Re-enter the backward path from the current protocol's decision point.
5. Reject the borrowed pattern quickly when current code lacks a required condition.

Do not keep pattern-searching merely to produce candidates. One focused pass should either create a locally anchored lead or end the fallback.

## Stop Conditions

Stop when concrete evidence rejects the chain, one unavailable external fact blocks it, it reaches `CODE_VALIDATED`, or another pass cannot name a check likely to change status. Preserve exact kill evidence and reopen conditions.

Economic rejection requires the full-lifecycle balance sheet and the sourcing/composition routes considered. Do not stop only because one leg is unprofitable, external liquidity is absent, capital is initially missing, or the manipulated state is later restored.
