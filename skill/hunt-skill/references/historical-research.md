# Historical Research And Novelty

Historical material supplies hypotheses and duplicate checks. It does not replace local reachability or impact proof.

## Two Permitted Modes

### Job-Idea Generation

Use this after basic RECON through [agent-driven job ideation](job-ideation.md).

1. Start from a locally derived invariant, decision point, or attacker objective; select only checklist questions with concrete current-code triggers.
2. For the highest-value seed, inspect at most one closely related accepted finding or reproduced exploit when available.
3. Extract `prerequisite -> primitive -> trusted consumer -> consequence`, not the report title or exact protocol sequence.
4. Test both the direct issue and nearby edge-case/composition variants against the current graph.
5. Promote only a graph-anchored job; additional historical search is allowed if the active code-led investigation later stalls.

Do not import the old finding as a hypothesis with positive confidence. Start it as `UNKNOWN` or `LEAD` until current code supports it.

### Finding Validation

Use this after a local hypothesis survives falsification.

1. Search the same root cause, invariant, affected decision, and integration.
2. Compare prerequisites, impact, and mitigation rather than wording.
3. Decide whether the current issue is `NEW`, `DISTINCT`, `KNOWN`, `DUPLICATE`, or `UNCLEAR`.
4. Block reporting until all required novelty sources have a recorded disposition.

## Research Order

1. Anchor the search to local code, a protocol impact/invariant, or a material external integration.
2. Use only the relevant domain from the [Cyfrin audit checklist](https://github.com/Cyfrin/audit-checklist) or [EVM Audit Skills](https://github.com/austintgriffith/evm-audit-skills); do not import their full catalogs or workflows.
3. Search repository-known issues and bundled audits.
4. Search Solodit using the root cause, protocol mechanism, invariant, and integration name when `SOLODIT_API_KEY` and tooling are available.
5. Search the [EVM Hack Registry](https://github.com/sanbir/evm-hack-registry) for reproduced incident mechanics and missing variants.
6. Return matches to local code as questions. For validation, record overlaps in SQLite and explain why the root cause is duplicate, distinct, or unclear.

## Search Form

Avoid broad labels such as `reentrancy` or `oracle`. Combine:

```text
protocol mechanism + invariant + decision point + attacker primitive
```

Examples:

```text
ERC4626 collateral donation lending liquidation bad debt
vault delayed checkpoint deposit historical yield capture
bridge refund recipient retry stranded funds blacklist
```

## Tool Routing

- Use the installed Solodit skill/MCP for targeted historical findings when `SOLODIT_API_KEY` is configured. If the key or tooling is unavailable, state that Solodit research was not performed and continue local hunting.
- Use bundled PDFs/Markdown and official audit repositories for known-issue screening.
- Use a small CLI adapter for `sanbir/evm-hack-registry` rather than building an MCP unless authentication, remote hosting, or multi-client access becomes necessary.
- Pin source URL, record/commit/date, query, and conclusion in each novelty check.

Never store or print `SOLODIT_API_KEY`. Solodit results generate attack primitives and duplicate leads, not evidence for the current protocol.

## Promotion Rule

A finding is not real merely because a historical match exists, and it is not novel merely because its title differs. Compare root cause, affected decision, attacker prerequisites, impact, and recommended fix. Treat a documented root cause with a new cosmetic path as known unless the new path changes reachable impact or defeats the documented mitigation.
