# RECON Workflow

RECON has two depths: a reusable global structural map of the agreed scope, and deep local coverage for the chosen Job. It owns graph construction; investigation may return here to resolve new dependencies.

## Phase 1: Bound The Map

1. Lock a clean commit or explicit baseline snapshot, exact primary scope, production dependencies, and supporting-only paths.
2. Classify tests, mocks, handlers, harnesses, and deployment scripts as supporting context.

**Exit:** Scope, baseline, support-only paths, and recon depth are explicit.

## Phase 2: Global Structural Recon

1. Understand architecture, actors, assets, money/value flow, integrations, major lifecycles, documented behavior, and important invariants.
2. Inventory every production contract/module in the agreed scope, all external/public state-changing entrypoints (including inherited functions, fallback/receive and callbacks), persistent state roots, and external dependencies. Include read-only interfaces consumed by integrations. Internal helpers and modifiers connect their callers to direct effects. Separate supporting tests/mocks from production paths.
3. Prefer compiler/build artifacts for declarations, direct calls, and provable reads/writes. Record dynamic dispatch, storage aliases, assembly, missing artifacts, and unknown external targets as extraction gaps. Do not invent resolved edges or claim that `auditctl` itself extracts compiler graphs.
4. Store compact `RECON_COVERAGE` facts against module/function nodes: baseline, mapped declarations/edges, unresolved areas, exclusions with reasons, and next extraction check. Compare the inventory with scoped files; give every scoped module a disposition. Record zero effects separately from unexamined effects. Reuse unchanged coverage and refresh affected records only.
5. Review bounded neighborhoods for discovery signals: shared state with multiple consumers or differently guarded writers, artifacts crossing subsystem boundaries, and writes/reads spanning different lifecycle stages. A relationship alone is not a defect. Trust differences, coupled state, and context collisions require evidence and remain `INFERRED` or `UNKNOWN` until checked. Preserve useful signals with `fact-upsert --kind OBSERVATION --subject-id <graph-anchor>` and source evidence; do not attach unrelated discoveries to the active Job or activate another Job.
6. Pass the inventory, observations, and material gaps to [Job ideation](../references/job-ideation.md). Broad mapping does not require argument provenance, complete transitive effects, economic feasibility, or full lifecycle closure for every function. If extraction is incomplete, state the limit; block only research that depends on the missing relationships.

**Exit:** The agreed scope has a queryable inventory and explicit coverage gaps, sufficient to propose ranked Jobs without claiming a complete audit.

## Phase 3: Deep Local Recon

**Entry:** An `ACTIVE` job, subsystem, function, state variable, integration, invariant, or impact is selected.

1. Build the graph for the selected Job's causal surface, not merely its focal function. Close over the sensitive consumer's trusted inputs, every material local/external producer of those inputs, attacker paths to the producers, later consumers of attacker-influenced outputs, and relevant sibling/inverse lifecycle paths.
2. Compile the pinned baseline when feasible and use compiler AST/build artifacts for declarations, overloads, modifiers, source spans, and resolvable calls.
3. Create nodes for relevant contracts, external/public functions, internal functions, modifiers, storage/state roots, roles, assets, lifecycle states, external systems, logical identities/instances, shared resource keys, produced artifacts when material, tests/harness anchors, invariants, impacts, and the `ACTIVE` job.
4. Give every invocation its own call-site identity, including repeated and nested calls on the same line.
5. For relevant call sites, record caller, declared callee, dispatch kind, condition, argument expression, callee parameter binding, argument origin IDs, and return use.
6. Represent modifiers, `using for`, tuple returns, callbacks, hooks, internal/external/library/super/virtual/interface/low-level/delegate/static/dynamic dispatch, and runtime target candidates when relevant to the job.
7. Mark mechanically proven facts `VERIFIED`, semantic/economic interpretations and possible runtime targets `INFERRED`, and unresolved dispatch or assembly `UNKNOWN`.

### Integration Semantics

For each material external value or operation, trace the local consumer to the actual dependency implementation and its specification. Record what the value represents, units/precision, whether it is stored, projected, or settled, what updates it, and when the consuming transaction observes that update. Check that local accounting and external execution use the same effective state, especially around interest/fee accrual, checkpoints, rebases, settlement, and callbacks. A trusted provider may return a valid cached value that is unsuitable for the consumer's assumption; no manipulated input is required for an integration mismatch.

Pin dependency versions or deployed implementations and material configuration; use [live evidence](../references/live-investigation.md) when deployment behavior matters. Read only the relevant dependency paths and authoritative docs. If unavailable, retain the exact assumption as `UNKNOWN`; do not substitute a mock or the local interface for its implementation. Dependency behavior is part of causal understanding even when the dependency itself is outside reporting scope.

**Exit:** The active job's selected surface can be queried for exact local graph/context without loading the whole repository.

## Phase 4: Direct And Effective Effects

1. Prove persistent writes from state-variable or `storage` roots; do not classify struct-field member access as storage without proving its root.
2. Cover relevant assignment, compound assignment, increment, decrement, delete, mapping/array/nested-struct mutation, push, pop, and provable Yul/assembly writes.
3. Separate persistent state, semantic token effects, and external-protocol effects.
4. Compute bounded cycle-safe paths from relevant entrypoints to reachable effects.

**Exit:** The active job can query direct/effective effects by entrypoint and affected state.

## Phase 5: Security Views

1. Map authorization, asset flow, state mutation, lifecycle, callbacks, external dependencies, and invariants for the selected surface.
2. For sensitive consumers, map the material context dimensions they assume and the identifiers, keys, fields, flags, sentinels, proofs, receipts, callbacks, or cached records that are supposed to preserve that context across the flow.
3. Link active jobs to relevant impacts, invariants, sensitive consumers, attacker entrypoints, state roots, effect paths, assumptions, observations, hypotheses, known findings, and live evidence where useful.
4. Refine only material impact goals into `READY` status.
5. Derive extension triggers from the selected graph instead of running a universal checklist:
   - price, rate, reserve, oracle, NAV, share, exchange-rate, or internal valuation edges trigger price/value closure;
   - division, fixed-point or decimal scaling, explicit rounding, narrowing casts, iterative approximation, invariant/tick/liquidity math, or inverse quote/accounting paths trigger precision/conservation closure;
   - delegatecall, generic forwarding, callbacks, direct-callable implementation/helper code, or downstream authorization based on caller identity triggers execution-context identity closure;
   - zero/default/sentinel, delete/reset, or partially updated coupled state triggers singularity analysis;
   - signature, message, proof, receipt, callback, or cross-domain identity triggers typed-proof closure;
   - a balance, allowance, registration, liquidity, role, or position used as a gate triggers unwind/reset/replay analysis;
   - keeper, manager, relayer, oracle updater, partner, or another authorized actor able to allocate loss or value triggers an economic-trust review.
6. For every triggered extension, map the extra producers, consumers, persistence boundary, reset/unwind path, and external assumptions needed to answer it. If the trigger is absent, do not spend the Job on that lens.

**Exit:** The selected job has enough evidence to hunt or a bounded repair queue.

## Phase 6: Gates

The graph gate is a hard blocker. Do not advance into HUNT job execution with placeholder nodes, orphan records, or graph entries that do not answer the active impact's reachability/effect questions.

For HUNT:

1. Run `lint` and bounded orphan checks for the relevant records. Confirm the source snapshot was freshness-checked during boot; do not repeat `stale` during the same unchanged task.
2. Confirm the `ACTIVE` job is linked to at least one concrete impact/invariant, one sensitive consumer or state root, and the relevant attacker-accessible entrypoint or explicit `UNKNOWN`.
3. Confirm relevant calls, parameter bindings, return use, direct effects, effective paths, unresolved dispatch, and assumptions are represented.
4. Confirm the graph records material logical-context -> representation/resource -> sensitive-consumer bindings, including any shared key, optional mode, default/sentinel, proof, callback, or lifecycle identity relevant to the job.
5. Confirm graph queries can retrieve a backward path from sensitive consumer to trusted state/source and a forward path from attacker-accessible action to relevant mutation/effect, or store the missing segment as `UNKNOWN` with the next extraction step.
6. Confirm the graph can support an initial attacker-lifecycle sketch, including the durable state/artifact and its later consumers or explicit `UNKNOWN`s. When a special extension was triggered, confirm its value source, precision domains and conserved quantities, effective caller/storage context, coupled state, proof context, unwind path, or trusted actor is represented.
7. Let local `UNKNOWN`s block or shape the active job; do not block the whole audit unless the missing fact is globally material.
8. Confirm that operations were excluded only with a concrete no-path or no-effect reason; "not the focal function" is not an exclusion reason.

**Exit:** HUNT starts after sufficient broad context and deep local coverage for the active job.
