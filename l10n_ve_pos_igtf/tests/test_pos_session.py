from unittest.mock import patch

from odoo import Command
from odoo.addons.point_of_sale.models.pos_session import PosSession as CorePosSession
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosSessionIgtfConfiguration(TransactionCase):
    def _new_session(self, apply_igtf):
        config = self.env["pos.config"].new(
            {
                "name": "IGTF test POS",
                "company_id": self.env.company.id,
                "payment_method_ids": [
                    Command.create(
                        {
                            "name": "IGTF test payment method",
                            "apply_igtf": apply_igtf,
                        }
                    )
                ],
            }
        )
        return self.env["pos.session"].new(
            {
                "config_id": config.id,
                "user_id": self.env.user.id,
            }
        )

    def test_pos_without_igtf_method_does_not_require_igtf_account(self):
        self.env.company.write(
            {
                "customer_account_igtf_id": False,
                "igtf_percentage": 3.0,
            }
        )
        session = self._new_session(apply_igtf=False)

        with patch.object(
            CorePosSession,
            "action_pos_session_open",
            autospec=True,
            return_value=True,
        ) as core_action:
            self.assertTrue(session.action_pos_session_open())
        core_action.assert_called_once_with(session)

    def test_pos_with_igtf_method_requires_igtf_account(self):
        self.env.company.write(
            {
                "customer_account_igtf_id": False,
                "igtf_percentage": 3.0,
            }
        )

        with self.assertRaisesRegex(ValidationError, "IGTF"):
            self._new_session(apply_igtf=True).action_pos_session_open()
