from odoo import _, models
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _filter_printable_report_ids(self, report_ref, res_ids):
        if not res_ids:
            return res_ids

        model = self._get_report(report_ref).model
        if model == "account.move":
            records = self.env[model].browse(res_ids).filtered(
                lambda record: record.state == "posted"
            )
            error = _(
                "None of the selected documents are posted.\n"
                "Only posted documents can be printed."
            )
        elif model == "sale.order":
            records = self.env[model].browse(res_ids).filtered(
                lambda record: record.state != "draft"
            )
            error = _(
                "None of the selected sale orders are confirmed.\n"
                "Only non-draft orders can be printed."
            )
        else:
            return res_ids

        if not records:
            raise UserError(error)
        return records.ids

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        res_ids = self._filter_printable_report_ids(report_ref, res_ids)
        return super()._render_qweb_pdf_prepare_streams(
            report_ref, data, res_ids=res_ids
        )

    def _render_qweb_html(self, report_ref, docids, data=None):
        docids = self._filter_printable_report_ids(report_ref, docids)
        return super()._render_qweb_html(report_ref, docids, data=data)
