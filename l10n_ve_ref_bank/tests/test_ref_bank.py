from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "l10n_ve_ref_bank")
class TestBankReference(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.bank_journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "bank")],
            limit=1,
        )
        if not cls.bank_journal:
            raise AssertionError("The test database needs one bank journal")
        cls.manual_inbound = cls.bank_journal.inbound_payment_method_line_ids[:1]
        if not cls.manual_inbound:
            raise AssertionError(
                "The test bank journal needs an inbound payment method"
            )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Bank Reference Test Partner"}
        )

    def _payment(self, memo):
        bank_journal = self.env["account.journal"].new(
            {
                "name": "Bank Reference Test",
                "code": "BRFT",
                "type": "bank",
                "company_id": self.company.id,
                "ref_length_required": 8,
            }
        )
        return self.env["account.payment"].new(
            {
                "company_id": self.company.id,
                "journal_id": bank_journal.id,
                "memo": memo,
            }
        )

    def _create_payment(self, memo, journal=None, extra_values=None):
        journal = journal or self.bank_journal
        manual_inbound = journal.inbound_payment_method_line_ids[:1]
        if not manual_inbound:
            manual_inbound = self.env["account.payment.method.line"].create(
                {
                    "name": "Manual Inbound Bank Reference Test",
                    "journal_id": journal.id,
                    "payment_method_id": self.env.ref(
                        "account.account_payment_method_manual_in"
                    ).id,
                    "payment_type": "inbound",
                }
            )
        values = {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": self.partner.id,
            "amount": 10,
            "journal_id": journal.id,
            "payment_method_line_id": manual_inbound.id,
            "date": fields.Date.today(),
            "memo": memo,
        }
        if self.company.currency_id:
            values["currency_id"] = self.company.currency_id.id
        values.update(extra_values or {})
        return self.env["account.payment"].create(values)

    def test_validation_is_disabled_by_default(self):
        self.company.ref_required = False
        self._payment("short").validate_bank_payment_reference_length()

    def test_reference_length_uses_odoo_19_memo(self):
        self.company.ref_required = True
        with self.assertRaisesRegex(ValidationError, "8 caracteres"):
            self._payment("short").validate_bank_payment_reference_length()
        self._payment("12345678").validate_bank_payment_reference_length()

    def test_duplicate_domain_is_scoped_to_company_and_journal(self):
        self.company.ref_required = True
        payment = self._payment("12345678")
        with patch.object(
            type(payment), "search_count", return_value=1
        ) as search_count:
            with self.assertRaisesRegex(ValidationError, "este diario bancario"):
                payment.validate_bank_payment_reference_unique()
        domain = search_count.call_args.args[0]
        self.assertIn(("memo", "=", "12345678"), domain)
        self.assertIn(("company_id", "=", self.company.id), domain)
        self.assertIn(("journal_id", "=", payment.journal_id.id), domain)
        self.assertIn(("state", "in", ["in_process", "paid"]), domain)

    def test_duplicate_reference_in_same_batch_is_blocked(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        payments = self._create_payment("12345678") | self._create_payment("12345678")

        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            payments.action_post()

        self.assertEqual(set(payments.mapped("state")), {"draft"})

    def test_reservation_key_cannot_be_forged_on_create(self):
        with self.assertRaisesRegex(ValidationError, "administrada internamente"):
            self._create_payment(
                "45454545",
                extra_values={"bank_reference_key": "forged"},
            )

    def test_reservation_key_cannot_be_forged_through_create_context(self):
        Payment = self.env["account.payment"].with_context(
            default_bank_reference_key="forged"
        )
        with self.assertRaisesRegex(ValidationError, "administrada internamente"):
            Payment.create(
                {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": self.partner.id,
                    "amount": 10,
                    "journal_id": self.bank_journal.id,
                    "payment_method_line_id": self.manual_inbound.id,
                    "date": fields.Date.today(),
                    "memo": "46464646",
                }
            )

    def test_processed_state_on_create_reserves_reference(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8

        original = self._create_payment(
            "67676767",
            extra_values={"state": "in_process"},
        )
        self.assertEqual(original.state, "in_process")
        self.assertTrue(original.bank_reference_key)

        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            self._create_payment(
                "67676767",
                extra_values={"state": "in_process"},
            )

    def test_linked_move_posting_reserves_reference(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment(
            "68686868",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        duplicate = self._create_payment(
            "68686868",
            extra_values={"write_off_line_vals": []},
        )
        duplicate.write({"state": "draft"})

        self.assertEqual(original.move_id.state, "draft")
        self.assertEqual(duplicate.move_id.state, "draft")
        self.assertFalse(original.bank_reference_key)
        self.assertFalse(duplicate.bank_reference_key)

        original.move_id.action_post()
        self.assertEqual(original.move_id.state, "posted")
        self.assertTrue(original.bank_reference_key)

        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            duplicate.move_id.action_post()

        self.assertEqual(duplicate.move_id.state, "draft")
        self.assertFalse(duplicate.bank_reference_key)

    def test_linked_move_direct_state_write_tracks_reservation(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment(
            "67676767",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        duplicate = self._create_payment(
            "67676767",
            extra_values={"write_off_line_vals": []},
        )
        duplicate.write({"state": "draft"})

        original.move_id.write({"state": "posted"})
        self.assertTrue(original.bank_reference_key)

        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            duplicate.move_id.write({"state": "posted"})
        self.assertEqual(duplicate.move_id.state, "draft")
        self.assertFalse(duplicate.bank_reference_key)

        original.move_id.write({"state": "draft"})
        self.assertFalse(original.bank_reference_key)
        duplicate.move_id.write({"state": "posted"})
        self.assertTrue(duplicate.bank_reference_key)

    def test_linked_move_direct_cancel_state_releases_reference(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment(
            "65656565",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        original.move_id.action_post()
        self.assertTrue(original.bank_reference_key)

        original.move_id.write({"state": "cancel"})
        self.assertEqual(original.move_id.state, "cancel")
        self.assertFalse(original.bank_reference_key)

        replacement = self._create_payment("65656565")
        replacement.action_post()
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_linked_move_button_cancel_releases_reference(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment(
            "64646464",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        original.move_id.action_post()
        self.assertTrue(original.bank_reference_key)

        original.move_id.button_cancel()
        self.assertEqual(original.move_id.state, "cancel")
        self.assertEqual(original.state, "canceled")
        self.assertFalse(original.bank_reference_key)

        replacement = self._create_payment("64646464")
        replacement.action_post()
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_canceled_linked_move_action_post_does_not_reserve(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment(
            "63636363",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        original.move_id.action_post()
        original.move_id.button_cancel()
        self.assertFalse(original.bank_reference_key)

        original.move_id.action_post()
        self.assertEqual(original.move_id.state, "cancel")
        self.assertFalse(original.bank_reference_key)

        replacement = self._create_payment("63636363")
        replacement.action_post()
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_future_linked_move_soft_post_does_not_reserve(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment(
            "62626262",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        original.move_id.write(
            {"date": fields.Date.add(fields.Date.today(), days=1)}
        )
        self.assertFalse(original.bank_reference_key)

        original.move_id._post(soft=True)
        self.assertEqual(original.move_id.state, "draft")
        self.assertEqual(original.move_id.auto_post, "at_date")
        self.assertFalse(original.bank_reference_key)

    def test_linked_move_reset_releases_reference(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment(
            "69696969",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        original.move_id.action_post()
        self.assertTrue(original.bank_reference_key)

        original.move_id.button_draft()
        self.assertEqual(original.move_id.state, "draft")
        self.assertFalse(original.bank_reference_key)

        replacement = self._create_payment("69696969")
        replacement.action_post()
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_linked_posted_move_memo_change_updates_reservation(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        occupied = self._create_payment("71717171")
        occupied.action_post()
        original = self._create_payment(
            "70707070",
            extra_values={"write_off_line_vals": []},
        )
        original.write({"state": "draft"})
        original.move_id.action_post()
        old_key = original.bank_reference_key

        original.write({"state": "draft"})
        self.assertEqual(original.bank_reference_key, old_key)

        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            original.write({"memo": "71717171"})
        self.assertEqual(original.memo, "70707070")
        self.assertEqual(original.bank_reference_key, old_key)

        with self.assertRaisesRegex(ValidationError, "exactamente 8 caracteres"):
            original.write({"memo": "short"})
        self.assertEqual(original.memo, "70707070")
        self.assertEqual(original.bank_reference_key, old_key)

        original.write({"memo": "72727272"})
        self.assertNotEqual(original.bank_reference_key, old_key)

        replacement = self._create_payment("70707070")
        replacement.action_post()
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_linked_move_reassignment_synchronizes_reservation(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        carrier = self._create_payment(
            "73737373",
            extra_values={"write_off_line_vals": []},
        )
        carrier.write({"state": "draft"})
        carrier.move_id.action_post()
        target = self._create_payment("74747474")
        self.assertFalse(target.move_id)
        self.assertFalse(target.bank_reference_key)

        target.write({"move_id": carrier.move_id.id})
        self.assertTrue(target.bank_reference_key)

        target.write({"move_id": False})
        self.assertFalse(target.bank_reference_key)

    def test_database_reservation_key_is_unique(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment("87654321")
        duplicate = self._create_payment("87654321")

        original._reserve_bank_reference_keys()
        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            duplicate._reserve_bank_reference_keys()

        self.assertTrue(original.bank_reference_key)
        self.assertFalse(duplicate.bank_reference_key)

    def test_sequential_duplicate_is_blocked_and_original_stays_posted(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment("11223344")
        duplicate = self._create_payment("11223344")

        original.action_post()
        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            duplicate.action_post()

        self.assertIn(original.state, {"in_process", "paid"})
        self.assertEqual(duplicate.state, "draft")

    def test_same_reference_in_another_bank_journal_is_allowed(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        second_journal = (
            self.env["account.journal"]
            .with_context(install_mode=True)
            .create(
                {
                    "name": "Second Bank Reference Test",
                    "code": "BRF2",
                    "type": "bank",
                    "company_id": self.company.id,
                    "ref_length_required": 8,
                }
            )
        )
        first = self._create_payment("55667788")
        second = self._create_payment("55667788", journal=second_journal)

        first.action_post()
        second.action_post()

        self.assertIn(first.state, {"in_process", "paid"})
        self.assertIn(second.state, {"in_process", "paid"})

    def test_canceled_payment_releases_reference(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment("99887766")
        replacement = self._create_payment("99887766")

        original.action_post()
        original.action_cancel()
        replacement.action_post()

        self.assertFalse(original.bank_reference_key)
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_canceled_payment_action_post_does_not_reserve(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        canceled = self._create_payment("99886655")
        replacement = self._create_payment("99886655")

        canceled.action_post()
        canceled.action_cancel()
        canceled.action_post()

        self.assertEqual(canceled.state, "canceled")
        self.assertFalse(canceled.bank_reference_key)
        replacement.action_post()
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_processed_memo_change_revalidates_and_updates_reservation(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment("12121212")
        occupied = self._create_payment("34343434")

        original.action_post()
        occupied.action_post()
        original_key = original.bank_reference_key
        self.assertTrue(original_key)

        with self.assertRaisesRegex(ValidationError, "administrada internamente"):
            original.bank_reference_key = False
        self.assertEqual(original.bank_reference_key, original_key)

        with self.assertRaisesRegex(ValidationError, "administrada internamente"):
            original.with_context(l10n_ve_ref_bank_sync=True).write(
                {"bank_reference_key": False}
            )
        self.assertEqual(original.bank_reference_key, original_key)

        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            original.memo = "34343434"
        self.assertEqual(original.memo, "12121212")
        self.assertEqual(original.bank_reference_key, original_key)

        with self.assertRaisesRegex(ValidationError, "8 caracteres"):
            original.memo = "short"
        self.assertEqual(original.memo, "12121212")
        self.assertEqual(original.bank_reference_key, original_key)

        original.memo = "56565656"
        self.assertNotEqual(original.bank_reference_key, original_key)

        replacement = self._create_payment("12121212")
        replacement.action_post()
        self.assertIn(replacement.state, {"in_process", "paid"})

    def test_direct_processed_state_transition_reserves_reference(self):
        self.company.ref_required = True
        self.bank_journal.ref_length_required = 8
        original = self._create_payment("78787878")
        duplicate = self._create_payment("78787878")

        original.write({"state": "in_process"})
        self.assertTrue(original.bank_reference_key)

        with self.assertRaisesRegex(ValidationError, "misma referencia"):
            duplicate.write({"state": "in_process"})

        self.assertEqual(duplicate.state, "draft")
        self.assertFalse(duplicate.bank_reference_key)
