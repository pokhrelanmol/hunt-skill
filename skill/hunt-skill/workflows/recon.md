# RECON Workflow

RECON has two depths: basic global context for interactive hunting, and deep deterministic local coverage for the active job.

## Phase 1: Bound The Map

1. Lock a clean commit or explicit baseline snapshot, exact primary scope, production dependencies, and supporting-only paths.
2. Classify tests, mocks, handlers, harnesses, and deployment scripts as supporting context.

**Exit:** Scope, baseline, support-only paths, and recon depth are explicit.

## Phase 2: Basic Global Recon

1. Understand architecture, actors, assets, money/value flow, integrations, major lifecycles, documented behavior, and important invariants.
2. Enumerate the most important permissionless/state-changing surfaces enough to propose meaningful research.
3. Use [agent-driven job ideation](../references/job-ideation.md) to compare prior coverage and derive lightweight candidate questions from the observed architecture, state, value flow, and sensitive consumers. Apply triggered checklist questions and real edge cases only as lenses that challenge or expand those local candidates.
4. Store material unknowns as `UNKNOWN`; ask the user only when intended behavior matters and cannot be established from code/docs.

**Exit:** Hunt can propose one niche invariant or `ACTIVE` job without claiming the whole repository graph is complete.

## Phase 3: Deep Local Recon

**Entry:** An `ACTIVE` job, subsystem, function, state variable, integration, invariant, or impact is selected.

1. Build the graph for the selected Job's causal surface, not merely its focal function. Close over the sensitive consumer's trusted inputs, every material local/external producer of those inputs, attacker paths to the producers, later consumers of attacker-influenced outputs, and relevant sibling/inverse lifecycle paths.
2. Compile the pinned baseline when feasible and use compiler AST/build artifacts for declarations, overloads, modifiers, source spans, and resolvable calls.
3. Create nodes for relevant contracts, external/public functions, internal functions, modifiers, storage/state roots, roles, assets, lifecycle states, external systems, logical identities/instances, shared resource keys, produced artifacts when material, tests/harness anchors, invariants, impacts, and the `ACTIVE` job.
4. Give every invocation its own call-site identity, including repeated and nested calls on the same line.
5. For relevant call sites, record caller, declared callee, dispatch kind, condition, argument expression, callee parameter binding, argument origin IDs, and return use.
6. Represent modifiers, `using for`, tuple returns, callbacks, hooks, internal/external/library/super/virtual/interface/low-level/delegate/static/dynamic dispatch, and runtime target candidates when relevant to the job.
7. Mark mechanically proven facts `VERIFIED`, semantic/economic interpretations and possible runtime targets `INFERRED`, and unresolved dispatch or assembly `UNKNOWN`.

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
   - zero/default/sentinel, delete/reset, precision, or partially updated coupled state triggers singularity analysis;
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
6. Confirm the graph can support an initial attacker-lifecycle sketch, including the durable state/artifact and its later consumers or explicit `UNKNOWN`s. When a special extension was triggered, confirm its value source, coupled state, proof context, unwind path, or trusted actor is represented.
7. Let local `UNKNOWN`s block or shape the active job; do not block the whole audit unless the missing fact is globally material.
8. Confirm that operations were excluded only with a concrete no-path or no-effect reason; "not the focal function" is not an exclusion reason.

**Exit:** HUNT starts after sufficient broad context and deep local coverage for the active job.
