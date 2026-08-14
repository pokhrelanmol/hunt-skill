# FULL AUDIT Workflow

FULL AUDIT is an orchestration mode, not a second bug-hunting methodology.

Use it only when the user explicitly asks for a full audit, complete audit, full scan, autonomous full audit, audit everything in scope, or audit the full codebase. Do not infer FULL AUDIT from ordinary requests like "hunt", "find bugs", "check this flow", or "go deeper"; those stay in normal interactive HUNT.

## Mode Start And Resume

**Entry:** The user explicitly requests full-scope autonomous coverage.

1. Run `mode-set --mode FULL_AUDIT`.
2. Verify scope, pinned snapshot, dirty state, exclusions, docs, tests, and prior-audit corpus.
3. On resume, run `mode-status`; if mode is `FULL_AUDIT`, continue the agenda instead of stopping after one job.
4. Leave FULL AUDIT only when the audit completes, the user stops it, or the user explicitly switches back to `NORMAL_HUNT`.

**Exit:** `.audit/CURRENT.md` makes the mode, active job, completed count, and next job obvious.

## Broader RECON For Agenda Construction

FULL AUDIT needs broader coverage than interactive HUNT, but not irrelevant graph detail.

Map enough of the pinned scope to identify:

- state-changing entrypoints;
- assets and value flows;
- important state and coupled accounting relationships;
- roles, permissions, and privileged sensitive decisions;
- lifecycles, async steps, queues, cancellation, settlement, and finalization;
- external integrations, live dependencies, and cross-chain state;
- major protocol-specific invariants and forbidden states.

Use [recon.md](recon.md) for deterministic mapping and repair silent coverage gaps that would prevent agenda construction.

Do not build the agenda from informal source-reading notes alone. FULL AUDIT must create detailed graph records for the scoped audit surface: entrypoints, important internal functions, storage/state roots, roles/assets, external systems, call edges, read/write/effect edges, sensitive consumers, and invariant/impact links. If the graph is too thin to explain why a job exists or how it reaches a sensitive decision, keep building RECON instead of moving into HUNT.

## Build The Audit Agenda

Create concrete `JOB` rows from combinations of:

- protocol-specific invariants;
- sensitive decisions;
- major lifecycle transitions;
- important coupled state;
- external dependencies;
- attacker-accessible surfaces.
- capability fragments or missing prerequisites discovered while resolving earlier jobs.

Each agenda job must be linked to graph records before it becomes `ACTIVE`: the impact/invariant, the sensitive consumer or state root, relevant attacker entrypoint or explicit `UNKNOWN`, and any known external dependency. A job without these links is not ready for hunting; leave it `NEXT` or `BLOCKED` with the missing graph work.

Do not create generic category jobs such as "find reentrancy" or "find rounding bugs". Shape jobs as impact questions, for example:

```text
Can partial liquidation leave collateral/debt state inconsistent before a later borrow?
Can an external collateral-value change be consumed by borrow before synchronization?
Can withdrawal/cancellation restore collateral accounting incorrectly?
```

Deduplicate aggressively. Prioritize by:

```text
potential impact
× attacker reachability
× state sensitivity
× integration complexity
× novel or unexplored behavior
```

Prefer jobs involving asset movement, debt/collateral, share/accounting conversions, liquidation, withdrawals/redemptions, asynchronous state, privileged sensitive decisions, external integrations, cross-chain state, and coupled-state consistency.

## Coverage Tracking

Use the existing `coverage` table; do not create another database.

Track audit surfaces and important invariants/sensitive decisions with statuses such as `NEXT`, `ACTIVE`, `COVERED`, `BLOCKED`, and `NOT_APPLICABLE`.

Coverage does not mean "source was read". A surface is `COVERED` only when meaningful protocol-specific invariants or forbidden states were investigated through the relevant dimensions. For example, liquidation coverage should include debt reduction, collateral seizure, partial liquidation, accounting synchronization, post-liquidation borrow/withdraw effects, rounding/boundaries where relevant, and external price interaction where relevant.

## Process One ACTIVE Job At A Time

Keep one `ACTIVE` job, a prioritized `NEXT` agenda, and `PARKED`/`DONE`/`BLOCKED` jobs.

For each `ACTIVE` job, follow [hunt.md](hunt.md). `hunt.md` remains the single bug-hunting brain:

```text
niche invariant
-> forbidden state
-> sensitive consumer
-> backward trace from impact + forward trace from attacker
-> selected dimensions
-> State Probe when useful
-> observation
-> hypothesis when justified
-> aggressive falsification
-> CODE_VALIDATED
-> automatic PoC handoff
```

The only behavioral difference from interactive HUNT is the driver:

- interactive HUNT resolves one job, reports, recommends the next direction, and stops for human steering;
- FULL AUDIT resolves one job, persists the result and coverage, selects the next highest-value unresolved job, and continues automatically.

## Child Jobs

If an observation reveals a new meaningful audit question, add it to `NEXT` with suitable priority. Do not abandon the current job prematurely.

Example:

```text
ACTIVE: Can partial liquidation corrupt debt accounting?
OBSERVATION: cancelLiquidation() restores debt through a different path.
NEXT: Can cancellation restore debt/collateral asymmetrically?
```

Also add child jobs when a primitive produces a meaningful capability fragment, an initially missing resource becomes sourceable, or another subsystem may consume an intermediate representation. Keep the fragment as `OBSERVATION`/`UNKNOWN` until a complete lifecycle is proven.

## Probes, Live State, And History

Use State Probes systematically where tests, forks, or harnesses exist: dust, threshold +/- 1, partial operations, repeated actions, equivalent paths, operation reordering, different actors, time boundaries, and realistic external-state changes. Do not blindly fuzz everything.

External integrations are part of coverage. Derive impact-driven jobs for each material dependency and verify real external behavior only when required.

Historical research remains targeted: derive the required attack primitive for the current job, search Solodit or historical sources, extract relevant mechanisms, and verify locally. Do not dump broad historical findings into context.

## Findings And Rejections

If a hypothesis reaches `CODE_VALIDATED`, immediately run `poc-handoff` and follow the configured PoC skill. Do not postpone all PoCs until the end.

Rejected jobs are valuable coverage. Store the question, checked paths, blocking reason, evidence, remaining uncertainty, and reopen condition before marking the job resolved.

## Human Interaction

Because the user requested autonomous full coverage, do not ask for approval between jobs. Ask only when required information materially blocks analysis: missing scope, proprietary docs, deployment information, RPC/fork environment, or ambiguous intended behavior.

## Stop Condition

Do not stop because a fixed number of jobs ran. Stop when:

- all high-value protocol-specific surfaces are covered;
- major invariants and sensitive decisions have been exercised;
- material integrations have been investigated;
- serious observations and hypotheses are resolved;
- remaining jobs are low-value, duplicate, not applicable, or explicitly blocked by unavailable information.

Report unresolved coverage instead of inventing certainty.

## Final Report

End with:

- scope and snapshot;
- coverage summary;
- jobs investigated;
- validated findings;
- rejected high-value hypotheses;
- unresolved assumptions or blocked surfaces;
- residual risk and areas not fully covered.
