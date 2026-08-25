from __future__ import annotations

import json
import os
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
        job = self.run_cli(
            "job-upsert",
            "--id",
            "JOB-001",
            "--goal",
            "Can partial settlement make cancellation restore too much collateral?",
            "--status",
            "ACTIVE",
        )
        self.assertEqual(job["status"], "ACTIVE")
        self.run_cli(
            "job-upsert",
            "--id",
            "JOB-002",
            "--goal",
            "Can FalconX NAV lag affect rebalance?",
            "--status",
            "ACTIVE",
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

    def test_hunt_and_recon_docs_preserve_user_boundary_and_local_recon(self) -> None:
        hunt = (SKILL_ROOT / "workflows" / "hunt.md").read_text(encoding="utf-8")
        recon = (SKILL_ROOT / "workflows" / "recon.md").read_text(encoding="utf-8")
        self.assertIn("one meaningful `ACTIVE` job", hunt)
        self.assertIn("Forbidden state", hunt)
        self.assertIn("Sensitive consumer", hunt)
        self.assertIn("Trace backward from impact", hunt)
        self.assertIn("Trace forward from attacker", hunt)
        self.assertIn("economic reality vs protocol representation", hunt)
        self.assertIn("stop for human steering", hunt)
        self.assertIn("Basic Global Recon", recon)
        self.assertIn("Deep Local Recon", recon)

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
