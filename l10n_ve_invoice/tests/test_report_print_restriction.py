from odoo.tests import TransactionCase, tagged
from odoo import fields, Command
from odoo.addons.base.models.ir_actions_report import (
    IrActionsReport as BaseIrActionsReport,
)
from odoo.exceptions import UserError
from unittest.mock import patch


@tagged("post_install", "-at_install", "l10n_ve_invoice")
class TestReportPrintRestriction(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Invoice Print Restriction Test Company',
            'currency_id': self.env.ref('base.VES').id,
            'foreign_currency_id': self.env.ref('base.USD').id,
            'country_id': self.env.ref('base.ve').id,
        })
        self.env = self.env(context={
            **self.env.context,
            'allowed_company_ids': [self.company.id],
        })

        self.account_receivable = self.env['account.account'].create({
            'name': 'Receivable', 'code': '1111111',
            'account_type': 'asset_receivable', 'reconcile': True,
        })
        self.account_revenue = self.env['account.account'].create({
            'name': 'Revenue', 'code': '4444444',
            'account_type': 'income',
        })
        self.account_expense = self.env['account.account'].create({
            'name': 'Expense', 'code': '5555555',
            'account_type': 'expense',
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'property_account_receivable_id': self.account_receivable.id,
        })
        tax_group = self.env['account.tax.group'].create({
            'name': 'IVA Test',
            'country_id': self.env.ref('base.ve').id,
        })
        sale_tax = self.env['account.tax'].create({
            'name': 'IVA venta Test',
            'amount': 16,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'country_id': self.env.ref('base.ve').id,
            'tax_group_id': tax_group.id,
        })
        purchase_tax = self.env['account.tax'].create({
            'name': 'IVA compra Test',
            'amount': 16,
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
            'company_id': self.company.id,
            'country_id': self.env.ref('base.ve').id,
            'tax_group_id': tax_group.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Product Test', 'type': 'service',
            'property_account_income_id': self.account_revenue.id,
            'property_account_expense_id': self.account_expense.id,
            'taxes_id': [Command.set(sale_tax.ids)],
            'supplier_taxes_id': [Command.set(purchase_tax.ids)],
        })
        self.journal_sale = self.env['account.journal'].create({
            'name': 'Sale Journal', 'type': 'sale',
            'code': 'SALE1',
            'default_account_id': self.account_revenue.id,
        })

        self.report_invoice = 'account.account_invoices'

    def _create_invoice(self, move_type='out_invoice', state='draft'):
        inv = self.env['account.move'].with_context(check_move_validity=False).create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'journal_id': self.journal_sale.id,
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        if state == 'posted':
            inv.with_context(move_action_post_alert=True).action_post()
        elif state == 'cancel':
            inv.with_context(move_action_post_alert=True).action_post()
            inv.button_cancel()
        return inv

    def _test_pdf_raises(self, res_ids):
        with self.assertRaises(UserError):
            self.env['ir.actions.report']._render_qweb_pdf_prepare_streams(
                self.report_invoice, {}, res_ids=res_ids
            )

    def _test_pdf_ok(self, res_ids):
        with patch.object(type(self.env['ir.actions.report']), '_render_qweb_pdf_prepare_streams') as mock:
            mock.return_value = {}
            result = self.env['ir.actions.report']._render_qweb_pdf_prepare_streams(
                self.report_invoice, {}, res_ids=res_ids
            )
        self.assertEqual(result, {})

    def _test_html_raises(self, docids, data=None):
        with self.assertRaises(UserError):
            self.env['ir.actions.report']._render_qweb_html(
                self.report_invoice, docids, data=data
            )

    def _test_html_ok(self, docids, data=None):
        with patch.object(type(self.env['ir.actions.report']), '_render_qweb_html') as mock:
            mock.return_value = [b'%PDF']
            result = self.env['ir.actions.report']._render_qweb_html(
                self.report_invoice, docids, data=data
            )
        self.assertEqual(result, [b'%PDF'])

    # ═══════════════════════════════════════════════════════════════
    # account.move PDF
    # ═══════════════════════════════════════════════════════════════

    def test_01_print_posted_invoice_pdf(self):
        inv = self._create_invoice(state='posted')
        self._test_pdf_ok(inv.ids)

    def test_02_print_draft_invoice_pdf(self):
        inv = self._create_invoice(state='draft')
        self._test_pdf_raises(inv.ids)

    def test_03_print_cancel_invoice_pdf(self):
        inv = self._create_invoice(state='cancel')
        self._test_pdf_raises(inv.ids)

    def test_04_print_mixed_invoices_pdf(self):
        inv_posted = self._create_invoice(state='posted')
        inv_draft = self._create_invoice(state='draft')
        self._test_pdf_ok(inv_posted.ids + inv_draft.ids)

    def test_05_print_posted_refund_pdf(self):
        inv = self._create_invoice(state='posted')
        refund = self._create_invoice(move_type='out_refund', state='draft')
        self._test_pdf_raises(refund.ids)

    # ═══════════════════════════════════════════════════════════════
    # _render_qweb_html (incluye fix del bypass)
    # ═══════════════════════════════════════════════════════════════

    def test_06_print_posted_invoice_html_no_data(self):
        inv = self._create_invoice(state='posted')
        self._test_html_ok(inv.ids)

    def test_07_print_draft_invoice_html_no_data(self):
        inv = self._create_invoice(state='draft')
        self._test_html_raises(inv.ids)

    def test_08_print_draft_invoice_html_with_context(self):
        inv = self._create_invoice(state='draft')
        data = {'context': {'active_ids': inv.ids, 'active_model': 'account.move'}}
        self._test_html_raises(inv.ids, data=data)

    def test_09_print_cancel_invoice_html_no_data(self):
        inv = self._create_invoice(state='cancel')
        self._test_html_raises(inv.ids)

    def test_10_print_mixed_invoices_html(self):
        inv_posted = self._create_invoice(state='posted')
        inv_draft = self._create_invoice(state='draft')
        self._test_html_ok(inv_posted.ids + inv_draft.ids)

    def _assert_boundary(self, report, valid_ids, invalid_ids, hostile_data):
        report_model = self.env['ir.actions.report']
        for method in ('_render_qweb_pdf_prepare_streams', '_render_qweb_html'):
            with self.subTest(method=method, case='invalid requested IDs'):
                with patch.object(BaseIrActionsReport, method) as downstream:
                    with self.assertRaises(UserError):
                        if method == '_render_qweb_pdf_prepare_streams':
                            report_model._render_qweb_pdf_prepare_streams(
                                report, hostile_data, res_ids=invalid_ids
                            )
                        else:
                            report_model._render_qweb_html(
                                report, invalid_ids, data=hostile_data
                            )
                downstream.assert_not_called()

            with self.subTest(method=method, case='mixed requested IDs'):
                sentinel = {}
                with patch.object(
                    BaseIrActionsReport, method, return_value=sentinel
                ) as downstream:
                    if method == '_render_qweb_pdf_prepare_streams':
                        result = report_model._render_qweb_pdf_prepare_streams(
                            report, hostile_data, res_ids=invalid_ids + valid_ids
                        )
                        downstream.assert_called_once_with(
                            report, hostile_data, res_ids=valid_ids
                        )
                    else:
                        result = report_model._render_qweb_html(
                            report, invalid_ids + valid_ids, data=hostile_data
                        )
                        downstream.assert_called_once_with(
                            report, valid_ids, data=hostile_data
                        )
                self.assertIs(result, sentinel)

    def test_server_authoritative_invoice_report_boundary(self):
        posted = self._create_invoice(state='posted')
        draft = self._create_invoice(state='draft')
        self._assert_boundary(
            self.report_invoice,
            posted.ids,
            draft.ids,
            {'context': {
                'active_model': 'res.partner',
                'active_ids': self.partner.ids,
            }},
        )

    def test_server_authoritative_sale_report_boundary(self):
        report = self.env['ir.actions.report'].create({
            'name': 'Sale print boundary test',
            'model': 'sale.order',
            'report_name': 'l10n_ve_invoice.test_sale_order',
            'report_type': 'qweb-pdf',
        })
        confirmed, draft = self.env['sale.order'].create([
            {'partner_id': self.partner.id, 'state': 'sale'},
            {'partner_id': self.partner.id, 'state': 'draft'},
        ])
        self._assert_boundary(
            report,
            confirmed.ids,
            draft.ids,
            {'context': {
                'active_model': 'account.move',
                'active_ids': [self._create_invoice(state='posted').id],
            }},
        )

    def test_account_move_uses_report_and_requested_ids(self):
        self.test_server_authoritative_invoice_report_boundary()

    def test_sale_order_uses_report_and_requested_ids(self):
        self.test_server_authoritative_sale_report_boundary()

    def test_empty_and_unrelated_reports_pass_through(self):
        unrelated_report = self.env['ir.actions.report'].create({
            'name': 'Unrelated print boundary test',
            'model': 'res.partner',
            'report_name': 'l10n_ve_invoice.test_res_partner',
            'report_type': 'qweb-pdf',
        })
        hostile_data = {'context': {
            'active_model': 'account.move',
            'active_ids': [self._create_invoice(state='draft').id],
        }}
        cases = (
            (self.report_invoice, None),
            (self.report_invoice, []),
            (unrelated_report, self.partner.ids),
        )
        for method in ('_render_qweb_pdf_prepare_streams', '_render_qweb_html'):
            for report, record_ids in cases:
                with self.subTest(method=method, report=report, record_ids=record_ids):
                    sentinel = {}
                    with patch.object(
                        BaseIrActionsReport, method, return_value=sentinel
                    ) as downstream:
                        if method == '_render_qweb_pdf_prepare_streams':
                            result = self.env['ir.actions.report']._render_qweb_pdf_prepare_streams(
                                report, hostile_data, res_ids=record_ids
                            )
                            downstream.assert_called_once_with(
                                report, hostile_data, res_ids=record_ids
                            )
                        else:
                            result = self.env['ir.actions.report']._render_qweb_html(
                                report, record_ids, data=hostile_data
                            )
                            downstream.assert_called_once_with(
                                report, record_ids, data=hostile_data
                            )
                    self.assertIs(result, sentinel)
