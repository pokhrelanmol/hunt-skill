# PROVE Workflow

## Phase 1: Enforce Handoff Gate

**Entry:** A hypothesis is `CODE_VALIDATED`.

1. Run `poc-handoff` before touching any proof file.
2. If it fails, stop and report the single missing item: configured PoC skill, source freshness, or proof environment/context.
3. Read the configured dedicated PoC skill's `SKILL.md` and follow its proof methodology; do not duplicate that methodology here.

**Exit:** Proof work is delegated to the configured PoC method for the current claim and source snapshot.

## Phase 2: Choose Smallest Decisive Proof

**Entry:** PoC gate passes.

1. Choose a state table or numerical example when execution is unnecessary.
2. Use a targeted unit test for isolated mechanics.
3. Use a fork/Tenderly simulation when live state or integrations matter.
4. Separate prepared-state mechanics from attacker-created prerequisites.

**Exit:** Proof method and exact claim are aligned.

## Phase 3: Build And Verify

**Entry:** Proof method is selected.

1. Make the smallest scoped proof change.
2. Assert the invariant before and violation after.
3. Demonstrate attacker benefit or protocol/user loss.
4. Run focused tests and include exact environment, block, configuration, and assumptions.

**Exit:** The proof decisively confirms or rejects the complete claim.

## Phase 4: Report Gate

**Entry:** Proof result is stable.

1. Run `novelty-gate` and `report-gate`.
2. Mark `POC_VALIDATED` only when the proof demonstrates the broken property; mark `POC_BLOCKED` for missing environment, or reject/demote when proof kills the claim.
3. Report only when impact, exploitability, proof, and novelty pass.
4. Otherwise demote or reject and preserve why.

**Exit:** A concise report or a precise rejection is available.
