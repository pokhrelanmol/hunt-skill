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
- time boundaries.
- realistic external-state changes.

Common state to snapshot when relevant: total assets, total debt, total shares, user shares, user debt, health, borrow capacity, external position value, pending amount, claim amount, fees, and lifecycle flags.

## Provenance

- Executed unit/integration/fork test with output or harness handle: may be `VERIFIED`.
- Agent-described or planned probe without execution evidence: `INFERRED` or `UNKNOWN`.
- User-supplied probe/observation: store as `USER_CONTEXT` until reproduced.

`probe-add --status VERIFIED` requires `--executed` and execution provenance such as a test name, fork handle, trace, or log reference.
