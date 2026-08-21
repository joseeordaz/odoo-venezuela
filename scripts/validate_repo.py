#!/usr/bin/env python3
"""Validate Odoo addon source without importing Odoo."""

import ast
import py_compile
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOYABLE_MODULES = ("l10n_ve_contact", "l10n_ve_sale", "l10n_ve_stock")
BANNED_DEPENDENCIES = {
    "account_reports",
    "account_accountant",
    "currency_rate_live",
    "hr_payroll",
    "iot",
    "pos_iot",
    "web_enterprise",
}


def load_manifest(path):
    manifest = ast.literal_eval(path.read_text())
    if not isinstance(manifest, dict) or not manifest.get("version"):
        raise SystemExit(f"invalid manifest: {path.parent.name}")
    dependencies = manifest.get("depends", [])
    if not isinstance(dependencies, list) or not all(
        isinstance(dependency, str) and dependency for dependency in dependencies
    ):
        raise SystemExit(f"invalid dependencies: {path.parent.name}")
    return manifest


def main() -> int:
    modules = sorted(path for path in ROOT.glob("l10n_ve_*") if (path / "__manifest__.py").is_file())
    if not modules:
        raise SystemExit("no l10n_ve_* modules found")
    local_manifests = {
        path.parent.name: path for path in ROOT.glob("*/__manifest__.py")
    }
    manifests = {}
    files = 0
    for module in modules:
        manifest = load_manifest(module / "__manifest__.py")
        manifests[module.name] = manifest
        for path in module.rglob("*.py"):
            py_compile.compile(str(path), doraise=True)
            files += 1
        for path in module.rglob("*.xml"):
            data = path.read_bytes()
            # Repository XML never needs DTDs. Reject them before stdlib parsing.
            if len(data) > 2_000_000 or b"<!DOCTYPE" in data.upper():
                raise SystemExit(f"unsafe or oversized XML: {path}")
            ET.fromstring(data)
            files += 1
    for deployable in DEPLOYABLE_MODULES:
        if deployable not in manifests:
            raise SystemExit(f"missing deployable module: {deployable}")
        pending = [(deployable, [deployable])]
        visited = set()
        while pending:
            module, path = pending.pop()
            if module in visited:
                continue
            visited.add(module)
            for dependency in manifests[module].get("depends", []):
                dependency_path = [*path, dependency]
                if dependency in BANNED_DEPENDENCIES:
                    raise SystemExit(
                        "deployable dependency is not Community-safe: "
                        + " -> ".join(dependency_path)
                    )
                if dependency in local_manifests:
                    if dependency not in manifests:
                        manifests[dependency] = load_manifest(local_manifests[dependency])
                    pending.append((dependency, dependency_path))
                elif dependency.startswith("l10n_ve_"):
                    raise SystemExit(
                        "missing local dependency: " + " -> ".join(dependency_path)
                    )
    print(f"validated {len(modules)} modules and {files} Python/XML files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
