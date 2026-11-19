def seed_base_rate(env, rate=380.0):
    """Seed one old rate for the company's foreign currency.

    Fork HOLA: l10n_ve_rate.compute_rate takes the latest rate on or before the
    document date, so a single 2020 rate covers every date these tests use
    (on a fresh database there is no rate at all and documents fail to create).
    """
    company = env.company.root_id or env.company
    env["res.currency.rate"].create({
        "currency_id": company.foreign_currency_id.id,
        "company_id": company.id,
        "name": "2020-01-01",
        "rate": 1 / rate,
        "inverse_company_rate": rate,
    })
