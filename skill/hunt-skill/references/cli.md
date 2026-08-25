# Audit CLI Reference

For a project-local installation, set a helper for the current shell:

```bash
PROJECT=/absolute/path/to/audit-project
AUDITCTL="$PROJECT/.agents/skills/hunt-skill/scripts/auditctl.py"
```

## Initialization And Scope

```bash
python3 "$AUDITCTL" init --repo .
python3 "$AUDITCTL" snapshot --repo . --scope-file .audit/SCOPE_FILES.txt
```

`--scope` accepts files or directories and may be repeated. Prefer an exact scope file for contests and bounties.

## Graph Writes

```bash
python3 "$AUDITCTL" node-upsert --repo . --id function:... --kind function --name redeem --status VERIFIED
python3 "$AUDITCTL" relation-upsert --repo . --src function:... --type READS --dst storage:... --status VERIFIED
python3 "$AUDITCTL" invariant-upsert --repo . --id invariant:... --title "..." --statement "..." --protocol-case "..."
python3 "$AUDITCTL" impact-upsert --repo . --id impact:... --title "..." \
  --invariant-id invariant:... --protocol-case "..." --decision-point "..." \
  --bad-state "..." --attacker-goal "..." --candidate-primitive function:... --status READY
python3 "$AUDITCTL" hypothesis-upsert --repo . --id HYP-001 --title "..." --claim "..." \
  --impact-goal-id impact:... --next-check "..."
```

Create invariants, impacts, and Jobs only after [agent-driven job ideation](job-ideation.md) ties them to current-protocol code and graph evidence. Checklist and historical material do not seed records automatically. `--archetype` on `impact-upsert` is only an optional retrieval label and defaults to `protocol`.

## Retrieval

```bash
python3 "$AUDITCTL" search --repo . "cancel debt"
python3 "$AUDITCTL" neighbors --repo . function:... --types CALLS,READS,WRITES --depth 1 --limit 30
python3 "$AUDITCTL" path --repo . role:attacker asset:USDC --max-depth 3
python3 "$AUDITCTL" context --repo . --goal "Can cancellation desync debt?" --limit 20
python3 "$AUDITCTL" research-packet --repo . JOB-001 --limit 20
python3 "$AUDITCTL" stale --repo .
python3 "$AUDITCTL" lint --repo .
```

`research-packet` follows explicit `relations` linked to the Job and bounded graph anchors inherited from its variant lineage, then falls back to bounded FTS when neither exists.

## Research Jobs And User Context

```bash
python3 "$AUDITCTL" job-upsert --repo . --id JOB-001 \
  --goal "Can partial settlement make cancellation restore too much collateral?" --status ACTIVE
python3 "$AUDITCTL" job-list --repo . --limit 30
python3 "$AUDITCTL" job-list --repo . --linked-record impact:... --limit 20
python3 "$AUDITCTL" job-list --repo . --family JOB-001 --limit 30
python3 "$AUDITCTL" job-upsert --repo . --id JOB-002 --status NEXT \
  --goal "Can a different consumer accept the same bad representation?" \
  --variant-of JOB-001 --variant-delta "New consumer: collateral valuation" \
  --inherits "Producer reachability, state graph, and killed withdrawal path" \
  --distinctness "The new consumer does not use the withdrawal guard" \
  --next-check "Trace its valuation and liquidation paths"
python3 "$AUDITCTL" job-upsert --repo . --id JOB-001 --goal "..." --status DONE \
  --result "Coverage: ...; disposition: ...; unresolved: ...; reopen when: ..."
python3 "$AUDITCTL" job-upsert --repo . --id JOB-002 --goal "..." --status DONE \
  --result "Coverage: all supported family frontiers; disposition: ...; unresolved: none; reopen when: new evidence" \
  --saturate-family
python3 "$AUDITCTL" job-upsert --repo . --id JOB-003 --goal "..." --status NEXT \
  --variant-of JOB-002 --variant-delta "New deployed integration consumer" \
  --inherits "Existing producer and lifecycle coverage" \
  --distinctness "The integration validates the representation differently" \
  --next-check "Trace deployed valuation and liquidation paths" \
  --reopen-family-reason "Deployment evidence shows a newly reachable integration"
python3 "$AUDITCTL" context-add --repo . \
  --statement "FalconX NAV updates asynchronously."
python3 "$AUDITCTL" observation-add --repo . --job-id JOB-001 \
  --statement "Cancellation restores a different value path than settlement."
python3 "$AUDITCTL" probe-add --repo . --job-id JOB-001 \
  --setup "focused unit test" --sequence "requestWithdraw -> settlePartial -> cancelWithdraw" \
  --state-before "claim=100 settled=40" --state-after "claim=?" --result "record observed state"
```

Before creating a Job, use bounded `job-list`, `impact-list`, and graph queries to compare it with prior coverage. A new variant requires `--variant-delta`, `--inherits`, `--distinctness`, and `--next-check`; its research packet reuses parent-lineage graph anchors. `--saturate-family` is valid only for a `DONE` Job. A saturated family rejects new variants unless `--reopen-family-reason` records genuinely new evidence. `DONE` and `BLOCKED` require a result that records coverage, disposition, unresolved segments, and the reopen condition. Keep only one `ACTIVE` job and stop for human steering before switching to an independent research direction. User context starts as `UNKNOWN` unless independently verified. A probe is `INFERRED` by default; use `--executed --status VERIFIED --harness <test-or-trace>` only after actually running it.

## Novelty And Live Evidence

```bash
python3 "$AUDITCTL" known-add --repo . --id KNOWN-001 --source-kind repo-known --source "audit.pdf" --title "..." --root-cause "..."
python3 "$AUDITCTL" novelty-add --repo . HYP-001 --source-kind solodit --query "..." --result "..." --overlap NEW
python3 "$AUDITCTL" novelty-gate --repo . HYP-001
python3 "$AUDITCTL" rpc-resolve --repo . --chain base
python3 "$AUDITCTL" cast-read --repo . --chain base --operation call \
  --address 0x... --signature "totalAssets()(uint256)"
python3 "$AUDITCTL" live-add --repo . --id LIVE-001 --source-tool tenderly --chain-id 1 --block 123 \
  --address 0x... --claim "..." --status VERIFIED --retrieval-handle "simulation/fork id"
```

`cast-read` prefers `ALCHEMY_API_KEY` when available and otherwise uses a public RPC fallback for supported chains. Secret-bearing URLs are redacted from output.

## Automatic PoC Handoff

Configure the dedicated proof skill once:

```bash
python3 "$AUDITCTL" poc-config --repo . --path /absolute/path/to/poc-skill
```

After code validation, Codex checks and returns the proof handoff packet:

```bash
python3 "$AUDITCTL" poc-handoff --repo . HYP-001
```

If handoff fails, ask the user only for the missing proof input.

## Checkpoints

```bash
python3 "$AUDITCTL" checkpoint --repo .
```

Commands emit compact JSON for reliable Codex retrieval. Nonzero exit codes indicate a failed gate or invalid operation.

## Diagnostics

Do not run these at routine boot. Use them when installation, SQLite, search, or tooling behavior fails:

```bash
python3 "$AUDITCTL" doctor --repo .
python3 "$AUDITCTL" db-info --repo .
```
