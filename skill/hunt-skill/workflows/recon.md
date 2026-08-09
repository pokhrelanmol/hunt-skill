# RECON Workflow

## Phase 1: Bound The Map

**Entry:** The user requests architecture, surface, relationship, or flow mapping.

1. Lock exact scope and subsystem.
2. Enumerate assets, roles, external systems, and permissionless state-changing entrypoints once.
3. Batch by connected subsystem; do not create one task per function.

**Exit:** The map target and bounded batches are explicit.

## Phase 2: Build Deterministic Facts

**Entry:** Scope is fresh.

1. Record contracts, functions, storage, direct calls, guards, and source spans.
2. Mark mechanical extraction `VERIFIED`; model-derived edges remain `INFERRED`.
3. Link reads/writes and later consumers for economically coupled state.

**Exit:** Core nodes and direct relationships have source evidence.

## Phase 3: Build Security Views

**Entry:** Deterministic facts exist.

1. Map authorization, asset flow, state mutation, lifecycle, callbacks, external dependencies, and invariants.
2. Create protocol profile and draft impact seeds for all applicable archetypes.
3. Refine the most material impacts into protocol-specific `READY` goals.

**Exit:** The map explains who can change protected state, how value moves, and which decisions could produce meaningful bad states.

## Phase 4: QA

**Entry:** Selected views are populated.

1. Run `lint`, `stale`, and bounded orphan searches.
2. Resolve dangling edges and unsupported `VERIFIED` claims.
3. Rank unknowns by security relevance.

**Exit:** Graph gaps are explicit and no unsupported verified relationship remains.
