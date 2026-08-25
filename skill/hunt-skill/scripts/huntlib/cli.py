from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any

from . import SCHEMA_VERSION
from .db import (
    SEARCHABLE_TABLES,
    as_dicts,
    canonical_json,
    connect,
    db_path,
    initialize,
    refresh_search,
    upsert_search,
    utcnow,
)
from .gates import NOVELTY_SOURCES, novelty_gate, poc_gate, record_poc_approval, report_gate
from .scope import (
    capture_snapshot,
    current_scope,
    expand_scope,
    parse_scope_file,
    source_hash_for_path,
)


EVIDENCE_STATUSES = {"VERIFIED", "INFERRED", "UNKNOWN", "STALE"}
IMPACT_STATUSES = {"DRAFT", "READY", "COVERED"}
HYPOTHESIS_STATUSES = {
    "LEAD",
    "INVESTIGATING",
    "CODE_VALIDATED",
    "POC_VALIDATED",
    "POC_BLOCKED",
    "MANUAL_VALIDATED",
    "CONFIRMED",
    "BLOCKED",
    "REJECTED",
}
JOB_STATUSES = {"ACTIVE", "NEXT", "PARKED", "DONE", "BLOCKED"}
RELATION_TYPES = {
    "DECLARES",
    "INHERITS",
    "OVERRIDES",
    "CALLS",
    "DELEGATECALLS",
    "CALLBACKS_TO",
    "READS",
    "WRITES",
    "DERIVES_FROM",
    "INVALIDATES",
    "CHECKPOINTS",
    "GUARDED_BY",
    "AUTHORIZES",
    "GRANTS_ROLE",
    "REVOKES_ROLE",
    "TRUSTS",
    "TRANSFERS",
    "MINTS",
    "BURNS",
    "DEPOSITS",
    "WITHDRAWS",
    "BORROWS",
    "REPAYS",
    "LIFECYCLE_NEXT",
    "CANCELS",
    "SETTLES",
    "LIQUIDATES",
    "CLAIMS",
    "ENFORCES",
    "RELIES_ON",
    "CONFLICTS_WITH",
    "CONSUMES",
    "PRODUCES",
    "EXTERNALIZES_TO",
    "CONFIGURED_BY",
    "PRICES",
    "BACKS",
    "BREAKS",
    "FOCUSES_ON",
    "INVESTIGATES",
    "OBSERVED_IN",
    "ASSUMES",
    "REVIVES",
    "VARIANT_OF",
}


def emit(value: Any) -> None:
    print(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True))


def repo_path(args) -> Path:
    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists() or not repo.is_dir():
        raise ValueError(f"repository directory not found: {repo}")
    return repo


def require_status(value: str, allowed: set[str], label: str) -> str:
    normalized = value.upper()
    if normalized not in allowed:
        raise ValueError(f"invalid {label}: {value}; expected one of {', '.join(sorted(allowed))}")
    return normalized


def claim_hash(claim: str) -> str:
    return hashlib.sha256(claim.strip().encode()).hexdigest()


CHAIN_INFO: dict[int, dict[str, Any]] = {
    1: {
        "name": "Ethereum",
        "aliases": {"ethereum", "eth", "mainnet", "ethereum-mainnet"},
        "alchemy": "https://eth-mainnet.g.alchemy.com/v2/{key}",
        "public": ["https://eth.llamarpc.com", "https://ethereum.publicnode.com"],
    },
    10: {
        "name": "Optimism",
        "aliases": {"optimism", "op", "op-mainnet", "optimism-mainnet"},
        "alchemy": "https://opt-mainnet.g.alchemy.com/v2/{key}",
        "public": ["https://mainnet.optimism.io"],
    },
    137: {
        "name": "Polygon",
        "aliases": {"polygon", "matic", "polygon-mainnet"},
        "alchemy": "https://polygon-mainnet.g.alchemy.com/v2/{key}",
        "public": ["https://polygon.drpc.org", "https://polygon.publicnode.com"],
    },
    8453: {
        "name": "Base",
        "aliases": {"base", "base-mainnet"},
        "alchemy": "https://base-mainnet.g.alchemy.com/v2/{key}",
        "public": ["https://mainnet.base.org", "https://base.publicnode.com"],
    },
    42161: {
        "name": "Arbitrum",
        "aliases": {"arbitrum", "arbitrum-one", "arb", "arb1"},
        "alchemy": "https://arb-mainnet.g.alchemy.com/v2/{key}",
        "public": ["https://arb1.arbitrum.io/rpc", "https://arbitrum-one-rpc.publicnode.com"],
    },
}


def detect_skill(keyword: str) -> list[str]:
    home = Path.home()
    roots = [home / ".agents" / "skills", home / ".codex" / "skills", home / ".claude" / "skills"]
    skills = []
    for root in roots:
        if not root.exists():
            continue
        for skill_file in root.glob("*/SKILL.md"):
            try:
                header = skill_file.read_text(encoding="utf-8", errors="ignore")[:4000]
            except OSError:
                continue
            name_match = re.search(r"(?m)^name:\s*['\"]?([^'\"\n]+)", header)
            declared_name = name_match.group(1).strip().lower() if name_match else ""
            haystack = f"{skill_file.parent.name.lower()} {declared_name}"
            if keyword.lower() in haystack:
                skills.append(str(skill_file.parent))
    return sorted(skills)


def chain_by_name_or_id(value: str | int | None) -> tuple[int, dict[str, Any]] | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text.isdigit():
        chain_id = int(text)
        info = CHAIN_INFO.get(chain_id)
        return (chain_id, info) if info else None
    for chain_id, info in CHAIN_INFO.items():
        if text == info["name"].lower() or text in info["aliases"]:
            return chain_id, info
    return None


def detected_chain(repo: Path) -> tuple[int, dict[str, Any]] | None:
    try:
        conn = connect(repo)
    except (FileNotFoundError, sqlite3.Error):
        return None
    try:
        row = conn.execute("SELECT value FROM meta WHERE key='chain_id'").fetchone()
        if row:
            found = chain_by_name_or_id(row["value"])
            if found:
                return found
        row = conn.execute(
            "SELECT chain_id FROM live_evidence ORDER BY observed_at DESC LIMIT 1"
        ).fetchone()
        if row:
            return chain_by_name_or_id(row["chain_id"])
    finally:
        conn.close()
    return None


def resolve_chain(repo: Path, chain: str | None, chain_id: int | None) -> tuple[int, dict[str, Any]]:
    requested = chain_by_name_or_id(chain_id if chain_id is not None else chain)
    if requested:
        return requested
    current = detected_chain(repo)
    if current:
        return current
    raise ValueError("chain not detected; provide --chain or --chain-id for this live read")


def resolve_rpc(repo: Path, chain: str | None = None, chain_id: int | None = None) -> dict[str, Any]:
    resolved_chain_id, info = resolve_chain(repo, chain, chain_id)
    alchemy_key = os.environ.get("ALCHEMY_API_KEY")
    if alchemy_key and info.get("alchemy"):
        return {
            "chain": info["name"],
            "chain_id": resolved_chain_id,
            "provider": "alchemy",
            "rpc_url": info["alchemy"].format(key=alchemy_key),
            "rpc_url_redacted": info["alchemy"].format(key="<redacted>"),
            "public_fallbacks": info["public"],
        }
    public = info["public"][0] if info.get("public") else None
    if not public:
        raise ValueError(f"no RPC fallback configured for chain_id={resolved_chain_id}")
    return {
        "chain": info["name"],
        "chain_id": resolved_chain_id,
        "provider": "public",
        "rpc_url": public,
        "rpc_url_redacted": public,
        "public_fallbacks": info["public"],
    }


def redact_secret_text(text: str) -> str:
    redacted = text
    for name in ("ALCHEMY_API_KEY", "SOLODIT_API_KEY"):
        value = os.environ.get(name)
        if value:
            redacted = redacted.replace(value, "<redacted>")
    return redacted


def detect_tenderly() -> dict[str, Any]:
    env_names = [
        name
        for name in ("TENDERLY_ACCESS_KEY", "TENDERLY_ACCOUNT_SLUG", "TENDERLY_PROJECT_SLUG")
        if os.environ.get(name)
    ]
    return {
        "skill_paths": detect_skill("tenderly"),
        "cli": shutil.which("tenderly"),
        "environment_names_present": env_names,
        "available": bool(detect_skill("tenderly") or shutil.which("tenderly")),
    }


def detect_solodit() -> dict[str, Any]:
    skills = detect_skill("solodit")
    return {
        "api_key": "configured" if os.environ.get("SOLODIT_API_KEY") else "missing",
        "skill_paths": skills,
        "available": bool(skills and os.environ.get("SOLODIT_API_KEY")),
    }


def cmd_doctor(args) -> None:
    repo = repo_path(args)
    capabilities: dict[str, bool] = {}
    memory = sqlite3.connect(":memory:")
    try:
        memory.execute("SELECT json('{}')").fetchone()
        capabilities["json1"] = True
    except sqlite3.OperationalError:
        capabilities["json1"] = False
    try:
        memory.execute("CREATE VIRTUAL TABLE test_fts USING fts5(body)")
        capabilities["fts5"] = True
    except sqlite3.OperationalError:
        capabilities["fts5"] = False
    finally:
        memory.close()
    python_ok = sys.version_info >= (3, 11)
    chain = detected_chain(repo)
    rpc_status = {
        "alchemy_api_key": "configured" if os.environ.get("ALCHEMY_API_KEY") else "missing",
        "cast": shutil.which("cast"),
        "fallback": "alchemy" if os.environ.get("ALCHEMY_API_KEY") else "public RPC",
    }
    if chain:
        chain_id, info = chain
        rpc_status["detected_chain"] = info["name"]
        rpc_status["chain_id"] = chain_id
    result = {
        "ok": python_ok and all(capabilities.values()),
        "python": sys.version.split()[0],
        "python_ok": python_ok,
        "sqlite": sqlite3.sqlite_version,
        "sqlite_cli": shutil.which("sqlite3"),
        "capabilities": capabilities,
        "solodit": detect_solodit(),
        "tenderly": detect_tenderly(),
        "live_state": rpc_status,
        "runtime_dependencies": [],
        "next": "run init only if .audit/graph/audit.db is absent" if python_ok and all(capabilities.values()) else "fix failed requirements",
    }
    emit(result)
    if not result["ok"]:
        raise SystemExit(2)


CONTROL_FILES = {
    "INDEX.md": """# Audit Index

Protocol: TODO
Scope snapshot: not captured
Active job: none
Current focus: capture exact scope and map the protocol
""",
    "PROJECT.md": """# Protocol Model

Keep only stable, verified architecture, roles, assets, accounting, invariants, integrations, and deployment facts here. Detailed relationships belong in SQLite.
""",
    "CURRENT.md": """# Current Audit State

Focus: scope and reconnaissance
Next discriminating check: capture exact scope, then map one protocol-specific impact
""",
    "LEADS.md": """# Active Leads

Compact human summaries only. Detailed hypothesis evidence belongs in SQLite.
""",
    "REJECTIONS.md": """# Rejected Paths

Record concise kill reasons and reopen conditions. Detailed evidence belongs in SQLite.
""",
    "SCOPE_FILES.txt": """# One repository-relative in-scope file or directory per line.
# Prefer exact file lists for contests and bounties.
""",
    ".gitignore": """graph/audit.db
graph/audit.db-shm
graph/audit.db-wal
""",
}


def cmd_init(args) -> None:
    repo = repo_path(args)
    audit_dir = repo / ".audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    created = []
    preserved = []
    for name, content in CONTROL_FILES.items():
        path = audit_dir / name
        if path.exists():
            preserved.append(str(path.relative_to(repo)))
        else:
            path.write_text(content, encoding="utf-8")
            created.append(str(path.relative_to(repo)))
    conn = initialize(repo)
    conn.close()
    emit(
        {
            "ok": True,
            "database": str(db_path(repo)),
            "schema_version": SCHEMA_VERSION,
            "created": created,
            "preserved": preserved,
            "next": "edit .audit/SCOPE_FILES.txt, then run snapshot --scope-file .audit/SCOPE_FILES.txt",
        }
    )


def cmd_snapshot(args) -> None:
    repo = repo_path(args)
    entries = list(args.scope or [])
    if args.scope_file:
        entries.extend(parse_scope_file(repo, Path(args.scope_file)))
    if not entries:
        raise ValueError("provide at least one --scope or --scope-file")
    paths = expand_scope(repo, entries)
    conn = connect(repo)
    result = capture_snapshot(conn, repo, paths)
    conn.close()
    result["ok"] = True
    result["scope_entries"] = entries
    emit(result)


def cmd_invariant_upsert(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    now = utcnow()
    conn.execute(
        "INSERT INTO invariants(id, title, statement, scope, protocol_case, status, created_at, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, "
        "statement=excluded.statement, scope=excluded.scope, protocol_case=excluded.protocol_case, "
        "status=excluded.status, updated_at=excluded.updated_at",
        (args.id, args.title, args.statement, args.scope or "", args.protocol_case or "", status, now, now),
    )
    upsert_search(conn, "invariants", args.id)
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id, "status": status})


def cmd_impact_upsert(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    existing = conn.execute("SELECT * FROM impact_goals WHERE id = ?", (args.id,)).fetchone()
    status_value = args.status if args.status is not None else (existing["status"] if existing else "DRAFT")
    status = require_status(status_value, IMPACT_STATUSES, "impact status")

    def choose(name: str, default: Any = "") -> Any:
        value = getattr(args, name)
        if value is not None:
            return value
        return existing[name] if existing is not None else default

    values = {
        "archetype": choose("archetype", "protocol"),
        "title": choose("title"),
        "invariant_id": choose("invariant_id", None),
        "protocol_case": choose("protocol_case"),
        "decision_point": choose("decision_point"),
        "bad_state": choose("bad_state"),
        "attacker_goal": choose("attacker_goal"),
    }
    if args.candidate_primitive is not None:
        primitives = args.candidate_primitive
    elif existing is not None:
        primitives = json.loads(existing["candidate_primitives_json"])
    else:
        primitives = []
    if status == "READY":
        required = ("title", "invariant_id", "protocol_case", "decision_point", "bad_state", "attacker_goal")
        missing = [name for name in required if not values[name]]
        if not primitives:
            missing.append("candidate_primitives")
        if missing:
            raise ValueError(f"READY impact missing protocol-specific fields: {', '.join(missing)}")
        invariant = conn.execute("SELECT id FROM invariants WHERE id = ?", (values["invariant_id"],)).fetchone()
        if invariant is None:
            raise ValueError(f"invariant not found: {values['invariant_id']}")
    now = utcnow()
    conn.execute(
        "INSERT INTO impact_goals(id, archetype, title, invariant_id, protocol_case, decision_point, "
        "bad_state, attacker_goal, candidate_primitives_json, status, source, created_at, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'custom', ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "archetype=excluded.archetype, title=excluded.title, invariant_id=excluded.invariant_id, "
        "protocol_case=excluded.protocol_case, decision_point=excluded.decision_point, "
        "bad_state=excluded.bad_state, attacker_goal=excluded.attacker_goal, "
        "candidate_primitives_json=excluded.candidate_primitives_json, status=excluded.status, "
        "updated_at=excluded.updated_at",
        (
            args.id,
            values["archetype"],
            values["title"],
            values["invariant_id"],
            values["protocol_case"],
            values["decision_point"],
            values["bad_state"],
            values["attacker_goal"],
            canonical_json(primitives),
            status,
            now,
            now,
        ),
    )
    upsert_search(conn, "impact_goals", args.id)
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id, "status": status, "candidate_primitives": primitives})


def cmd_impact_list(args) -> None:
    conn = connect(repo_path(args))
    query = "SELECT * FROM impact_goals"
    params: list[Any] = []
    clauses = []
    if args.status:
        clauses.append("status = ?")
        params.append(args.status.upper())
    if args.archetype:
        clauses.append("archetype = ?")
        params.append(args.archetype)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY archetype, id LIMIT ?"
    params.append(args.limit)
    rows = as_dicts(conn.execute(query, params))
    for row in rows:
        row["candidate_primitives"] = json.loads(row.pop("candidate_primitives_json"))
    conn.close()
    emit({"count": len(rows), "rows": rows})


def cmd_node_upsert(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    now = utcnow()
    conn.execute(
        "INSERT INTO nodes(id, kind, name, summary, file_path, line_start, line_end, status, confidence, "
        "created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "kind=excluded.kind, name=excluded.name, summary=excluded.summary, file_path=excluded.file_path, "
        "line_start=excluded.line_start, line_end=excluded.line_end, status=excluded.status, "
        "confidence=excluded.confidence, updated_at=excluded.updated_at",
        (
            args.id,
            args.kind,
            args.name,
            args.summary or "",
            args.file_path,
            args.line_start,
            args.line_end,
            status,
            args.confidence,
            now,
            now,
        ),
    )
    upsert_search(conn, "nodes", args.id)
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id, "status": status})


def relation_id(src: str, relation_type: str, dst: str) -> str:
    digest = hashlib.sha256(f"{src}\0{relation_type}\0{dst}".encode()).hexdigest()[:16]
    return f"relation:{digest}"


def cmd_relation_upsert(args) -> None:
    conn = connect(repo_path(args))
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    relation_type = args.type.upper()
    if relation_type not in RELATION_TYPES and ":" not in relation_type:
        raise ValueError("unknown relation type; use a controlled type or namespaced extension")
    rid = args.id or relation_id(args.src, relation_type, args.dst)
    now = utcnow()
    conn.execute(
        "INSERT INTO relations(id, src_id, type, dst_id, summary, status, confidence, created_at, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET src_id=excluded.src_id, "
        "type=excluded.type, dst_id=excluded.dst_id, summary=excluded.summary, status=excluded.status, "
        "confidence=excluded.confidence, updated_at=excluded.updated_at",
        (rid, args.src, relation_type, args.dst, args.summary or "", status, args.confidence, now, now),
    )
    conn.commit()
    conn.close()
    emit({"ok": True, "id": rid, "status": status})


def cmd_fact_upsert(args) -> None:
    conn = connect(repo_path(args))
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    now = utcnow()
    conn.execute(
        "INSERT INTO facts(id, subject_id, kind, statement, status, confidence, created_at, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET subject_id=excluded.subject_id, "
        "kind=excluded.kind, statement=excluded.statement, status=excluded.status, "
        "confidence=excluded.confidence, updated_at=excluded.updated_at",
        (args.id, args.subject_id, args.kind, args.statement, status, args.confidence, now, now),
    )
    upsert_search(conn, "facts", args.id)
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id, "status": status})


def cmd_evidence_add(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    file_path = args.file_path
    snapshot_id = None
    file_hash = None
    if file_path:
        normalized = (repo / file_path).resolve().relative_to(repo).as_posix()
        snapshot_id, file_hash = source_hash_for_path(conn, normalized)
        if file_hash is None and args.source_kind == "code":
            raise ValueError(f"code evidence is not in latest scope snapshot: {normalized}")
        file_path = normalized
    cursor = conn.execute(
        "INSERT INTO evidence(record_type, record_id, source_kind, file_path, file_sha256, line_start, "
        "line_end, note, retrieval_handle, snapshot_id, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            args.record_type,
            args.record_id,
            args.source_kind,
            file_path,
            file_hash,
            args.line_start,
            args.line_end,
            args.note,
            args.retrieval_handle,
            snapshot_id,
            utcnow(),
        ),
    )
    conn.commit()
    conn.close()
    emit({"ok": True, "evidence_id": cursor.lastrowid, "snapshot_id": snapshot_id})


def cmd_hypothesis_upsert(args) -> None:
    conn = connect(repo_path(args))
    existing = conn.execute("SELECT * FROM hypotheses WHERE id = ?", (args.id,)).fetchone()
    status_value = args.status if args.status is not None else (existing["status"] if existing else "LEAD")
    status = require_status(status_value, HYPOTHESIS_STATUSES, "hypothesis status")
    if status in {"MANUAL_VALIDATED", "POC_VALIDATED", "CONFIRMED"}:
        raise ValueError("use hypothesis-status for gated proof/report transitions")

    def choose(name: str, default: Any = "") -> Any:
        value = getattr(args, name)
        if value is not None:
            return value
        return existing[name] if existing is not None else default

    title = choose("title")
    claim = choose("claim")
    if not title or not claim:
        raise ValueError("hypothesis title and claim are required")
    if status == "CODE_VALIDATED":
        required = {
            "attacker_capability": choose("attacker_capability"),
            "impact_goal_id": choose("impact_goal_id", None),
            "root_cause_key": choose("root_cause_key"),
            "next_check": choose("next_check"),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"CODE_VALIDATED missing fields: {', '.join(missing)}")
        impact = conn.execute(
            "SELECT id FROM impact_goals WHERE id = ? AND status IN ('READY', 'COVERED')",
            (required["impact_goal_id"],),
        ).fetchone()
        if impact is None:
            raise ValueError("CODE_VALIDATED hypothesis requires a READY or COVERED impact goal")
    now = utcnow()
    conn.execute(
        "INSERT INTO hypotheses(id, title, claim, claim_hash, status, confidence, severity_candidate, "
        "attacker_capability, impact_goal_id, root_cause_key, next_check, rejection_reason, reopen_condition, "
        "created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET title=excluded.title, claim=excluded.claim, "
        "claim_hash=excluded.claim_hash, status=excluded.status, confidence=excluded.confidence, "
        "severity_candidate=excluded.severity_candidate, attacker_capability=excluded.attacker_capability, "
        "impact_goal_id=excluded.impact_goal_id, root_cause_key=excluded.root_cause_key, "
        "next_check=excluded.next_check, rejection_reason=excluded.rejection_reason, "
        "reopen_condition=excluded.reopen_condition, updated_at=excluded.updated_at",
        (
            args.id,
            title,
            claim,
            claim_hash(claim),
            status,
            choose("confidence", 0.25),
            choose("severity_candidate", "UNKNOWN"),
            choose("attacker_capability"),
            choose("impact_goal_id", None),
            choose("root_cause_key"),
            choose("next_check"),
            choose("rejection_reason"),
            choose("reopen_condition"),
            now,
            now,
        ),
    )
    upsert_search(conn, "hypotheses", args.id)
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id, "status": status, "claim_hash": claim_hash(claim)})


def cmd_hypothesis_status(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    status = require_status(args.status, HYPOTHESIS_STATUSES, "hypothesis status")
    row = conn.execute("SELECT * FROM hypotheses WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        raise ValueError(f"hypothesis not found: {args.id}")
    if status == "MANUAL_VALIDATED":
        raise ValueError("MANUAL_VALIDATED is legacy compatibility; use automatic poc-handoff and POC_VALIDATED")
    if status == "REJECTED" and (not args.reason or not args.reopen_condition):
        raise ValueError("REJECTED requires --reason and --reopen-condition")
    if status == "POC_BLOCKED" and not args.reason:
        raise ValueError("POC_BLOCKED requires --reason")
    if status == "CODE_VALIDATED":
        required = {
            "attacker_capability": row["attacker_capability"],
            "impact_goal_id": row["impact_goal_id"],
            "root_cause_key": row["root_cause_key"],
            "next_check": row["next_check"],
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"CODE_VALIDATED missing fields: {', '.join(missing)}")
    if status == "POC_VALIDATED":
        current_poc = poc_gate(conn, repo, args.id)
        if not current_poc["ok"]:
            raise ValueError("cannot mark POC_VALIDATED: PoC handoff gate failed")
    if status == "CONFIRMED":
        current_report = report_gate(conn, repo, args.id)
        if not current_report["ok"]:
            raise ValueError("cannot confirm: report gate failed")
    conn.execute(
        "UPDATE hypotheses SET status=?, rejection_reason=?, reopen_condition=?, updated_at=? WHERE id=?",
        (
            status,
            args.reason or row["rejection_reason"],
            args.reopen_condition or row["reopen_condition"],
            utcnow(),
            args.id,
        ),
    )
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id, "from": row["status"], "to": status})


def cmd_hypothesis_link(args) -> None:
    conn = connect(repo_path(args))
    if conn.execute("SELECT id FROM hypotheses WHERE id = ?", (args.hypothesis_id,)).fetchone() is None:
        raise ValueError(f"hypothesis not found: {args.hypothesis_id}")
    conn.execute(
        "INSERT INTO hypothesis_links(hypothesis_id, record_type, record_id, role, created_at) "
        "VALUES(?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
        (args.hypothesis_id, args.record_type, args.record_id, args.role, utcnow()),
    )
    conn.commit()
    conn.close()
    emit({"ok": True, "hypothesis_id": args.hypothesis_id, "record_id": args.record_id})


def cmd_known_add(args) -> None:
    conn = connect(repo_path(args))
    if args.source_kind not in NOVELTY_SOURCES:
        raise ValueError(f"source-kind must be one of {', '.join(sorted(NOVELTY_SOURCES))}")
    now = utcnow()
    conn.execute(
        "INSERT INTO known_findings(id, source_kind, source, title, root_cause, affected_area, resolution, "
        "retrieval_handle, created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET source_kind=excluded.source_kind, source=excluded.source, "
        "title=excluded.title, root_cause=excluded.root_cause, affected_area=excluded.affected_area, "
        "resolution=excluded.resolution, retrieval_handle=excluded.retrieval_handle, updated_at=excluded.updated_at",
        (
            args.id,
            args.source_kind,
            args.source,
            args.title,
            args.root_cause,
            args.affected_area or "",
            args.resolution or "",
            args.retrieval_handle or "",
            now,
            now,
        ),
    )
    upsert_search(conn, "known_findings", args.id)
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id})


def cmd_novelty_add(args) -> None:
    conn = connect(repo_path(args))
    if args.source_kind not in NOVELTY_SOURCES:
        raise ValueError(f"source-kind must be one of {', '.join(sorted(NOVELTY_SOURCES))}")
    if conn.execute("SELECT id FROM hypotheses WHERE id = ?", (args.hypothesis_id,)).fetchone() is None:
        raise ValueError(f"hypothesis not found: {args.hypothesis_id}")
    overlap = args.overlap.upper()
    if overlap not in {"NEW", "DISTINCT", "KNOWN", "DUPLICATE", "UNCLEAR"}:
        raise ValueError("overlap must be NEW, DISTINCT, KNOWN, DUPLICATE, or UNCLEAR")
    cursor = conn.execute(
        "INSERT INTO novelty_checks(hypothesis_id, source_kind, query, result, overlap, retrieval_handle, checked_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)",
        (
            args.hypothesis_id,
            args.source_kind,
            args.query,
            args.result,
            overlap,
            args.retrieval_handle or "",
            utcnow(),
        ),
    )
    conn.commit()
    conn.close()
    emit({"ok": True, "novelty_check_id": cursor.lastrowid, "overlap": overlap})


def cmd_novelty_gate(args) -> None:
    conn = connect(repo_path(args))
    result = novelty_gate(conn, args.hypothesis_id)
    conn.close()
    emit(result)
    if not result["ok"]:
        raise SystemExit(3)


def cmd_live_add(args) -> None:
    conn = connect(repo_path(args))
    if args.block is None and not args.tx_hash:
        raise ValueError("live evidence requires --block or --tx-hash")
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    now = utcnow()
    conn.execute(
        "INSERT INTO live_evidence(id, source_tool, chain_id, block_number, tx_hash, address, code_hash, "
        "claim, status, retrieval_handle, observed_at, retest_trigger) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET source_tool=excluded.source_tool, chain_id=excluded.chain_id, "
        "block_number=excluded.block_number, tx_hash=excluded.tx_hash, address=excluded.address, "
        "code_hash=excluded.code_hash, claim=excluded.claim, status=excluded.status, "
        "retrieval_handle=excluded.retrieval_handle, observed_at=excluded.observed_at, "
        "retest_trigger=excluded.retest_trigger",
        (
            args.id,
            args.source_tool,
            args.chain_id,
            args.block,
            args.tx_hash,
            args.address,
            args.code_hash,
            args.claim,
            status,
            args.retrieval_handle,
            now,
            args.retest_trigger or "",
        ),
    )
    conn.commit()
    conn.close()
    emit({"ok": True, "id": args.id, "observed_at": now})


def cmd_rpc_resolve(args) -> None:
    repo = repo_path(args)
    rpc = resolve_rpc(repo, args.chain, args.chain_id)
    emit(
        {
            "ok": True,
            "chain": rpc["chain"],
            "chain_id": rpc["chain_id"],
            "provider": rpc["provider"],
            "rpc_url": rpc["rpc_url_redacted"],
            "public_fallbacks": rpc["public_fallbacks"],
            "alchemy_api_key": "configured" if os.environ.get("ALCHEMY_API_KEY") else "missing",
        }
    )


def cmd_cast_read(args) -> None:
    repo = repo_path(args)
    rpc = resolve_rpc(repo, args.chain, args.chain_id)
    cast = shutil.which("cast")
    if cast is None:
        raise ValueError("cast not available; install Foundry or use Tenderly/explorer evidence")
    command = [cast]
    if args.operation == "call":
        if not args.signature:
            raise ValueError("cast call requires --signature")
        command.extend(["call", args.address, args.signature, *(args.argument or [])])
    elif args.operation == "storage":
        if args.slot is None:
            raise ValueError("cast storage requires --slot")
        command.extend(["storage", args.address, args.slot])
    elif args.operation == "code":
        command.extend(["code", args.address])
    elif args.operation == "balance":
        command.extend(["balance", args.address])
    else:
        raise ValueError(f"unsupported cast operation: {args.operation}")
    command.extend(["--rpc-url", rpc["rpc_url"]])
    if args.block is not None:
        command.extend(["--block", str(args.block)])
    redacted_command = [redact_secret_text(part) for part in command]
    run = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
    output = redact_secret_text(run.stdout.strip())
    error = redact_secret_text(run.stderr.strip())
    emit(
        {
            "ok": run.returncode == 0,
            "operation": args.operation,
            "chain": rpc["chain"],
            "chain_id": rpc["chain_id"],
            "provider": rpc["provider"],
            "block": args.block,
            "address": args.address,
            "output": output,
            "stderr": error,
            "command": redacted_command,
            "retrieval_handle": (
                f"cast {args.operation} provider={rpc['provider']} chain_id={rpc['chain_id']} "
                f"block={args.block or 'latest'} address={args.address}"
            ),
        }
    )
    if run.returncode != 0:
        raise SystemExit(8)


def fts_query(raw: str) -> str:
    terms = re.findall(r"[A-Za-z0-9_:.\-/]+", raw)
    if not terms:
        raise ValueError("search query has no searchable terms")
    return " AND ".join(f'"{term.replace(chr(34), "")}"' for term in terms[:12])


def search_rows(conn, query: str, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT record_type, record_id, snippet(search_fts, 2, '[', ']', '...', 12) AS snippet, "
        "bm25(search_fts) AS rank FROM search_fts WHERE search_fts MATCH ? ORDER BY rank LIMIT ?",
        (fts_query(query), limit),
    ).fetchall()
    return as_dicts(rows)


def cmd_search(args) -> None:
    conn = connect(repo_path(args))
    rows = search_rows(conn, args.query, args.limit)
    conn.close()
    emit({"query": args.query, "count": len(rows), "rows": rows})


def adjacent_relations(conn, node_ids: set[str], types: set[str] | None, remaining: int) -> list[dict[str, Any]]:
    if not node_ids or remaining <= 0:
        return []
    placeholders = ",".join("?" for _ in node_ids)
    params: list[Any] = [*sorted(node_ids), *sorted(node_ids)]
    query = f"SELECT * FROM relations WHERE (src_id IN ({placeholders}) OR dst_id IN ({placeholders}))"
    if types:
        type_placeholders = ",".join("?" for _ in types)
        query += f" AND type IN ({type_placeholders})"
        params.extend(sorted(types))
    query += " ORDER BY id LIMIT ?"
    params.append(remaining)
    return as_dicts(conn.execute(query, params))


def graph_neighbors(conn, start: str, depth: int, limit: int, types: set[str] | None) -> dict[str, Any]:
    visited = {start}
    frontier = {start}
    edges: list[dict[str, Any]] = []
    for _ in range(depth):
        found = adjacent_relations(conn, frontier, types, limit - len(edges))
        if not found:
            break
        edges.extend(found)
        next_frontier = {edge[side] for edge in found for side in ("src_id", "dst_id")} - visited
        visited.update(next_frontier)
        frontier = next_frontier
        if len(edges) >= limit:
            break
    placeholders = ",".join("?" for _ in visited)
    nodes = []
    if placeholders:
        nodes = as_dicts(
            conn.execute(
                f"SELECT * FROM nodes WHERE id IN ({placeholders}) ORDER BY id", sorted(visited)
            )
        )
    return {"start": start, "depth": depth, "nodes": nodes, "relations": edges, "truncated": len(edges) >= limit}


def cmd_neighbors(args) -> None:
    if args.depth < 1 or args.depth > 3:
        raise ValueError("depth must be between 1 and 3")
    types = {value.strip().upper() for value in args.types.split(",") if value.strip()} if args.types else None
    conn = connect(repo_path(args))
    result = graph_neighbors(conn, args.id, args.depth, args.limit, types)
    conn.close()
    emit(result)


def cmd_path(args) -> None:
    if args.max_depth < 1 or args.max_depth > 3:
        raise ValueError("max-depth must be between 1 and 3")
    conn = connect(repo_path(args))
    queue = deque([(args.src, [])])
    seen = {args.src}
    found = None
    while queue:
        node, path = queue.popleft()
        if len(path) >= args.max_depth:
            continue
        edges = adjacent_relations(conn, {node}, None, args.limit)
        for edge in edges:
            other = edge["dst_id"] if edge["src_id"] == node else edge["src_id"]
            new_path = [*path, edge]
            if other == args.dst:
                found = new_path
                queue.clear()
                break
            if other not in seen:
                seen.add(other)
                queue.append((other, new_path))
    conn.close()
    emit({"src": args.src, "dst": args.dst, "found": found is not None, "path": found or []})


def cmd_context(args) -> None:
    conn = connect(repo_path(args))
    hits = search_rows(conn, args.goal, args.limit)
    node_ids = {hit["record_id"] for hit in hits if hit["record_type"] == "nodes"}
    relations = adjacent_relations(conn, node_ids, None, args.relation_limit)
    unresolved = as_dicts(
        conn.execute(
            "SELECT id, subject_id, kind, statement, status FROM facts "
            "WHERE status IN ('UNKNOWN', 'INFERRED') ORDER BY updated_at DESC LIMIT ?",
            (min(args.limit, 10),),
        )
    )
    evidence = []
    selected = [(hit["record_type"], hit["record_id"]) for hit in hits[:10]]
    for record_type, record_id in selected:
        evidence.extend(
            as_dicts(
                conn.execute(
                    "SELECT record_type, record_id, source_kind, file_path, line_start, line_end, note, "
                    "retrieval_handle FROM evidence WHERE record_type = ? AND record_id = ? "
                    "ORDER BY id DESC LIMIT 3",
                    (record_type, record_id),
                )
            )
        )
    conn.close()
    emit(
        {
            "goal": args.goal,
            "hits": hits,
            "relations": relations,
            "unresolved": unresolved,
            "evidence": evidence,
            "bounds": {
                "search_limit": args.limit,
                "relation_limit": args.relation_limit,
                "source_text_included": False,
            },
        }
    )


def stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha256(text.strip().encode()).hexdigest()[:16]
    return f"{prefix}:{digest}"


def job_parent(conn, job_id: str) -> str | None:
    rows = conn.execute(
        "SELECT dst_id FROM relations WHERE src_id=? AND type='VARIANT_OF' ORDER BY id LIMIT 2",
        (job_id,),
    ).fetchall()
    if len(rows) > 1:
        raise ValueError(f"job has multiple VARIANT_OF parents: {job_id}")
    return rows[0]["dst_id"] if rows else None


def job_lineage(conn, job_id: str) -> list[str]:
    lineage: list[str] = []
    seen = {job_id}
    current = job_id
    for _ in range(100):
        parent = job_parent(conn, current)
        if parent is None:
            return lineage
        if parent in seen:
            raise ValueError(f"cycle in Job variant family at {parent}")
        if conn.execute(
            "SELECT 1 FROM investigations WHERE id=? AND mode='JOB'", (parent,)
        ).fetchone() is None:
            raise ValueError(f"variant parent job not found: {parent}")
        lineage.append(parent)
        seen.add(parent)
        current = parent
    raise ValueError(f"Job variant family exceeds maximum depth: {job_id}")


def job_family_root(conn, job_id: str) -> str:
    lineage = job_lineage(conn, job_id)
    return lineage[-1] if lineage else job_id


def job_fact(conn, job_id: str, kind: str) -> str:
    row = conn.execute(
        "SELECT statement FROM facts WHERE subject_id=? AND kind=? "
        "ORDER BY updated_at DESC, id DESC LIMIT 1",
        (job_id, kind),
    ).fetchone()
    return row["statement"] if row else ""


def upsert_job_fact(conn, job_id: str, kind: str, statement: str, now: str) -> str:
    fact_id = stable_id(f"fact:{kind.lower()}", job_id)
    conn.execute(
        "INSERT INTO facts(id, subject_id, kind, statement, status, confidence, created_at, updated_at) "
        "VALUES(?, ?, ?, ?, 'INFERRED', 0.5, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "subject_id=excluded.subject_id, kind=excluded.kind, statement=excluded.statement, "
        "status=excluded.status, confidence=excluded.confidence, updated_at=excluded.updated_at",
        (fact_id, job_id, kind, statement, now, now),
    )
    upsert_search(conn, "facts", fact_id)
    return fact_id


def job_family_state(conn, root_id: str) -> tuple[str, str]:
    statement = job_fact(conn, root_id, "JOB_FAMILY_STATUS")
    if not statement:
        return "OPEN", "not marked saturated"
    state, separator, note = statement.partition(" | ")
    normalized = state.strip().upper()
    if normalized not in {"OPEN", "SATURATED"}:
        return "OPEN", statement
    return normalized, note.strip() if separator else ""


def job_view(conn, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    parent = job_parent(conn, item["id"])
    root = job_family_root(conn, item["id"])
    family_status, family_note = job_family_state(conn, root)
    item.update(
        {
            "variant_of": parent,
            "family_root": root,
            "family_status": family_status,
            "family_note": family_note,
            "variant_delta": job_fact(conn, item["id"], "JOB_VARIANT_DELTA"),
            "inherited_coverage": job_fact(conn, item["id"], "JOB_INHERITED_COVERAGE"),
            "variant_distinctness": job_fact(conn, item["id"], "JOB_VARIANT_DISTINCTNESS"),
            "next_check": job_fact(conn, item["id"], "JOB_NEXT_CHECK"),
        }
    )
    return item


def related_candidates(conn, text: str, limit: int = 10) -> list[dict[str, Any]]:
    def add_unique(rows: list[dict[str, Any]], row: dict[str, Any]) -> None:
        key = (row["record_type"], row["record_id"])
        if key not in {(item["record_type"], item["record_id"]) for item in rows}:
            rows.append(row)

    unique: list[dict[str, Any]] = []
    subject_tokens = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_:\-]{3,}", text)[:12]]
    if subject_tokens:
        clauses = " OR ".join(
            "(lower(r.src_id) LIKE ? OR lower(r.dst_id) LIKE ? OR lower(n.name) LIKE ? OR lower(n.summary) LIKE ?)"
            for _ in subject_tokens
        )
        params: list[Any] = []
        for token in subject_tokens:
            like = f"%{token}%"
            params.extend([like, like, like, like])
        rows = conn.execute(
            "SELECT DISTINCT r.src_id, r.dst_id, r.type FROM relations r "
            "LEFT JOIN nodes n ON n.id IN (r.src_id, r.dst_id) "
            f"WHERE {clauses} ORDER BY r.id LIMIT ?",
            (*params, limit * 4),
        ).fetchall()
        for row in rows:
            for endpoint in (row["src_id"], row["dst_id"]):
                if endpoint.startswith("JOB-"):
                    add_unique(
                        unique,
                        {
                            "record_type": "investigations",
                            "record_id": endpoint,
                            "snippet": f"explicit relation {row['type']} may be affected",
                        },
                    )
                elif endpoint.startswith("HYP-"):
                    add_unique(
                        unique,
                        {
                            "record_type": "hypotheses",
                            "record_id": endpoint,
                            "snippet": f"explicit relation {row['type']} may be affected",
                        },
                    )

    try:
        hits = search_rows(conn, text, limit)
    except ValueError:
        hits = []
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9_]{4,}", text)[:8]]
    if tokens:
        clauses = " OR ".join(
            "(lower(rejection_reason) LIKE ? OR lower(reopen_condition) LIKE ?)" for _ in tokens
        )
        params: list[Any] = []
        for token in tokens:
            like = f"%{token}%"
            params.extend([like, like])
        rows = conn.execute(
            "SELECT 'hypotheses' AS record_type, id AS record_id, "
            "'rejection/reopen text may be affected' AS snippet FROM hypotheses "
            f"WHERE status = 'REJECTED' AND ({clauses}) ORDER BY updated_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        hits.extend(as_dicts(rows))
        job_clauses = " OR ".join("(lower(goal) LIKE ? OR lower(result) LIKE ?)" for _ in tokens)
        job_params: list[Any] = []
        for token in tokens:
            like = f"%{token}%"
            job_params.extend([like, like])
        rows = conn.execute(
            "SELECT 'investigations' AS record_type, id AS record_id, "
            "'job goal/result may be affected' AS snippet FROM investigations "
            "WHERE mode='JOB' AND status IN ('ACTIVE','NEXT','PARKED','BLOCKED') "
            f"AND ({job_clauses}) ORDER BY started_at DESC LIMIT ?",
            (*job_params, limit),
        ).fetchall()
        hits.extend(as_dicts(rows))
    for hit in hits:
        add_unique(unique, hit)
    return unique[:limit]


def cmd_context_add(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    if args.status.upper() == "VERIFIED":
        raise ValueError("user context cannot be stored as VERIFIED; verify independently first")
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    fact_id = args.id or stable_id("fact:user-context", args.statement)
    now = utcnow()
    affected = related_candidates(conn, args.statement, args.limit)
    conn.execute(
        "INSERT INTO facts(id, subject_id, kind, statement, status, confidence, created_at, updated_at) "
        "VALUES(?, ?, 'USER_CONTEXT', ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "subject_id=excluded.subject_id, statement=excluded.statement, status=excluded.status, "
        "confidence=excluded.confidence, updated_at=excluded.updated_at",
        (fact_id, args.subject_id, args.statement, status, args.confidence, now, now),
    )
    conn.execute(
        "INSERT INTO evidence(record_type, record_id, source_kind, note, retrieval_handle, created_at) "
        "VALUES('facts', ?, 'user-context', ?, ?, ?)",
        (fact_id, args.note or args.statement, args.retrieval_handle, now),
    )
    upsert_search(conn, "facts", fact_id)
    conn.commit()
    conn.close()
    emit(
        {
            "ok": True,
            "id": fact_id,
            "status": status,
            "affected_candidates": affected,
            "next": "verify if this affects the active job, a hypothesis, a rejection, or a parked direction",
        }
    )


def cmd_job_upsert(args) -> None:
    conn = connect(repo_path(args))
    status = require_status(args.status, JOB_STATUSES, "job status")
    job_id = args.id or stable_id("job", args.goal)
    now = utcnow()
    existing = conn.execute("SELECT * FROM investigations WHERE id = ?", (job_id,)).fetchone()
    current_parent = job_parent(conn, job_id)
    if args.variant_of == job_id:
        raise ValueError("a Job cannot be a variant of itself")
    if args.variant_of and current_parent and args.variant_of != current_parent:
        raise ValueError(
            f"job already belongs to a different parent: {job_id} VARIANT_OF {current_parent}"
        )
    variant_parent = args.variant_of or current_parent
    if variant_parent:
        if conn.execute(
            "SELECT 1 FROM investigations WHERE id=? AND mode='JOB'", (variant_parent,)
        ).fetchone() is None:
            raise ValueError(f"variant parent job not found: {variant_parent}")
        if job_id in job_lineage(conn, variant_parent) or variant_parent == job_id:
            raise ValueError(f"VARIANT_OF would create a cycle: {job_id} -> {variant_parent}")
        root = job_family_root(conn, variant_parent)
        family_status, family_note = job_family_state(conn, root)
        creating_variant = bool(args.variant_of and not current_parent)
        if (
            family_status == "SATURATED"
            and not args.reopen_family_reason
            and (creating_variant or status in {"ACTIVE", "NEXT", "PARKED"})
        ):
            raise ValueError(
                f"Job family {root} is SATURATED: {family_note}; provide "
                "--reopen-family-reason with genuinely new evidence or rotate to another family"
            )
        if args.variant_of and not current_parent:
            if not all((args.variant_delta, args.inherits, args.distinctness, args.next_check)):
                raise ValueError(
                    "new Job variants require --variant-delta, --inherits, --distinctness, and "
                    "--next-check so reused coverage and the new falsifiable causal path are explicit"
                )
    elif args.variant_delta or args.inherits or args.distinctness:
        raise ValueError(
            "variant metadata requires --variant-of or an existing variant Job"
        )
    if existing and not variant_parent:
        root = job_family_root(conn, job_id)
        family_status, family_note = job_family_state(conn, root)
        if (
            family_status == "SATURATED"
            and status in {"ACTIVE", "NEXT", "PARKED"}
            and not args.reopen_family_reason
        ):
            raise ValueError(
                f"Job family {root} is SATURATED: {family_note}; provide "
                "--reopen-family-reason with genuinely new evidence or rotate to another family"
            )
    if args.reopen_family_reason and not (existing or variant_parent):
        raise ValueError("--reopen-family-reason requires an existing Job family")
    if args.saturate_family and status != "DONE":
        raise ValueError("--saturate-family requires the Job status DONE")
    started_at = existing["started_at"] if existing else now
    ended_at = now if status in {"DONE", "BLOCKED"} else None
    result = args.result if args.result is not None else (existing["result"] if existing else "")
    if status in {"DONE", "BLOCKED"} and not result.strip():
        raise ValueError(
            f"{status} job requires --result with coverage boundary, disposition, unresolved segments, "
            "and reopen condition"
        )
    if status == "ACTIVE":
        conn.execute(
            "UPDATE investigations SET status='NEXT', ended_at=NULL "
            "WHERE mode='JOB' AND status='ACTIVE' AND id<>?",
            (job_id,),
        )
    conn.execute(
        "INSERT INTO investigations(id, mode, goal, status, result, started_at, ended_at) "
        "VALUES(?, 'JOB', ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "goal=excluded.goal, status=excluded.status, result=excluded.result, ended_at=excluded.ended_at",
        (job_id, args.goal, status, result, started_at, ended_at),
    )
    upsert_search(conn, "investigations", job_id)
    if args.variant_of and not current_parent:
        conn.execute(
            "INSERT INTO relations(id, src_id, type, dst_id, summary, status, confidence, created_at, updated_at) "
            "VALUES(?, ?, 'VARIANT_OF', ?, ?, 'INFERRED', 0.5, ?, ?)",
            (
                relation_id(job_id, "VARIANT_OF", args.variant_of),
                job_id,
                args.variant_of,
                "reuses parent coverage but tests a materially different causal path",
                now,
                now,
            ),
        )
    if args.variant_delta:
        upsert_job_fact(conn, job_id, "JOB_VARIANT_DELTA", args.variant_delta, now)
    if args.inherits:
        upsert_job_fact(conn, job_id, "JOB_INHERITED_COVERAGE", args.inherits, now)
    if args.distinctness:
        upsert_job_fact(conn, job_id, "JOB_VARIANT_DISTINCTNESS", args.distinctness, now)
    if args.next_check:
        upsert_job_fact(conn, job_id, "JOB_NEXT_CHECK", args.next_check, now)
    root = job_family_root(conn, job_id)
    if args.reopen_family_reason:
        upsert_job_fact(conn, root, "JOB_FAMILY_STATUS", f"OPEN | {args.reopen_family_reason}", now)
    if args.saturate_family:
        upsert_job_fact(conn, root, "JOB_FAMILY_STATUS", f"SATURATED | {result}", now)
    view = job_view(conn, conn.execute("SELECT * FROM investigations WHERE id=?", (job_id,)).fetchone())
    conn.commit()
    conn.close()
    emit({"ok": True, **view})


def cmd_job_list(args) -> None:
    conn = connect(repo_path(args))
    limit = min(max(args.limit, 1), 100)
    clauses = ["mode='JOB'"]
    params: list[Any] = []
    if args.status:
        clauses.append("status=?")
        params.append(require_status(args.status, JOB_STATUSES, "job status"))
    if args.linked_record:
        clauses.append(
            "EXISTS (SELECT 1 FROM relations r WHERE "
            "(r.src_id=investigations.id AND r.dst_id=?) OR "
            "(r.dst_id=investigations.id AND r.src_id=?))"
        )
        params.extend([args.linked_record, args.linked_record])
    requested_root = None
    scan_limit = limit
    if args.family:
        if conn.execute(
            "SELECT 1 FROM investigations WHERE id=? AND mode='JOB'", (args.family,)
        ).fetchone() is None:
            raise ValueError(f"job not found: {args.family}")
        requested_root = job_family_root(conn, args.family)
        scan_limit = 500
    params.append(scan_limit)
    rows = as_dicts(
        conn.execute(
            "SELECT * FROM investigations WHERE "
            + " AND ".join(clauses)
            + " ORDER BY CASE status WHEN 'ACTIVE' THEN 0 WHEN 'NEXT' THEN 1 "
            "WHEN 'PARKED' THEN 2 WHEN 'BLOCKED' THEN 3 WHEN 'DONE' THEN 4 ELSE 5 END, "
            "started_at DESC LIMIT ?",
            params,
        )
    )
    rows = [job_view(conn, row) for row in rows]
    if requested_root:
        rows = [row for row in rows if row["family_root"] == requested_root][:limit]
    for row in rows:
        linked = conn.execute(
            "SELECT CASE WHEN src_id=? THEN dst_id ELSE src_id END AS record_id "
            "FROM relations WHERE src_id=? OR dst_id=? ORDER BY record_id",
            (row["id"], row["id"], row["id"]),
        ).fetchall()
        row["linked_records"] = [item["record_id"] for item in linked]
    conn.close()
    emit(
        {
            "count": len(rows),
            "rows": rows,
            "bounds": {"limit": limit, "family_scan_limit": scan_limit if requested_root else None},
        }
    )


def cmd_observation_add(args) -> None:
    conn = connect(repo_path(args))
    fact_id = args.id or stable_id("fact:observation", f"{args.job_id}\0{args.statement}")
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    now = utcnow()
    conn.execute(
        "INSERT INTO facts(id, subject_id, kind, statement, status, confidence, created_at, updated_at) "
        "VALUES(?, ?, 'OBSERVATION', ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "subject_id=excluded.subject_id, statement=excluded.statement, status=excluded.status, "
        "confidence=excluded.confidence, updated_at=excluded.updated_at",
        (fact_id, args.job_id, args.statement, status, args.confidence, now, now),
    )
    if args.note:
        conn.execute(
            "INSERT INTO evidence(record_type, record_id, source_kind, note, retrieval_handle, created_at) "
            "VALUES('facts', ?, 'observation', ?, ?, ?)",
            (fact_id, args.note, args.retrieval_handle, now),
        )
    upsert_search(conn, "facts", fact_id)
    conn.commit()
    conn.close()
    emit({"ok": True, "id": fact_id, "job_id": args.job_id, "status": status})


def cmd_probe_add(args) -> None:
    conn = connect(repo_path(args))
    status = require_status(args.status, EVIDENCE_STATUSES, "evidence status")
    if args.executed and status == "UNKNOWN":
        status = "VERIFIED"
    if status == "VERIFIED" and not args.executed:
        raise ValueError("VERIFIED state probes require --executed and execution provenance")
    if status == "VERIFIED" and not args.harness:
        raise ValueError("VERIFIED state probes require --harness or execution handle")
    body = (
        f"setup: {args.setup}\nsequence: {args.sequence}\n"
        f"before: {args.state_before or ''}\nafter: {args.state_after or ''}\nresult: {args.result}"
    )
    fact_id = args.id or stable_id("fact:state-probe", f"{args.job_id}\0{body}")
    now = utcnow()
    conn.execute(
        "INSERT INTO facts(id, subject_id, kind, statement, status, confidence, created_at, updated_at) "
        "VALUES(?, ?, 'STATE_PROBE', ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "subject_id=excluded.subject_id, statement=excluded.statement, status=excluded.status, "
        "confidence=excluded.confidence, updated_at=excluded.updated_at",
        (fact_id, args.job_id, body, status, args.confidence, now, now),
    )
    conn.execute(
        "INSERT INTO evidence(record_type, record_id, source_kind, note, retrieval_handle, created_at) "
        "VALUES('facts', ?, 'state-probe', ?, ?, ?)",
        (fact_id, args.result, args.harness, now),
    )
    upsert_search(conn, "facts", fact_id)
    conn.commit()
    conn.close()
    result = {"ok": True, "id": fact_id, "job_id": args.job_id, "status": status}
    if args.observation:
        observation_id = stable_id("fact:observation", f"{args.job_id}\0{args.observation}")
        conn = connect(repo_path(args))
        conn.execute(
            "INSERT INTO facts(id, subject_id, kind, statement, status, confidence, created_at, updated_at) "
            "VALUES(?, ?, 'OBSERVATION', ?, 'INFERRED', 0.5, ?, ?) ON CONFLICT(id) DO UPDATE SET "
            "subject_id=excluded.subject_id, statement=excluded.statement, updated_at=excluded.updated_at",
            (observation_id, args.job_id, args.observation, now, now),
        )
        upsert_search(conn, "facts", observation_id)
        conn.commit()
        conn.close()
        result["observation_id"] = observation_id
    emit(result)


def cmd_research_packet(args) -> None:
    conn = connect(repo_path(args))
    job = conn.execute("SELECT * FROM investigations WHERE id=? AND mode='JOB'", (args.job_id,)).fetchone()
    if job is None:
        raise ValueError(f"job not found: {args.job_id}")
    job_item = job_view(conn, job)
    lineage = job_lineage(conn, args.job_id)
    linked_relations = as_dicts(
        conn.execute(
            "SELECT * FROM relations WHERE src_id=? OR dst_id=? ORDER BY id LIMIT ?",
            (args.job_id, args.job_id, args.limit),
        )
    )
    inherited_relations: list[dict[str, Any]] = []
    inherited_relation_ids: set[str] = set()
    for ancestor_id in lineage:
        remaining = args.limit - len(inherited_relations)
        if remaining <= 0:
            break
        rows = as_dicts(
            conn.execute(
                "SELECT * FROM relations WHERE (src_id=? OR dst_id=?) AND type<>'VARIANT_OF' "
                "ORDER BY id LIMIT ?",
                (ancestor_id, ancestor_id, remaining),
            )
        )
        for row in rows:
            if row["id"] in inherited_relation_ids:
                continue
            row["inherited_from_job"] = ancestor_id
            inherited_relations.append(row)
            inherited_relation_ids.add(row["id"])
    packet_relations = linked_relations + inherited_relations
    family_job_ids = {args.job_id, *lineage}
    linked_ids = {
        edge[side]
        for edge in packet_relations
        for side in ("src_id", "dst_id")
        if edge[side] not in family_job_ids
    }
    linked: dict[str, list[dict[str, Any]]] = {
        "jobs": [],
        "nodes": [],
        "impact_goals": [],
        "invariants": [],
        "facts": [],
        "hypotheses": [],
        "known_findings": [],
        "live_evidence": [],
    }
    deferred_ids: set[str] = set()
    if job_item["variant_of"]:
        parent = conn.execute(
            "SELECT * FROM investigations WHERE id=? AND mode='JOB'", (job_item["variant_of"],)
        ).fetchone()
        if parent:
            linked["jobs"].append(job_view(conn, parent))
    for record_id in sorted(linked_ids):
        if record_id.startswith("JOB-"):
            row = conn.execute(
                "SELECT * FROM investigations WHERE id=? AND mode='JOB'", (record_id,)
            ).fetchone()
            if row:
                linked["jobs"].append(job_view(conn, row))
        elif record_id.startswith("impact:"):
            row = conn.execute("SELECT * FROM impact_goals WHERE id=?", (record_id,)).fetchone()
            if row:
                item = dict(row)
                item["candidate_primitives"] = json.loads(item.pop("candidate_primitives_json"))
                linked["impact_goals"].append(item)
                if item["invariant_id"]:
                    deferred_ids.add(item["invariant_id"])
        elif record_id.startswith("invariant:"):
            row = conn.execute("SELECT * FROM invariants WHERE id=?", (record_id,)).fetchone()
            if row:
                linked["invariants"].append(dict(row))
        elif record_id.startswith("fact:"):
            row = conn.execute("SELECT * FROM facts WHERE id=?", (record_id,)).fetchone()
            if row:
                linked["facts"].append(dict(row))
        elif record_id.startswith("HYP-"):
            row = conn.execute(
                "SELECT id, title, status, claim, next_check, rejection_reason, reopen_condition "
                "FROM hypotheses WHERE id=?",
                (record_id,),
            ).fetchone()
            if row:
                linked["hypotheses"].append(dict(row))
        elif record_id.startswith("KNOWN-"):
            row = conn.execute("SELECT * FROM known_findings WHERE id=?", (record_id,)).fetchone()
            if row:
                linked["known_findings"].append(dict(row))
        elif record_id.startswith("LIVE-"):
            row = conn.execute("SELECT * FROM live_evidence WHERE id=?", (record_id,)).fetchone()
            if row:
                linked["live_evidence"].append(dict(row))
        else:
            row = conn.execute("SELECT * FROM nodes WHERE id=?", (record_id,)).fetchone()
            if row:
                linked["nodes"].append(dict(row))
    for record_id in sorted(deferred_ids - linked_ids):
        if record_id.startswith("invariant:"):
            row = conn.execute("SELECT * FROM invariants WHERE id=?", (record_id,)).fetchone()
            if row:
                linked["invariants"].append(dict(row))
    graph_relations = [row for row in linked_relations if row["type"] != "VARIANT_OF"] + inherited_relations
    if graph_relations:
        context_hits = []
    else:
        try:
            context_hits = search_rows(conn, job["goal"], args.limit)
        except ValueError:
            context_hits = []
    job_facts = as_dicts(
        conn.execute(
            "SELECT id, kind, statement, status, confidence, updated_at FROM facts "
            "WHERE subject_id=? ORDER BY updated_at DESC LIMIT ?",
            (args.job_id, args.limit),
        )
    )
    hypotheses = as_dicts(
        conn.execute(
            "SELECT id, title, status, claim, next_check, rejection_reason, reopen_condition "
            "FROM hypotheses WHERE claim LIKE ? OR next_check LIKE ? OR root_cause_key LIKE ? "
            "ORDER BY updated_at DESC LIMIT ?",
            (f"%{job['goal'][:80]}%", f"%{job['goal'][:80]}%", f"%{job['goal'][:80]}%", args.limit),
        )
    )
    conn.close()
    emit(
        {
            "job": job_item,
            "linked_relations": linked_relations,
            "inherited_relations": inherited_relations,
            "linked": linked,
            "context_hits": context_hits,
            "job_facts": job_facts,
            "related_hypotheses": hypotheses,
            "bounds": {
                "limit": args.limit,
                "source_text_included": False,
                "retrieval": "explicit-relations-first-with-family-inheritance",
                "fts_fallback_used": not graph_relations,
            },
        }
    )


def stale_evidence(conn, repo: Path) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, record_type, record_id, file_path, file_sha256 FROM evidence "
        "WHERE file_path IS NOT NULL AND file_sha256 IS NOT NULL ORDER BY id"
    ).fetchall()
    stale = []
    for row in rows:
        path = repo / row["file_path"]
        if not path.exists():
            current = "MISSING"
        else:
            current = hashlib.sha256(path.read_bytes()).hexdigest()
        if current != row["file_sha256"]:
            item = dict(row)
            item["current_sha256"] = current
            stale.append(item)
    return stale


def cmd_stale(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    scope = current_scope(conn, repo)
    evidence = stale_evidence(conn, repo)
    conn.close()
    result = {"ok": scope["ok"] and not evidence, "scope": scope, "stale_evidence": evidence}
    emit(result)
    if not result["ok"]:
        raise SystemExit(4)


def cmd_lint(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    issues = []
    node_ids = {row["id"] for row in conn.execute("SELECT id FROM nodes")}
    for row in conn.execute("SELECT id, src_id, dst_id, status FROM relations ORDER BY id"):
        missing = [endpoint for endpoint in (row["src_id"], row["dst_id"]) if endpoint not in node_ids]
        if missing:
            issues.append({"type": "dangling_relation", "id": row["id"], "missing": missing})
        if row["status"] == "VERIFIED":
            count = conn.execute(
                "SELECT count(*) FROM evidence WHERE record_type='relations' AND record_id=?",
                (row["id"],),
            ).fetchone()[0]
            if count == 0:
                issues.append({"type": "verified_without_evidence", "record_type": "relations", "id": row["id"]})
    required_impact = (
        "archetype",
        "title",
        "invariant_id",
        "protocol_case",
        "decision_point",
        "bad_state",
        "attacker_goal",
    )
    for row in conn.execute("SELECT * FROM impact_goals WHERE status='READY' ORDER BY id"):
        missing = [column for column in required_impact if not row[column]]
        if not json.loads(row["candidate_primitives_json"]):
            missing.append("candidate_primitives")
        if missing:
            issues.append({"type": "ready_impact_incomplete", "id": row["id"], "missing": missing})
    for row in conn.execute("SELECT * FROM hypotheses WHERE status='CODE_VALIDATED' ORDER BY id"):
        required = ("attacker_capability", "impact_goal_id", "root_cause_key", "next_check")
        missing = [column for column in required if not row[column]]
        if missing:
            issues.append({"type": "validated_hypothesis_incomplete", "id": row["id"], "missing": missing})
    fts_count = conn.execute("SELECT count(*) FROM search_fts").fetchone()[0]
    source_count = sum(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in SEARCHABLE_TABLES)
    if fts_count != source_count:
        issues.append({"type": "search_index_mismatch", "search_rows": fts_count, "source_rows": source_count})
    scope = current_scope(conn, repo)
    if not scope["ok"]:
        issues.append({"type": "stale_scope", "changes": scope["changes"]})
    conn.close()
    emit({"ok": not issues, "issue_count": len(issues), "issues": issues})
    if issues:
        raise SystemExit(5)


def cmd_refresh_search(args) -> None:
    conn = connect(repo_path(args))
    count = refresh_search(conn)
    conn.commit()
    conn.close()
    emit({"ok": True, "indexed": count})


def cmd_db_info(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    tables = [
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    counts = {table: conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables if not table.startswith("search_fts_")}
    version = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    scope = current_scope(conn, repo)
    journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    emit(
        {
            "ok": True,
            "database": str(db_path(repo)),
            "schema_version": version[0] if version else None,
            "journal_mode": journal,
            "scope": scope,
            "counts": counts,
        }
    )


CHECKPOINT_TABLES = [
    "meta",
    "snapshots",
    "files",
    "nodes",
    "relations",
    "evidence",
    "invariants",
    "impact_goals",
    "facts",
    "hypotheses",
    "hypothesis_links",
    "investigations",
    "known_findings",
    "novelty_checks",
    "live_evidence",
    "manual_approvals",
]


def cmd_checkpoint(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    output_dir = repo / ".audit" / "graph" / "checkpoints"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utcnow().replace(":", "").replace("+00:00", "Z")
    output = Path(args.output).expanduser().resolve() if args.output else output_dir / f"checkpoint-{timestamp}.jsonl"
    counts = {}
    with output.open("w", encoding="utf-8") as handle:
        for table in CHECKPOINT_TABLES:
            columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
            order = ", ".join(columns) if columns else "rowid"
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
            counts[table] = len(rows)
            for row in rows:
                handle.write(canonical_json({"table": table, "record": dict(row)}) + "\n")
    conn.close()
    emit({"ok": True, "output": str(output), "counts": counts})


def cmd_approve_poc(args) -> None:
    if not sys.stdin.isatty():
        raise ValueError("approve-poc requires an interactive terminal and direct human confirmation")
    phrase = f"APPROVE {args.hypothesis_id}"
    print("This records that the named human manually validated the current allegation.")
    print("It unlocks PoC file creation only for the current claim and source snapshot.")
    entered = input(f"Type exactly '{phrase}' to continue: ").strip()
    if entered != phrase:
        raise ValueError("approval phrase did not match; no approval recorded")
    repo = repo_path(args)
    conn = connect(repo)
    result = record_poc_approval(conn, repo, args.hypothesis_id, args.approved_by, args.note)
    conn.close()
    result["ok"] = True
    emit(result)


def cmd_poc_gate(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    result = poc_gate(conn, repo, args.hypothesis_id)
    conn.close()
    emit(result)
    if not result["ok"]:
        raise SystemExit(6)


def cmd_poc_config(args) -> None:
    repo = repo_path(args)
    path = Path(args.path).expanduser().resolve()
    if not (path / "SKILL.md").exists():
        raise ValueError(f"PoC skill path must contain SKILL.md: {path}")
    conn = connect(repo)
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('poc_skill_path', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(path),),
    )
    conn.commit()
    conn.close()
    emit({"ok": True, "poc_skill_path": str(path)})


def cmd_poc_handoff(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    gate = poc_gate(conn, repo, args.hypothesis_id)
    hypothesis = conn.execute(
        "SELECT id, title, claim, attacker_capability, impact_goal_id, root_cause_key, next_check "
        "FROM hypotheses WHERE id=?",
        (args.hypothesis_id,),
    ).fetchone()
    conn.close()
    if hypothesis is None:
        raise ValueError(f"hypothesis not found: {args.hypothesis_id}")
    result = {
        "ok": gate["ok"],
        "gate": gate,
        "handoff": {
            "poc_skill_path": gate.get("poc_skill_path", ""),
            "hypothesis": dict(hypothesis),
            "instruction": "read the configured PoC skill SKILL.md and attempt the strongest practical proof",
        },
    }
    emit(result)
    if not gate["ok"]:
        raise SystemExit(6)


def cmd_report_gate(args) -> None:
    repo = repo_path(args)
    conn = connect(repo)
    result = report_gate(conn, repo, args.hypothesis_id)
    conn.close()
    emit(result)
    if not result["ok"]:
        raise SystemExit(7)


def add_repo(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=".", help="target repository (default: current directory)")


def add_status_confidence(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--status", default="UNKNOWN")
    parser.add_argument("--confidence", type=float, default=0.5)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compact SQLite audit graph and human-steered hunt workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="check Python, SQLite, FTS, and Tenderly visibility")
    add_repo(doctor)
    doctor.set_defaults(func=cmd_doctor)

    init = sub.add_parser("init", help="initialize repository-local audit store")
    add_repo(init)
    init.set_defaults(func=cmd_init)

    snapshot = sub.add_parser("snapshot", help="capture exact source scope hashes")
    add_repo(snapshot)
    snapshot.add_argument("--scope", action="append", help="in-scope file or directory; repeatable")
    snapshot.add_argument("--scope-file", help="newline-delimited scope manifest")
    snapshot.set_defaults(func=cmd_snapshot)

    invariant = sub.add_parser("invariant-upsert", help="create or update an invariant")
    add_repo(invariant)
    invariant.add_argument("--id", required=True)
    invariant.add_argument("--title", required=True)
    invariant.add_argument("--statement", required=True)
    invariant.add_argument("--scope")
    invariant.add_argument("--protocol-case")
    invariant.add_argument("--status", default="INFERRED")
    invariant.set_defaults(func=cmd_invariant_upsert)

    impact = sub.add_parser("impact-upsert", help="create or refine a protocol-specific impact")
    add_repo(impact)
    impact.add_argument("--id", required=True)
    impact.add_argument("--archetype", help="optional retrieval family; defaults to protocol")
    impact.add_argument("--title")
    impact.add_argument("--invariant-id")
    impact.add_argument("--protocol-case")
    impact.add_argument("--decision-point")
    impact.add_argument("--bad-state")
    impact.add_argument("--attacker-goal")
    impact.add_argument("--candidate-primitive", action="append")
    impact.add_argument("--status")
    impact.set_defaults(func=cmd_impact_upsert)

    impacts = sub.add_parser("impact-list", help="list bounded impact rows")
    add_repo(impacts)
    impacts.add_argument("--status")
    impacts.add_argument("--archetype")
    impacts.add_argument("--limit", type=int, default=20)
    impacts.set_defaults(func=cmd_impact_list)

    node = sub.add_parser("node-upsert", help="create or update a graph node")
    add_repo(node)
    node.add_argument("--id", required=True)
    node.add_argument("--kind", required=True)
    node.add_argument("--name", required=True)
    node.add_argument("--summary")
    node.add_argument("--file-path")
    node.add_argument("--line-start", type=int)
    node.add_argument("--line-end", type=int)
    add_status_confidence(node)
    node.set_defaults(func=cmd_node_upsert)

    relation = sub.add_parser("relation-upsert", help="create or update a directed graph edge")
    add_repo(relation)
    relation.add_argument("--id")
    relation.add_argument("--src", required=True)
    relation.add_argument("--type", required=True)
    relation.add_argument("--dst", required=True)
    relation.add_argument("--summary")
    add_status_confidence(relation)
    relation.set_defaults(func=cmd_relation_upsert)

    fact = sub.add_parser("fact-upsert", help="create or update a fact or assumption")
    add_repo(fact)
    fact.add_argument("--id", required=True)
    fact.add_argument("--subject-id")
    fact.add_argument("--kind", required=True)
    fact.add_argument("--statement", required=True)
    add_status_confidence(fact)
    fact.set_defaults(func=cmd_fact_upsert)

    evidence = sub.add_parser("evidence-add", help="attach source-backed evidence to a record")
    add_repo(evidence)
    evidence.add_argument("--record-type", required=True)
    evidence.add_argument("--record-id", required=True)
    evidence.add_argument("--source-kind", required=True)
    evidence.add_argument("--file-path")
    evidence.add_argument("--line-start", type=int)
    evidence.add_argument("--line-end", type=int)
    evidence.add_argument("--note", required=True)
    evidence.add_argument("--retrieval-handle")
    evidence.set_defaults(func=cmd_evidence_add)

    context_add = sub.add_parser("context-add", help="store unverified user context and report affected records")
    add_repo(context_add)
    context_add.add_argument("--id")
    context_add.add_argument("--subject-id")
    context_add.add_argument("--statement", required=True)
    context_add.add_argument("--status", default="UNKNOWN")
    context_add.add_argument("--confidence", type=float, default=0.5)
    context_add.add_argument("--note")
    context_add.add_argument("--retrieval-handle")
    context_add.add_argument("--limit", type=int, default=10)
    context_add.set_defaults(func=cmd_context_add)

    job = sub.add_parser("job-upsert", help="create or update one meaningful research job")
    add_repo(job)
    job.add_argument("--id")
    job.add_argument("--goal", required=True)
    job.add_argument("--status", default="NEXT")
    job.add_argument("--result")
    job.add_argument("--variant-of", help="parent Job whose proven coverage this variant reuses")
    job.add_argument("--variant-delta", help="materially different causal path tested by this variant")
    job.add_argument("--inherits", help="specific parent graph, evidence, and killed paths not repeated")
    job.add_argument("--distinctness", help="why the variant can produce a result its parent could not")
    job.add_argument("--next-check", help="cheapest falsification check for this Job or variant")
    job.add_argument(
        "--saturate-family",
        action="store_true",
        help="mark this DONE Job family exhausted for the currently known evidence",
    )
    job.add_argument(
        "--reopen-family-reason",
        help="new code, graph, deployment, integration, or evidence that invalidates saturation",
    )
    job.set_defaults(func=cmd_job_upsert)

    jobs = sub.add_parser("job-list", help="list bounded current and prior research jobs")
    add_repo(jobs)
    jobs.add_argument("--status")
    jobs.add_argument("--linked-record", help="only jobs linked to this impact, invariant, or graph record")
    jobs.add_argument("--family", help="only Jobs in the same variant family as this Job ID")
    jobs.add_argument("--limit", type=int, default=30)
    jobs.set_defaults(func=cmd_job_list)

    observation = sub.add_parser("observation-add", help="record a job-scoped observation")
    add_repo(observation)
    observation.add_argument("--id")
    observation.add_argument("--job-id", required=True)
    observation.add_argument("--statement", required=True)
    observation.add_argument("--status", default="INFERRED")
    observation.add_argument("--confidence", type=float, default=0.5)
    observation.add_argument("--note")
    observation.add_argument("--retrieval-handle")
    observation.set_defaults(func=cmd_observation_add)

    probe = sub.add_parser("probe-add", help="record a focused exploratory state probe")
    add_repo(probe)
    probe.add_argument("--id")
    probe.add_argument("--job-id", required=True)
    probe.add_argument("--setup", required=True)
    probe.add_argument("--sequence", required=True)
    probe.add_argument("--state-before")
    probe.add_argument("--state-after")
    probe.add_argument("--result", required=True)
    probe.add_argument("--harness")
    probe.add_argument("--status", default="INFERRED")
    probe.add_argument("--confidence", type=float, default=0.5)
    probe.add_argument("--executed", action="store_true")
    probe.add_argument("--observation")
    probe.set_defaults(func=cmd_probe_add)

    hypothesis = sub.add_parser("hypothesis-upsert", help="create or update a hypothesis")
    add_repo(hypothesis)
    hypothesis.add_argument("--id", required=True)
    hypothesis.add_argument("--title")
    hypothesis.add_argument("--claim")
    hypothesis.add_argument("--status")
    hypothesis.add_argument("--confidence", type=float)
    hypothesis.add_argument("--severity-candidate")
    hypothesis.add_argument("--attacker-capability")
    hypothesis.add_argument("--impact-goal-id")
    hypothesis.add_argument("--root-cause-key")
    hypothesis.add_argument("--next-check")
    hypothesis.add_argument("--rejection-reason")
    hypothesis.add_argument("--reopen-condition")
    hypothesis.set_defaults(func=cmd_hypothesis_upsert)

    hyp_status = sub.add_parser("hypothesis-status", help="transition a hypothesis with gates")
    add_repo(hyp_status)
    hyp_status.add_argument("hypothesis_id", metavar="ID")
    hyp_status.add_argument("--status", required=True)
    hyp_status.add_argument("--reason")
    hyp_status.add_argument("--reopen-condition")
    hyp_status.set_defaults(func=lambda args: cmd_hypothesis_status(_alias_id(args)))

    link = sub.add_parser("hypothesis-link", help="link hypothesis to graph/evidence records")
    add_repo(link)
    link.add_argument("hypothesis_id")
    link.add_argument("--record-type", required=True)
    link.add_argument("--record-id", required=True)
    link.add_argument("--role", required=True)
    link.set_defaults(func=cmd_hypothesis_link)

    known = sub.add_parser("known-add", help="index a known finding or audit issue")
    add_repo(known)
    known.add_argument("--id", required=True)
    known.add_argument("--source-kind", required=True)
    known.add_argument("--source", required=True)
    known.add_argument("--title", required=True)
    known.add_argument("--root-cause", required=True)
    known.add_argument("--affected-area")
    known.add_argument("--resolution")
    known.add_argument("--retrieval-handle")
    known.set_defaults(func=cmd_known_add)

    novelty = sub.add_parser("novelty-add", help="record one historical novelty check")
    add_repo(novelty)
    novelty.add_argument("hypothesis_id")
    novelty.add_argument("--source-kind", required=True)
    novelty.add_argument("--query", required=True)
    novelty.add_argument("--result", required=True)
    novelty.add_argument("--overlap", required=True)
    novelty.add_argument("--retrieval-handle")
    novelty.set_defaults(func=cmd_novelty_add)

    ngate = sub.add_parser("novelty-gate", help="require all novelty sources and no duplicate")
    add_repo(ngate)
    ngate.add_argument("hypothesis_id")
    ngate.set_defaults(func=cmd_novelty_gate)

    live = sub.add_parser("live-add", help="record pinned on-chain evidence")
    add_repo(live)
    live.add_argument("--id", required=True)
    live.add_argument("--source-tool", required=True)
    live.add_argument("--chain-id", type=int, required=True)
    live.add_argument("--block", type=int)
    live.add_argument("--tx-hash")
    live.add_argument("--address")
    live.add_argument("--code-hash")
    live.add_argument("--claim", required=True)
    live.add_argument("--status", default="UNKNOWN")
    live.add_argument("--retrieval-handle", required=True)
    live.add_argument("--retest-trigger")
    live.set_defaults(func=cmd_live_add)

    rpc = sub.add_parser("rpc-resolve", help="resolve chain to Alchemy or public RPC without printing secrets")
    add_repo(rpc)
    rpc.add_argument("--chain")
    rpc.add_argument("--chain-id", type=int)
    rpc.set_defaults(func=cmd_rpc_resolve)

    cast_read = sub.add_parser("cast-read", help="run a narrow cast live-state read with redacted provenance")
    add_repo(cast_read)
    cast_read.add_argument("--operation", choices=("call", "storage", "code", "balance"), required=True)
    cast_read.add_argument("--chain")
    cast_read.add_argument("--chain-id", type=int)
    cast_read.add_argument("--address", required=True)
    cast_read.add_argument("--signature")
    cast_read.add_argument("--argument", action="append")
    cast_read.add_argument("--slot")
    cast_read.add_argument("--block", type=int)
    cast_read.add_argument("--timeout", type=int, default=30)
    cast_read.set_defaults(func=cmd_cast_read)

    search = sub.add_parser("search", help="bounded FTS search")
    add_repo(search)
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(func=cmd_search)

    neighbors = sub.add_parser("neighbors", help="bounded graph neighborhood")
    add_repo(neighbors)
    neighbors.add_argument("id")
    neighbors.add_argument("--types")
    neighbors.add_argument("--depth", type=int, default=1)
    neighbors.add_argument("--limit", type=int, default=30)
    neighbors.set_defaults(func=cmd_neighbors)

    path = sub.add_parser("path", help="bounded relationship path")
    add_repo(path)
    path.add_argument("src")
    path.add_argument("dst")
    path.add_argument("--max-depth", type=int, default=3)
    path.add_argument("--limit", type=int, default=50)
    path.set_defaults(func=cmd_path)

    context = sub.add_parser("context", help="compact evidence bundle for a goal")
    add_repo(context)
    context.add_argument("--goal", required=True)
    context.add_argument("--limit", type=int, default=20)
    context.add_argument("--relation-limit", type=int, default=30)
    context.set_defaults(func=cmd_context)

    packet = sub.add_parser("research-packet", help="bounded packet for one active research job")
    add_repo(packet)
    packet.add_argument("job_id")
    packet.add_argument("--limit", type=int, default=20)
    packet.set_defaults(func=cmd_research_packet)

    stale = sub.add_parser("stale", help="check source scope and evidence freshness")
    add_repo(stale)
    stale.set_defaults(func=cmd_stale)

    lint = sub.add_parser("lint", help="check graph integrity and promotion fields")
    add_repo(lint)
    lint.set_defaults(func=cmd_lint)

    refresh = sub.add_parser("refresh-search", help="rebuild deterministic FTS rows")
    add_repo(refresh)
    refresh.set_defaults(func=cmd_refresh_search)

    info = sub.add_parser("db-info", help="show compact schema and table counts")
    add_repo(info)
    info.set_defaults(func=cmd_db_info)

    checkpoint = sub.add_parser("checkpoint", help="export deterministic JSONL checkpoint")
    add_repo(checkpoint)
    checkpoint.add_argument("--output")
    checkpoint.set_defaults(func=cmd_checkpoint)

    approve = sub.add_parser("approve-poc", help="legacy interactive PoC approval compatibility")
    add_repo(approve)
    approve.add_argument("hypothesis_id")
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--note", required=True)
    approve.set_defaults(func=cmd_approve_poc)

    poc_config = sub.add_parser("poc-config", help="configure the dedicated PoC skill path")
    add_repo(poc_config)
    poc_config.add_argument("--path", required=True)
    poc_config.set_defaults(func=cmd_poc_config)

    pgate = sub.add_parser("poc-gate", help="verify automatic PoC handoff readiness")
    add_repo(pgate)
    pgate.add_argument("hypothesis_id")
    pgate.set_defaults(func=cmd_poc_gate)

    handoff = sub.add_parser("poc-handoff", help="return the configured PoC skill handoff packet")
    add_repo(handoff)
    handoff.add_argument("hypothesis_id")
    handoff.set_defaults(func=cmd_poc_handoff)

    rgate = sub.add_parser("report-gate", help="verify proof validation and novelty")
    add_repo(rgate)
    rgate.add_argument("hypothesis_id")
    rgate.set_defaults(func=cmd_report_gate)

    return parser


def _alias_id(args):
    args.id = args.hypothesis_id
    return args


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except SystemExit:
        raise
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        emit({"ok": False, "error": str(exc), "command": args.command})
        return 2
    return 0
