from odoo import fields


def ensure_usd_rate(env, company):
    """Invoices compute foreign_rate on create; a fresh database has no USD rate at all."""
    usd = env.ref("base.USD")
    if not env["res.currency.rate"].search_count(
        [("currency_id", "=", usd.id), ("company_id", "=", company.id)]
    ):
        env["res.currency.rate"].create({
            "name": fields.Date.today(),
            "currency_id": usd.id,
            "company_id": company.id,
            "inverse_company_rate": 1.0,
        })
