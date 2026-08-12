# Historical Research And Novelty

Historical material supplies hypotheses and duplicate checks. It does not replace local reachability or impact proof.

## Two Permitted Modes

### Fallback Inspiration

Use this only after a bounded first-principles and state-consistency hunt fails to produce a useful lead.

1. Select one `READY` protocol impact, invariant, or material external integration.
2. Search similar findings by protocol archetype, economic decision, bad state, and attacker primitive.
3. Extract the historical root cause and required conditions, not its title alone.
4. Convert it into a question about the current protocol.
5. Return to current code and independently trace reachability, state mutation, blockers, and impact.

Do not import the old finding as a hypothesis with positive confidence. Start it as `UNKNOWN` or `LEAD` until current code supports it.

### Finding Validation

Use this after a local hypothesis survives falsification.

1. Search the same root cause, invariant, affected decision, and integration.
2. Compare prerequisites, impact, and mitigation rather than wording.
3. Decide whether the current issue is `NEW`, `DISTINCT`, `KNOWN`, `DUPLICATE`, or `UNCLEAR`.
4. Block reporting until all required novelty sources have a recorded disposition.

## Research Order

1. Anchor the search to local code, a `READY` protocol impact/invariant, or a material external integration.
2. Search repository-known issues and bundled audits first.
3. Search Solodit using the root cause, protocol archetype, invariant, and integration name when `SOLODIT_API_KEY` and tooling are available.
4. Review similar protocol audits for the same economic decision and attacker flow.
5. Search the EVM Hack Registry for incident mechanics and missing variants.
6. For inspiration, return matches to local code as questions. For validation, record overlaps in SQLite and explain why the root cause is duplicate, distinct, or unclear.

## Search Form

Avoid broad labels such as `reentrancy` or `oracle`. Combine:

```text
protocol archetype + invariant + decision point + attacker primitive
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
