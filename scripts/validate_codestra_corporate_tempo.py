#!/usr/bin/env python3
"""Exact-head entrypoint for the Codestra Tempo corporate validation suite.

The comprehensive policy checks remain in validate_codestra_enterprise_profile.py.
This entrypoint deliberately scans the deployable Codestra overlay for secret material
without scanning the scanner's own source code.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY_VALIDATOR = ROOT / "scripts" / "validate_codestra_enterprise_profile.py"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_policy_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("codestra_tempo_policy", LEGACY_VALIDATOR)
    if spec is None or spec.loader is None:
        fail("unable to load the Tempo policy validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scan_deployable_overlay(module: ModuleType) -> None:
    module.require_file(module.FEATURES_DOC)
    module.require_file(module.OPERATING_MODEL)

    # Build signatures at runtime so this source file cannot match its own scanner.
    dash = chr(45) * 5
    private_key = dash + "BEGIN " + "PRIVATE" + chr(32) + "KEY" + dash
    openssh_key = dash + "BEGIN " + "OPENSSH" + chr(32) + "PRIVATE" + chr(32) + "KEY" + dash
    aws_access_prefix = "A" + "K" + "I" + "A"
    signatures = (private_key, openssh_key, aws_access_prefix)

    for path in module.CODESTRA.rglob("*"):
        if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for signature in signatures:
            if signature in text:
                fail(f"secret-shaped material found in {path.relative_to(ROOT)}")

    tempo_text = module.TEMPO_CONFIG.read_text(encoding="utf-8").lower()
    inline_secret_fields = (
        r"(?m)^\s*access_key\s*:",
        r"(?m)^\s*secret_key\s*:",
        r"(?m)^\s*password\s*:",
        r"(?m)^\s*authorization\s*:",
        r"(?m)^\s*session_token\s*:",
    )
    for pattern in inline_secret_fields:
        if re.search(pattern, tempo_text):
            fail("Tempo source contains an inline credential field")


def main() -> None:
    module = load_policy_module()
    module.validate_profile()
    module.validate_tempo_config()
    module.validate_overrides()
    module.validate_packaging()
    scan_deployable_overlay(module)
    print("Codestra Tempo corporate configuration validation PASS")


if __name__ == "__main__":
    main()
