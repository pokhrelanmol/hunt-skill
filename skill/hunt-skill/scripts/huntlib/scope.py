from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable

from .db import canonical_json, utcnow


LANGUAGES = {
    ".sol": "solidity",
    ".vy": "vyper",
    ".rs": "rust",
    ".move": "move",
    ".cairo": "cairo",
    ".ts": "typescript",
    ".js": "javascript",
    ".py": "python",
    ".md": "markdown",
    ".toml": "toml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def git_state(repo: Path) -> tuple[str | None, bool]:
    commit = _git(repo, "rev-parse", "HEAD")
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=normal")
    return commit, bool(status) if status is not None else False


def parse_scope_file(repo: Path, path: Path) -> list[str]:
    resolved = path if path.is_absolute() else repo / path
    if not resolved.exists():
        raise FileNotFoundError(f"scope file not found: {resolved}")
    entries = []
    for raw in resolved.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if value and not value.startswith("#"):
            entries.append(value)
    return entries


def expand_scope(repo: Path, entries: Iterable[str]) -> list[Path]:
    repo = repo.resolve()
    files: set[Path] = set()
    for entry in entries:
        candidate = (repo / entry).resolve() if not Path(entry).is_absolute() else Path(entry).resolve()
        try:
            candidate.relative_to(repo)
        except ValueError as exc:
            raise ValueError(f"scope path escapes repository: {entry}") from exc
        if not candidate.exists():
            raise FileNotFoundError(f"scope path not found: {candidate}")
        if candidate.is_file():
            files.add(candidate)
            continue
        for path in candidate.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(repo)
            if relative.parts[0] in {".git", ".audit"}:
                continue
            files.add(path.resolve())
    if not files:
        raise ValueError("scope contains no files")
    return sorted(files, key=lambda path: path.relative_to(repo).as_posix())


def scope_records(repo: Path, paths: Iterable[Path]) -> list[dict[str, str]]:
    records = []
    for path in paths:
        relative = path.resolve().relative_to(repo.resolve()).as_posix()
        records.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "language": LANGUAGES.get(path.suffix.lower(), "unknown"),
            }
        )
    return records


def compute_scope_hash(records: list[dict[str, str]]) -> str:
    payload = [{"path": item["path"], "sha256": item["sha256"]} for item in records]
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def capture_snapshot(conn, repo: Path, paths: Iterable[Path]) -> dict[str, object]:
    records = scope_records(repo, paths)
    scope_hash = compute_scope_hash(records)
    commit, dirty = git_state(repo)
    cursor = conn.execute(
        "INSERT INTO snapshots(created_at, git_commit, git_dirty, scope_hash, scope_json) "
        "VALUES(?, ?, ?, ?, ?)",
        (utcnow(), commit, int(dirty), scope_hash, canonical_json([r["path"] for r in records])),
    )
    snapshot_id = int(cursor.lastrowid)
    conn.executemany(
        "INSERT INTO files(snapshot_id, path, sha256, language, in_scope) VALUES(?, ?, ?, ?, 1)",
        [
            (snapshot_id, record["path"], record["sha256"], record["language"])
            for record in records
        ],
    )
    conn.commit()
    return {
        "snapshot_id": snapshot_id,
        "scope_hash": scope_hash,
        "git_commit": commit,
        "git_dirty": dirty,
        "file_count": len(records),
    }


def latest_snapshot(conn) -> dict[str, object] | None:
    row = conn.execute("SELECT * FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def current_scope(conn, repo: Path) -> dict[str, object]:
    snapshot = latest_snapshot(conn)
    if snapshot is None:
        return {"ok": False, "reason": "no source snapshot", "scope_hash": None, "changes": []}
    paths = json.loads(str(snapshot["scope_json"]))
    records: list[dict[str, str]] = []
    changes = []
    recorded = {
        row["path"]: row["sha256"]
        for row in conn.execute("SELECT path, sha256 FROM files WHERE snapshot_id = ?", (snapshot["id"],))
    }
    for relative in paths:
        path = repo / relative
        if not path.exists():
            digest = "MISSING"
        else:
            digest = sha256_file(path)
        records.append({"path": relative, "sha256": digest})
        if recorded.get(relative) != digest:
            changes.append(
                {"path": relative, "recorded": recorded.get(relative), "current": digest}
            )
    current_hash = compute_scope_hash(records)
    return {
        "ok": current_hash == snapshot["scope_hash"],
        "snapshot_id": snapshot["id"],
        "recorded_scope_hash": snapshot["scope_hash"],
        "scope_hash": current_hash,
        "changes": changes,
    }


def source_hash_for_path(conn, relative: str) -> tuple[int | None, str | None]:
    snapshot = latest_snapshot(conn)
    if snapshot is None:
        return None, None
    row = conn.execute(
        "SELECT sha256 FROM files WHERE snapshot_id = ? AND path = ?",
        (snapshot["id"], relative),
    ).fetchone()
    return int(snapshot["id"]), str(row["sha256"]) if row else None
