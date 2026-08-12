# FULL AUDIT Workflow

Run this workflow only after an explicit broad-audit request.

## Phase 1: Scope Lock

**Entry:** The user explicitly requests a full audit.

1. Verify repository, pinned commit, exact files, hashes, exclusions, dirty state, dependencies, and prior-audit corpus.
2. Initialize SQLite and capture the exact source snapshot.

**Exit:** Scope is reproducible and accepted.

## Phase 2: Deterministic Index

**Entry:** Scope is locked.

1. Compile the clean pinned baseline where feasible.
2. Extract symbols, inheritance, modifiers, state-changing entrypoints, unique call sites, exact argument bindings, return use, storage-rooted direct effects, runtime-target candidates, and source spans.
3. Compute bounded shortest effective-effect paths and keep production paths isolated from supporting tests, mocks, handlers, harnesses, and scripts.
4. Record extraction confidence and every unresolved item as `UNKNOWN`.

**Exit:** Entrypoint call trees, argument flow, return use, runtime targets, and direct/effective effects are queryable without whole-repository prompts.

## Phase 3: Relationship Recon

**Entry:** Deterministic index exists.

1. Build authorization, state mutation, asset flow, lifecycle, callback, invariant, and external dependency views.
2. Profile every applicable protocol archetype.
3. Seed and refine protocol-specific impact goals.
4. Run the complete RECON gate and repair all silent coverage gaps.

**Exit:** High-value decisions and bad states are mapped with evidence, and impact-driven HUNT is unblocked only for the passing pinned scope.

## Phase 4: Bounded Sweep

**Entry:** At least one impact goal is `READY`.

1. Enumerate reachable entrypoints once.
2. Batch connected entrypoint-impact pairs by subsystem.
3. Apply Hunt's built-in first-principles, state-consistency, accounting, lifecycle, actor, and integration lenses to each batch.
4. Persist coverage and kill weak paths early.

**Exit:** Each material surface has a disposition or named unresolved check.

## Phase 5: Strategic Synthesis

**Entry:** Sweep primitives exist.

1. Consume all candidates, deduplicate root causes, and compose cross-function chains.
2. Select a small set of high-impact investigations.
3. Validate capability, reachability, state transition, blockers, economics, external assumptions, and strongest alternatives.

**Exit:** Only defensible hypotheses survive.

## Phase 6: Novelty And Skeptic

**Entry:** A hypothesis survives local validation.

1. Screen repository-known issues, similar audits, Solodit, and hack registry.
2. Run an independent skeptical review on raw evidence.
3. Promote only distinct, reportable root causes.

**Exit:** Survivors are `CODE_VALIDATED`; duplicates and failures are recorded.

## Phase 7: Automatic Proof Handoff

**Entry:** At least one hypothesis is `CODE_VALIDATED`.

1. Present each survivor with the evidence bundle and current strongest blocker.
2. Run `poc-handoff` for the selected survivor and follow the configured PoC skill.
3. Ask the user only for missing proof environment or material context.
4. Mark each survivor `POC_VALIDATED`, `POC_BLOCKED`, or `REJECTED` based on proof outcome.

**Exit:** Each selected lead is confirmed, blocked, or rejected by decisive evidence.

## Phase 8: Reporting And Checkpoint

**Entry:** Proof and novelty gates are complete.

1. Write concise findings for confirmed novel issues.
2. Preserve rejected paths and reopen conditions.
3. Update compact control-plane Markdown and export JSONL when requested.

**Exit:** The audit can resume or be reviewed without replaying the full context.
