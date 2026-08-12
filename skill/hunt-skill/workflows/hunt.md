# HUNT Workflow

HUNT is one meaningful `ACTIVE` job attacking one protocol-specific impact, not a category scan or batch queue. Work autonomously inside the current research question; stop before switching to an independent direction.

## Entry Gate

For normal interactive hunting, require broad protocol context from RECON: scope, architecture, actors, assets, value flow, integrations, lifecycles, and important invariants. Do not require perfect deterministic coverage for every state-changing entrypoint before the first hunt.

For the `ACTIVE` job, require deep local graph/context coverage for the relevant subsystem, function, state, integration, or impact. If local call/effect/argument coverage is stale or missing, deepen RECON only for that surface.

## Active Job Frame

Before tracing, make the job precise:

1. Niche invariant: what specifically must remain true?
2. Forbidden state: what exact state violates it?
3. Sensitive consumer: which decision/function/accounting operation makes it matter?
4. Attacker objective: what must the attacker cause or exploit?
5. Relevant dimensions: select only useful lenses, such as local state, economic/accounting, lifecycle/order, boundary/math, actors/cohorts, permissions, external integration, live state, historical primitive, cross-chain, or State Probe.

## Combined Impact Loop

1. Load the bounded `research-packet` for the `ACTIVE` job.
2. Trace backward from impact: sensitive consumer -> bad input -> state representation -> state source -> mutation path -> possible attacker primitive.
3. Trace forward from attacker: callable/actionable primitive -> state mutation -> bad representation -> sensitive consumer -> forbidden state -> impact.
4. Use selected dimensions together around this same forbidden state:
   - local code/dataflow: origin, cache, normalization, rounding, writers, consumers, sibling paths, guards, callbacks, inverse/cancel paths;
   - economic/accounting: economic reality vs protocol representation, stale or asymmetric updates, double counting, delayed loss, early gain, reset/restoration mismatch;
   - lifecycle/order: partial, repeated, delayed, cancelled, restored, async, reordered, or intermediate states that remain realistically reachable;
   - actor/cohort: first/last/early/late users, attacker/victim/keeper/liquidator/relayer interactions when they affect loss allocation;
   - external/live: exact external state, attacker reachability, local consumption before correction, and only necessary deployment/config facts;
   - historical: search for the primitive required by this impact, extract required conditions, then verify them locally.
5. Read relevant existing tests/harnesses before writing or running a probe.
6. When practical for an important job, run a focused State Probe; compare expected-equivalent before/after state.
7. Store probe results and unexpected behavior as `STATE_PROBE` or `OBSERVATION`. An anomaly is not automatically a hypothesis.
8. Form a hypothesis only when a concrete chain connects attacker -> reachable action -> local/external state -> bad representation -> sensitive consumer -> forbidden state -> impact.
9. Falsify serious hypotheses across all material dimensions: reachability, permissions, ordering, sync/correction, external reachability, live config, timing, liquidity/capital, actual impact, victim requirements, intended behavior, and known/duplicate issues.
10. Conclude the `ACTIVE` job as `DONE`, `BLOCKED`, or with a linked hypothesis.
11. Persist the result, explain what was learned/rejected/uncertain/suspicious, recommend the next highest-value direction, and stop for human steering.

## Pattern Fallback

If the active code-led job stalls, run one focused historical search anchored to the same forbidden state, sensitive consumer, integration, or attacker primitive. Convert any match into required conditions and retrace current code. Historical similarity never changes status by itself.
