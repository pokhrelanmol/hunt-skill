# HUNT Workflow

HUNT is one meaningful `ACTIVE` job attacking one protocol-specific impact, not a category scan or batch queue. Work autonomously inside the current research question, then stop before switching to an independent direction.

## Entry Gate

Require broad protocol context from RECON: scope, architecture, actors, assets, value flow, integrations, lifecycles, and important invariants. Do not require perfect deterministic coverage for every state-changing entrypoint before the first hunt.

For the `ACTIVE` Job, require deep graph/context coverage for its causal surface, not only the focal function. A variant may inherit still-valid parent coverage, but its stated delta and the edges connecting it to the inherited path must be detailed. If producer, consumer, lifecycle, call/effect, or argument coverage is stale or missing, deepen RECON for the missing surface.

Do not start from memory of source files alone. Before the Combined Impact Loop, the agent must create and query a useful graph packet for the `ACTIVE` job. The packet should include relevant impact/invariant links, attacker entrypoints or explicit `UNKNOWN`, sensitive consumers, state roots, call edges, read/write/effect edges, external integrations, and source/evidence anchors. If `research-packet`, `neighbors`, or `path` cannot retrieve these relationships, return to RECON and build the missing graph records.

## Active Job Frame

Before tracing, make the job precise:

1. Niche invariant: what specifically must remain true?
2. Forbidden state: what exact state violates it?
3. Sensitive consumer: which decision/function/accounting operation makes it matter?
4. Attacker objective: what must the attacker cause or exploit?
5. Context vector: which subject, owner, asset, scope/domain, mode, lifecycle/version, time/order, authority, source/destination, amount, nonce, or external environment must remain bound for the sensitive consumer to be correct? Select only dimensions material to this job.
6. Relevant dimensions: select only useful lenses, such as local state, economic/accounting, lifecycle/order, boundary/math, actors/cohorts, permissions, external integration, live state, historical primitive, cross-chain, or State Probe.
7. Lifecycle sketch: capability acquisition -> transient influence/action -> durable state or artifact -> prerequisite unwind -> sensitive consumer -> impact realization -> reset/replay -> full-cycle economics. Mark every unsolved stage `UNKNOWN` with its cheapest next check.

Persist the sketch through `job-upsert --attack-model` as one `JOB_ATTACK_MODEL` fact linked to the Job and relevant graph anchors. `ACTIVE` and `DONE` are mechanically gated on this fact. Update it as evidence changes; do not create another table, catalog, or parallel Job.

## Attacker Lifecycle Closure

The sketch becomes the central falsification model during HUNT:

```text
capability acquisition
-> transient influence or action
-> durable state, right, artifact, entitlement, or transfer
-> prerequisite unwind or restoration
-> sensitive protocol/integration consumer
-> impact realization
-> reset, replay, wait, or repetition
-> attacker cost/profit and victim/protocol loss across the full cycle
```

An exploit may skip a stage, but the Job must say why. A missing resource is an acquisition subgoal, not a rejection. When capital is material, test the cheapest plausible route from owned/recycled funds through atomic borrowing, collateralized or cross-block financing, third-party liquidity, and delayed future liquidity; stop when earlier evidence kills later routes. An intermediate asset or capability need not have an external market if a protocol or integration consumes it as value or authority. Restoration of temporary state does not undo a durable action committed before restoration.

The `JOB_ATTACK_MODEL` fact should stay compact and include: capability, transient influence, durable output and persistence boundary, unwind, consumer, impact, reset/repeat route, attacker costs, attacker proceeds, victim/protocol loss, limiting resource, and unresolved stages. For non-financial impacts, record the concrete authority or availability gain and the attacker's cost instead of inventing monetary profit.

## Graph-Triggered Extensions

Use only extensions activated by local RECON evidence:

- **Price/value closure:** sensitive consumer -> value used -> value source -> underlying reserves/state -> attacker influence -> freshness/window/liquidity -> durable action -> market restoration -> round-trip economics. This covers spot, TWAP, oracle, reserve ratio, share price, NAV, exchange rate, cached value, and internal accounting value without assuming any one oracle pattern.
- **Coupled-state singularity:** cross zero, empty, default, delete/reset, threshold, and rounding boundaries while another economically coupled value remains nonzero or stale. Compare equivalent paths and first/last/only-user states.
- **Typed-proof closure:** compare what a signature, message, proof, receipt, callback, or identifier actually binds with the complete context its consumer assumes. Reuse the same representation across changed subject, domain, lifecycle, mode, source/destination, amount, or instance when plausible.
- **Restorable-guard replay:** when eligibility depends on balance, allowance, liquidity, registration, role, or position state, test action -> remove/unwind prerequisite -> consume durable result, and action -> reset -> action again.
- **Economic-trust boundary:** for authorized actors, separate permission to call from permission to allocate loss, capture value, choose a victim, or violate user guarantees. Threat-model exclusions may affect reportability; they do not make the behavior economically safe.

## Combined Impact Loop

1. Load the bounded `research-packet` for the `ACTIVE` job. If it is empty, superficial, or not linked to concrete graph records, stop and repair the graph before hunting.
2. Trace backward from impact: sensitive consumer -> bad input -> state representation -> state source -> mutation path -> possible attacker primitive.
3. Trace forward from attacker: callable/actionable primitive -> state mutation -> bad representation -> sensitive consumer -> forbidden state -> impact.
4. Build or update the `JOB_ATTACK_MODEL`, then use selected dimensions together around this same forbidden state:
   - local code/dataflow: origin, cache, normalization, rounding, writers, consumers, sibling paths, guards, callbacks, inverse/cancel paths;
   - economic/accounting: economic reality vs protocol representation, stale or asymmetric updates, double counting, delayed loss, early gain, reset/restoration mismatch;
   - lifecycle/order: partial, repeated, delayed, cancelled, restored, async, reordered, or intermediate states that remain realistically reachable;
   - actor/cohort: first/last/early/late users, attacker/victim/keeper/liquidator/relayer interactions when they affect loss allocation;
   - external/live: exact external state, attacker reachability, local consumption before correction, and only necessary deployment/config facts;
   - historical: search for the primitive required by this impact, extract required conditions, then verify them locally.
5. Run [the edge-case lead pass](../references/edge-case-leads.md): compare the context vector with the fields actually used to identify, produce, validate, and consume the relevant representation. Search for fan-in, fan-out, sentinel/default ambiguity, partial binding, cross-instance effects, and lifecycle reuse.
6. Read relevant existing tests/harnesses before writing or running a probe.
7. When practical for an important job, run a focused State Probe; compare expected-equivalent before/after state and distinct-context/same-representation cases.
8. Store probe results and unexpected behavior as `STATE_PROBE` or `OBSERVATION`. An anomaly is not automatically a hypothesis.
9. Form a hypothesis only when a concrete chain connects attacker -> reachable action -> local/external state -> durable bad representation/artifact where relevant -> sensitive consumer -> forbidden state -> impact. Keep any material lifecycle gap explicit.
10. Preserve a `LEAD` when a context collision or producer/consumer mismatch reaches a sensitive consumer but a material prerequisite or consequence remains unknown. Kill it only with concrete separation, rebinding, harmlessness, or recovery evidence.
11. Falsify serious hypotheses across all material dimensions: reachability, permissions, ordering, sync/correction, persistence after unwind/restoration, external reachability, live config, timing, liquidity/capital, reset/repetition, full-cycle economics, actual impact, victim requirements, intended behavior, and known/duplicate issues.
12. Conclude the `ACTIVE` job as `DONE`, `BLOCKED`, or with a linked hypothesis.
13. Persist the result, coverage boundary, kill evidence or surviving lead, unresolved segments, and reopen condition. Compare bounded Job-family history before recommending a continuation, evidence-based reopen, graph-frontier variant, or genuinely new family.
14. If all locally promising family frontiers and material attacker-lifecycle stages are covered or explicitly killed, mark the family saturated. Documentation, blocked direct cash-out, temporary-state restoration, an illiquid intermediate artifact, an authorized actor, or unresolved financing alone is not saturation evidence. Do not create a cosmetic variant; rotate unless new evidence supplies an explicit reopen reason. Then stop for human steering.

## Additional Pattern Search

The initial job-idea pass may already have used one real finding to extract an edge case or composition. If the active code-led job still stalls, run at most one additional focused historical search anchored to the same forbidden state, sensitive consumer, integration, or attacker primitive. Convert any match into required conditions and retrace current code. Historical similarity never changes status by itself.
