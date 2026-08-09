from __future__ import annotations

from typing import Any

from .db import utcnow
from .scope import current_scope, latest_snapshot


NOVELTY_SOURCES = {"repo-known", "similar-audit", "solodit", "hack-registry"}
PASSING_OVERLAPS = {"NEW", "DISTINCT"}


def novelty_gate(conn, hypothesis_id: str) -> dict[str, Any]:
    hypothesis = conn.execute("SELECT id FROM hypotheses WHERE id = ?", (hypothesis_id,)).fetchone()
    if hypothesis is None:
        return {"ok": False, "reason": "hypothesis not found", "hypothesis_id": hypothesis_id}
    rows = conn.execute(
        "SELECT source_kind, overlap, result, checked_at FROM novelty_checks "
        "WHERE hypothesis_id = ? ORDER BY id",
        (hypothesis_id,),
    ).fetchall()
    latest = {}
    for row in rows:
        latest[row["source_kind"]] = dict(row)
    missing = sorted(NOVELTY_SOURCES - set(latest))
    blocked = {
        source: row["overlap"]
        for source, row in latest.items()
        if source in NOVELTY_SOURCES and row["overlap"] not in PASSING_OVERLAPS
    }
    return {
        "ok": not missing and not blocked,
        "hypothesis_id": hypothesis_id,
        "required_sources": sorted(NOVELTY_SOURCES),
        "missing": missing,
        "blocked": blocked,
        "checks": latest,
    }


def poc_gate(conn, repo, hypothesis_id: str) -> dict[str, Any]:
    hypothesis = conn.execute("SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)).fetchone()
    if hypothesis is None:
        return {"ok": False, "reason": "hypothesis not found", "hypothesis_id": hypothesis_id}
    allowed_statuses = {"MANUAL_VALIDATED", "CONFIRMED"}
    approval = conn.execute(
        "SELECT * FROM manual_approvals WHERE hypothesis_id = ? AND action = 'POC' "
        "AND revoked_at IS NULL ORDER BY id DESC LIMIT 1",
        (hypothesis_id,),
    ).fetchone()
    scope = current_scope(conn, repo)
    reasons = []
    if hypothesis["status"] not in allowed_statuses:
        reasons.append(f"status is {hypothesis['status']}, expected MANUAL_VALIDATED")
    if approval is None:
        reasons.append("manual PoC approval missing")
    else:
        if approval["claim_hash"] != hypothesis["claim_hash"]:
            reasons.append("hypothesis claim changed after approval")
        if not scope["ok"]:
            reasons.append("scoped source changed after the latest snapshot")
        if approval["scope_hash"] != scope["scope_hash"]:
            reasons.append("approval is bound to a different source scope")
    return {
        "ok": not reasons,
        "hypothesis_id": hypothesis_id,
        "reasons": reasons,
        "status": hypothesis["status"],
        "approval": dict(approval) if approval else None,
        "scope": scope,
    }


def record_poc_approval(conn, repo, hypothesis_id: str, approved_by: str, note: str) -> dict[str, Any]:
    hypothesis = conn.execute("SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)).fetchone()
    if hypothesis is None:
        raise ValueError(f"hypothesis not found: {hypothesis_id}")
    if hypothesis["status"] != "CODE_VALIDATED":
        raise ValueError(
            f"hypothesis must be CODE_VALIDATED before manual approval; current={hypothesis['status']}"
        )
    scope = current_scope(conn, repo)
    if not scope["ok"]:
        raise ValueError("source scope is stale or missing; capture and review a fresh snapshot first")
    snapshot = latest_snapshot(conn)
    if snapshot is None:
        raise ValueError("source snapshot missing")
    conn.execute(
        "UPDATE manual_approvals SET revoked_at = ? WHERE hypothesis_id = ? "
        "AND action = 'POC' AND revoked_at IS NULL",
        (utcnow(), hypothesis_id),
    )
    cursor = conn.execute(
        "INSERT INTO manual_approvals(hypothesis_id, action, approved_by, note, claim_hash, "
        "scope_hash, snapshot_id, approved_at) VALUES(?, 'POC', ?, ?, ?, ?, ?, ?)",
        (
            hypothesis_id,
            approved_by,
            note,
            hypothesis["claim_hash"],
            scope["scope_hash"],
            snapshot["id"],
            utcnow(),
        ),
    )
    conn.execute(
        "UPDATE hypotheses SET status='MANUAL_VALIDATED', updated_at=? WHERE id=?",
        (utcnow(), hypothesis_id),
    )
    conn.commit()
    return {
        "approval_id": cursor.lastrowid,
        "hypothesis_id": hypothesis_id,
        "approved_by": approved_by,
        "claim_hash": hypothesis["claim_hash"],
        "scope_hash": scope["scope_hash"],
        "snapshot_id": snapshot["id"],
    }


def report_gate(conn, repo, hypothesis_id: str) -> dict[str, Any]:
    hypothesis = conn.execute("SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)).fetchone()
    if hypothesis is None:
        return {"ok": False, "reason": "hypothesis not found", "hypothesis_id": hypothesis_id}
    poc = poc_gate(conn, repo, hypothesis_id)
    novelty = novelty_gate(conn, hypothesis_id)
    reasons = []
    if hypothesis["status"] != "CONFIRMED":
        reasons.append(f"status is {hypothesis['status']}, expected CONFIRMED")
    if not poc["ok"]:
        reasons.append("PoC/manual validation gate failed")
    if not novelty["ok"]:
        reasons.append("novelty gate failed")
    return {
        "ok": not reasons,
        "hypothesis_id": hypothesis_id,
        "reasons": reasons,
        "poc_gate": poc,
        "novelty_gate": novelty,
    }
