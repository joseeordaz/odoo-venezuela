from unittest.mock import patch

from odoo.addons.point_of_sale.models.pos_session import PosSession as CorePosSession
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosSessionIgtfConfiguration(TransactionCase):
    def test_pos_without_igtf_method_does_not_require_igtf_account(self):
        config = self.env["pos.config"].search([], limit=1)
        self.assertTrue(config, "The test database must contain one POS configuration")

        config.payment_method_ids.write({"apply_igtf": False})
        config.company_id.write(
            {
                "customer_account_igtf_id": False,
                "igtf_percentage": 3.0,
            }
        )
        session = self.env["pos.session"].new(
            {
                "config_id": config.id,
                "user_id": self.env.user.id,
            }
        )

        with patch.object(
            CorePosSession,
            "action_pos_session_open",
            autospec=True,
            return_value=True,
        ):
            self.assertTrue(session.action_pos_session_open())
