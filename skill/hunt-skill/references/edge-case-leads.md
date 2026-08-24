# Edge-Case Leads And Context Binding

Use this pass inside one impact-driven `ACTIVE` job. It is codebase-agnostic: reason about logical context and accepted representations rather than named protocols, assets, or vulnerability classes.

An edge case is not merely an unusual input. It is a reachable intersection of individually valid states, identities, modes, domains, or lifecycle stages where a sensitive consumer receives less context than it assumes.

## Context Model

For the active sensitive consumer, define only the material fields of its logical context:

```text
subject/instance/owner
asset or value domain
scope, namespace, chain, market, tenant, or subsystem
mode and authority
lifecycle state or version
time range and ordering
source, destination, amount, nonce, or request identity
external environment or dependency state
```

Then record:

```text
required_context  = dimensions the consumer assumes are preserved
identity_key      = dimensions used to locate the state/resource
producer_bound    = dimensions that shape or are committed into the result
consumer_checked  = dimensions independently validated before the effect
```

Do not require every possible field. The useful question is whether any omitted material dimension lets distinct logical contexts become indistinguishable.

## Generate Collision Candidates

Search both backward from the sensitive consumer and forward from attacker-controlled inputs for these general relationships:

1. **Fan-in:** two distinct logical subjects, instances, domains, or lifecycle states can map to the same storage key, account, position, range, hash, nonce, queue slot, external resource, or cached record.
2. **Fan-out:** one proof, receipt, signature, callback, return value, cache entry, or capability can be accepted by more contexts than the producer intended.
3. **Ambiguous modes:** flags, enums, optional fields, empty collections, zero/default values, or sentinels permit contradictory or non-canonical combinations.
4. **Partial binding:** an identifier or artifact commits to only a subset of the fields that determine ownership, meaning, freshness, or authorization.
5. **Producer/consumer mismatch:** a field changes what the producer searches, proves, calculates, or returns, but the consumer does not validate that field or interprets the result as a stronger/different statement.
6. **Cross-instance effects:** an action addressed to one instance can read, remove, settle, invalidate, credit, debit, or mutate a resource economically belonging to another.
7. **Lifecycle reuse:** old/new, active/cancelled, pre/post-reset, pre/post-upgrade, or repeated states reuse an identifier or artifact without version/freshness separation.

Treat permissionless triggers, attacker-chosen fields, legitimate multi-instance configurations, delayed execution, and external request construction as reachability amplifiers. A privileged or uncommon setup does not by itself kill the lead when the state is permitted and a lower-privileged actor can trigger or benefit from the sensitive action.

## Graph Procedure

Represent the material chain with existing SQLite nodes and relations:

```text
logical context A ----\
                       -> representation/key/resource -> sensitive consumer -> impact
logical context B ----/

attacker input -> producer/request -> artifact/result -> consumer validation -> effect
```

Use `IDENTIFIED_BY`, `MAPS_TO`, `SHARES_RESOURCE`, `PRODUCES`, `CONSUMES`, `BINDS_CONTEXT`, `VALIDATES_CONTEXT`, `RELIES_ON`, and ordinary call/read/write/effect edges as applicable. Every semantic edge remains `INFERRED` or `UNKNOWN` until evidence supports it.

With bounded `neighbors`, `path`, or `research-packet` queries, ask:

- Do multiple logical-context nodes converge on one representation or resource?
- Can one artifact reach multiple consumers or contexts?
- Which input fields change producer semantics, and where are they bound or revalidated?
- Does the consumer distinguish ownership, scope, mode, freshness, and lifecycle identity before its irreversible effect?
- Can correction or recovery occur before the sensitive consumer acts?

If these relationships are material but absent, return to RECON. Do not perform the pass from source-reading memory alone.

## State-Probe Matrix

Choose the smallest matrix that tests the suspected equivalence class:

```text
same context / same representation       expected control
different context / different representation
different context / same representation  collision candidate
same context / altered producer field    binding candidate
```

Cross optional flags or modes with zero, empty, default, stale, and non-empty values when those combinations are representable. Compare the full before/after state of both the addressed instance and any potentially aliased instance. Store surprising behavior as an `OBSERVATION` first.

## Lead And Rejection Rules

Create a bounded `LEAD` when:

- two distinct logical contexts can plausibly resolve to the same accepted representation/resource, or producer and consumer semantics plausibly differ;
- a sensitive consumer can be reached from that representation; and
- at least one material path to harmful effect remains undisproved.

The lead must name the collision/mismatch condition, affected consumer, possible victim state, known trigger, missing prerequisite, and next discriminating check. Do not inflate it into a finding before the complete attacker and impact path exists.

Reject only with concrete evidence that:

- construction or deployment constraints make the intersection unreachable;
- ownership/domain/mode/version/freshness is completely rebound before consumption;
- the alleged contexts are intentionally and safely equivalent;
- the effect cannot reach meaningful victim state; or
- correction/recovery reliably occurs before harm.

Rarity, an inconvenient setup, a trusted configuration step, or passing local checks are not sufficient rejection reasons by themselves.
