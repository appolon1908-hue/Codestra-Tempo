#!/usr/bin/env python3
"""Validate Codestra Tempo protected source authority."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def validate_upstream(source: dict, lock: dict) -> None:
    expected = {
        "component": "tempo",
        "codestra_repository": "appolon1908-hue/Codestra-Tempo",
        "upstream_repository": "grafana/tempo",
        "upstream_clone_url": "https://github.com/grafana/tempo.git",
        "import_path": "upstream",
        "deployment_enabled": False,
    }
    for key, value in expected.items():
        if source.get(key) != value:
            raise ValueError(f"upstream_authority_drift:{key}")
    ref = source.get("upstream_ref")
    if not isinstance(ref, str) or re.fullmatch(r"[0-9a-f]{40}", ref) is None:
        raise ValueError("upstream_ref_must_be_exact_commit")
    for key in ("upstream_clone_url", "import_path", "deployment_enabled"):
        if lock.get(key) != expected[key]:
            raise ValueError(f"upstream_lock_drift:{key}")
    if lock.get("upstream_ref") != ref or lock.get("upstream_commit") != ref:
        raise ValueError("upstream_lock_not_bound_to_exact_ref")


def validate_sync(source: str, document: dict) -> None:
    if (document.get("permissions") or {}) != {
        "actions": "write",
        "contents": "write",
        "pull-requests": "write",
    }:
        raise ValueError("sync_permissions_drift")
    forbidden = (
        r"git\s+push\s+origin\s+(?:HEAD:)?(?:main|staging|production)(?:\s|$)",
        r"git\s+push\s+--force",
    )
    if any(re.search(pattern, source) for pattern in forbidden):
        raise ValueError("protected_branch_sync_forbidden")
    required = (
        "[[ \"$UPSTREAM_REF\" =~ ^[0-9a-f]{40}$ ]]",
        "[[ \"$UPSTREAM_SHA\" == \"$UPSTREAM_REF\" ]]",
        'SYNC_BRANCH="sync/tempo-upstream-${UPSTREAM_SHA}"',
        'git read-tree --prefix=upstream/ "${UPSTREAM_SHA}^{tree}"',
        '[[ "$REMOTE_SHA" == "$LOCAL_SHA" ]]',
        "gh pr list",
        "Multiple open synchronization pull requests found.",
        "gh pr create",
        "--base main",
        'gh workflow run validate.yml --repo "$GITHUB_REPOSITORY" --ref "$SYNC_BRANCH"',
        "'synchronized_at': os.environ['UPSTREAM_TIMESTAMP']",
        'export GIT_AUTHOR_DATE="$UPSTREAM_TIMESTAMP"',
        'export GIT_COMMITTER_DATE="$UPSTREAM_TIMESTAMP"',
    )
    for token in required:
        if token not in source:
            raise ValueError(f"reviewed_sync_boundary_missing:{token}")


def validate_workflow(source: str) -> None:
    required = (
        "pull_request:",
        "workflow_dispatch:",
        "validate-source:",
        "name: validate-source",
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "persist-credentials: false",
        "Bind vendored Git tree to exact official commit",
        "git rev-parse 'HEAD:upstream'",
        '[[ "$vendored_tree" == "$official_tree" ]]',
    )
    for token in required:
        if token not in source:
            raise ValueError(f"validation_boundary_missing:{token}")
    if re.search(r"uses:\s+actions/(?:checkout|setup-python)@v\d+", source):
        raise ValueError("mutable_action_reference")
    if re.search(r"pull_request:\s*\n\s+paths:", source):
        raise ValueError("pull_request_validation_must_be_unconditional")


def validate_repository() -> None:
    source_path = ROOT / "CODESTRA_UPSTREAM.json"
    lock_path = ROOT / "CODESTRA_UPSTREAM_LOCK.json"
    sync_path = ROOT / ".github/workflows/upstream-source-sync.yml"
    workflow_path = ROOT / ".github/workflows/validate.yml"
    for path in (source_path, lock_path, sync_path, workflow_path):
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"required_regular_file_missing:{path.relative_to(ROOT)}")
    source = json.loads(source_path.read_text())
    lock = json.loads(lock_path.read_text())
    sync_source = sync_path.read_text()
    workflow_source = workflow_path.read_text()
    validate_upstream(source, lock)
    validate_sync(sync_source, yaml.safe_load(sync_source))
    yaml.safe_load(workflow_source)
    validate_workflow(workflow_source)
    if (ROOT / "upstream/.git").exists():
        raise ValueError("nested_upstream_git_metadata_forbidden")


if __name__ == "__main__":
    try:
        validate_repository()
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise SystemExit(f"TEMPO_SOURCE_SECURITY=FAIL ERROR={error}") from error
    print("TEMPO_SOURCE_SECURITY=PASS")
    print("UPSTREAM_COMMIT_PINNED=YES")
    print("SYNC_THROUGH_REVIEWED_PR=YES")
    print("DEPLOYMENT_ENABLED=NO")
