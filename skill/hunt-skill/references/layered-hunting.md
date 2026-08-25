# Layered Impact-First Hunting

Use forward and backward reasoning together around one active job. Critical bugs usually compose several valid functions across time, modules, cohorts, or external protocols.

Start from:

```text
NICHE IMPACT -> FORBIDDEN STATE -> SENSITIVE CONSUMER -> ATTACKER OBJECTIVE
```

Select only dimensions that could materially answer whether that forbidden state is reachable: local state, economic/accounting, lifecycle/order, boundary/math, actor/cohort, permissions, external integration, live state, historical primitive, cross-chain, or State Probe.

## Forward Path: Primitive To Impact

1. Identify a permissionless or attacker-controllable transition.
2. Record exactly what state, balance, rate, cache, role, or lifecycle flag it changes.
3. Query later consumers of that changed value.
4. Ask whether ordering, delay, cancellation, partial failure, callback, or external state lets the favorable divergence persist.
5. Connect the primitive to a `READY` impact goal or reject it as harmless.

## Backward Path: Impact To Trigger

1. Select one meaningful attacker objective derived from the current protocol.
2. Define the exact forbidden state and sensitive consumer.
3. Walk backward through the consumer's inputs, reads, guards, calculations, and dependencies.
4. Enumerate local write paths, lifecycle transitions, economic/accounting counterparts, and external systems that can shape those inputs.
5. Intersect with attacker capabilities and compose the shortest viable flow.

## Layer Questions

For each candidate chain, ask:

```text
Layer 1: What final impact does the attacker want?
Layer 2: What forbidden state is required?
Layer 3: Which sensitive consumer makes that state matter?
Layer 4: What local, economic, lifecycle, actor, external, or live facts feed it?
Layer 5: Which reachable flows can shape those inputs?
Layer 6: What keeps the bad representation alive until consumption?
Layer 7: What capital, timing, liquidity, ordering, and cohort behavior are required?
Layer 8: Which check, sync, normalization, external guarantee, or recovery path kills it?
```

## Composition Targets

Prioritize interactions among:

- request, fulfill, cancel, settle, claim, withdraw, liquidate;
- cached and live balances or exchange rates;
- inverse operations implemented on different paths;
- cross-contract role and authorization propagation;
- callbacks and state writes before/after external calls;
- external vaults, lending markets, AMMs, bridges, oracles, and tokens;
- delayed checkpoints, epochs, finality, and governance/config changes.

## Additional Pattern Expansion

The job-idea pass may already have used one real finding to extract an edge case or composition. Use an additional historical search only when the bounded forward/backward pass cannot produce a useful lead or discriminating next check.

1. Choose the highest-value unresolved impact goal or external integration.
2. Search historical findings for the same invariant, decision point, bad state, and attacker primitive.
3. Extract required conditions and ask whether each condition exists here.
4. Re-enter the backward path from the current protocol's decision point.
5. Reject the borrowed pattern quickly when current code lacks a required condition.

Do not keep pattern-searching merely to produce candidates. One focused pass should either create a locally anchored lead or end the fallback.

## Stop Conditions

Stop when concrete evidence rejects the chain, one unavailable external fact blocks it, it reaches `CODE_VALIDATED`, or another pass cannot name a check likely to change status. Preserve exact kill evidence and reopen conditions.
