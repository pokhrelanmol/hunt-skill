from __future__ import annotations

import json
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

    def run_cli(self, *args: str, expected: int = 0) -> dict:
        result = subprocess.run(
            [sys.executable, str(AUDITCTL), *args, "--repo", str(self.repo)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_doctor_does_not_mistake_hunt_skill_for_tenderly(self) -> None:
        result = self.run_cli("doctor")
        self.assertNotIn(str(SKILL_ROOT), result["tenderly"]["skill_paths"])

    def setup_store(self) -> None:
        self.run_cli("init")
        self.run_cli("snapshot", "--scope", "src")
        self.run_cli(
            "profile-set",
            "--name",
            "Fixture Vault",
            "--archetype",
            "vault",
            "--case",
            "Vault shares and totalAssets control deposit and redemption value.",
        )
        self.run_cli("impact-seed")

    def test_setup_seed_and_bounded_search(self) -> None:
        self.setup_store()
        impacts = self.run_cli("impact-list", "--status", "DRAFT")
        self.assertGreaterEqual(impacts["count"], 1)
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
            "--archetype",
            "vault",
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
