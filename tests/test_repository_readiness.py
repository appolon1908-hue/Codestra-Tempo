from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ReadinessTests(unittest.TestCase):
    def test_validator(self) -> None:
        subprocess.run(["python3", "scripts/validate_repository_readiness.py"], cwd=ROOT, check=True)

    def test_source_locks_agree(self) -> None:
        upstream = json.loads((ROOT / "CODESTRA_UPSTREAM_LOCK.json").read_text())
        lock = json.loads((ROOT / "codestra/release/runtime-base.lock.json").read_text())
        self.assertEqual(upstream["upstream_commit"], lock["sourceAuthorityCommit"])
        self.assertEqual(upstream["imported_tree_sha"], lock["sourceImportedTreeSha"])
        self.assertFalse(lock["runtimeBaseExecutableUsed"])

    def test_imported_tree_matches_locked_git_tree(self) -> None:
        upstream = json.loads((ROOT / "CODESTRA_UPSTREAM_LOCK.json").read_text())
        imported_tree = subprocess.run(
            ["git", "rev-parse", "HEAD:upstream"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(upstream["imported_tree_sha"], imported_tree)

    def test_runtime_is_deploy_only_and_file_secret_bound(self) -> None:
        compose = yaml.safe_load((ROOT / "codestra/deploy/compose.candidate.yaml").read_text())
        service = compose["services"]["tempo"]
        self.assertNotIn("build", service)
        self.assertEqual(set(service["secrets"]), {"tempo_s3_credentials", "tempo_s3_ca"})
        self.assertTrue(all("file" in value for value in compose["secrets"].values()))


if __name__ == "__main__": unittest.main()
