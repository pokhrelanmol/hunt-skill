# RECON Workflow

## Phase 1: Bound The Map

**Entry:** The user requests architecture, surface, relationship, or flow mapping.

1. Lock a clean commit or explicit baseline snapshot, exact primary scope, production dependencies, and supporting-only paths.
2. Enumerate assets, roles, external systems, and permissionless state-changing entrypoints once.
3. Classify tests, mocks, handlers, harnesses, and deployment scripts as supporting context. Never admit them into default production paths.
4. Batch by connected subsystem; do not create one task per function.

**Exit:** The map target and bounded batches are explicit.

## Phase 2: Build Deterministic Facts

**Entry:** Scope is fresh.

1. Compile the pinned baseline when feasible and use compiler AST/build artifacts for declarations, overloads, modifiers, source spans, and resolvable calls.
2. Give every invocation its own call-site identity, including repeated and nested calls on the same line.
3. For each call site, record caller, declared callee, dispatch kind, enclosing condition, exact positional or named argument expression, callee parameter binding, argument origin IDs, and return use.
4. Represent modifiers and modifier arguments as reachable call steps. Account for `using for` implicit receivers, tuple returns, callbacks, hooks, and internal, external, library, super, virtual, interface, low-level, delegate, static, and dynamic dispatch.
5. Record possible runtime targets separately from the compiler-declared target. Keep compiler candidates distinct from proxy, beacon, diamond, code-hash, or configured-address targets confirmed by live evidence.
6. Mark mechanically proven facts `VERIFIED`, semantic/economic interpretations and possible runtime targets `INFERRED`, and unresolved dispatch or assembly `UNKNOWN`.

**Exit:** Any scoped entrypoint can be queried for exact direct call sites, argument bindings, return use, runtime candidates, conditions, and source evidence without first reading its full transitive source tree.

## Phase 3: Map Direct And Effective Effects

**Entry:** Call-site and binding coverage exists.

1. Prove persistent writes from lvalues rooted in state variables or `storage` references. Do not classify a struct-field `MemberAccess` as storage without proving its root.
2. Cover assignment, compound assignment, increment, decrement, delete, mapping/array/nested-struct mutation, push, pop, and mechanically provable Yul or assembly writes.
3. Exclude memory and calldata mutations from persistent effects. Record ambiguous storage aliases or assembly effects as `UNKNOWN`.
4. Separate local persistent state from semantic token effects such as transfer, approve, mint, and burn, and from external-protocol effects such as deposit, withdraw, borrow, repay, liquidate, redeem, and callback.
5. From every state-changing entrypoint, compute the deterministic shortest cycle-safe path to each reachable effect. Bound depth and record the complete ordered call-site path, conditions, leaf function, status, and confidence.

**Exit:** Direct and transitive persistent, token, and external-protocol effects are queryable by entrypoint and by affected state.

## Phase 4: Build Security Views

**Entry:** Deterministic facts exist.

1. Map authorization, asset flow, state mutation, lifecycle, callbacks, external dependencies, and invariants.
2. Create protocol profile and draft impact seeds for all applicable archetypes.
3. Refine the most material impacts into protocol-specific `READY` goals.

**Exit:** The map explains who can change protected state, how value moves, and which decisions could produce meaningful bad states.

## Phase 5: RECON Gate

**Entry:** Selected views are populated.

1. Run `lint`, `stale`, and bounded orphan searches; confirm search indexes return newly recorded graph facts.
2. Confirm every scoped state-changing entrypoint has an explicit extraction-coverage record, even when it has zero calls or zero persistent effects.
3. Confirm resolvable calls have complete parameter bindings and every returned component is classified as assigned, tuple-bound, ignored, returned, or consumed.
4. Confirm persistent effects have proven roots and every reachable effect has a bounded effective path.
5. Confirm high-risk unresolved calls and assembly are stored as `UNKNOWN` with a concrete next check.
6. Reject dangling relationships, unsupported `VERIFIED` records, stale evidence, dirty or unpinned extraction, and production paths containing tests, mocks, handlers, harnesses, or scripts.
7. Report scoped-function coverage, state-changing-entrypoint coverage, call resolution, argument binding, return-use coverage, direct/effective-effect coverage, unresolved calls, production contamination, dangling edges, and verified records lacking evidence.

**Exit:** The gate passes for the pinned scope, or HUNT remains blocked with an explicit bounded repair queue. Unknowns may remain only when represented, evidenced, and ranked rather than silently omitted.
