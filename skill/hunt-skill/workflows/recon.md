# RECON Workflow

RECON has two depths: basic global context for interactive hunting, and deep deterministic local coverage for the active job.

## Phase 1: Bound The Map

1. Lock a clean commit or explicit baseline snapshot, exact primary scope, production dependencies, and supporting-only paths.
2. Classify tests, mocks, handlers, harnesses, and deployment scripts as supporting context.

**Exit:** Scope, baseline, support-only paths, and recon depth are explicit.

## Phase 2: Basic Global Recon

1. Understand architecture, actors, assets, money/value flow, integrations, major lifecycles, documented behavior, and important invariants.
2. Enumerate the most important permissionless/state-changing surfaces enough to propose meaningful research.
3. Create or refine the protocol profile and relevant impact goals.
4. Store material unknowns as `UNKNOWN`; ask the user only when intended behavior matters and cannot be established from code/docs.

**Exit:** Hunt can propose one niche invariant or `ACTIVE` job without claiming the whole repository graph is complete.

## Phase 3: Deep Local Recon

**Entry:** An `ACTIVE` job, subsystem, function, state variable, integration, invariant, or impact is selected.

1. Build the graph to be useful for the selected impact/job, not merely present. The graph must support real queries such as "which attacker entrypoints can reach this sensitive consumer?", "which state does this decision trust?", "who writes that state?", and "which later operation consumes the changed representation?"
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

**Exit:** The selected job has enough evidence to hunt or a bounded repair queue.

## Phase 6: Gates

The graph gate is a hard blocker. Do not advance into HUNT job execution with placeholder nodes, orphan records, or graph entries that do not answer the active impact's reachability/effect questions.

For HUNT:

1. Run `lint`, `stale`, and bounded orphan checks for the relevant records.
2. Confirm the `ACTIVE` job is linked to at least one concrete impact/invariant, one sensitive consumer or state root, and the relevant attacker-accessible entrypoint or explicit `UNKNOWN`.
3. Confirm relevant calls, parameter bindings, return use, direct effects, effective paths, unresolved dispatch, and assumptions are represented.
4. Confirm the graph records material logical-context -> representation/resource -> sensitive-consumer bindings, including any shared key, optional mode, default/sentinel, proof, callback, or lifecycle identity relevant to the job.
5. Confirm graph queries can retrieve a backward path from sensitive consumer to trusted state/source and a forward path from attacker-accessible action to relevant mutation/effect, or store the missing segment as `UNKNOWN` with the next extraction step.
6. Let local `UNKNOWN`s block or shape the active job; do not block the whole audit unless the missing fact is globally material.

**Exit:** HUNT starts after sufficient broad context and deep local coverage for the active job.
