from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosSession(models.Model):
    _inherit = "pos.session"

    def action_pos_session_open(self):
        igtf_payment_methods = self.config_id.payment_method_ids.filtered("apply_igtf")
        if igtf_payment_methods and not self.company_id.customer_account_igtf_id:
            raise ValidationError(
                _(
                    "You have the IGTF configuration turned on, first configure the account and the percentage"
                )
            )

        return super().action_pos_session_open()
