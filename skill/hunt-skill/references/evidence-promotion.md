# Evidence, Promotion, And Human Gates

## Code-Validation Gate

Promote a hypothesis to `CODE_VALIDATED` only when all material elements are established:

1. Attacker capability: actor, permissions, capital, timing, inputs.
2. Reachability: exact external entrypoint and complete call path.
3. State transition: relevant before/after state.
4. Broken invariant: precise protocol expectation that fails.
5. Blocking checks: guards, reverts, sync, caps, slippage, downstream corrections.
6. Impact path: concrete route from bad state to meaningful loss or denial of service.
7. Feasibility: liquidity, ordering, fees, price impact, timing, profitability/cost.
8. External assumptions: token, oracle, bridge, dependency, deployment, and configuration evidence.
9. Strongest alternative explanation: why behavior is not safe, intentional, or harmless.

Keep the issue as a lead when a material item is unknown. Reject it immediately when an item is disproven.

## Independent Skeptic Pass

Give the skeptic the claim and raw evidence, not the original persuasive narrative. Ask for the strongest reject reason, hidden checks, prerequisite realism, state persistence, economics, known-root-cause overlap, and whether the evidence proves the whole attacker lifecycle.

## Novelty Gate

Before reporting, record checks for:

- `repo-known`: README, issue lists, judge notes, bundled/official audits.
- `similar-audit`: audits of the same protocol archetype or external integration.
- `solodit`: root-cause and invariant searches anchored to local code.
- `hack-registry`: analogous incident mechanics and variants.

Any `KNOWN` or `DUPLICATE` overlap blocks reporting until the distinction is explicit. `UNCLEAR` remains blocked. Historical similarity never proves the local issue.

## Human PoC Gate

PoC work requires all of the following:

1. Hypothesis status is `CODE_VALIDATED`.
2. The user manually reviews and validates the allegation.
3. The user runs `approve-poc` interactively, or explicitly asks Codex to record that approval after review.
4. The approval matches the current hypothesis claim hash.
5. The approval matches the current in-scope source hash.

Codex must not invoke `approve-poc` merely because the user liked the idea or asked to continue. Run `poc-gate` immediately before creating or changing any proof file. A source or claim change invalidates the approval.

## Report Gate

Final reporting requires a confirmed proof or decisive state demonstration, a passing novelty gate, and no unresolved material blocker. Clearly separate mechanism proof from proof that an attacker can create every prerequisite in live conditions.
