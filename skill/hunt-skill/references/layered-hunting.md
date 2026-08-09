# Layered Impact-First Hunting

Use forward and backward reasoning together. Critical bugs usually compose several valid functions across time, modules, or external protocols.

## Forward Path: Primitive To Impact

1. Identify a permissionless or attacker-controllable transition.
2. Record exactly what state, balance, rate, cache, role, or lifecycle flag it changes.
3. Query later consumers of that changed value.
4. Ask whether ordering, delay, cancellation, partial failure, callback, or external state lets the favorable divergence persist.
5. Connect the primitive to a `READY` impact goal or reject it as harmless.

## Backward Path: Impact To Trigger

1. Select one meaningful attacker objective from the impact catalog.
2. Identify the final decision that must be fooled, bypassed, delayed, or made to revert.
3. Walk backward through its reads, guards, calculations, and dependencies.
4. Enumerate all write paths and external systems that can shape those inputs.
5. Intersect with attacker capabilities and compose the shortest viable flow.

## Layer Questions

For each candidate chain, ask:

```text
Layer 1: What final impact does the attacker want?
Layer 2: What protocol decision permits or prevents it?
Layer 3: What state and external facts feed that decision?
Layer 4: Which reachable flows can shape those inputs?
Layer 5: What keeps the manipulated state alive until consumption?
Layer 6: What capital, timing, liquidity, and ordering are required?
Layer 7: Which check, normalization, or recovery path kills it?
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
