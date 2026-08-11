# HUNT Workflow

## Entry Gate

Do not begin impact-driven hunting until the RECON gate passes for the current pinned scope. Retrieve the relevant entrypoint's call sites, argument bindings, return use, direct effects, effective effects, runtime candidates, and unresolved records first. If coverage is stale or incomplete, return to [recon.md](recon.md).

## Phase 1: Choose A Bounded Target

**Entry:** A concrete module, flow, invariant, attack surface, or impact is requested.

1. Select one or a small batch of connected `READY` impact goals.
2. Select relevant entrypoints from the gated production graph rather than re-enumerating them from memory.
3. Retrieve shortest effect paths and exact call-site bindings for the decision points that can create the target bad state.
4. Form focused entrypoint-impact pairs; avoid broad checklist scans.

**Exit:** Each task names one impact, one reachable surface, and the evidence needed to change status.

## Phase 2: Hunt Forward And Backward

**Entry:** Focused pairs exist.

1. Forward: trace attacker-controlled primitives into later consumers and impacts.
2. Backward: start from the bad decision and enumerate all reachable ways to shape its inputs.
3. At each step, distinguish the compiler-declared callee from possible runtime implementations and live-confirmed targets.
4. Alternate first-principles and state-consistency lenses.
5. Inspect multi-function, multi-transaction, and external-protocol composition.
6. Treat an `UNKNOWN` edge as a bounded investigation item, never as proof that a path exists or does not exist.

**Exit:** Each promising chain has attacker capability, state mutation, persistence, later consumer, and impact; weak paths have kill evidence.

## Phase 3: Consume And Rank

**Entry:** The bounded batch is complete.

1. Deduplicate by root cause, not title.
2. Merge compatible primitives into the shortest attacker lifecycle.
3. Rank hypotheses by likely Medium/High impact and next-check value.
4. Stop investigating paths with sub-Medium impact unless they compose with an active higher-impact chain.

**Exit:** A small set of hypotheses moves to `VALIDATE`; all others are rejected, blocked, or retained as primitives.

## Phase 4: Pattern-Inspiration Fallback

**Entry:** The bounded code-led hunt produced no useful hypothesis or next check.

1. Select one high-value `READY` impact, invariant, or material integration.
2. Search similar audits, Solodit, and the hack registry for the same economic decision and attacker primitive.
3. Convert each relevant match into a current-protocol question with explicit required conditions.
4. Return to Phase 2 and independently trace the current code.
5. Stop after one focused pass if no match becomes locally reachable.

**Exit:** A locally anchored lead moves to `VALIDATE`, or the fallback ends with no candidate. Historical similarity alone never changes status.
