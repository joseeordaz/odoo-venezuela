from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "l10n_ve_accountant")
class TestTaxSupportRule(TransactionCase):
    def test_archived_tax_read_and_archive_authority(self):
        rule = self.env.ref("l10n_ve_accountant.tax_support_no_archive_rule")
        self.assertFalse(rule.active)
        support = self.env["res.users"].create({
            "name": "Fiscal support test",
            "login": "fiscal-support-tax-test",
            "group_ids": [Command.set([
                self.env.ref("base.group_user").id,
                self.env.ref("l10n_ve_accountant.group_fiscal_config_support").id,
            ])],
            "company_ids": [Command.link(self.env.company.id)],
        })
        tax = self.env["account.tax"].create({"name": "Historical tax test", "amount": 15})
        tax.write({"active": False})
        self.assertEqual(
            self.env["account.tax"].with_user(support).with_context(active_test=False)
            .search([("id", "=", tax.id)]).ids,
            [tax.id],
        )
        tax.write({"active": True})
        with self.assertRaises(AccessError):
            tax.with_user(support).write({"active": False})
        self.assertTrue(tax.active)
        support.group_ids = [Command.link(self.env.ref("account.group_account_manager").id)]
        tax.with_user(support).write({"active": False})
        self.assertFalse(tax.active)