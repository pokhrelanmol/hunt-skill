# Risk Classification For Job Ideation

Use this during RECON and Job ideation to organize important unresolved assumptions. It is a compact view over existing graph anchors and facts, not a separate audit phase or a prerequisite for investigating the user's selected question. Create a record only when it preserves a useful question, observation, or coverage gap. Do not create an entry for every component/category combination.

## Classify The Concern

Start with the actual relationship and the assumption worth checking. Classification labels help retrieve related concerns; they do not establish defects, select Jobs, or limit which code can matter. A concern can span several functions, systems, and labels. Keep an unclassified concern when its meaning is still unclear.

Suggested labels are deliberately open:

| Label | What it describes |
|---|---|
| `custody-accounting` | Ownership, backing, and movement of assets or claims |
| `precision` | Units, numerical conversions, approximation, and rounding |
| `token-semantics` | Behavior assumed of tokens, shares, or receipt assets |
| `pricing` | Meaning, source, and timing of a consumed valuation |
| `solvency` | Consistency of obligations, collateral, and recovery |
| `lifecycle` | State across creation, updates, cancellation, settlement, and reuse |
| `composition` | A shared state or artifact interpreted across components |
| `integration` | Local assumptions about an external implementation or system |
| `cross-chain` | Message meaning, domain, delivery, and finality assumptions |
| `authorization` | Authority, identity, configuration, and authorization artifacts |
| `rewards-fees` | Entitlements, accrual, ownership, and allocation |
| `availability` | Access to assets or required operations and recovery |

Use these labels when they fit; add a descriptive label or leave labels empty when they do not. Multiple labels describe one concern, not multiple risks to count. An intersection must name a shared value, state, operation, or assumption; a combination of category names alone is not a research signal.

## Keep One Compact Record

Use an existing `OBSERVATION` fact when it already captures the concern; enrich its statement in place and preserve its ID, kind, and evidence. Otherwise use `fact-upsert` with kind `RISK_CONTEXT`, a stable `fact:risk:...` ID, and an existing function/state/module/dependency node as `subject_id`. Keep additional graph anchors and related fact IDs in the statement rather than copying their evidence. Use ordinary `evidence-add` records for provenance.

The statement should capture only what is useful:

```text
Concern: the specific relationship or assumption worth checking
Property at risk: the guarantee or possible consequence, or UNKNOWN
Labels: relevant labels, or unclassified
Evidence/counterevidence: source or existing record IDs; material gaps
Next check: the smallest check likely to change our understanding
Review boundary: unexamined/partial, or bounded conclusion with conditions and reopen reason
```

A verified source observation can support an unresolved concern; a classification or risk inference alone is not `VERIFIED`. Unknown impact, beneficiary, or failure mechanism does not invalidate a source-anchored question. Do not invent an exploit narrative to fill the record. Two records are distinct only when their uncertainty or causal context differs, not merely their labels.

## Retrieve, Compare, And Hand Off

1. Retrieve relevant `RISK_CONTEXT` and `OBSERVATION` facts through bounded `fact-list`, graph context, and source references. Search by category when the user requests one, but also inspect unclassified or newly discovered concerns around the same anchors. An empty category search is not evidence that no relevant surface exists; inspect the structural inventory and its gaps.
2. Compare concrete uncertainty, possible consequence, reachability basis, counterevidence, prior work, and expected value/cost of the next check. Category, number of labels, value custody, low supply, or uncertainty alone does not confer priority. Low supply and low market liquidity are different conditions; their relevance comes from the consuming system's assumptions. Availability, rewards, and configuration can be high-priority when evidence warrants it.
3. Derive candidate questions from the strongest supported concerns across the relevant scope. A source observation or unresolved dependency assumption may generate a candidate without a named risk family. Avoid repeatedly returning to familiar categories when a different unresolved relationship offers more information. Do not force diversity against stronger evidence.
4. Follow [Job ideation's ranked shortlist](job-ideation.md#4-rank-and-present-for-selection): present up to three Jobs for the user to choose. This view does not add a second approval step or automatically activate the highest-ranked surface. Keep priority on the existing `JOB_PRIORITY` record, rather than maintaining a competing surface score.
5. When a Job uses these records, store their IDs in one `JOB_RISK_CONTEXT` fact with that Job as subject; reuse its ID on updates. One Job can reference several concerns and several Jobs can reference one concern. Link the Job to its actual graph anchors as usual. `research-packet` returns the reference fact; use `fact-list --id ...` for the referenced records. These text references are not automatically expanded.

## Update Only What Was Learned

At disposition, update the relevant concern's review boundary with the Job/evidence IDs, tested conditions, remaining uncertainty, and reopen reason. A completed Job or one harmless path does not mark a category or entire surface safe. Keep source/configuration freshness explicit and revisit affected conclusions when their backing assumptions change. Reuse unchanged facts across sessions.

Report concrete tested questions and remaining gaps. Counts describe recorded concerns only; they do not measure the percentage of protocol security covered. Classification remains optional for new observations and never restricts the chosen Job's producers, consumers, external dependencies, or newly discovered relationships.
