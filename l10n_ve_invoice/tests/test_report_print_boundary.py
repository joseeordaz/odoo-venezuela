from unittest.mock import patch

from odoo import fields
from odoo.addons.base.models.ir_actions_report import (
    IrActionsReport as BaseIrActionsReport,
)
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "l10n_ve_invoice_report_boundary")
class TestReportPrintBoundary(TransactionCase):
    PDF = "_render_qweb_pdf_prepare_streams"
    HTML = "_render_qweb_html"

    def setUp(self):
        super().setUp()
        self.company = self.env["res.company"].create(
            {
                "name": "Invoice Print Boundary Test Company",
                "currency_id": self.env.ref("base.VES").id,
                "foreign_currency_id": self.env.ref("base.USD").id,
            }
        )
        self.env = self.env(
            context={
                **self.env.context,
                "allowed_company_ids": [self.company.id],
            }
        )
        self.report_model = self.env["ir.actions.report"]
        self.reports = {
            model: self.report_model.create(
                {
                    "name": f"Print boundary test: {model}",
                    "model": model,
                    "report_name": f"l10n_ve_invoice.test_{model.replace('.', '_')}",
                    "report_type": "qweb-pdf",
                }
            )
            for model in ("account.move", "sale.order", "res.partner")
        }

        journal = self.env["account.journal"].create(
            {
                "name": "Print Boundary Journal",
                "code": "PBJ",
                "type": "general",
                "company_id": self.company.id,
            }
        )
        self.moves = self.env["account.move"].create(
            [
                {
                    "company_id": self.company.id,
                    "journal_id": journal.id,
                    "date": fields.Date.today(),
                }
                for _index in range(4)
            ]
        )
        self.moves[0].write({"state": "posted"})
        self.moves[2].write({"state": "posted"})
        self.moves[3].write({"state": "cancel"})

        partner = self.env["res.partner"].create({"name": "Boundary Customer"})
        self.orders = self.env["sale.order"].create(
            [
                {
                    "partner_id": partner.id,
                    "company_id": self.company.id,
                    "state": state,
                }
                for state in ("sale", "draft", "sent")
            ]
        )
        self.partners = partner | self.env["res.partner"].create(
            {"name": "Unrelated Report Record"}
        )

    def _call(self, method, report, record_ids, data):
        if method == self.PDF:
            return getattr(self.report_model, method)(
                report, data, res_ids=record_ids
            )
        return getattr(self.report_model, method)(report, record_ids, data=data)

    def _assert_downstream(self, method, report, record_ids, data, expected_ids):
        sentinel = {}
        with patch.object(
            BaseIrActionsReport, method, return_value=sentinel
        ) as downstream:
            result = self._call(method, report, record_ids, data)

        self.assertIs(result, sentinel)
        if method == self.PDF:
            downstream.assert_called_once_with(report, data, res_ids=expected_ids)
            self.assertIs(downstream.call_args.args[1], data)
        else:
            downstream.assert_called_once_with(report, expected_ids, data=data)
            self.assertIs(downstream.call_args.kwargs["data"], data)
        self.assertIs(downstream.call_args.args[0], report)

    def _assert_blocked(self, method, report, record_ids, data):
        with patch.object(BaseIrActionsReport, method) as downstream:
            with self.assertRaises(UserError):
                self._call(method, report, record_ids, data)
        downstream.assert_not_called()

    def test_account_move_uses_report_and_requested_ids(self):
        posted_a, draft, posted_b, cancelled = self.moves
        requested_ids = [posted_b.id, draft.id, posted_a.id]
        expected_ids = [posted_b.id, posted_a.id]
        contexts = (
            None,
            {"context": {"active_model": "account.move", "active_ids": requested_ids}},
            {"context": {"active_model": "res.partner", "active_ids": self.partners.ids}},
            {"context": {"active_model": "account.move", "active_ids": [draft.id]}},
        )

        for method in (self.PDF, self.HTML):
            with self.subTest(method=method, case="all invalid hostile context"):
                self._assert_blocked(
                    method,
                    self.reports["account.move"],
                    [draft.id, cancelled.id],
                    {"context": {"active_model": "res.partner", "active_ids": [posted_a.id]}},
                )
            for data in contexts:
                with self.subTest(method=method, data=data):
                    self._assert_downstream(
                        method,
                        self.reports["account.move"],
                        requested_ids,
                        data,
                        expected_ids,
                    )

    def test_sale_order_uses_report_and_requested_ids(self):
        sale, draft, sent = self.orders
        requested_ids = [sent.id, draft.id, sale.id]
        expected_ids = [sent.id, sale.id]
        contexts = (
            None,
            {"context": {"active_model": "sale.order", "active_ids": requested_ids}},
            {"context": {"active_model": "account.move", "active_ids": self.moves.ids}},
            {"context": {"active_model": "sale.order", "active_ids": [draft.id]}},
        )

        for method in (self.PDF, self.HTML):
            with self.subTest(method=method, case="all invalid hostile context"):
                self._assert_blocked(
                    method,
                    self.reports["sale.order"],
                    [draft.id],
                    {"context": {"active_model": "account.move", "active_ids": [sale.id]}},
                )
            for data in contexts:
                with self.subTest(method=method, data=data):
                    self._assert_downstream(
                        method,
                        self.reports["sale.order"],
                        requested_ids,
                        data,
                        expected_ids,
                    )

    def test_empty_and_unrelated_reports_pass_through(self):
        hostile_data = {
            "context": {
                "active_model": "account.move",
                "active_ids": self.moves.ids,
                "active_id": self.moves[1].id,
            }
        }
        for method in (self.PDF, self.HTML):
            for record_ids in (None, []):
                with self.subTest(method=method, record_ids=record_ids):
                    self._assert_downstream(
                        method,
                        self.reports["account.move"],
                        record_ids,
                        hostile_data,
                        record_ids,
                    )
            with self.subTest(method=method, case="unrelated model"):
                self._assert_downstream(
                    method,
                    self.reports["res.partner"],
                    self.partners.ids,
                    hostile_data,
                    self.partners.ids,
                )
