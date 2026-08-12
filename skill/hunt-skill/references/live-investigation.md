# Live On-Chain Investigation

Use live evidence only when deployment state, configuration, external protocols, or historical execution materially affects exploitability.

## Routing

1. Discover the installed Tenderly skill by name/metadata and invoke it for transaction simulation, traces, forks, state overrides, and historical execution.
2. If Tenderly is unavailable, unsuitable, or unnecessary, use `auditctl.py cast-read` for narrow `cast` reads.
3. Use official explorers or verified deployment repositories to cross-check addresses and implementation versions.
4. If both Tenderly and `cast`/RPC are unavailable, state the missing capability and continue local hunting.

## RPC Resolution

`cast-read` resolves the chain from `--chain`, `--chain-id`, stored audit context, or recent live evidence. For supported chains it prefers `ALCHEMY_API_KEY` when present; otherwise it falls back to a small public RPC mapping. Do not ask the user to configure RPC URL templates for normal supported chains.

Never print or persist authenticated RPC URLs. Store safe provenance only: provider, chain ID, block/tx, address, method, and retrieval handle.

## Required Provenance

Record:

- chain ID and network;
- block number or transaction hash;
- contract and implementation addresses;
- relevant code hash when practical;
- observation time;
- Tenderly fork/simulation/trace identifier or redacted `cast` retrieval handle;
- configuration fields that control reachability;
- whether the result is historical, current, or hypothetical state override.

Use `live-add` to persist compact conclusions and retrieval handles, not full traces.

## Interpretation Rules

- A state override proves mechanics under assumed state, not that an attacker can create that state.
- A fork beginning from prepared historical state proves downstream behavior, not all prerequisites.
- Public RPC failures or archive limitations are not protocol behavior. Try another endpoint/provider or ask for missing capability.
- Current configuration is time-sensitive. Name a retest trigger such as proxy upgrade, market addition, oracle replacement, cap change, or pause transition.
- External permissionless manipulation must be analyzed at the external protocol too: entrypoint, capital, liquidity, fees, timing, and recovery/arbitrage forces.

## Dependency Check

`doctor` reports Tenderly, `cast`, Alchemy key presence, Solodit key/tooling, and detected chain when available. Missing optional tooling should not fail local analysis.
