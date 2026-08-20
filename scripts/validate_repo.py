#!/usr/bin/env python3
"""Validate Odoo addon source without importing Odoo."""

import ast
import py_compile
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    modules = sorted(path for path in ROOT.glob("l10n_ve_*") if (path / "__manifest__.py").is_file())
    if not modules:
        raise SystemExit("no l10n_ve_* modules found")
    files = 0
    for module in modules:
        manifest = ast.literal_eval((module / "__manifest__.py").read_text())
        if not isinstance(manifest, dict) or not manifest.get("version"):
            raise SystemExit(f"invalid manifest: {module.name}")
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
    print(f"validated {len(modules)} modules and {files} Python/XML files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
