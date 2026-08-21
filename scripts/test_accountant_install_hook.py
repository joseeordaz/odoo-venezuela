#!/usr/bin/env python3
"""Regression test for l10n_ve_accountant install hooks."""

import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AccountantInstallHookTest(unittest.TestCase):
    def test_manifest_does_not_force_vef_company_currency(self):
        module = ROOT / "l10n_ve_accountant"
        manifest = ast.literal_eval((module / "__manifest__.py").read_text())

        self.assertNotIn("post_init_hook", manifest)
        self.assertNotIn(
            "set_main_company_currency_to_vef",
            (module / "__init__.py").read_text(),
        )
        for filename in manifest.get("data", []):
            if filename.endswith(".xml"):
                data = (module / filename).read_bytes()
                # Repository XML does not support DTDs; reject before parsing.
                self.assertLessEqual(len(data), 2_000_000, filename)
                self.assertNotIn(b"<!DOCTYPE", data.upper(), filename)
                for record in ET.fromstring(data).iter("record"):
                    if record.get("model") == "res.company":
                        self.assertIsNone(
                            record.find("./field[@name='currency_id']"), filename
                        )


if __name__ == "__main__":
    unittest.main()
