from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from . import SCHEMA_VERSION


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER NOT NULL,
    scope_hash TEXT NOT NULL,
    scope_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    language TEXT NOT NULL,
    in_scope INTEGER NOT NULL DEFAULT 1,
    UNIQUE(snapshot_id, path)
);

CREATE INDEX IF NOT EXISTS idx_files_snapshot_path ON files(snapshot_id, path);

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    status TEXT NOT NULL DEFAULT 'UNKNOWN',
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(file_path);

CREATE TABLE IF NOT EXISTS relations (
    id TEXT PRIMARY KEY,
    src_id TEXT NOT NULL,
    type TEXT NOT NULL,
    dst_id TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'UNKNOWN',
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rel_src ON relations(src_id, type);
CREATE INDEX IF NOT EXISTS idx_rel_dst ON relations(dst_id, type);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    file_path TEXT,
    file_sha256 TEXT,
    line_start INTEGER,
    line_end INTEGER,
    note TEXT NOT NULL,
    retrieval_handle TEXT,
    snapshot_id INTEGER REFERENCES snapshots(id),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_record ON evidence(record_type, record_id);
CREATE INDEX IF NOT EXISTS idx_evidence_file ON evidence(file_path);

CREATE TABLE IF NOT EXISTS invariants (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT '',
    protocol_case TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'INFERRED',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_goals (
    id TEXT PRIMARY KEY,
    archetype TEXT NOT NULL,
    title TEXT NOT NULL,
    invariant_id TEXT,
    protocol_case TEXT NOT NULL DEFAULT '',
    decision_point TEXT NOT NULL DEFAULT '',
    bad_state TEXT NOT NULL DEFAULT '',
    attacker_goal TEXT NOT NULL DEFAULT '',
    candidate_primitives_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'DRAFT',
    source TEXT NOT NULL DEFAULT 'custom',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_impacts_status ON impact_goals(status, archetype);

CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    subject_id TEXT,
    kind TEXT NOT NULL,
    statement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'UNKNOWN',
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    claim TEXT NOT NULL,
    claim_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'LEAD',
    confidence REAL NOT NULL DEFAULT 0.25,
    severity_candidate TEXT NOT NULL DEFAULT 'UNKNOWN',
    attacker_capability TEXT NOT NULL DEFAULT '',
    impact_goal_id TEXT,
    root_cause_key TEXT NOT NULL DEFAULT '',
    next_check TEXT NOT NULL DEFAULT '',
    rejection_reason TEXT NOT NULL DEFAULT '',
    reopen_condition TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hyp_status ON hypotheses(status);
CREATE INDEX IF NOT EXISTS idx_hyp_root ON hypotheses(root_cause_key);

CREATE TABLE IF NOT EXISTS hypothesis_links (
    hypothesis_id TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_id TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(hypothesis_id, record_type, record_id, role)
);

CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS known_findings (
    id TEXT PRIMARY KEY,
    source_kind TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    affected_area TEXT NOT NULL DEFAULT '',
    resolution TEXT NOT NULL DEFAULT '',
    retrieval_handle TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS novelty_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    query TEXT NOT NULL,
    result TEXT NOT NULL,
    overlap TEXT NOT NULL,
    retrieval_handle TEXT NOT NULL DEFAULT '',
    checked_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_novelty_hyp ON novelty_checks(hypothesis_id, source_kind);

CREATE TABLE IF NOT EXISTS live_evidence (
    id TEXT PRIMARY KEY,
    source_tool TEXT NOT NULL,
    chain_id INTEGER NOT NULL,
    block_number INTEGER,
    tx_hash TEXT,
    address TEXT,
    code_hash TEXT,
    claim TEXT NOT NULL,
    status TEXT NOT NULL,
    retrieval_handle TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    retest_trigger TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS manual_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL,
    action TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    note TEXT NOT NULL,
    claim_hash TEXT NOT NULL,
    scope_hash TEXT NOT NULL,
    snapshot_id INTEGER NOT NULL,
    approved_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_approval_hyp ON manual_approvals(hypothesis_id, action, approved_at);
"""


SEARCHABLE_TABLES = {
    "nodes": ("id", ("name", "summary", "kind")),
    "facts": ("id", ("statement", "kind")),
    "invariants": ("id", ("title", "statement", "protocol_case")),
    "impact_goals": (
        "id",
        ("title", "protocol_case", "decision_point", "bad_state", "attacker_goal"),
    ),
    "hypotheses": ("id", ("title", "claim", "root_cause_key", "next_check")),
    "investigations": ("id", ("goal", "result")),
    "known_findings": ("id", ("title", "root_cause", "affected_area", "resolution")),
}


def utcnow() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def db_path(repo: Path) -> Path:
    return repo.resolve() / ".audit" / "graph" / "audit.db"


def connect(repo: Path, *, create: bool = False) -> sqlite3.Connection:
    path = db_path(repo)
    if not create and not path.exists():
        raise FileNotFoundError(f"audit database not found: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def initialize(repo: Path) -> sqlite3.Connection:
    conn = connect(repo, create=True)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5("
        "record_type UNINDEXED, record_id UNINDEXED, body, tokenize='unicode61')"
    )
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
    return conn


def as_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def upsert_search(conn: sqlite3.Connection, record_type: str, record_id: str) -> None:
    spec = SEARCHABLE_TABLES.get(record_type)
    if spec is None:
        return
    id_column, text_columns = spec
    columns = ", ".join((id_column, *text_columns))
    row = conn.execute(
        f"SELECT {columns} FROM {record_type} WHERE {id_column} = ?", (record_id,)
    ).fetchone()
    conn.execute(
        "DELETE FROM search_fts WHERE record_type = ? AND record_id = ?",
        (record_type, record_id),
    )
    if row is None:
        return
    body = "\n".join(str(row[column] or "") for column in text_columns)
    conn.execute(
        "INSERT INTO search_fts(record_type, record_id, body) VALUES(?, ?, ?)",
        (record_type, record_id, body),
    )


def refresh_search(conn: sqlite3.Connection) -> int:
    conn.execute("DELETE FROM search_fts")
    count = 0
    for table, (id_column, _) in SEARCHABLE_TABLES.items():
        for row in conn.execute(f"SELECT {id_column} AS id FROM {table}"):
            upsert_search(conn, table, row["id"])
            count += 1
    return count
