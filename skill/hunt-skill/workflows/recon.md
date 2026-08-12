# RECON Workflow

RECON has two depths: basic global context for normal interactive hunting, and deep deterministic local coverage for the active job. Explicit full-audit mode may still require broad systematic coverage.

## Phase 1: Bound The Map

1. Lock a clean commit or explicit baseline snapshot, exact primary scope, production dependencies, and supporting-only paths.
2. Classify tests, mocks, handlers, harnesses, and deployment scripts as supporting context.
3. Identify whether the user wants normal interactive hunting or explicit full-audit coverage.

**Exit:** Scope, baseline, support-only paths, and recon depth are explicit.

## Phase 2: Basic Global Recon

1. Understand architecture, actors, assets, money/value flow, integrations, major lifecycles, documented behavior, and important invariants.
2. Enumerate the most important permissionless/state-changing surfaces enough to propose meaningful research.
3. Create or refine the protocol profile and relevant impact goals.
4. Store material unknowns as `UNKNOWN`; ask the user only when intended behavior matters and cannot be established from code/docs.

**Exit:** Hunt can propose one niche invariant or `ACTIVE` job without claiming the whole repository graph is complete.

## Phase 3: Deep Local Recon

**Entry:** An `ACTIVE` job, subsystem, function, state variable, integration, invariant, or impact is selected.

1. Compile the pinned baseline when feasible and use compiler AST/build artifacts for declarations, overloads, modifiers, source spans, and resolvable calls.
2. Give every invocation its own call-site identity, including repeated and nested calls on the same line.
3. For relevant call sites, record caller, declared callee, dispatch kind, condition, argument expression, callee parameter binding, argument origin IDs, and return use.
4. Represent modifiers, `using for`, tuple returns, callbacks, hooks, internal/external/library/super/virtual/interface/low-level/delegate/static/dynamic dispatch, and runtime target candidates when relevant to the job.
5. Mark mechanically proven facts `VERIFIED`, semantic/economic interpretations and possible runtime targets `INFERRED`, and unresolved dispatch or assembly `UNKNOWN`.

**Exit:** The active job's selected surface can be queried for exact local graph/context without loading the whole repository.

## Phase 4: Direct And Effective Effects

1. Prove persistent writes from state-variable or `storage` roots; do not classify struct-field member access as storage without proving its root.
2. Cover relevant assignment, compound assignment, increment, decrement, delete, mapping/array/nested-struct mutation, push, pop, and provable Yul/assembly writes.
3. Separate persistent state, semantic token effects, and external-protocol effects.
4. Compute bounded cycle-safe paths from relevant entrypoints to reachable effects.

**Exit:** The active job can query direct/effective effects by entrypoint and affected state.

## Phase 5: Security Views

1. Map authorization, asset flow, state mutation, lifecycle, callbacks, external dependencies, and invariants for the selected surface.
2. Link active jobs to relevant impacts, invariants, graph nodes, assumptions, observations, hypotheses, known findings, and live evidence where useful.
3. Refine only material impact goals into `READY` status.

**Exit:** The selected job has enough evidence to hunt or a bounded repair queue.

## Phase 6: Gates

For normal interactive HUNT:

1. Run `lint`, `stale`, and bounded orphan checks for the relevant records.
2. Confirm relevant calls, parameter bindings, return use, direct effects, effective paths, unresolved dispatch, and assumptions are represented.
3. Let local `UNKNOWN`s block or shape the active job; do not block the whole audit unless the missing fact is globally material.

For explicit full-audit mode:

1. Confirm every scoped state-changing entrypoint has extraction coverage, including zero-call or zero-effect records.
2. Confirm resolvable calls, parameter bindings, return-use, direct/effective-effect coverage, unresolved calls, production contamination checks, dangling edges, and verified evidence support across the full pinned scope.

**Exit:** Interactive HUNT starts after sufficient broad context and deep local coverage for the active job. Full-audit HUNT waits for the broader gate.
