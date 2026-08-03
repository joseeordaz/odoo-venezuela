from unittest.mock import patch

from odoo.addons.point_of_sale.models.pos_session import PosSession as CorePosSession
from odoo.addons.point_of_sale.tests.common import CommonPosTest
from odoo.exceptions import ValidationError
from odoo.tests.common import tagged


@tagged("post_install", "-at_install")
class TestPosSessionIgtfConfiguration(CommonPosTest):
    def _new_session(self, config):
        return self.env["pos.session"].new(
            {
                "config_id": config.id,
                "user_id": self.env.user.id,
            }
        )

    def test_pos_without_igtf_method_does_not_require_igtf_account(self):
        config = self.pos_config_usd
        config.payment_method_ids.write({"apply_igtf": False})
        config.company_id.write(
            {
                "customer_account_igtf_id": False,
                "igtf_percentage": 3.0,
            }
        )
        session = self._new_session(config)

        with patch.object(
            CorePosSession,
            "action_pos_session_open",
            autospec=True,
            return_value=True,
        ) as core_action:
            self.assertTrue(session.action_pos_session_open())
        core_action.assert_called_once_with(session)

    def test_pos_with_igtf_method_requires_igtf_account(self):
        config = self.pos_config_usd
        payment_method = config.payment_method_ids[:1]
        self.assertTrue(payment_method)
        config.payment_method_ids.write({"apply_igtf": False})
        payment_method.apply_igtf = True
        config.company_id.write(
            {
                "customer_account_igtf_id": False,
                "igtf_percentage": 3.0,
            }
        )

        with self.assertRaisesRegex(ValidationError, "IGTF"):
            self._new_session(config).action_pos_session_open()
