#!/usr/bin/env python3
"""Focused source checks for the minimal HOLA overlay."""

import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TAX_UNIT = (
    "l10n_ve_accountant.tax_unit_data_l10n_ve_payment_extension"
)


class MinimalPatchStackTest(unittest.TestCase):
    def source(self, path):
        return (ROOT / path).read_text()

    def test_accountant_community_closure(self):
        manifest = ast.literal_eval(
            self.source("l10n_ve_accountant/__manifest__.py")
        )
        self.assertFalse({
            "account_reports",
            "account_invoice_pricelist",
            "account_invoice_pricelist_sale",
        } & set(manifest["depends"]))

    def test_contact_guard_is_opt_in_and_transaction_company_aware(self):
        company = self.source("l10n_ve_contact/models/res_company.py")
        partner = self.source("l10n_ve_contact/models/res_partner.py")
        self.assertIn("validate_partner_name_immutable = fields.Boolean(\n        default=False,", company)
        self.assertIn("company_id.validate_partner_name_immutable", partner)
        self.assertIn(".sudo().search_count", partner)
        self.assertIn('if partner.name == vals["name"]:', partner)
        partner_class = next(
            node
            for node in ast.parse(partner).body
            if isinstance(node, ast.ClassDef) and node.name == "ResPartner"
        )
        write = next(
            node
            for node in partner_class.body
            if isinstance(node, ast.FunctionDef) and node.name == "write"
        )
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "write"
                and isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Name)
                and node.func.value.func.id == "super"
                for node in ast.walk(write)
            )
        )

    def test_report_identity_never_comes_from_serialized_context(self):
        source = self.source("l10n_ve_invoice/models/ir_actions_report.py")
        tree = ast.parse(source)
        methods = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        }
        for method in (
            "_render_qweb_pdf_prepare_streams",
            "_render_qweb_html",
        ):
            calls = {
                node.func.attr
                for node in ast.walk(methods[method])
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
            }
            self.assertIn("_filter_printable_report_ids", calls)
        self.assertNotIn("active_model", source)
        self.assertNotIn("active_ids", source)

    def test_retention_data_uses_canonical_tax_unit(self):
        # This parses a source-controlled XML file, never untrusted input.
        root = ET.parse(
            ROOT
            / "l10n_ve_payment_extension"
            / "data"
            / "fees_retention_data.xml"
        ).getroot()
        fields = root.findall(".//field[@name='tax_unit_ids']")
        self.assertEqual(len(fields), 7)
        self.assertTrue(
            all(field.get("ref") == CANONICAL_TAX_UNIT for field in fields)
        )

    def test_pos_requires_account_only_for_enabled_igtf_method(self):
        source = self.source("l10n_ve_pos_igtf/models/pos_session.py")
        self.assertIn('filtered("apply_igtf")', source)
        self.assertIn(
            "if igtf_payment_methods and not "
            "self.company_id.customer_account_igtf_id:",
            source,
        )

    def test_sale_currency_fixtures_do_not_mutate_main_company(self):
        for filename in (
            "l10n_ve_sale/tests/test_pricelist.py",
            "l10n_ve_sale/tests/test_sale_order_rate.py",
        ):
            source = self.source(filename)
            self.assertNotIn("base.main_company", source, filename)
            self.assertIn("self.env['res.company'].create", source, filename)


if __name__ == "__main__":
    unittest.main()
