# Evidence, Promotion, And Proof Handoff

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

For context-collision leads, “rare” is not kill evidence. Preserve the lead when two distinct logical contexts can plausibly share an accepted representation or when a producer's result can mean something different from what a sensitive consumer assumes. Promote only after the collision/mismatch, attacker reachability, consumer acceptance, and meaningful consequence are established. Reject when code or deployment constraints make the intersection unreachable, the consumer rebinds every material context dimension, the effect is harmless, or a reliable recovery path prevents impact.

## Independent Skeptic Pass

Give the skeptic the claim and raw evidence, not the original persuasive narrative. Ask for the strongest reject reason, hidden checks, prerequisite realism, state persistence, economics, known-root-cause overlap, and whether the evidence proves the whole attacker lifecycle.

## Novelty Gate

Before reporting, record checks for:

- `repo-known`: README, issue lists, judge notes, bundled/official audits.
- `similar-audit`: audits of the same protocol archetype or external integration.
- `solodit`: root-cause and invariant searches anchored to local code.
- `hack-registry`: analogous incident mechanics and variants.

Any `KNOWN` or `DUPLICATE` overlap blocks reporting until the distinction is explicit. `UNCLEAR` remains blocked. Historical similarity never proves the local issue.

## Automatic PoC Handoff

PoC work requires all of the following:

1. Hypothesis status is `CODE_VALIDATED`.
2. The current source scope is fresh.
3. A dedicated PoC skill path is configured with `poc-config`.
4. The configured PoC skill path contains `SKILL.md`.

Run `poc-handoff` immediately before creating or changing any proof file. If it fails, ask only for the missing proof input: PoC skill path, source refresh, RPC/fork environment, deployed address, or other material context. The PoC can validate the hypothesis, block on environment, or kill the hypothesis.

## Report Gate

Final reporting requires a confirmed proof or decisive state demonstration, a passing novelty gate, and no unresolved material blocker. Clearly separate mechanism proof from proof that an attacker can create every prerequisite in live conditions.
