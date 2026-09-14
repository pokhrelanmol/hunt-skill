# Capability-Only Tool Routing

Job ideation and user selection determine the question; `hunt.md` owns its investigation. This file routes missing evidence during RECON, ideation, and the chosen Job.

Do not route to a separate skill only for first-principles questioning, state consistency, accounting analysis, lifecycle reasoning, actor/boundary analysis, or simple mechanism explanation. Those reasoning lenses are built into Hunt.

## Use External Capabilities Only When Evidence Requires Them

| Evidence need | Route |
|---|---|
| Meaning, update timing, or guarantees of an external dependency | Pinned dependency source and authoritative documentation; verify deployment identity when material |
| Historical primitive, similar prior finding, or novelty check | Solodit / historical finding search when key and tooling are available |
| Current or historical on-chain behavior requiring trace, simulation, fork, or state override | Installed Tenderly capability when available and useful |
| Narrow live-chain fact such as config, balance, code, storage, or view call | `auditctl.py cast-read` with pinned chain/block/address and redacted RPC provenance |
| Executable proof after `CODE_VALIDATED` | Configured dedicated PoC skill via `poc-handoff` |
| Specialized external analyzer that returns unique evidence Hunt cannot efficiently derive locally | Use only for the specific ACTIVE JOB and record the evidence/provenance |

If local code, SQLite graph context, compiler artifacts, tests, or focused State Probes answer the question, do not load an external skill.

Kept tools remain on-demand. An ACTIVE Job is not required to resolve a material dependency assumption during RECON or candidate preparation; keep retrieval bounded to that question.
