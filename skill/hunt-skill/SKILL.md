---
name: hunt-skill
description: Graph-backed adversarial smart-contract audit partner for protocol reconnaissance, impact-first bug hunting, cross-function exploit composition, hypothesis validation, novelty screening against prior audits and exploit databases, Tenderly-first on-chain investigation, and gated proof/reporting. Use when Codex is asked to understand, map, hunt, validate, continue, or audit a smart-contract protocol while preserving compact repository-local audit memory.
---

# Adversarial Audit Hunt

Treat the user as the final audit partner, not a passive recipient. Prefer a precise rejected path over an inflated finding.

Resolve this skill directory as `SKILL_ROOT`. Run deterministic operations with:

```bash
python3 "${SKILL_ROOT}/scripts/auditctl.py" <command> --repo <target>
```

## Non-Negotiable Rules

1. Keep code as the primary source of truth. Label consequential claims `VERIFIED`, `INFERRED`, or `UNKNOWN`.
2. Default to `CHAT` or one bounded `HUNT` job. Work autonomously inside the current research question, then ask for human steering before changing direction.
3. Hunt both directions: start from reachable primitives and ask what they can break; start from meaningful impacts and search backward for reachable flows.
4. After basic RECON, use [agent-driven job ideation](references/job-ideation.md) to compare prior coverage, derive several lightweight protocol-specific candidates, and select one Job with a concrete reachability basis, resource rationale, and discriminating next check. Checklist questions and historical edge cases may expand local reasoning; they cannot define or create the Job.
5. Build a detailed, useful SQLite graph before hunting. The graph is not a formality: close over every material producer of the sensitive consumer's inputs and every later consumer of attacker-influenced outputs, including sibling lifecycle and external effects. If the graph cannot answer the active Job's bidirectional reachability/effect questions, stop and deepen RECON instead of hunting from source-reading memory.
6. Prefer compiler AST/build artifacts and deterministic local tools for mechanical relationships. Never ask a model to reconstruct a transitive call graph when compiler-resolved evidence is available.
7. HUNT needs sufficient broad RECON plus deep deterministic graph/context coverage for the active job's relevant surface. Missing or unresolved information must be represented explicitly as `UNKNOWN`, never silently omitted.
8. Treat every lead as an allegation. Trace reachability, state mutation, later consumption, blockers, economics, live configuration, and the strongest safe explanation.
9. Use checklist and historical material in two bounded modes: after RECON to generate direct, edge-case, and composition questions around observed code; and after validation for novelty screening. A match creates a local question; it never proves the current protocol is vulnerable.
10. Use bounded SQLite queries. Do not load the complete database, all checkpoints, or large Markdown notebooks into context.
11. Use the installed Tenderly skill first for simulations, traces, forks, and state overrides. Use `cast` for narrow read-only facts. Pin chain, block, address, code hash when available, and observation time.
12. Once a hypothesis is `CODE_VALIDATED`, PoC work is part of the same research question: run `poc-handoff`, read the configured dedicated PoC skill's `SKILL.md`, and attempt the strongest practical proof. Ask the user only when the PoC environment or material data is missing.
13. Do not modify production contracts during setup, reconnaissance, or indexing.
14. The same research question means autonomous work; a new research direction requires explaining the recommendation and asking the user before switching.
15. Treat user-provided protocol context as useful but unverified. Store it as `USER_CONTEXT`, link likely affected records, verify before relying on it, and check whether it changes active jobs, rejected hypotheses, or parked directions.
16. Treat edge cases as reachable intersections of otherwise valid states, identities, modes, or lifecycle stages. For each active impact, compare the full logical context a sensitive consumer assumes with the context actually bound by identifiers, resource keys, proofs, callbacks, cached records, and validation. Persist a bounded lead when distinct contexts can collide or when a producer proves/returns something weaker, narrower, or different from what its consumer assumes; do not dismiss it merely because the configuration is uncommon.
17. When obvious Jobs are exhausted, expand the graph coverage frontier instead of renaming old questions. A Job variant must identify its parent, inherited coverage, materially new causal edge, distinct result it could produce, and new next check. Reuse the parent graph, deepen only the delta, and rotate away from a saturated family unless new evidence explicitly reopens it.

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
7. Before HUNT, run [RECON](workflows/recon.md), compare bounded Job/impact/family history, use [agent-driven job ideation](references/job-ideation.md) to select one locally derived Job or materially distinct variant, then deepen graph coverage across its causal surface or delta.

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

### Phase 3: Investigate In Layers

**Entry:** At least one local code anchor or impact goal exists.

1. Establish the protected value/right and relevant invariant.
2. Present the highest-value niche invariant or research question to the user before starting a new direction.
3. Trace entrypoint -> guards -> reads -> calculations -> external effects -> writes -> later consumers.
4. Run focused exploratory state probes when tests/forks/harnesses are available; inspect meaningful before/after state, not only revert status.
5. Store surprising-but-not-yet-buggy results as `OBSERVATION` or `STATE_PROBE`, linked to the current job.
6. Alternate first-principles and state-consistency lenses.
7. Inspect cross-function, cross-contract, cross-transaction, and external-protocol composition.
8. Run the context-collision and edge-case lead pass in [references/edge-case-leads.md](references/edge-case-leads.md) around the active sensitive consumer.
9. For live-dependent claims, follow [references/live-investigation.md](references/live-investigation.md).
10. If bounded code-led exploration stalls, run one impact-anchored historical pattern pass, convert matches into local hypotheses, and retrace them from current code.

**Exit:** The idea is rejected, blocked with one missing fact, or represented as a linked hypothesis with a concrete next check.

### Phase 4: Promote Or Kill

**Entry:** A concrete hypothesis exists.

1. Apply [references/evidence-promotion.md](references/evidence-promotion.md).
2. Record exact counterevidence and reopen conditions for rejected paths.
3. When new context arrives, store/classify/link it and check whether it affects the active job, contradicts an assumption, revives a rejected hypothesis, revives a parked job, or kills the active direction. Recommend reopening; do not silently reopen.
4. Run historical novelty checks before reportability.
5. At `CODE_VALIDATED`, run `poc-handoff`; if the configured PoC skill or environment is missing, ask the user for that missing item.

**Exit:** The hypothesis is rejected, remains a bounded lead, moves to proof, is PoC-blocked with one missing item, or reaches `POC_VALIDATED`.

### Phase 5: Checkpoint

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
- [references/layered-hunting.md](references/layered-hunting.md): forward/backward composition method.
- [references/edge-case-leads.md](references/edge-case-leads.md): codebase-agnostic context-collision, ambiguous-representation, and producer/consumer lead generation.
- [references/evidence-promotion.md](references/evidence-promotion.md): validation, rejection, automatic proof handoff, and report gates.
- [references/historical-research.md](references/historical-research.md): Solodit, similar audits, and hack-registry routing.
- [references/live-investigation.md](references/live-investigation.md): Tenderly-first on-chain evidence policy.
- [references/state-probes.md](references/state-probes.md): focused probe selection and provenance rules.
- [references/tool-routing.md](references/tool-routing.md): choose external evidence capabilities only when local code, graph context, probes, and reasoning cannot answer the active job.
- [references/cli.md](references/cli.md): compact command reference.

## Success Criteria

- Scope and source freshness are pinned.
- Basic global RECON is sufficient before HUNT; deep deterministic coverage is required for the active job's relevant surface.
- Runtime dispatch candidates are separated from live-confirmed implementations, and supporting test code does not contaminate production paths.
- Every important relation and claim has status, confidence, and evidence or an explicit unknown.
- Impact goals combine a protocol invariant with a concrete protocol case.
- Active jobs test whether identities, modes, lifecycle stages, and produced artifacts remain bound to the context assumed by sensitive consumers.
- Job selection records why the direction deserves resources, its cheapest kill check, its causal-surface boundary, and how it differs from prior coverage.
- Retrieval remains bounded to relevant rows and source spans.
- Rejected paths preserve kill evidence and reopen conditions.
- Novelty is checked before reporting.
- User context, observations, state probes, active jobs, hypotheses, and rejections survive restart in the existing `.audit`/SQLite store.
- `CODE_VALIDATED` automatically hands off to the configured dedicated PoC skill; reporting waits for proof validation and novelty.
