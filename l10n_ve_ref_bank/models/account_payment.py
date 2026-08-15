import hashlib

from psycopg2.errors import UniqueViolation

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bank_reference_key = fields.Char(copy=False, readonly=True)

    _bank_reference_key_unique = models.Constraint(
        "UNIQUE(bank_reference_key)",
        "Bank references must be unique within each configured bank journal.",
    )
    _bank_reference_key_fields = {"company_id", "journal_id", "memo", "move_id"}

    @api.model_create_multi
    def create(self, values_list):
        if "default_bank_reference_key" in self.env.context or any(
            "bank_reference_key" in values for values in values_list
        ):
            raise ValidationError(
                _("La clave de referencia bancaria es administrada internamente.")
            )
        with self.env.cr.savepoint():
            payments = super().create(values_list)
            payments._synchronize_bank_reference_keys()
            return payments

    def action_post(self):
        payments_to_post = self.filtered(
            lambda payment: payment.state in {False, "draft", "in_process"}
            or payment.outstanding_account_id.account_type == "asset_cash"
        )
        payments_to_post.validate_bank_payment_reference_length()
        with self.env.cr.savepoint():
            payments_to_post.validate_bank_payment_reference_unique()
            payments_to_post._reserve_bank_reference_keys()
            return super().action_post()

    def write(self, values):
        if "bank_reference_key" in values:
            raise ValidationError(
                _("La clave de referencia bancaria es administrada internamente.")
            )
        requires_key_sync = bool(self._bank_reference_key_fields & values.keys())
        requires_key_sync = requires_key_sync or "state" in values
        if not requires_key_sync:
            return super().write(values)
        with self.env.cr.savepoint():
            result = super().write(values)
            self._synchronize_bank_reference_keys()
            return result

    def _write_bank_reference_key(self, value):
        return super(AccountPayment, self).write({"bank_reference_key": value})

    def _requires_bank_reference_validation(self):
        self.ensure_one()
        return (
            self.company_id.ref_required
            and self.journal_id.type == "bank"
            and self.journal_id.ref_length_required > 0
        )

    def validate_bank_payment_reference_length(self):
        for payment in self:
            if not payment._requires_bank_reference_validation():
                continue
            reference = payment.memo or ""
            required_length = payment.journal_id.ref_length_required
            if len(reference) != required_length:
                raise ValidationError(
                    _(
                        "La referencia bancaria del campo Memo debe contener "
                        "exactamente %(length)s caracteres.",
                        length=required_length,
                    )
                )

    def _get_bank_reference_key(self):
        self.ensure_one()
        value = "\0".join(
            [str(self.company_id.id), str(self.journal_id.id), self.memo or ""]
        )
        return hashlib.sha256(value.encode()).hexdigest()

    def _synchronize_bank_reference_keys(self):
        reservable = self.filtered(
            lambda payment: (
                payment.state in {"in_process", "paid"}
                or (
                    payment.state == "draft"
                    and payment.move_id.state == "posted"
                )
            )
            and payment._requires_bank_reference_validation()
        )
        released = (self - reservable).filtered("bank_reference_key")
        if released:
            released._write_bank_reference_key(False)
        if reservable:
            reservable.validate_bank_payment_reference_length()
            reservable.validate_bank_payment_reference_unique()
            needs_reservation = reservable.filtered(
                lambda payment: payment.bank_reference_key
                != payment._get_bank_reference_key()
            )
            needs_reservation._reserve_bank_reference_keys()

    def _reserve_bank_reference_keys(self):
        for payment in self:
            if not payment._requires_bank_reference_validation():
                continue
            try:
                with mute_logger("odoo.sql_db"):
                    with self.env.cr.savepoint():
                        payment._write_bank_reference_key(
                            payment._get_bank_reference_key()
                        )
            except UniqueViolation as exc:
                if (
                    exc.diag.constraint_name
                    != "account_payment_bank_reference_key_unique"
                ):
                    raise
                raise ValidationError(
                    _(
                        "Ya existe un pago procesado en este diario bancario "
                        "con la misma referencia del campo Memo."
                    )
                ) from exc

    def validate_bank_payment_reference_unique(self):
        seen = set()
        for payment in self:
            if not payment._requires_bank_reference_validation():
                continue
            key = (payment.company_id.id, payment.journal_id.id, payment.memo)
            if key in seen:
                raise ValidationError(
                    _(
                        "Ya existe otro pago en este lote con la misma referencia "
                        "del campo Memo para este diario bancario."
                    )
                )
            seen.add(key)
            duplicate = self.search_count(
                [
                    ("id", "!=", payment.id),
                    ("memo", "=", payment.memo),
                    ("company_id", "=", payment.company_id.id),
                    ("journal_id", "=", payment.journal_id.id),
                    ("state", "in", ["in_process", "paid"]),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    _(
                        "Ya existe un pago procesado en este diario bancario "
                        "con la misma referencia del campo Memo."
                    )
                )
