# Tenderly-First On-Chain Investigation

Use live evidence only when deployment state, configuration, external protocols, or historical execution materially affects exploitability.

## Routing

1. Discover the installed Tenderly skill by name/metadata and invoke it for transaction simulation, traces, forks, state overrides, and historical execution.
2. Use `cast call`, `cast code`, and pinned RPC reads for narrow facts that do not need simulation.
3. Use official explorers or verified deployment repositories to cross-check addresses and implementation versions.
4. If Tenderly is unavailable, state that explicitly; do not silently claim equivalent simulation evidence.

## Required Provenance

Record:

- chain ID and network;
- block number or transaction hash;
- contract and implementation addresses;
- relevant code hash when practical;
- observation time;
- Tenderly fork/simulation/trace identifier or exact RPC command;
- configuration fields that control reachability;
- whether the result is historical, current, or hypothetical state override.

Use `live-add` to persist compact conclusions and retrieval handles, not full traces.

## Interpretation Rules

- A state override proves mechanics under assumed state, not that an attacker can create that state.
- A fork beginning from prepared historical state proves downstream behavior, not all prerequisites.
- Current configuration is time-sensitive. Name a retest trigger such as proxy upgrade, market addition, oracle replacement, cap change, or pause transition.
- External permissionless manipulation must be analyzed at the external protocol too: entrypoint, capital, liquidity, fees, timing, and recovery/arbitrage forces.

## Dependency Check

`doctor` reports whether a Tenderly skill, CLI, or common Tenderly environment variables are visible. The hunt workflow remains usable when absent, but live simulation claims remain blocked until the integration is available.
