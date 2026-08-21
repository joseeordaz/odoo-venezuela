#!/usr/bin/env python3
"""Source-level guard for native stock report bindings."""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = {
    "stock.action_report_picking",
    "stock.action_report_delivery",
    "stock.return_label_report",
}


class StockReportBindingsTest(unittest.TestCase):
    def test_localization_does_not_unbind_native_stock_reports(self):
        # This parses a source-controlled XML file, never untrusted input.
        root = ET.parse(
            ROOT / "l10n_ve_stock" / "views" / "stock_picking_views.xml"
        ).getroot()
        unbound = {
            record.get("id")
            for record in root.findall(".//record[@model='ir.actions.report']")
            if record.find("./field[@name='binding_model_id'][@eval='False']")
            is not None
        }
        self.assertFalse(REPORTS & unbound, sorted(REPORTS & unbound))


if __name__ == "__main__":
    unittest.main()
