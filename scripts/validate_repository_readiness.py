#!/usr/bin/env python3
"""Validate repository-only Tempo signed-image readiness."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
IMAGE = re.compile(r"^[a-z0-9./_-]+@sha256:[0-9a-f]{64}$")
AUTHORITY = "appolon1908-hue/Codestra-Telemetry/.github/workflows/reusable-release-image.yml@9a6aebb849bbc068105c10d9d1dfd39ebf6f78bd"
REQUIRED = (
    "README.md", "REPOSITORY_PROFILE.md", "SECURITY.md", ".github/CODEOWNERS",
    "docs/BACKUP_RESTORE_ROLLBACK.md", "docs/UPGRADE.md", ".dockerignore", ".gitleaks.toml",
    "codestra/release/image-build.v1.json", "codestra/release/runtime-base.lock.json",
    "codestra/source-image-contract.v1.json", ".github/workflows/release-image.yml",
    "scripts/build_and_inspect_locked_image.sh", "requirements-validation.txt",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load(relative: str) -> dict:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict): fail(f"{relative} must contain an object")
    return value


def main() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing: fail(f"missing readiness files: {missing}")
    if any(path.is_file() for path in (ROOT / "codestra/runtime-v1").glob("**/*")):
        fail("ambiguous legacy runtime-v1 authority remains")
    manifest = load("codestra/release/image-build.v1.json")
    lock = load("codestra/release/runtime-base.lock.json")
    upstream = load("CODESTRA_UPSTREAM_LOCK.json")
    contract = load("codestra/source-image-contract.v1.json")
    if manifest.get("imageId") != "tempo" or manifest.get("context") != "." or manifest.get("productionActivation") is not False:
        fail("image manifest identity/context/activation mismatch")
    if lock.get("artifactModel") != "repository-built-signed-image" or lock.get("productionActivation") is not False:
        fail("runtime lock model/activation mismatch")
    for field in ("buildFrontendImage", "builderImage", "runtimeBaseImage"):
        if not IMAGE.fullmatch(str(lock.get(field, ""))): fail(f"mutable build input: {field}")
    expected_args = {"GO_BUILDER_IMAGE": lock["builderImage"], "TEMPO_BASE_IMAGE": lock["runtimeBaseImage"], "TEMPO_SOURCE_REVISION": lock["sourceAuthorityCommit"]}
    if manifest.get("buildArgs") != expected_args: fail("image build arguments mismatch")
    source_map = {"sourceAuthorityCommit": "upstream_commit", "sourceOfficialTreeSha": "official_tree_sha", "sourceImportedTreeSha": "imported_tree_sha"}
    for lock_key, upstream_key in source_map.items():
        if lock.get(lock_key) != upstream.get(upstream_key): fail(f"source tree mismatch: {lock_key}")
    source_authority = contract.get("sourceAuthority", {})
    if source_authority.get("upstreamCommit") != lock["sourceAuthorityCommit"] or source_authority.get("importedTreeSha") != lock["sourceImportedTreeSha"]:
        fail("source image contract mismatch")
    if lock.get("runtimeBaseExecutableUsed") is not False: fail("runtime base executable may not be source authority")
    dockerfile = (ROOT / manifest["dockerfile"]).read_text(encoding="utf-8")
    if dockerfile.splitlines()[0] != f"# syntax={lock['buildFrontendImage']}": fail("Dockerfile frontend mismatch")
    for token in ("COPY upstream /src/upstream", "-o /out/tempo", "COPY --from=tempo-builder", 'ENTRYPOINT ["/tempo"]'):
        if token not in dockerfile: fail(f"source-built executable boundary missing: {token}")
    dockerignore = (ROOT / ".dockerignore").read_text()
    for token in ("upstream/docs", "upstream/integration", "upstream/**/*_test.go"):
        if token not in dockerignore: fail(f"upstream test fixture not excluded: {token}")
    compose = yaml.safe_load((ROOT / "codestra/deploy/compose.candidate.yaml").read_text())
    service = compose.get("services", {}).get("tempo", {})
    if "build" in service or service.get("privileged") is True or service.get("network_mode") == "host" or service.get("pid") == "host":
        fail("unsafe deployment candidate")
    if service.get("ports") != ["127.0.0.1:${TEMPO_QUERY_HOST_PORT:-3200}:3200"]:
        fail("Tempo may publish only its loopback query endpoint")
    if set(service.get("secrets", [])) != {"tempo_s3_credentials", "tempo_s3_ca"}:
        fail("secret-file mounts missing")
    if set(compose.get("secrets", {})) != {"tempo_s3_credentials", "tempo_s3_ca"} or any("file" not in item or "external" in item for item in compose["secrets"].values()):
        fail("top-level secrets must be mounted files")
    config = (ROOT / "codestra/config/tempo.yaml").read_text().lower()
    if "insecure: true" in config or re.search(r"(?m)^\s*(?:access_key|secret_key|session_token)\s*:", config):
        fail("unsafe object-store TLS or credential configuration")
    release = yaml.safe_load((ROOT / ".github/workflows/release-image.yml").read_text())
    job = release.get("jobs", {}).get("release", {})
    if job.get("uses") != AUTHORITY or job.get("with", {}).get("image_id") != "tempo": fail("release authority mismatch")
    build_call = 'bash scripts/build_and_inspect_locked_image.sh "$GITHUB_SHA"'
    for relative in (".github/workflows/validate-repository-readiness.yml", ".github/workflows/validate-repository-readiness-protected.yml"):
        if build_call not in (ROOT / relative).read_text(): fail(f"merge/protected image build missing: {relative}")
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        text = workflow.read_text()
        for reference in re.findall(r"(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)", text):
            if not reference.startswith("./") and not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", reference): fail(f"mutable action: {workflow.name}: {reference}")
        if re.search(r"git push\s+origin\s+HEAD:(?:main|development|test|staging|production)", text): fail(f"direct protected-branch push: {workflow.name}")
    print("TEMPO_REPOSITORY_READINESS_SOURCE=PASS")
    print("ARTIFACT_MODEL=SIGNED_IMAGE")
    print("PRODUCTION_ACTIVATION=NO")


if __name__ == "__main__": main()
