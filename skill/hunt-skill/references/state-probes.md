# State Probes

Use State Probes only inside the `ACTIVE` job. Prefer structured weirdness over blind fuzzing.

## Probe Selection

1. Inspect relevant existing tests/harnesses first.
2. Pick one small behavior question tied to the job's invariant or bad state.
3. State the mental model first: if the protocol understanding is correct, which outcomes should be equivalent or bounded?
4. Capture concise important state before and after the action sequence.
5. Compare economically relevant before/after state, not only revert status.
6. Store unexpected behavior as `OBSERVATION`; promote to hypothesis only after attacker path, bad state, and impact are concrete.

High-value families:

- `0`, `1 wei`, dust.
- min/threshold/precision `-1`, exact, `+1`.
- partial operations.
- repeated operations.
- equivalent-path comparison, such as `deposit(100)` vs `deposit(40); deposit(60)`.
- operation reordering.
- different actors.
- two distinct logical instances resolving to the same key, account, resource, range, identifier, or artifact.
- optional-mode matrices, including flag on/off crossed with empty, zero, default, stale, or non-empty values.
- producer/consumer binding changes: vary one context field that changes what is produced or searched, then confirm whether the consumer detects the change.
- lifecycle identity reuse: old/new, cancelled/active, pre/post-upgrade, pre/post-reset, or repeated identifiers.
- time boundaries.
- realistic external-state changes.

## Lifecycle Sequences

Choose these only when the active graph exposes the corresponding boundary:

- durable output: execute -> unwind or restore the prerequisite -> consume the output;
- replay: execute -> reset/cancel/withdraw -> execute again;
- value dependence: influence price/value -> commit entitlement, debt, shares, payout, or transfer -> restore price/value;
- coupled-state singularity: drive the primary balance/supply/position to zero while a dependent value remains nonzero or stale;
- typed context: reuse the same proof/artifact while changing one material subject, domain, mode, lifecycle, source/destination, amount, or instance;
- financing: compare the minimal sequence with owned/recycled, atomic, and cross-block capital only as far as the mechanism requires.

For repeated or value-dependent paths, record per-cycle cost/proceeds/loss, the maximum plausible repetitions, and the limiting resource. A successful sequence proves mechanics only; promotion still requires attacker-created prerequisites and full-cycle impact.

Common state to snapshot when relevant: total assets, total debt, total shares, user shares, user debt, health, borrow capacity, external position value, pending amount, claim amount, fees, and lifecycle flags.

## Provenance

- Executed unit/integration/fork test with output or harness handle: may be `VERIFIED`.
- Agent-described or planned probe without execution evidence: `INFERRED` or `UNKNOWN`.
- User-supplied probe/observation: store as `USER_CONTEXT` until reproduced.

`probe-add --status VERIFIED` requires `--executed` and execution provenance such as a test name, fork handle, trace, or log reference.
