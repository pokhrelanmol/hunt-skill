---
name: hunt-skill
description: Audit skill and graph-based bug hunting skill to discover deep bugs in smart contracts and protocol integrations. Use for smart-contract audits, security reviews, deep analysis, bug hunting, invariant and accounting review, or investigating cross-function and external-system behavior. Preserves research jobs, source evidence, and audit context in a project-local SQLite graph.
---

# Adversarial Audit Hunt

Treat the user as the final audit partner, not a passive recipient. Prefer a precise rejected path over an inflated finding.

Resolve this skill directory as `SKILL_ROOT`. Run deterministic operations with:

```bash
python3 "${SKILL_ROOT}/scripts/auditctl.py" <command> --repo <target>
```

## Non-Negotiable Rules

1. Ground claims in the relevant system's evidence: pinned local and dependency code, external contract semantics, deployment/configuration, observed state, and authoritative specifications. Local source alone cannot establish integration correctness; distinguish intended behavior from observed execution and resolve material conflicts. Label consequential claims `VERIFIED`, `INFERRED`, or `UNKNOWN`.
2. Default to `CHAT` or one bounded `HUNT` job. Work autonomously inside the current research question, then ask for human steering before changing direction.
3. Hunt both directions: start from reachable primitives and ask what they can break; start from meaningful impacts and search backward for reachable flows.
4. After structural RECON, use [agent-driven job ideation](references/job-ideation.md) to compare prior coverage and present up to three locally grounded Jobs with research priorities, reasons, and next checks. Keep candidates pending for the user's selection unless the user already chose the question or explicitly delegated selection. Checklist questions and historical edge cases may inform candidates; they cannot create Jobs automatically.
5. Build a detailed, useful SQLite graph before hunting. The graph is not a formality: close over every material producer of the sensitive consumer's inputs and every later consumer of attacker-influenced outputs, including sibling lifecycle and external effects. If the graph cannot answer the active Job's bidirectional reachability/effect questions, stop and deepen RECON instead of hunting from source-reading memory.
6. Prefer compiler AST/build artifacts and deterministic local tools for mechanical relationships. Never ask a model to reconstruct a transitive call graph when compiler-resolved evidence is available.
7. HUNT needs sufficient broad RECON plus deep deterministic graph/context coverage for the active job's relevant surface. Missing or unresolved information must be represented explicitly as `UNKNOWN`, never silently omitted.
8. Treat every lead as an allegation. Trace reachability, state mutation, later consumption, blockers, economics, live configuration, and the strongest safe explanation.
9. Use checklist and historical material in two bounded modes: after RECON to generate direct, edge-case, and composition questions around observed code; and after validation for novelty screening. A match creates a local question; it never proves the current protocol is vulnerable.
10. Use bounded SQLite queries. Do not load the complete database, all checkpoints, or large Markdown notebooks into context.
11. Use the installed Tenderly skill first for simulations, traces, forks, and state overrides. Use `cast` for narrow read-only facts. Pin chain, block, address, code hash when available, and observation time.
12. Once a hypothesis is `CODE_VALIDATED`, PoC work is part of the same research question: run `poc-handoff`, read the configured dedicated PoC skill's `SKILL.md`, and attempt the strongest practical proof. Ask the user only when the PoC environment or material data is missing.
13. Do not modify production contracts during setup, reconnaissance, or indexing.
14. Preserve observations outside the current Job against their graph anchors for later selection; discovering a different concern does not change the active question.
15. Treat user-provided protocol context as useful but unverified. Store it as `USER_CONTEXT`, link likely affected records, verify before relying on it, and check whether it changes active jobs, rejected hypotheses, or parked directions.
16. Treat edge cases as reachable intersections of otherwise valid states, identities, modes, or lifecycle stages. For each active impact, compare the full logical context a sensitive consumer assumes with the context actually bound by identifiers, resource keys, proofs, callbacks, cached records, and validation. Persist a bounded lead when distinct contexts can collide or when a producer proves/returns something weaker, narrower, or different from what its consumer assumes; do not dismiss it merely because the configuration is uncommon.
17. When obvious Jobs are exhausted, expand the graph coverage frontier instead of renaming old questions. A Job variant must identify its parent, inherited coverage, materially new causal edge, distinct result it could produce, and new next check. Reuse the parent graph, deepen only the delta, and rotate away from a saturated family unless new evidence explicitly reopens it.
18. Before rejecting, promoting, completing, or saturating a Job, close the attacker lifecycle in [HUNT](workflows/hunt.md): capability acquisition -> transient influence/action -> durable state or artifact -> prerequisite unwind -> sensitive consumer -> impact realization -> reset/replay -> full-cycle economics. A missing stage is an `UNKNOWN` subgoal, not automatic kill evidence. Activate price/value, precision/conservation, execution-context, coupled-state, typed-proof, restorable-guard, or economic-trust extensions only when the local code or graph triggers them.

## Mode Router

| Intent | Mode | Workflow |
|---|---|---|
| Question, confusion, attack idea, continuation | `CHAT` | [workflows/chat.md](workflows/chat.md) |
| Architecture, relationships, value/state flow | `RECON` | [workflows/recon.md](workflows/recon.md) |
| Concrete module, invariant, flow, or impact after RECON gate | `HUNT` | [workflows/hunt.md](workflows/hunt.md) |
| One hypothesis requiring falsification | `VALIDATE` | [workflows/validate.md](workflows/validate.md) |
| Automatic proof handoff or final write-up | `PROVE` | [workflows/prove.md](workflows/prove.md) |

If intent is ambiguous, answer in `CHAT` or `HUNT` and name the next discriminating check.

## Universal Phases

### Phase 1: Boot And Scope

**Entry:** A repository or audit question is available.

1. Read `AGENTS.md`, then `.audit/INDEX.md` and `.audit/CURRENT.md` when present.
2. Verify commit, dirty state, exact scope, exclusions, and prior-audit corpus before broad analysis.
3. If `.audit/graph/audit.db` is absent, run `init` once. Do not run `doctor` or `db-info` during routine boot; reserve them for installation, database, or tooling failures.
4. Before relying on stored graph/evidence, run `stale` once when source freshness is unknown or the scoped source may have changed. Refresh affected facts instead of repeating every diagnostic.
5. If this is a new audit, use RECON, snapshot, and graph mechanisms to establish architecture, actors, assets, value flow, lifecycles, integrations, intended behavior, and material invariants before hunting.
6. Ask the user only for material missing context that docs/code cannot establish; record non-material unknowns as `UNKNOWN` and continue.
7. Follow [RECON](workflows/recon.md) and [Job ideation](references/job-ideation.md) to prepare the ranked shortlist. Deepen the chosen Job's graph after selection; reuse fresh global and inherited records.

**Exit:** The active source snapshot and research question are explicit.

### Phase 2: Retrieve Bounded Context

**Entry:** Scope and question are explicit.

1. Before HUNT or VALIDATE job execution, prove that graph records exist for the active surface: relevant functions, storage/state, assets/roles/external systems, call edges, read/write/effect edges, and job/impact links. If these records are missing or only superficial, return to RECON and build them.
2. Query `search`, `neighbors`, `path`, or `context` with small limits.
3. For active research, use `research-packet` or an equivalent bounded query around one `JOB`; variants inherit bounded graph anchors from their parent lineage, so do not reload the whole database or regenerate already proven coverage.
4. For an entrypoint, retrieve exact call sites, parameter bindings, return use, runtime targets, direct effects, and shortest effective-effect paths before opening its transitive source tree.
5. Load exact source spans only after graph results identify them.
6. Refresh stale facts before relying on them.

**Exit:** The current question has a compact evidence bundle, unresolved assumptions, and exact code anchors.

### Phase 3: Execute The Selected Workflow

[RECON](workflows/recon.md) owns discovery and graph construction; [Job ideation](references/job-ideation.md) owns candidate comparison and human selection; [HUNT](workflows/hunt.md) owns investigation. Use [VALIDATE](workflows/validate.md) with the canonical [evidence gates](references/evidence-promotion.md), then [PROVE](workflows/prove.md) for proof mechanics. Return to RECON whenever investigation exposes a missing relationship; a populated graph is not proof of semantic completeness.

### Phase 4: Checkpoint

**Entry:** The investigation reached a stable disposition.

1. Update only compact `.audit/INDEX.md`, `.audit/CURRENT.md`, `.audit/LEADS.md`, and `.audit/REJECTIONS.md` summaries that changed.
2. Keep detailed relationships, evidence, and history in SQLite.
3. Export deterministic JSONL only for portability, review, or a requested checkpoint.

**Exit:** A new session can resume from IDs and bounded queries without replaying the conversation.

## Rationalizations To Reject

- "A generic vault invariant is protocol-specific enough." It is not; derive the invariant from this protocol's value, state, and sensitive consumers.
- "The checklist should define the next Job." Derive the Job locally; use only triggered checklist items to challenge it or expose missing edge cases and compositions.
- "This function is not the Job, so it is out of scope." A Job narrows the impact, not the causal surface; retain any operation that produces a trusted input or consumes an attacker-influenced output.
- "A different function name makes this a new Job." Compare the impact, sensitive consumer, primitive/mechanism, and lifecycle context with bounded Job history; continue or reopen equivalent work.
- "Several suspicious functions imply a bug." Show the composed attacker lifecycle and bad state.
- "The temporary condition can be restored, so no exploit exists." Check whether it commits a durable state, entitlement, proof, price-dependent action, or transfer before restoration.
- "The rounding error is only dust." Identify who receives the bias, then test equivalent paths, repetition, reset cost, coupled-state drift, nonlinear boundaries, and later consumers before bounding its impact.
- "The behavior is documented or uses an authorized actor." Intended mechanism and actor authorization do not by themselves prove economic safety, harmlessness, scope eligibility, or reportability.
- "A known exploit looks similar." Similarity is inspiration, not evidence or novelty.
- "No local lead means search every historical bug." Use one bounded fallback search anchored to this protocol's mechanism, invariant, impact, or integration.
- "Tenderly simulation succeeded." Separate vulnerable mechanics from attacker-created prerequisites.
- "The user seemed convinced." CODE_VALIDATED requires evidence; PoC handoff still checks scope freshness and configured proof tooling.
- "The user said it, so it is evidence." User context starts as `UNKNOWN` until independently verified.
- "The current question is done, so start a new one." Recommend the next direction and wait for the user's steering.
- "More Markdown is easier." Store detail in SQLite and retrieve only selected rows.

## Reference Index

- [references/graph-schema.md](references/graph-schema.md): tables, IDs, statuses, and relationship vocabulary.
- [references/job-ideation.md](references/job-ideation.md): agent-derived invariant, impact, and Job selection with checklists used only as bounded lenses.
- [references/risk-mapping.md](references/risk-mapping.md): optional classification of unresolved assumptions for retrieval and candidate comparison, including unclassified concerns.
- [references/edge-case-leads.md](references/edge-case-leads.md): codebase-agnostic context-collision, ambiguous-representation, and producer/consumer lead generation.
- [references/evidence-promotion.md](references/evidence-promotion.md): validation, rejection, automatic proof handoff, and report gates.
- [references/historical-research.md](references/historical-research.md): Solodit, similar audits, and hack-registry routing.
- [references/live-investigation.md](references/live-investigation.md): Tenderly-first on-chain evidence policy.
- [references/state-probes.md](references/state-probes.md): focused probe selection and provenance rules.
- [references/tool-routing.md](references/tool-routing.md): choose external evidence capabilities only when local code, graph context, probes, and reasoning cannot answer the active job.
- [references/cli.md](references/cli.md): compact command reference.

## Success Criteria

- Scope and source freshness are pinned.
- Global structural coverage and its gaps are explicit; deep deterministic coverage is required for the chosen Job's relevant surface.
- Runtime dispatch candidates are separated from live-confirmed implementations, and supporting test code does not contaminate production paths.
- Every important relation and claim has status, confidence, and evidence or an explicit unknown.
- Impact goals combine a protocol invariant with a concrete protocol case.
- Active jobs test whether identities, modes, lifecycle stages, and produced artifacts remain bound to the context assumed by sensitive consumers.
- Active jobs persist a full attacker-lifecycle model; material gaps remain explicit subgoals, and completion or saturation requires closure or concrete kill evidence.
- Precision-triggered jobs identify the rounding beneficiary and bound path dependence, accumulated state drift, downstream amplification, and full-cycle economics.
- Job selection presents the ranked shortlist and records the user's choice or existing selection authority, the next check, and the difference from prior coverage.
- Retrieval remains bounded to relevant rows and source spans.
- Rejected paths preserve kill evidence and reopen conditions.
- Novelty is checked before reporting.
- User context, observations, state probes, active jobs, hypotheses, and rejections survive restart in the existing `.audit`/SQLite store.
- `CODE_VALIDATED` automatically hands off to the configured dedicated PoC skill; reporting waits for proof validation and novelty.
