# Audit CLI Reference

For a project-local installation, set a helper for the current shell:

```bash
PROJECT=/absolute/path/to/audit-project
AUDITCTL="$PROJECT/.agents/skills/hunt-skill/scripts/auditctl.py"
python3 "$AUDITCTL" doctor --repo "$PROJECT"
```

## Setup

```bash
python3 "$AUDITCTL" doctor --repo .
python3 "$AUDITCTL" init --repo .
python3 "$AUDITCTL" snapshot --repo . --scope-file .audit/SCOPE_FILES.txt
python3 "$AUDITCTL" profile-set --repo . --name Grunt --archetype vault \
  --case "Facility shares, principal, requests, claims, and debt settlement form one vault-like accounting system."
python3 "$AUDITCTL" impact-seed --repo .
```

`--scope` accepts files or directories and may be repeated. Prefer an exact scope file for contests and bounties.

## Graph Writes

```bash
python3 "$AUDITCTL" node-upsert --repo . --id function:... --kind function --name redeem --status VERIFIED
python3 "$AUDITCTL" relation-upsert --repo . --src function:... --type READS --dst storage:... --status VERIFIED
python3 "$AUDITCTL" invariant-upsert --repo . --id invariant:... --title "..." --statement "..." --protocol-case "..."
python3 "$AUDITCTL" impact-upsert --repo . --id impact:... --archetype vault --title "..." \
  --invariant-id invariant:... --protocol-case "..." --decision-point "..." \
  --bad-state "..." --attacker-goal "..." --candidate-primitive function:... --status READY
python3 "$AUDITCTL" hypothesis-upsert --repo . --id HYP-001 --title "..." --claim "..." \
  --impact-goal-id impact:... --next-check "..."
```

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

`research-packet` follows explicit `relations` linked to the job first, then falls back to bounded FTS when no links exist.

## Research Jobs And User Context

```bash
python3 "$AUDITCTL" job-upsert --repo . --id JOB-001 \
  --goal "Can partial settlement make cancellation restore too much collateral?" --status ACTIVE
python3 "$AUDITCTL" context-add --repo . \
  --statement "FalconX NAV updates asynchronously."
python3 "$AUDITCTL" observation-add --repo . --job-id JOB-001 \
  --statement "Cancellation restores a different value path than settlement."
python3 "$AUDITCTL" probe-add --repo . --job-id JOB-001 \
  --setup "focused unit test" --sequence "requestWithdraw -> settlePartial -> cancelWithdraw" \
  --state-before "claim=100 settled=40" --state-after "claim=?" --result "record observed state"
```

Keep only one `ACTIVE` job. User context starts as `UNKNOWN` unless independently verified. A probe is `INFERRED` by default; use `--executed --status VERIFIED --harness <test-or-trace>` only after actually running it.

## Novelty And Live Evidence

```bash
python3 "$AUDITCTL" known-add --repo . --id KNOWN-001 --source-kind repo-known --source "audit.pdf" --title "..." --root-cause "..."
python3 "$AUDITCTL" novelty-add --repo . HYP-001 --source-kind solodit --query "..." --result "..." --overlap NEW
python3 "$AUDITCTL" novelty-gate --repo . HYP-001
python3 "$AUDITCTL" live-add --repo . --id LIVE-001 --source-tool tenderly --chain-id 1 --block 123 \
  --address 0x... --claim "..." --status VERIFIED --retrieval-handle "simulation/fork id"
```

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
python3 "$AUDITCTL" db-info --repo .
```

Commands emit compact JSON for reliable Codex retrieval. Nonzero exit codes indicate a failed gate or invalid operation.
