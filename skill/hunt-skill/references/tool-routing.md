# Evidence-Driven Tool Routing

Choose tools because the current evidence demands them. Do not run a universal scanner stack.

| Need | Preferred route |
|---|---|
| Scope, history, dirty state | `git`, SHA-256 scope snapshot |
| Fast code and symbol search | `rg` |
| Solidity compile/AST facts | Foundry build-info, optional Slither |
| Entrypoint inventory | `entry-point-analyzer` skill |
| Coupled state concern | `state-inconsistency-auditor` skill |
| Business-logic assumption | `feynman-auditor` skill |
| Spec mismatch | `spec-to-code-compliance` skill |
| Token semantics | `token-integration-analyzer` skill |
| Root-cause variants | `variant-analysis` after validation |
| Historical precedent | Solodit after a local anchor |
| On-chain simulation/trace | Installed Tenderly skill |
| Narrow live read | `cast` with pinned chain/block |
| Focused behavior proof | Configured PoC skill, then Foundry test/fuzz/invariant test or fork/Tenderly proof |
| Graph/path/context | `auditctl.py` bounded SQLite commands |
| Portable checkpoint | Deterministic JSONL export |

Pass specialists a compact question, relevant IDs, source spans, and unresolved assumptions. The main agent owns status, deduplication, graph updates, and final judgment.

Prefer deterministic extraction for symbols, hashes, direct edges, freshness, and search. Reserve model reasoning for invariants, protocol-specific impacts, cross-module composition, economics, and skeptical validation.
