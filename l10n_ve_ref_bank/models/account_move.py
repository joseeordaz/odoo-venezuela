from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        moves_to_post = self.filtered(lambda move: move.state == "draft")
        if soft:
            today = fields.Date.context_today(self)
            moves_to_post = moves_to_post.filtered(lambda move: move.date <= today)
        payments = moves_to_post.payment_ids
        payments.validate_bank_payment_reference_length()
        with self.env.cr.savepoint():
            payments.validate_bank_payment_reference_unique()
            payments._reserve_bank_reference_keys()
            return super()._post(soft=soft)

    def write(self, values):
        payments = self.payment_ids
        if values.get("state") == "posted":
            payments.validate_bank_payment_reference_length()
            with self.env.cr.savepoint():
                payments.validate_bank_payment_reference_unique()
                payments._reserve_bank_reference_keys()
                result = super().write(values)
                payments._synchronize_bank_reference_keys()
                return result

        result = super().write(values)
        if "state" in values:
            payments._synchronize_bank_reference_keys()
        return result
