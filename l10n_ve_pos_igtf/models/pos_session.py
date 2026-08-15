from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from collections import defaultdict
from odoo.tools import float_is_zero, float_compare


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_payment_method(self):
        res = super()._loader_params_pos_payment_method()
        res["search_params"]["fields"].append("apply_igtf")
        return res

    def action_pos_session_open(self):
        igtf_payment_methods = self.config_id.payment_method_ids.filtered("apply_igtf")
        if igtf_payment_methods and not self.company_id.customer_account_igtf_id:
            raise ValidationError(
                _(
                    "You have the IGTF configuration turned on, first configure the account and the percentage"
                )
            )

        return super().action_pos_session_open()
