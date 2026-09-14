from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
AUDITCTL = SKILL_ROOT / "scripts" / "auditctl.py"


class AuditCtlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "src" / "Vault.sol").write_text(
            "contract Vault { uint256 public totalAssets; function deposit() external {} }\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "src/Vault.sol"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, expected: int = 0, env: dict[str, str] | None = None) -> dict:
        child_env = os.environ.copy()
        if env:
            child_env.update(env)
        result = subprocess.run(
            [sys.executable, str(AUDITCTL), *args, "--repo", str(self.repo)],
            capture_output=True,
            text=True,
            env=child_env,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_doctor_does_not_mistake_hunt_skill_for_tenderly(self) -> None:
        result = self.run_cli("doctor")
        self.assertNotIn(str(SKILL_ROOT), result["tenderly"]["skill_paths"])
        self.assertIn("solodit", result)
        self.assertIn("live_state", result)
        self.assertIn("alchemy_api_key", result["live_state"])

    def test_rpc_resolution_prefers_alchemy_without_printing_key_and_public_fallback(self) -> None:
        key = "test-alchemy-secret"
        alchemy = self.run_cli(
            "rpc-resolve",
            "--chain",
            "base",
            env={"ALCHEMY_API_KEY": key},
        )
        self.assertEqual(alchemy["provider"], "alchemy")
        self.assertIn("<redacted>", alchemy["rpc_url"])
        self.assertNotIn(key, json.dumps(alchemy))

        public = self.run_cli(
            "rpc-resolve",
            "--chain-id",
            "42161",
            env={"ALCHEMY_API_KEY": ""},
        )
        self.assertEqual(public["provider"], "public")
        self.assertEqual(public["chain_id"], 42161)
        self.assertIn("arb1.arbitrum.io", public["rpc_url"])

    def setup_store(self) -> None:
        self.run_cli("init")
        self.run_cli("snapshot", "--scope", "src")

    def test_impact_creation_is_agent_driven_and_protocol_specific(self) -> None:
        self.run_cli("init")
        self.run_cli("snapshot", "--scope", "src")
        impacts = self.run_cli("impact-list", "--status", "DRAFT")
        self.assertEqual(impacts["count"], 0)

        invariant_id = "invariant:vault-deposit-accounting"
        impact_id = "impact:vault-deposit-dilution"
        self.run_cli(
            "invariant-upsert",
            "--id",
            invariant_id,
            "--title",
            "Deposits preserve ownership",
            "--statement",
            "Deposit share issuance preserves proportional ownership of economically owned assets.",
            "--protocol-case",
            "Vault.deposit consumes totalAssets to issue shares.",
        )
        created = self.run_cli(
            "impact-upsert",
            "--id",
            impact_id,
            "--title",
            "Deposit dilution",
            "--invariant-id",
            invariant_id,
            "--protocol-case",
            "Vault.deposit converts assets using totalAssets.",
            "--decision-point",
            "deposit share conversion",
            "--bad-state",
            "issued shares exceed the depositor's economic contribution",
            "--attacker-goal",
            "obtain excess ownership",
            "--candidate-primitive",
            "function:src/Vault.sol:Vault.deposit()",
            "--status",
            "READY",
        )
        self.assertEqual(created["status"], "READY")
        impacts = self.run_cli("impact-list", "--status", "READY")
        self.assertEqual([row["id"] for row in impacts["rows"]], [impact_id])

    def test_setup_and_bounded_search(self) -> None:
        self.setup_store()
        impacts = self.run_cli("impact-list", "--status", "DRAFT")
        self.assertEqual(impacts["count"], 0)
        failed = self.run_cli(
            "impact-upsert",
            "--id",
            "impact:vault:share-dilution",
            "--status",
            "READY",
            expected=2,
        )
        self.assertIn("missing protocol-specific fields", failed["error"])

        function_id = "function:src/Vault.sol:Vault.deposit()"
        storage_id = "storage:src/Vault.sol:Vault.totalAssets"
        self.run_cli(
            "node-upsert",
            "--id",
            function_id,
            "--kind",
            "function",
            "--name",
            "deposit",
            "--summary",
            "Permissionless vault deposit",
        )
        self.run_cli(
            "node-upsert",
            "--id",
            storage_id,
            "--kind",
            "storage",
            "--name",
            "totalAssets",
            "--summary",
            "Vault accounting authority",
        )
        relation = self.run_cli(
            "relation-upsert",
            "--src",
            function_id,
            "--type",
            "WRITES",
            "--dst",
            storage_id,
            "--status",
            "INFERRED",
        )
        search = self.run_cli("search", "vault deposit")
        self.assertTrue(any(row["record_id"] == function_id for row in search["rows"]))
        neighbors = self.run_cli("neighbors", function_id)
        self.assertEqual(neighbors["relations"][0]["id"], relation["id"])

    def test_automatic_poc_handoff_binds_claim_and_scope(self) -> None:
        self.setup_store()
        poc_skill = self.repo / ".agents" / "skills" / "poc"
        poc_skill.mkdir(parents=True)
        (poc_skill / "SKILL.md").write_text(
            "---\nname: poc\ndescription: fixture PoC skill\n---\n# PoC\n",
            encoding="utf-8",
        )
        invariant_id = "invariant:vault:share-accounting"
        impact_id = "impact:vault:fixture-share-dilution"
        self.run_cli(
            "invariant-upsert",
            "--id",
            invariant_id,
            "--title",
            "Shares track assets",
            "--statement",
            "Shares preserve proportional ownership of totalAssets.",
            "--protocol-case",
            "Fixture deposit and redeem consume totalAssets.",
        )
        self.run_cli(
            "impact-upsert",
            "--id",
            impact_id,
            "--archetype",
            "vault",
            "--title",
            "Fixture share dilution",
            "--invariant-id",
            invariant_id,
            "--protocol-case",
            "Fixture deposit converts assets using mutable totalAssets.",
            "--decision-point",
            "deposit share conversion",
            "--bad-state",
            "totalAssets diverges from economically owned assets",
            "--attacker-goal",
            "mint excess shares",
            "--candidate-primitive",
            "function:src/Vault.sol:Vault.deposit()",
            "--status",
            "READY",
        )
        self.run_cli(
            "hypothesis-upsert",
            "--id",
            "HYP-001",
            "--title",
            "Donation dilutes deposits",
            "--claim",
            "An attacker can alter totalAssets before deposit and mint excess shares.",
            "--status",
            "CODE_VALIDATED",
            "--attacker-capability",
            "permissionless donation and deposit",
            "--impact-goal-id",
            impact_id,
            "--root-cause-key",
            "vault-totalassets-authority",
            "--next-check",
            "automatic PoC handoff",
        )
        blocked = self.run_cli("poc-gate", "HYP-001", expected=6)
        self.assertIn("dedicated PoC skill path not configured", blocked["reasons"])

        self.assertTrue(self.run_cli("poc-config", "--path", str(poc_skill))["ok"])
        handoff = self.run_cli("poc-handoff", "HYP-001")
        self.assertTrue(handoff["ok"])
        self.assertEqual(handoff["handoff"]["poc_skill_path"], str(poc_skill.resolve()))

        with (self.repo / "src" / "Vault.sol").open("a", encoding="utf-8") as handle:
            handle.write("// changed\n")
        stale = self.run_cli("poc-gate", "HYP-001", expected=6)
        self.assertIn("scoped source changed after the latest snapshot", stale["reasons"])

    def test_jobs_context_observations_and_probes_reuse_existing_store(self) -> None:
        self.setup_store()
        missing_model = self.run_cli(
            "job-upsert",
            "--id",
            "JOB-001",
            "--goal",
            "Can partial settlement make cancellation restore too much collateral?",
            "--status",
            "ACTIVE",
            expected=2,
        )
        self.assertIn("requires --attack-model", missing_model["error"])
        job = self.run_cli(
            "job-upsert",
            "--id",
            "JOB-001",
            "--goal",
            "Can partial settlement make cancellation restore too much collateral?",
            "--status",
            "ACTIVE",
            "--attack-model",
            "capability: public settlement; transient: partial settlement; durable: restored claim; "
            "unwind: UNKNOWN; consumer: cancellation; impact: excess collateral; "
            "reset/repeat: UNKNOWN; economics: UNKNOWN",
        )
        self.assertEqual(job["status"], "ACTIVE")
        self.assertIn("durable: restored claim", job["attack_model"])
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-002",
            "--goal",
            "Can FalconX NAV lag affect rebalance?",
            "--status",
            "ACTIVE",
            "--attack-model",
            "capability: rebalance caller; transient: stale NAV; durable: rebalance accounting; "
            "unwind: NAV refresh; consumer: rebalance; impact: UNKNOWN; "
            "reset/repeat: UNKNOWN; economics: UNKNOWN",
        )
        packet = self.run_cli("research-packet", "JOB-001")
        self.assertEqual(packet["job"]["status"], "NEXT")
        jobs = self.run_cli("job-list", "--limit", "10")
        self.assertEqual([row["id"] for row in jobs["rows"]], ["JOB-002", "JOB-001"])
        search = self.run_cli("search", "FalconX NAV lag")
        self.assertTrue(
            any(
                row["record_type"] == "investigations" and row["record_id"] == "JOB-002"
                for row in search["rows"]
            )
        )
        failed = self.run_cli(
            "job-upsert",
            "--id",
            "JOB-001",
            "--goal",
            "Can partial settlement make cancellation restore too much collateral?",
            "--status",
            "DONE",
            expected=2,
        )
        self.assertIn("DONE job requires --result", failed["error"])
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-001",
            "--goal",
            "Can partial settlement make cancellation restore too much collateral?",
            "--status",
            "DONE",
            "--attack-model",
            "capability: public settlement; transient: partial settlement; durable: restored claim; "
            "unwind: cancellation; consumer: collateral accounting; impact: tested; "
            "reset/repeat: tested; economics: harmless",
            "--result",
            "Coverage: partial settlement and cancellation; disposition: rejected; "
            "unresolved: none; reopen when: settlement accounting changes.",
        )

        self.run_cli(
            "observation-add",
            "--job-id",
            "JOB-002",
            "--statement",
            "A 1 wei deposit changes totalAssets but not shares in the fixture.",
            "--status",
            "INFERRED",
        )
        self.run_cli(
            "probe-add",
            "--job-id",
            "JOB-002",
            "--setup",
            "Fixture vault with empty supply",
            "--sequence",
            "deposit(1)",
            "--state-before",
            "totalAssets=0 shares=0",
            "--state-after",
            "totalAssets=1 shares=0",
            "--result",
            "No revert; accounting discontinuity observed",
            "--harness",
            "test/Vault.t.sol::testDepositOne",
        )
        packet = self.run_cli("research-packet", "JOB-002")
        self.assertTrue(any(row["kind"] == "OBSERVATION" for row in packet["job_facts"]))
        self.assertTrue(any(row["kind"] == "STATE_PROBE" for row in packet["job_facts"]))

        self.run_cli(
            "hypothesis-upsert",
            "--id",
            "HYP-REVIVE",
            "--title",
            "Partial settlement cancellation over-restores",
            "--claim",
            "Partial settlement can make cancellation restore too much collateral.",
            "--rejection-reason",
            "partial settlement is impossible",
            "--reopen-condition",
            "partial settlement is possible",
            "--status",
            "REJECTED",
        )
        context = self.run_cli(
            "context-add",
            "--statement",
            "New docs say partial settlement is possible.",
        )
        self.assertTrue(
            any(candidate["record_id"] == "HYP-REVIVE" for candidate in context["affected_candidates"])
        )

    def test_job_variants_inherit_graph_and_enforce_family_saturation(self) -> None:
        self.setup_store()
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-BASE",
            "--goal",
            "Can donation-inflated share value corrupt withdrawal accounting?",
            "--status",
            "DONE",
            "--attack-model",
            "capability: donation; transient: inflated value; durable: share valuation; "
            "unwind: donation retained; consumer: withdrawal; impact: tested; "
            "reset/repeat: tested; economics: unprofitable",
            "--result",
            "Coverage: donation producer and withdrawal consumer; disposition: rejected; "
            "unresolved: other consumers; reopen when: a new consumer or integration is found.",
        )
        self.run_cli(
            "node-upsert",
            "--id",
            "function:Vault.withdraw",
            "--kind",
            "function",
            "--name",
            "withdraw",
        )
        self.run_cli(
            "relation-upsert",
            "--src",
            "JOB-BASE",
            "--type",
            "FOCUSES_ON",
            "--dst",
            "function:Vault.withdraw",
            "--status",
            "INFERRED",
        )
        variant = self.run_cli(
            "job-upsert",
            "--id",
            "JOB-VARIANT-1",
            "--goal",
            "Can the same inflated share value be consumed by collateral valuation?",
            "--status",
            "NEXT",
            "--variant-of",
            "JOB-BASE",
            "--variant-delta",
            "New consumer: collateral valuation rather than withdrawal accounting.",
            "--inherits",
            "Donation reachability, share-value producer graph, and withdrawal rejection.",
            "--distinctness",
            "Collateral valuation may trust the inflated representation without withdrawal's guard.",
            "--next-check",
            "Trace every collateral-value consumer of the share token.",
        )
        self.assertEqual(variant["variant_of"], "JOB-BASE")
        self.assertEqual(variant["family_root"], "JOB-BASE")
        self.assertEqual(variant["family_status"], "OPEN")
        self.assertIn("Collateral valuation", variant["variant_distinctness"])
        self.assertIn("collateral-value consumer", variant["next_check"])

        packet = self.run_cli("research-packet", "JOB-VARIANT-1")
        self.assertEqual(packet["linked"]["jobs"][0]["id"], "JOB-BASE")
        self.assertTrue(
            any(
                edge["dst_id"] == "function:Vault.withdraw"
                and edge["inherited_from_job"] == "JOB-BASE"
                for edge in packet["inherited_relations"]
            )
        )
        self.assertEqual(packet["linked"]["nodes"][0]["id"], "function:Vault.withdraw")

        family = self.run_cli("job-list", "--family", "JOB-VARIANT-1", "--limit", "10")
        self.assertEqual({row["id"] for row in family["rows"]}, {"JOB-BASE", "JOB-VARIANT-1"})
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-VARIANT-1",
            "--goal",
            "Can the same inflated share value be consumed by collateral valuation?",
            "--status",
            "DONE",
            "--attack-model",
            "capability: donation; transient: inflated value; durable: share valuation; "
            "unwind: donation retained; consumer: collateral valuation; impact: tested; "
            "reset/repeat: tested; economics: unprofitable",
            "--result",
            "Coverage: withdrawal and collateral consumers; disposition: rejected; "
            "unresolved: none found; reopen when: new code or integration consumes share value.",
            "--saturate-family",
        )
        blocked = self.run_cli(
            "job-upsert",
            "--id",
            "JOB-VARIANT-2",
            "--goal",
            "Can an external integration consume inflated share value?",
            "--variant-of",
            "JOB-VARIANT-1",
            "--variant-delta",
            "New integration consumer.",
            "--inherits",
            "Donation and share-value producer coverage.",
            "--distinctness",
            "An external consumer may omit the local withdrawal guard.",
            "--next-check",
            "Resolve deployed consumers of the share token.",
            expected=2,
        )
        self.assertIn("is SATURATED", blocked["error"])
        reopened = self.run_cli(
            "job-upsert",
            "--id",
            "JOB-VARIANT-2",
            "--goal",
            "Can an external integration consume inflated share value?",
            "--variant-of",
            "JOB-VARIANT-1",
            "--variant-delta",
            "New integration consumer discovered in deployment configuration.",
            "--inherits",
            "Donation and share-value producer coverage.",
            "--distinctness",
            "The deployed integration consumes the representation under different validation.",
            "--next-check",
            "Trace the integration's collateral valuation and liquidation paths.",
            "--reopen-family-reason",
            "New deployed integration accepts the share token as collateral.",
        )
        self.assertEqual(reopened["family_root"], "JOB-BASE")
        self.assertEqual(reopened["family_status"], "OPEN")

    def test_research_packet_prefers_explicit_links_and_excludes_unrelated_context(self) -> None:
        self.setup_store()
        invariant_id = "invariant:falconx-nav"
        impact_id = "impact:falconx-nav-rebalance"
        function_id = "function:src/Vault.sol:Vault.deposit()"
        linked_context = "fact:user-context:falconx-async"
        unrelated_context = "fact:user-context:governance-delay"
        self.run_cli(
            "invariant-upsert",
            "--id",
            invariant_id,
            "--title",
            "Fresh NAV",
            "--statement",
            "Rebalance decisions use fresh NAV.",
        )
        self.run_cli(
            "impact-upsert",
            "--id",
            impact_id,
            "--archetype",
            "vault",
            "--title",
            "Stale NAV rebalance",
            "--invariant-id",
            invariant_id,
            "--protocol-case",
            "FalconX NAV feeds rebalance accounting.",
            "--decision-point",
            "rebalance NAV read",
            "--bad-state",
            "rebalance consumes stale NAV",
            "--attacker-goal",
            "increase leverage against stale value",
            "--candidate-primitive",
            function_id,
            "--status",
            "READY",
        )
        self.run_cli(
            "node-upsert",
            "--id",
            function_id,
            "--kind",
            "function",
            "--name",
            "deposit",
        )
        self.run_cli(
            "context-add",
            "--id",
            linked_context,
            "--statement",
            "FalconX NAV updates asynchronously.",
        )
        self.run_cli(
            "context-add",
            "--id",
            unrelated_context,
            "--statement",
            "Governance timelock is two days.",
        )
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-LINKED",
            "--goal",
            "Can FalconX stale NAV affect rebalance?",
            "--status",
            "ACTIVE",
            "--attack-model",
            "capability: rebalance caller; transient: stale NAV; durable: rebalance accounting; "
            "unwind: NAV refresh; consumer: rebalance; impact: value shift; reset/repeat: UNKNOWN; economics: UNKNOWN",
        )
        for record_id in (impact_id, function_id, linked_context):
            self.run_cli(
                "relation-upsert",
                "--src",
                "JOB-LINKED",
                "--type",
                "FOCUSES_ON",
                "--dst",
                record_id,
                "--status",
                "INFERRED",
            )
        jobs = self.run_cli("job-list", "--linked-record", impact_id)
        self.assertEqual([row["id"] for row in jobs["rows"]], ["JOB-LINKED"])
        self.assertIn(impact_id, jobs["rows"][0]["linked_records"])
        packet = self.run_cli("research-packet", "JOB-LINKED")
        self.assertFalse(packet["bounds"]["fts_fallback_used"])
        self.assertEqual(packet["linked"]["impact_goals"][0]["id"], impact_id)
        self.assertEqual(packet["linked"]["invariants"][0]["id"], invariant_id)
        linked_fact_ids = {row["id"] for row in packet["linked"]["facts"]}
        self.assertIn(linked_context, linked_fact_ids)
        self.assertNotIn(unrelated_context, linked_fact_ids)

    def test_context_revives_parked_job_and_avoids_unrelated_false_positive(self) -> None:
        self.setup_store()
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-044",
            "--goal",
            "Check FalconX NAV during rebalance",
            "--status",
            "PARKED",
            "--result",
            "Blocked because FalconX NAV is synchronous.",
        )
        self.run_cli(
            "relation-upsert",
            "--src",
            "external:falconx",
            "--type",
            "REVIVES",
            "--dst",
            "JOB-044",
            "--status",
            "INFERRED",
        )
        revived = self.run_cli(
            "context-add",
            "--statement",
            "FalconX NAV updates asynchronously.",
        )
        self.assertTrue(any(candidate["record_id"] == "JOB-044" for candidate in revived["affected_candidates"]))
        unrelated = self.run_cli(
            "context-add",
            "--statement",
            "Governance timelock is two days.",
        )
        self.assertFalse(
            any(candidate["record_id"] == "JOB-044" for candidate in unrelated["affected_candidates"])
        )

    def test_state_probe_provenance_and_observation_separation(self) -> None:
        self.setup_store()
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-PROBE",
            "--goal",
            "Compare split deposit accounting",
            "--status",
            "ACTIVE",
            "--attack-model",
            "capability: depositor; transient: split deposits; durable: shares; unwind: withdrawal; "
            "consumer: share accounting; impact: imbalance; reset/repeat: probe; economics: UNKNOWN",
        )
        unexecuted = self.run_cli(
            "probe-add",
            "--job-id",
            "JOB-PROBE",
            "--setup",
            "planned unit test",
            "--sequence",
            "deposit(40); deposit(60)",
            "--result",
            "agent has not run this yet",
        )
        self.assertEqual(unexecuted["status"], "INFERRED")
        failed = self.run_cli(
            "probe-add",
            "--job-id",
            "JOB-PROBE",
            "--setup",
            "planned unit test",
            "--sequence",
            "deposit(100)",
            "--result",
            "claimed verified without execution",
            "--status",
            "VERIFIED",
            expected=2,
        )
        self.assertIn("VERIFIED state probes require --executed", failed["error"])
        executed = self.run_cli(
            "probe-add",
            "--job-id",
            "JOB-PROBE",
            "--setup",
            "Fixture vault",
            "--sequence",
            "deposit(100) vs deposit(40); deposit(60)",
            "--state-before",
            "shares=0 assets=0",
            "--state-after",
            "shares differ",
            "--result",
            "focused test executed",
            "--status",
            "VERIFIED",
            "--executed",
            "--harness",
            "test/Vault.t.sol::testSplitDeposit",
            "--observation",
            "Split deposits produce a different final share count.",
        )
        self.assertEqual(executed["status"], "VERIFIED")
        packet = self.run_cli("research-packet", "JOB-PROBE")
        kinds = {row["kind"] for row in packet["job_facts"]}
        self.assertIn("STATE_PROBE", kinds)
        self.assertIn("OBSERVATION", kinds)

    def test_pending_candidates_preserve_focus_and_retrieve_priority(self) -> None:
        self.setup_store()
        self.run_cli(
            "job-upsert", "--id", "JOB-CURRENT", "--goal", "Review withdrawal accounting",
            "--status", "ACTIVE", "--attack-model", "consumer: withdrawal; gaps: UNKNOWN",
        )
        for index in range(1, 4):
            job_id = f"JOB-CANDIDATE-{index}"
            self.run_cli(
                "job-upsert", "--id", job_id, "--goal", f"Review accounting boundary {index}",
                "--status", "NEXT", "--next-check", "Compare the relevant accounting views",
            )
            self.run_cli(
                "fact-upsert", "--id", f"fact:{job_id}:priority", "--subject-id", job_id,
                "--kind", "JOB_PRIORITY", "--statement", f"P{index}; rationale: fixture evidence",
            )
        jobs = {row["id"]: row for row in self.run_cli("job-list")["rows"]}
        self.assertEqual([job_id for job_id, row in jobs.items() if row["status"] == "ACTIVE"],
                         ["JOB-CURRENT"])
        for index in range(1, 4):
            row = jobs[f"JOB-CANDIDATE-{index}"]
            self.assertEqual(row["status"], "NEXT")
            self.assertEqual(row["attack_model"], "")
            self.assertEqual(row["research_priority"], f"P{index}; rationale: fixture evidence")
        self.run_cli(
            "fact-upsert", "--id", "fact:JOB-CANDIDATE-2:priority",
            "--subject-id", "JOB-CANDIDATE-2", "--kind", "JOB_PRIORITY",
            "--statement", "P1; rationale: new dependency evidence",
        )
        packet = self.run_cli("research-packet", "JOB-CANDIDATE-2")
        self.assertEqual(packet["job"]["research_priority"],
                         "P1; rationale: new dependency evidence")
        self.assertEqual(len([fact for fact in packet["job_facts"]
                              if fact["kind"] == "JOB_PRIORITY"]), 1)

    def test_global_observation_survives_without_placeholder_job(self) -> None:
        self.setup_store()
        self.run_cli("node-upsert", "--id", "external:ledger", "--kind", "external",
                     "--name", "External ledger")
        self.run_cli(
            "fact-upsert", "--id", "fact:ledger-observation", "--subject-id", "external:ledger",
            "--kind", "OBSERVATION", "--statement", "LedgerSnapshot returns stored accounting",
            "--status", "INFERRED",
        )
        self.assertEqual(self.run_cli("job-list")["count"], 0)
        result = self.run_cli("search", "LedgerSnapshot")
        self.assertTrue(any(row["record_id"] == "fact:ledger-observation" for row in result["rows"]))
        self.assertTrue(self.run_cli("lint")["ok"])

    def test_fact_list_filters_paginates_and_keeps_unclassified_concerns(self) -> None:
        self.setup_store()
        records = [
            ("fact:risk:a", "RISK_CONTEXT", "external:ledger", "INFERRED", "Labels: integration, lifecycle"),
            ("fact:risk:b", "OBSERVATION", "external:ledger", "UNKNOWN", "Unclassified accounting discrepancy"),
            ("fact:risk:c", "RISK_CONTEXT", "storage:supply", "UNKNOWN", "Labels: precision"),
            ("fact:priority", "JOB_PRIORITY", "JOB-SELECTED", "INFERRED", "P1 integration review"),
        ]
        for fact_id, kind, subject, status, statement in records:
            self.run_cli("fact-upsert", "--id", fact_id, "--kind", kind, "--subject-id", subject,
                         "--status", status, "--statement", statement)
        filters = ("--kind", "RISK_CONTEXT", "--kind", "OBSERVATION")
        first = self.run_cli("fact-list", *filters, "--limit", "2")
        self.assertEqual([row["id"] for row in first["rows"]], ["fact:risk:a", "fact:risk:b"])
        self.assertTrue(first["has_more"])
        second = self.run_cli("fact-list", *filters, "--limit", "2",
                              "--offset", str(first["next_offset"]))
        self.assertEqual([row["id"] for row in second["rows"]], ["fact:risk:c"])
        self.assertFalse(second["has_more"])
        self.assertIsNone(second["next_offset"])
        scoped = self.run_cli("fact-list", *filters, "--subject-id", "external:ledger",
                              "--status", "UNKNOWN")
        self.assertEqual([row["id"] for row in scoped["rows"]], ["fact:risk:b"])
        matched = self.run_cli("fact-list", *filters, "--query", "integration")
        self.assertEqual([row["id"] for row in matched["rows"]], ["fact:risk:a"])
        exact = self.run_cli("fact-list", "--id", "fact:risk:b", "--id", "fact:risk:c")
        self.assertEqual([row["statement"] for row in exact["rows"]],
                         ["Unclassified accounting discrepancy", "Labels: precision"])
        self.assertEqual(self.run_cli("fact-list", "--id", "missing")["count"], 0)
        self.assertEqual(self.run_cli("fact-list", "--limit", "0")["count"], 1)
        bounded = self.run_cli("fact-list", "--limit", "1000", "--offset", "-1")
        self.assertEqual(bounded["bounds"], {"limit": 100, "offset": 0, "order": "id"})
        self.run_cli("fact-list", "--status", "INVALID", expected=2)
        self.run_cli("fact-list", "--query", "!!!", expected=2)
        self.assertEqual(self.run_cli("job-list")["count"], 0)

    def test_risk_context_reuse_preserves_evidence_and_active_job(self) -> None:
        self.setup_store()
        self.run_cli("job-upsert", "--id", "JOB-SELECTED", "--goal", "Review ledger consistency",
                     "--status", "ACTIVE", "--attack-model", "consumer: ledger; gaps: UNKNOWN")
        self.run_cli("fact-upsert", "--id", "fact:risk:ledger", "--subject-id", "external:ledger",
                     "--kind", "RISK_CONTEXT", "--statement", "Labels: integration; review: unexamined")
        evidence = self.run_cli("evidence-add", "--record-type", "facts", "--record-id", "fact:risk:ledger",
                                "--source-kind", "documentation", "--note", "Fixture dependency semantics")
        for job_id in ("JOB-SELECTED", "JOB-PENDING"):
            if job_id == "JOB-PENDING":
                self.run_cli("job-upsert", "--id", job_id, "--goal", "Review a different ledger consumer",
                             "--status", "NEXT")
            self.run_cli("fact-upsert", "--id", f"fact:{job_id}:risk", "--subject-id", job_id,
                         "--kind", "JOB_RISK_CONTEXT", "--statement", "fact:risk:ledger")
        self.run_cli("fact-upsert", "--id", "fact:risk:ledger", "--subject-id", "external:ledger",
                     "--kind", "RISK_CONTEXT", "--statement",
                     "Labels: integration; review: first consumer bounded; second consumer unresolved")
        facts = self.run_cli("fact-list", "--kind", "RISK_CONTEXT")["rows"]
        self.assertEqual(len(facts), 1)
        self.assertIn("second consumer unresolved", facts[0]["statement"])
        for job_id in ("JOB-SELECTED", "JOB-PENDING"):
            packet = self.run_cli("research-packet", job_id)
            self.assertTrue(any(fact["kind"] == "JOB_RISK_CONTEXT" and fact["statement"] == "fact:risk:ledger"
                                for fact in packet["job_facts"]))
        self.assertEqual([row["id"] for row in self.run_cli("job-list", "--status", "ACTIVE")["rows"]],
                         ["JOB-SELECTED"])
        with sqlite3.connect(self.repo / ".audit/graph/audit.db") as conn:
            self.assertEqual(conn.execute("SELECT record_id FROM evidence WHERE id=?",
                                          (evidence["evidence_id"],)).fetchone()[0], "fact:risk:ledger")

    def test_code_validation_gate_is_shared_across_transitions_and_lint(self) -> None:
        self.setup_store()
        self.run_cli("impact-upsert", "--id", "impact:review", "--title", "Accounting mismatch")
        self.run_cli(
            "hypothesis-upsert", "--id", "HYP-REVIEW", "--title", "Review claim",
            "--claim", "Accounting views disagree", "--attacker-capability", "fixture actor",
            "--impact-goal-id", "impact:review", "--root-cause-key", "fixture-accounting",
            "--next-check", "Review evidence",
        )
        transitions = [
            ("hypothesis-upsert", "--id", "HYP-REVIEW", "--status", "CODE_VALIDATED"),
            ("hypothesis-status", "HYP-REVIEW", "--status", "CODE_VALIDATED"),
        ]
        for transition in transitions:
            result = self.run_cli(*transition, expected=2)
            self.assertIn("READY or COVERED", result["error"])
        with sqlite3.connect(self.repo / ".audit/graph/audit.db") as conn:
            self.assertEqual(conn.execute("SELECT status FROM hypotheses WHERE id='HYP-REVIEW'")
                             .fetchone()[0], "LEAD")
        self.run_cli(
            "invariant-upsert", "--id", "invariant:review", "--title", "Consistent accounting",
            "--statement", "Both views reflect the same effective accounting state",
        )
        self.run_cli(
            "impact-upsert", "--id", "impact:review", "--status", "READY",
            "--invariant-id", "invariant:review", "--protocol-case", "Fixture ledger views",
            "--decision-point", "Accounting read", "--bad-state", "Views disagree",
            "--attacker-goal", "Incorrect accounting", "--candidate-primitive", "external:ledger",
        )
        self.run_cli("hypothesis-upsert", "--id", "HYP-REVIEW", "--next-check", "   ")
        for transition in transitions:
            result = self.run_cli(*transition, expected=2)
            self.assertIn("missing fields: next_check", result["error"])
        self.run_cli("hypothesis-upsert", "--id", "HYP-REVIEW", "--next-check", "Review evidence")
        for transition in transitions:
            result = self.run_cli(*transition)
            status_key = "status" if transition[0] == "hypothesis-upsert" else "to"
            self.assertEqual(result[status_key], "CODE_VALIDATED")
        self.assertTrue(self.run_cli("lint")["ok"])
        self.run_cli("impact-upsert", "--id", "impact:review", "--status", "DRAFT")
        lint = self.run_cli("lint", expected=5)
        issue = next(item for item in lint["issues"] if item["id"] == "HYP-REVIEW")
        self.assertIn("READY or COVERED", " ".join(issue["reasons"]))

    def test_novelty_requires_all_sources(self) -> None:
        self.setup_store()
        invariant_id = "invariant:fixture"
        impact_id = "impact:fixture"
        self.run_cli(
            "invariant-upsert",
            "--id",
            invariant_id,
            "--title",
            "Fixture invariant",
            "--statement",
            "Fixture state remains consistent.",
        )
        self.run_cli(
            "impact-upsert",
            "--id",
            impact_id,
            "--title",
            "Fixture impact",
            "--invariant-id",
            invariant_id,
            "--protocol-case",
            "Fixture protocol case",
            "--decision-point",
            "fixture decision",
            "--bad-state",
            "fixture bad state",
            "--attacker-goal",
            "fixture loss",
            "--candidate-primitive",
            "fixture:primitive",
            "--status",
            "READY",
        )
        self.run_cli(
            "hypothesis-upsert",
            "--id",
            "HYP-002",
            "--title",
            "Fixture lead",
            "--claim",
            "Fixture claim",
            "--impact-goal-id",
            impact_id,
        )
        missing = self.run_cli("novelty-gate", "HYP-002", expected=3)
        self.assertEqual(set(missing["missing"]), {"repo-known", "similar-audit", "solodit", "hack-registry"})
        for source in ("repo-known", "similar-audit", "solodit", "hack-registry"):
            self.run_cli(
                "novelty-add",
                "HYP-002",
                "--source-kind",
                source,
                "--query",
                "fixture query",
                "--result",
                "no matching root cause",
                "--overlap",
                "NEW",
            )
        self.assertTrue(self.run_cli("novelty-gate", "HYP-002")["ok"])


if __name__ == "__main__":
    unittest.main()
