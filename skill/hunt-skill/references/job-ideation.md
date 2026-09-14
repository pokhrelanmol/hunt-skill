# Agent-Driven Job Ideation

Use this after structural RECON when proposing a new Job. The agent derives and ranks protocol-specific questions; the user selects the research direction. Detailed mapping and investigation follow selection.

## 1. Review What Is Already Known

Use bounded `job-list`, `impact-list`, `search`, and graph queries. Read current, completed, blocked, and parked Jobs; covered impacts; rejected hypotheses; material observations; and unresolved `UNKNOWN`s relevant to the candidate surface.

Use [risk classification](risk-mapping.md) to retrieve important unresolved assumptions and compare related surfaces. Include unclassified observations and counterevidence. A classification view helps prepare candidates; it is not a required intermediate record for every Job or a second source of priorities.

For each candidate with a known impact, invariant, consumer, or primitive anchor, also run `job-list --linked-record <id>` so an older equivalent Job is not hidden by the general history limit. For each match, run `job-list --family <job-id>` before deciding that its variants are uncovered.

Do not create a new Job that merely renames an existing combination of:

```text
impact or forbidden state
+ sensitive consumer
+ attacker primitive or mechanism
+ material lifecycle/integration context
```

Continue or reopen the existing Job when new evidence changes it. The same impact may justify another Job only when a materially different consumer, primitive, prerequisite, or composition creates a distinct research question. Prefer an uncovered protected value, consumer, subsystem, lifecycle, or integration when candidates are otherwise comparable, but never force variety over stronger local evidence.

## 2. Derive Lightweight Candidates

Start from observed local/dependency code, documentation, integration semantics, and the structural graph—not a predefined catalog. Keep each candidate compact and address these fields, using explicit `UNKNOWN`s for unsettled parts:

```text
Goal                 the falsifiable security question
Local trigger        exact code, state, flow, or integration that raised it
Reachability         production actor/path evidence, or the exact UNKNOWN
Controlled influence input, ordering, state, asset, right, proof, or capability
Invariant            protocol-specific property that must remain true
Sensitive consumer   decision or operation that makes the state matter
Forbidden state      concrete invariant violation
Impact               protected value, right, solvency, authority, or availability harmed
Causal surface       likely producers, consumers, sibling/inverse lifecycle paths, and external effects
Lifecycle sketch     capability -> transient influence -> durable output -> unwind -> consumer -> impact; mark gaps UNKNOWN
Why now              signal strength, impact ceiling, composition potential, and expected information gain
Next check           cheapest query, trace, or State Probe likely to reject or strengthen it
```

Checklist questions and historical bugs are optional lenses. Apply only those with a current-code trigger, restate them in this protocol's terms, and follow [historical research](historical-research.md) when one relevant source could reveal a missing prerequisite. They may expand a candidate; they cannot define or prove it.

For a precision-triggered candidate, identify a concrete numerical inconsistency or questionable rounding assumption at a sensitive consumer or conserved quantity. Record known direction, beneficiary, retained discrepancy, and possible amplification; unresolved answers are valid research questions, not prerequisites for selection. Name the cheapest equivalence or high-precision comparison that would distinguish harmless numerical error from an invariant failure. `Uses division` alone is insufficient.

The lifecycle sketch is deliberately incomplete at ideation time. Its purpose is to expose composition and choose the next check, not to pretend the exploit is already solved. Missing capital, liquidity, timing, cash-out, or a later consumer becomes a named subgoal. Reject the candidate only when a required stage is concretely unreachable, harmless, or economically impossible under the same conditions.

An unresolved relationship with a meaningful property and discriminating next check is enough to propose research; exact failure and impact may still be `UNKNOWN`. For a category request such as "review rounding," use that category to find relevant concerns and current-code anchors, then compare specific questions using the same shortlist. Do not auto-select a category's presumed highest-risk component.

## 3. Keep The Causal Surface Open

A Job narrows the question, not the source analysis to one function. Sketch likely producers, consumers, sibling paths, and external dependencies; retain gaps as `UNKNOWN`. An operation remains relevant when it produces a consumer input or consumes an affected output. After selection, [Deep Local RECON](../workflows/recon.md#phase-3-deep-local-recon) owns detailed expansion; do not perform full closure for every candidate during ideation.

## 4. Rank And Present For Selection

Compare candidates by judgment, not a rigid numeric score:

1. plausible impact and sensitive-consumer importance;
2. production reachability and attacker control;
3. strength of the local code/graph signal;
4. ability to compose incomplete primitives;
5. cost and decisiveness of the next check;
6. useful coverage not already provided by prior Jobs.

Persist credible candidates as `NEXT` or `PARKED`, linked to initial graph anchors and proposed invariant/impact. Present the top three when three or more exist, both when two exist, and the sole candidate when only one exists. Do not manufacture candidates to fill the table. Use this compact format:

| Research priority | Job ID and specific question | Why this ranks here / possible impact | Evidence or material UNKNOWN | Next check |
|---|---|---|---|---|
| P1 — recommended | ... | ... | ... | ... |

Use P2/P3 for the remaining displayed choices. Priority means relative research value, not finding severity or proof of a bug. State material scope limits and explain each candidate's difference from prior coverage. Persist the rank and rationale in a `JOB_PRIORITY` fact against the Job using the existing facts store; revise it when evidence changes. `job-list` recency order is not priority order.

End the proposal with a concise request for the user's choice. Do not activate or investigate a candidate while waiting. If the user already selected the precise question or explicitly delegated selection, follow that authority and identify the chosen Job without asking again. A generic request to audit, hunt, go deeper, or create Jobs is not by itself a choice among new independent candidates. Continuing the already selected Job does not require reselection.

Activate only the selected Job; preserve other candidates and any existing active question until a switch is chosen. The Job goal must let another session understand the question, initial causal surface, rationale, unresolved assumptions, and next check. An early `DRAFT` impact may remain incomplete; promotion must satisfy its own evidence requirements.

## 5. Expand The Coverage Frontier

When the obvious Jobs are already hunted, do not generate synonyms. Classify the next action:

- **Continue:** the existing Job still has an unresolved segment or next check.
- **Reopen:** new code, deployment state, integration, evidence, or a disproved assumption changes a completed Job.
- **Create a variant:** prior work is reusable, but a materially different causal path remains untested.
- **Create a new family:** the impact/invariant and causal question are genuinely different.
- **Rotate:** the family is saturated and no new evidence justifies reopening it.

Search for variants at graph frontiers, not by rewording the impact. Useful frontier changes include a different producer/writer, sensitive consumer, lifecycle/order/context, actor or authority, economic boundary, prerequisite-acquisition path, or cross-contract/integration consumer. The same impact may remain useful when one of these changes the causal path and the next check.

Every variant must record:

```text
Parent Job          the prior Job whose coverage is reused
Inherited coverage graph, evidence, assumptions, and killed paths that remain valid
Variant delta       the new producer, consumer, context, prerequisite, or composition edge
Distinctness        why the delta can create a result the parent could not
Next check          the cheapest test of the new edge
```

Use `VARIANT_OF` plus the stored inherited coverage, delta, distinctness, and next-check facts. Do not rebuild inherited graph coverage: `research-packet` retrieves bounded graph anchors from the parent lineage. Add and verify only the delta and its connections to the inherited path before HUNT.

Mark a family `SATURATED` only after its locally promising producer, consumer, lifecycle/context, prerequisite, and integration frontiers are investigated or explicitly killed. A saturated family rejects another variant unless genuinely new evidence is recorded as the reopen reason. Without that evidence, rotate to a different impact, subsystem, invariant, or causal family.

Do not mark a family saturated while a high-impact stage of its attacker lifecycle remains merely `UNKNOWN`. In particular, search all protocol and integration consumers of a durable artifact or capability before treating its lack of direct market liquidity as a dead end.

## 6. Build, Hunt, And Rotate Deliberately

After selection, follow [RECON's graph gate](../workflows/recon.md#phase-6-gates), then [HUNT](../workflows/hunt.md). Return to RECON when reasoning exposes missing relationships; ideation does not certify graph completeness.

When the Job ends, record its result, coverage boundary, kill evidence or surviving lead, unresolved segments, and reopen condition. Mark an impact `COVERED` only when its materially promising consumers and primitive paths were investigated or explicitly rejected.

Before proposing the next direction, compare Job and family history again and use the ranked shortlist above for supported continuations, reopens, variants, or new families. Explain each coverage delta, then stop for human steering before activating an independent direction. If no candidate is supported, report that limit instead of inventing another Job.
