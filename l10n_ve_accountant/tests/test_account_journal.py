from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "l10n_ve_accountant_journal")
class TestAccountJournal(TransactionCase):
    def test_international_purchase_journal_is_unique_per_company(self):
        currency = self.env.company.currency_id
        company_a = self.env["res.company"].create(
            {"name": "International Journal Company A", "currency_id": currency.id}
        )
        company_b = self.env["res.company"].create(
            {"name": "International Journal Company B", "currency_id": currency.id}
        )
        Journal = self.env["account.journal"].sudo()
        Journal.create({
            "name": "International Purchases A",
            "code": "INPA",
            "type": "purchase",
            "company_id": company_a.id,
            "is_purchase_international": True,
        })
        with self.assertRaises(ValidationError):
            Journal.create({
                "name": "Duplicate International Purchases A",
                "code": "DIPA",
                "type": "purchase",
                "company_id": company_a.id,
                "is_purchase_international": True,
            })
        journal_b = Journal.create({
            "name": "International Purchases B",
            "code": "INPB",
            "type": "purchase",
            "company_id": company_b.id,
            "is_purchase_international": True,
        })
        self.assertTrue(journal_b.is_purchase_international)