#!/usr/bin/env python3
"""Focused source checks for unavoidable HOLA vendor patches."""

import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

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

    def test_invoice_book_defaults_accept_both_local_currencies(self):
        module = ast.parse(self.source("l10n_ve_invoice/wizard/accounting_reports.py"))
        wizard = next(node for node in module.body if isinstance(node, ast.ClassDef)
                      and node.name == "WizardAccountingReportsBinauralInvoice")
        methods = ("_default_check_currency_system", "_default_currency_system")
        for name in methods:
            definition = next(node for node in wizard.body if isinstance(node, ast.FunctionDef)
                              and node.name == name)
            namespace = {}
            exec(compile(ast.Module(body=[definition], type_ignores=[]), "<wizard>", "exec"), namespace)
            for currency, expected in (("VES", True), ("VEF", True), ("USD", False)):
                with self.subTest(method=name, currency=currency):
                    company = SimpleNamespace(currency_id=SimpleNamespace(
                        name=currency, id={"VES": 1, "VEF": 2, "USD": 3}[currency]))
                    env = SimpleNamespace(company=company, ref=lambda _: SimpleNamespace(id=2))
                    self.assertIs(namespace[name](SimpleNamespace(env=env)), expected)

    def test_invoice_template_local_and_foreign_currency(self):
        data = self.source("l10n_ve_invoice/report/report_invoice_free_form.xml")
        self.assertNotIn("<!DOCTYPE", data.upper())
        root = ET.fromstring(data)
        document = root.find(".//template[@id='report_freeform_document']")
        wrapper = root.find(".//template[@id='template_invoice_free_form_l10n_ve_invoice']")
        assert document is not None and wrapper is not None
        currency_base = document.find(".//t[@t-set='currency_base']")
        base_vef = wrapper.find(".//t[@t-set='base_vef']")
        foreign_totals = document.find(".//div[@id='total']/t[@t-if]")
        clause = document.find(".//div[@name='coletilla']/span")
        assert clause is not None
        rate = clause.find(".//t[@t-out='o.company_currency_rate']")
        totals = document.findall(".//div[@id='total']//th[@colspan='2']")
        subtotal = document.find(".//span[@t-out='current_subtotal']")
        rounded_label = root.find(".//template[@id='document_tax_totals_ve']//t[@t-if='has_rounding']/td/span")
        assert currency_base is not None and base_vef is not None
        assert foreign_totals is not None and rate is not None and len(totals) == 2
        assert subtotal is not None and rounded_label is not None
        local_total = totals[1]
        label = local_total.find("span")
        assert label is not None
        # QWeb resolves XML IDs before evaluating these trusted local template expressions.
        def qweb(expr, o):
            assert expr is not None
            return eval(expr.replace("%(base.VEF)s", "2"), {"o": o})

        for company_code, invoice_code, symbol, foreign in (
            ("VES", "VES", "Bs", False),
            ("VES", "USD", "Bs", True),
            ("VEF", "VEF", "Bs.F", False),
            ("VEF", "USD", "Bs.F", True),
        ):
            with self.subTest(company=company_code, invoice=invoice_code):
                company_currency = SimpleNamespace(name=company_code, symbol=symbol)
                o = SimpleNamespace(currency_id=SimpleNamespace(name=invoice_code, id={"VES": 1, "VEF": 2, "USD": 3}[invoice_code]),
                                    company_id=SimpleNamespace(currency_id=company_currency,
                                                               show_tag_on_usd_invoice=True),
                                    env={"res.currency": SimpleNamespace(browse=lambda _: SimpleNamespace(name="VEF"))})
                self.assertIs(qweb(currency_base.get("t-value"), o), not foreign)
                self.assertIs(qweb(base_vef.get("t-value"), o), not foreign)
                self.assertIs(qweb(foreign_totals.get("t-if"), o), foreign)
                self.assertIs(qweb(clause.get("t-if"), o), foreign)
                self.assertIs(qweb(rate.get("t-options"), o)["display_currency"],
                              company_currency)
                self.assertIs(qweb(subtotal.get("t-options"), o)["display_currency"],
                              o.currency_id)
                self.assertEqual(qweb(label.get("t-out"), o), symbol)
                self.assertEqual(qweb(rounded_label.get("t-out"), o), company_code)


if __name__ == "__main__":
    unittest.main()
