# Agent-Driven Job Ideation

Use this after basic RECON whenever selecting a new `ACTIVE` Job. This is the resource-allocation gate: the agent derives the direction from the current protocol, compares it with prior coverage, and chooses one question worth deeper graph construction and HUNT.

## 1. Review What Is Already Known

Use bounded `job-list`, `impact-list`, `search`, and graph queries. Read current, completed, blocked, and parked Jobs; covered impacts; rejected hypotheses; material observations; and unresolved `UNKNOWN`s relevant to the candidate surface.

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

Start from observed code, documentation, and the coarse graph—not a predefined catalog. A candidate should be compact but answer:

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
Why now              signal strength, impact ceiling, composition potential, and expected information gain
Next check           cheapest query, trace, or State Probe likely to reject or strengthen it
```

Checklist questions and historical bugs are optional lenses. Apply only those with a current-code trigger, restate them in this protocol's terms, and follow [historical research](historical-research.md) when one relevant source could reveal a missing prerequisite. They may expand a candidate; they cannot define or prove it.

## 3. Keep The Causal Surface Open

A Job narrows the invariant and impact, not the source analysis to one function. Before HUNT, close over the selected question:

- **Consumer closure:** state, balances, rates, rights, proofs, roles, configuration, and external facts trusted by the sensitive consumer.
- **Producer closure:** local and external paths that write, derive, transfer, mint, burn, invalidate, or economically change those inputs.
- **Attacker closure:** production-reachable entrypoints that can reach or shape any producer.
- **Output closure:** later protocol or integration consumers of every attacker-influenced state, asset, right, proof, authority, or capability.
- **Lifecycle closure:** sibling, inverse, partial, repeated, cancelled, delayed, restored, callback, reset, and recovery paths material to the question.

An operation that is not selected as its own Job remains in the active causal surface when it can produce a consumer input or consume a primitive output. Mark incomplete closure `UNKNOWN`; do not silently exclude the path.

## 4. Select One Job

Compare candidates by judgment, not a rigid numeric score:

1. plausible impact and sensitive-consumer importance;
2. production reachability and attacker control;
3. strength of the local code/graph signal;
4. ability to compose incomplete primitives;
5. cost and decisiveness of the next check;
6. useful coverage not already provided by prior Jobs.

Promote only the strongest candidate to `ACTIVE`. Preserve other locally anchored candidates as `NEXT` or `PARKED`; discard external prompts with no local trigger. Job creation is an agent judgment—no checklist match or command creates it automatically.

Persist the invariant, impact, and Job, then link the Job to its impact/invariant and initial graph anchors. The Job goal must be self-contained enough that another session can understand the question, reachability basis, causal surface, why it deserved resources, and next check without replaying the conversation.

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

## 6. Build, Hunt, And Rotate Deliberately

After selection, build the detailed graph packet for the whole causal surface. HUNT begins only when graph queries support both:

```text
sensitive consumer -> trusted inputs -> producers -> attacker path
attacker primitive -> changed representation/capability -> later consumers -> impact
```

When the Job ends, record its result, coverage boundary, kill evidence or surviving lead, unresolved segments, and reopen condition. Mark an impact `COVERED` only when its materially promising consumers and primitive paths were investigated or explicitly rejected.

Before recommending the next direction, compare Job and family history again. Choose the strongest locally supported continuation, reopen, variant, or new family; otherwise mark the exhausted family saturated and rotate. Explain the exact coverage delta, then stop for human steering before activating it.
