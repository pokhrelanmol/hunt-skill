# VALIDATE Workflow

## Phase 1: Reconstruct The Allegation

**Entry:** One hypothesis is selected.

1. Query its impact, invariant, linked graph records, evidence, live facts, and blockers.
2. State the complete attacker lifecycle in transaction order.
3. Identify the single strongest reason it may fail.

**Exit:** Claim and falsification target are precise.

## Phase 2: Falsify

**Entry:** A precise lifecycle exists.

1. Verify access, reachability, ordering, state persistence, checks, synchronization, liquidity, capital, and economics.
2. Verify external protocol semantics and live configuration where material.
3. Test intentional-design and harmless-outcome explanations.
4. Reject immediately when concrete evidence kills a material element.

**Exit:** Every material promotion criterion is verified, disproven, or named as missing.

## Phase 3: Novelty And Skeptic

**Entry:** The local mechanism survives falsification.

1. Screen repository-known issues, similar audits, Solodit, and hack registry using the validated local root cause; this is validation/novelty mode, not inspiration mode.
2. Run an independent skeptic pass using raw claim/evidence only.
3. Compare root cause and impact, not wording.

**Exit:** The lead is duplicate/rejected, blocked, or novel enough to reach `CODE_VALIDATED`.

## Phase 4: Proof Handoff

**Entry:** Status is `CODE_VALIDATED`.

1. Present capability, call path, before/after state, broken invariant, impact, strongest blocker addressed, and novelty result.
2. Run `poc-handoff` and read the configured dedicated PoC skill when it passes.
3. Ask the user only when the PoC skill, fork/live environment, deployment data, or other material proof input is missing.

**Exit:** Proof begins for the same hypothesis, or the hypothesis is `POC_BLOCKED` with one concrete missing item.
