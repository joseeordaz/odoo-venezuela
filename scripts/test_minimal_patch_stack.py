#!/usr/bin/env python3
"""Focused source checks for unavoidable HOLA vendor patches."""

import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MinimalPatchStackTest(unittest.TestCase):
    def source(self, path):
        return (ROOT / path).read_text()

    def test_accountant_community_closure(self):
        manifest = ast.literal_eval(
            self.source("l10n_ve_accountant/__manifest__.py")
        )
        self.assertNotIn("account_reports", manifest["depends"])

    def test_accountant_install_preserves_company_currency(self):
        module = ROOT / "l10n_ve_accountant"
        manifest = ast.literal_eval((module / "__manifest__.py").read_text())
        self.assertNotIn("post_init_hook", manifest)
        self.assertNotIn(
            "set_main_company_currency_to_vef",
            (module / "__init__.py").read_text(),
        )
        for filename in manifest.get("data", []):
            if not filename.endswith(".xml"):
                continue
            data = (module / filename).read_bytes()
            # Repository XML never needs DTDs; reject before stdlib parsing.
            self.assertLessEqual(len(data), 2_000_000, filename)
            self.assertNotIn(b"<!DOCTYPE", data.upper(), filename)
            for record in ET.fromstring(data).iter("record"):
                if record.get("model") == "res.company":
                    self.assertIsNone(
                        record.find("./field[@name='currency_id']"), filename
                    )

    def test_pos_igtf_disabled_behavior_is_upstreamed(self):
        source = self.source("l10n_ve_pos_igtf/models/pos_session.py")
        self.assertIn('mapped("apply_igtf")', source)
        self.assertIn(
            "if igtf_in_use and not self.company_id.customer_account_igtf_id:",
            source,
        )

    def test_sale_note_line_loop_fix_is_upstreamed(self):
        source = self.source("l10n_ve_sale/models/sale_order.py")
        self.assertIn("lambda line: not line.display_type", source)
        self.assertIn("if remaining == invoiceable_lines:", source)


if __name__ == "__main__":
    unittest.main()
