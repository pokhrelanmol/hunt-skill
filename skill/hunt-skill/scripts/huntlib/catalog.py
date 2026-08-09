from __future__ import annotations

import json
from pathlib import Path

from .db import canonical_json, upsert_search, utcnow


def catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "impact-catalogs.json"


def load_catalog() -> dict:
    return json.loads(catalog_path().read_text(encoding="utf-8"))


def set_profile(
    conn,
    *,
    name: str,
    archetypes: list[str],
    protocol_case: str,
    assets: list[str],
    roles: list[str],
    integrations: list[str],
) -> None:
    available = set(load_catalog()["archetypes"])
    unknown = sorted(set(archetypes) - available)
    if unknown:
        raise ValueError(f"unknown archetypes: {', '.join(unknown)}; available: {', '.join(sorted(available))}")
    if not protocol_case.strip():
        raise ValueError("protocol case is required")
    conn.execute(
        "INSERT INTO protocol_profiles(id, name, archetypes_json, protocol_case, assets_json, "
        "roles_json, integrations_json, updated_at) VALUES('primary', ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET name=excluded.name, archetypes_json=excluded.archetypes_json, "
        "protocol_case=excluded.protocol_case, assets_json=excluded.assets_json, "
        "roles_json=excluded.roles_json, integrations_json=excluded.integrations_json, "
        "updated_at=excluded.updated_at",
        (
            name,
            canonical_json(sorted(set(archetypes))),
            protocol_case,
            canonical_json(assets),
            canonical_json(roles),
            canonical_json(integrations),
            utcnow(),
        ),
    )
    conn.commit()


def seed_impacts(conn) -> list[str]:
    profile = conn.execute("SELECT * FROM protocol_profiles WHERE id='primary'").fetchone()
    if profile is None:
        raise ValueError("protocol profile missing; run profile-set first")
    catalog = load_catalog()["archetypes"]
    archetypes = json.loads(profile["archetypes_json"])
    seeded: list[str] = []
    now = utcnow()
    for archetype in archetypes:
        for item in catalog[archetype]:
            invariant_id = f"invariant:template:{archetype}:{item['key']}"
            impact_id = f"impact:{archetype}:{item['key']}"
            protocol_case = f"{profile['protocol_case']} Lens to resolve: {item['case_prompt']}"
            conn.execute(
                "INSERT INTO invariants(id, title, statement, scope, protocol_case, status, created_at, updated_at) "
                "VALUES(?, ?, ?, ?, ?, 'INFERRED', ?, ?) ON CONFLICT(id) DO NOTHING",
                (
                    invariant_id,
                    item["title"],
                    item["invariant"],
                    archetype,
                    protocol_case,
                    now,
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO impact_goals(id, archetype, title, invariant_id, protocol_case, "
                "decision_point, bad_state, attacker_goal, candidate_primitives_json, status, source, "
                "created_at, updated_at) VALUES(?, ?, ?, ?, ?, '', '', ?, '[]', 'DRAFT', 'template', ?, ?) "
                "ON CONFLICT(id) DO NOTHING",
                (
                    impact_id,
                    archetype,
                    item["title"],
                    invariant_id,
                    protocol_case,
                    item["attacker_goal"],
                    now,
                    now,
                ),
            )
            upsert_search(conn, "invariants", invariant_id)
            upsert_search(conn, "impact_goals", impact_id)
            seeded.append(impact_id)
    conn.commit()
    return seeded
