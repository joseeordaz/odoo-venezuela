# HOLA ↔ Binaural 19.0 reconciliation matrix

Retrieved from GitHub: 2026-08-21 11:04–11:08 -05:00. This is a source-level planning baseline only. It does not authorize implementation, merge, deployment, module installation, fiscal configuration, or production mutation.

## Answer

**Verified fact.** After fresh fetches, `origin/hola/main` is `58474ac6329d1d42cbdc5555c03a02c44cba3aac`, `upstream/19.0` is `57dafc3300aedf0985d159981adf2cc42a24a36a`, and their merge-base is `5bad3d00ad0877659e56ca477063ca14dc2c2c33`. The side-specific history is 11 HOLA-only commits and 331 upstream-only commits. Upstream's 331 comprise 90 merge commits, 239 tree-changing non-merge commits, and 2 non-merge commits with no tree change. The final trees differ in 393 files under exactly 18 top-level paths.

**Decision.** The explicit first safe batch is closed as a planning/source/required-gate unit, criterion by criterion:

1. **`l10n_ve_contact`: accepted with explained residuals.** HOLA intentionally keeps name locking opt-in, checks the company of the related transaction, performs the policy lookup with `sudo()`, and permits same-name writes (`origin/hola/main:l10n_ve_contact/models/res_partner.py:60-78,174-186`). Upstream defaults the flag on and uses the active company inside a constraint (`upstream/19.0:l10n_ve_contact/models/res_company.py:21-24`; `upstream/19.0:l10n_ve_contact/models/res_partner.py:60-90`). The three-file residual remains a HOLA requirement.
2. **`l10n_ve_sale`: accepted with explained residuals.** HOLA preserves each delivery boundary when splitting and invokes one shared helper after confirmation (`origin/hola/main:l10n_ve_sale/models/sale_order.py:600-627,629-677`). Upstream treats all `sale.picking_ids` as one recordset and consumes only the first `read()` result (`upstream/19.0:l10n_ve_sale/models/sale_order.py:647-671`). HOLA also retains production-clone-safe currency fixtures from `60417435a7a17067751b3be0b423b8ce70f55843`. The five-file residual is accepted; import-order-only test noise remains unnecessary but harmless.
3. **`l10n_ve_stock`: accepted with explained residuals.** HOLA omits upstream's unreachable quantity override (upstream sets `location = False` and returns immediately), keeps a Community-safe manifest, invalidates computed physical addresses when warehouse addresses change, preserves native reports, and retains isolated/real-model fixtures (`origin/hola/main:l10n_ve_stock/__manifest__.py:11-16`; `origin/hola/main:l10n_ve_stock/models/stock_picking.py:159-170`; `upstream/19.0:l10n_ve_stock/models/product_product.py:70-77`; commits `3432950dca9e289a1345e37d71a4220a16c4eab5` and `59661a88eeca4365ef10a2cf5538e7fbac1ef843`). The eight-file residual is intentional Community/quality behavior.
4. **Community dependency gate: accepted for exactly the three named roots.** PR [#13](https://github.com/joseeordaz/odoo-venezuela/pull/13) merged as `9c889eed3011f3a633f08eae747e29a6714df565`. The validator names only contact, sale, and stock, traverses repository-local manifest dependencies, rejects every named banned dependency, and fails closed on missing local `l10n_ve_*` dependencies (`origin/hola/main:scripts/validate_repo.py:11-20,23-31,57-82`). Focused regressions cover direct, transitive, optional, cyclic, malformed, and missing-local cases (`origin/hola/main:scripts/test_validate_repo.py:23-91`). Exact merged-SHA push run [32494942502](https://github.com/joseeordaz/odoo-venezuela/actions/runs/32494942502) passed. This is source/CI evidence; CT123 and CT125 were not accessed for this gate.
5. **Install-time VEF mutation: removed without replacement and accepted.** PR [#14](https://github.com/joseeordaz/odoo-venezuela/pull/14) merged as `58474ac6329d1d42cbdc5555c03a02c44cba3aac`. HOLA no longer defines or registers `set_main_company_currency_to_vef`, no longer loads `data/res_company_data.xml`, and deleted that XML (`origin/hola/main:l10n_ve_accountant/__init__.py:1-43`; `origin/hola/main:l10n_ve_accountant/__manifest__.py:21-58`; `origin/hola/main:scripts/test_accountant_install_hook.py:12-30`). Exact merged-SHA push run [32497216770](https://github.com/joseeordaz/odoo-venezuela/actions/runs/32497216770) passed. The program-card landing record is the only CT125 evidence used here: it reports a SHA-verified production clone preserving both companies as VES before/after upgrade, a fresh install preserving USD without VEF, focused regression 1/1 OK, no Odoo error/registry failures, candidate first in `addons_path`, cleanup complete, and CT123 active/read-only. This report did not access either container.

**Inference.** Closing this batch means that all residuals and required gates for the explicit contact/sale/stock roots are accounted for. It does not establish a full HOLA deployable-root authority, runtime equivalence for every dependent capability, or fiscal acceptance outside this narrow batch.

## Reproducible Git accounting

Commands were run after fresh remote fetches:

```text
git fetch --prune origin hola/main
git fetch --prune upstream 19.0
git rev-parse origin/hola/main upstream/19.0
git merge-base origin/hola/main upstream/19.0
git rev-list --left-right --count origin/hola/main...upstream/19.0
git rev-list --count --merges origin/hola/main..upstream/19.0
git diff --name-only origin/hola/main upstream/19.0
```

History grouping is deterministic and single-valued:

1. More than one parent → `merge/history`.
2. A non-merge → sorted unique top-level paths from `git diff-tree --no-commit-id --name-only -r <sha>`, joined with `+`.
3. A non-merge with no tree change → `history/no-tree-change`.

Appendices A and B map every side-only commit exactly once. Twelve-character IDs are unambiguous in each current set.

### Side-specific group totals

| Side/group | Count |
|---|---:|
| HOLA `.github+scripts` | 1 |
| HOLA `l10n_ve_accountant` | 1 |
| HOLA `l10n_ve_accountant+scripts` | 1 |
| HOLA `l10n_ve_contact` | 1 |
| HOLA `l10n_ve_payment_extension` | 1 |
| HOLA `l10n_ve_pos_igtf` | 1 |
| HOLA `l10n_ve_sale` | 2 |
| HOLA `l10n_ve_stock` | 2 |
| HOLA `scripts` | 1 |
| **HOLA total** | **11** |
| Upstream `merge/history` | 90 |
| Upstream `history/no-tree-change` | 2 |
| Upstream `l10n_ve_pos` | 104 |
| Upstream `l10n_ve_accountant` | 25 |
| Upstream `l10n_ve_invoice` | 17 |
| Upstream `l10n_ve_payment_extension` | 14 |
| Upstream `l10n_ve_crm` | 14 |
| Upstream `l10n_ve_crm_foreign_currency` | 13 |
| Upstream `l10n_ve_igtf` | 10 |
| Upstream `l10n_ve_pos_mf` | 7 |
| Upstream `l10n_ve_pos_igtf` | 6 |
| Upstream `l10n_ve_stock` | 4 |
| Upstream `l10n_ve_mf_base` | 3 |
| Upstream `l10n_ve_sale` | 3 |
| Upstream `l10n_ve_contact` | 2 |
| Upstream `l10n_ve_accountant+l10n_ve_igtf+l10n_ve_invoice` | 2 |
| Upstream `l10n_ve_accountant+l10n_ve_invoice` | 2 |
| Upstream all other single/cross-path groups | 13 |
| **Upstream total** | **331** |

The 20 commits added since the prior upstream snapshot are 6 merges and 14 tree-changing non-merges. Seven `l10n_ve_payment_extension` commits are an attempted retention-rate fix plus its complete revert; the later merged final tree instead adds invoice-date/rate alignment under `7dc7660ea8b2...` and `f7d317be1360...`. The remaining new final behavior concerns credit-note rates, indexed/non-indexed payment conversion, partial-payment/write-off rounding, invoice labels/tests, and retention payment date/rate alignment. History entries remain in Appendix B even when later reverted; matrix claims use the final tree.

## HOLA-only capabilities and current final-tree state

| Commit | Capability | Current verdict |
|---|---|---|
| `c31247dc2368f2ca03c25366d265aba9ce869e82` | Community accounting base | HOLA has no `account_reports` dependency (`origin/hola/main:l10n_ve_accountant/__manifest__.py:11-20`). The install-time VEF mutations that remained at the prior snapshot are now removed by `58474ac6329...`; the wider accountant behavior remains unreconciled. |
| `5437294bdd3ac36046578e9c96adf13aae25437d` | Contact name immutability | Accepted with the opt-in, transaction-company-aware residual above. |
| `8208fcd88a51677cb6e625a16a74feaf849cb4b6` | Sale Odoo 19 service/picking and VAT fixes | Accepted; HOLA's per-picking splitter is safer than current upstream final state. |
| `3432950dca9e289a1345e37d71a4220a16c4eab5` | Stock Odoo 19/physical-address/report adaptation | Accepted; residuals are Community compatibility and stronger cache/test behavior. |
| `db16f90a22bc0b3277de7b5db354c19499057d19` | Validator CI baseline | Accepted baseline source validator; dependency enforcement is now supplied by `9c889eed3011...`. |
| `59661a88eeca4365ef10a2cf5538e7fbac1ef843` | Stock fixture isolation | Accepted and intentionally divergent from ambient upstream fixtures. |
| `60417435a7a17067751b3be0b423b8ce70f55843` | Sale fixture isolation | Accepted and intentionally divergent from tests that mutate main-company currency/rates. |
| `ab4902633d315c87aae9487452ce9578f412bb2f` | POS session when IGTF is disabled | Accepted independent HOLA guard (`origin/hola/main:l10n_ve_pos_igtf/models/pos_session.py:15-24`); the rest of POS-IGTF remains unreconciled. |
| `0106121d29fbce82494087da39204315ead917d4` | Canonical retention UT XML ID | Accepted HOLA requirement. Upstream HEAD still uses a literal database ID; draft PR [#1186](https://github.com/binaural-dev/odoo-venezuela/pull/1186) remains context only. |
| `9c889eed3011f3a633f08eae747e29a6714df565` | Three-root Community dependency gate | Accepted for exactly contact, sale, and stock; merged PR #13 and exact merged-SHA CI passed. |
| `58474ac6329d1d42cbdc5555c03a02c44cba3aac` | Preserve company currency on accountant install | Accepted removal without replacement of both HOLA VEF mutation paths; merged PR #14, exact merged-SHA CI, and the program-card CT125 landing record passed. |

## Current final-state matrix

`git diff origin/hola/main upstream/19.0` reports these 18 top-level paths. Counts are differing files, not behavioral equivalence claims.

| Top-level path (files) | Upstream intent/current final state | HOLA state and residual | Classification | Evidence | Next gate |
|---|---|---|---|---|---|
| `.github` (1) | No HOLA branch validator workflow. | HOLA pins actions, grants read-only contents, and runs the repository validator. | HOLA requirement | `origin/hola/main:.github/workflows/validate.yml:3-23`; `db16f90a22bc...` | Accepted for the explicit first batch; change root policy only with a new authority. |
| `l10n_ve_account_mf` (23) | New TFHKA Web Serial accounting/invoicing integration; depends on accountant and stock-account. | Absent; adopting it would reach upstream `account_reports`. | not-yet-evaluated | `upstream/19.0:l10n_ve_account_mf/__manifest__.py:11-18`; `4a0f0b36d313...` | Fiscal-machine scope, Community-safe closure, browser/hardware review, then CT125. |
| `l10n_ve_accountant` (31) | Adds accounting/rate/payment/credit-note behavior, but directly requires `account_reports` and still changes the main company to VEF by SQL. Current moved-head additions include invoice-date conversion for indexed/non-indexed payments and credit-note rate inheritance. | Community manifest retained; both install-time VEF paths removed without replacement. HOLA is still behind many accounting behaviors. | Community compatibility / security fix / not-yet-evaluated | Upstream manifest `:11-23,61-62`; upstream `__init__.py:44-60`; upstream `models/account_payment.py:73-150`; HOLA manifest `:11-20,21-58`; `58474ac6329...` | Reconcile one accountant capability at a time with fiscal owner, focused tests, independent review, CI, and CT125. Never restore VEF mutation. |
| `l10n_ve_contact` (3) | Defaults name lock on and uses active-company constraint. | Opt-in, transaction-company-aware policy retained. | HOLA requirement | HOLA `models/res_partner.py:60-78,174-186`; upstream `models/res_company.py:21-24`; upstream `models/res_partner.py:60-90` | **Accepted; no repair card.** |
| `l10n_ve_crm_foreign_currency` (18) | CRM alternate-currency fields, reports, migration hook, and tests; directly depends on accountant. | Entire module absent. | not-yet-evaluated | `upstream/19.0:l10n_ve_crm_foreign_currency/__manifest__.py:1-16`; `250b8e9e1216...` | Requires a named deployable root and Community accountant adapter first. |
| `l10n_ve_igtf` (16) | Advances, IGTF/indexed-payment conversion, rounding, reports, configuration, and tests; current moved-head fixes conversion date and partial-payment/write-off behavior. | Older final state; no fiscal or behavioral equivalence is claimed. | not-yet-evaluated | `upstream/19.0:l10n_ve_igtf/models/account_payment.py:147-203,234-240`; `d269ef1bc2c5...`; `c7438bdb212e...` | Fiscal owner chooses one payment contract; focused tests and CT125 required. |
| `l10n_ve_invoice` (12) | PDF guard filters to posted invoices/non-draft sales. HTML attempts the same, but replaces server-selected `report.model` and `docids` with serializable `data.context.active_model/active_ids`; a hostile mismatched `active_model` skips both guards and falls through with original `docids`. Current tests cover only honest `active_model='account.move'`. | Lacks the print guard and other upstream behavior. | security fix / not-yet-evaluated | `upstream/19.0:l10n_ve_invoice/models/ir_actions_report.py:8-28,30-55`; tests `:124-144`, especially honest context `:132-135` | **Do not accept upstream HEAD as a boundary.** Implement the hardened capability below. |
| `l10n_ve_iot_mf` (2) | Still directly depends on Enterprise `iot`. | Older optional legacy IoT implementation; cannot enter a Community closure. | temporary adaptation | Both refs `l10n_ve_iot_mf/__manifest__.py:14-20`; direct banned-edge trace below | Exclude; consider Web Serial only after fiscal/hardware decision. |
| `l10n_ve_mf_base` (9) | New Community-compatible Web Serial transport/protocol/TFHKA driver with unit tests; depends only on `web`. | Entire module absent. | not-yet-evaluated | `upstream/19.0:l10n_ve_mf_base/__manifest__.py:1-23`; `dff918656b8f...` | Hardware/protocol/browser-security review and physical printer test. |
| `l10n_ve_payment_extension` (17) | Retention-domain/amount/report behavior plus current retention payment move date/rate alignment. An earlier seven-commit exchange-rate attempt in the moved range was reverted and is not final behavior. | Canonical UT reference retained; other retention changes remain unreconciled. | HOLA requirement / not-yet-evaluated | Upstream `models/account_payment.py:87-111`; tests `test_retention_payment_move_date.py:12-18,99-148`; `7dc7660ea8b2...`; `f7d317be1360...`; HOLA `data/fees_retention_data.xml:4-64` | Keep canonical UT; evaluate each remaining retention rule only with fiscal confirmation and CT125. |
| `l10n_ve_pos` (132) | Large Odoo 19 POS migration across data loading, foreign payments, accounting, refunds, permissions, reports, UI, and tests. | Far behind; equivalence cannot be inferred from history volume. | not-yet-evaluated | `upstream/19.0:l10n_ve_pos/__manifest__.py:11-48`; Appendix B | One POS contract per card, each with focused tests, independent review, and CT125. |
| `l10n_ve_pos_igtf` (40) | Odoo 19 POS-IGTF backend/frontend/receipt/test migration. | Only the independent disabled-IGTF session guard is accepted; remainder unreconciled. | HOLA requirement / not-yet-evaluated | Upstream manifest `:9-27`; HOLA `models/pos_session.py:15-24`; `ab4902633d31...` | Preserve guard; defer migration slices to fiscal/POS cards with CT125. |
| `l10n_ve_pos_mf` (66) | Replaces legacy `pos_iot`/IoT Box coupling with Web Serial via `l10n_ve_mf_base`. | Still directly depends on banned `pos_iot` and transitively on `iot`; optional/non-deployable under current Community policy. | temporary adaptation | HOLA manifest `:11-16`; upstream manifest `:10-17`; upstream module spec `:1-16` | Exclude now; replacement requires fiscal/hardware scope and CT125. |
| `l10n_ve_sale` (5) | Fixes service confirmation/VAT but retains recordset-wide splitter and ambient fixtures. | Accepted behavior plus per-picking split and isolated fixtures. | HOLA requirement | HOLA `models/sale_order.py:600-677`; upstream `:647-671`; `60417435a7a1...` | **Accepted; remove import-order noise only on next sale touch.** |
| `l10n_ve_stock` (8) | Physical addresses/report hiding plus unreachable quantity override, optional stock-barcode API, and ambient fixtures. | Community manifest, native reports, address invalidation, and isolated/real fixtures retained. | Community compatibility / HOLA requirement | HOLA manifest `:11-16`; HOLA `models/stock_picking.py:159-170`; upstream `models/product_product.py:70-77` | **Accepted; no repair card.** |
| `l10n_ve_stock_account` (4) | Adds dispatch-guide physical addresses and account-move/view changes; transitively reaches `account_reports`. | Older final state; no fiscal/report equivalence claimed. | not-yet-evaluated | `upstream/19.0:l10n_ve_stock_account/__manifest__.py:11-19,39-46`; `52770c0a74b3...` | Community accountant closure, fiscal confirmation, and CT125. |
| `module-specs` (3) | Documents the three Web Serial fiscal modules. | Absent because runtime modules are absent. | temporary adaptation | `upstream/19.0:module-specs/openspec/specs/l10n_ve_mf_base/spec.md:1-23`; `261f0912ba1b...` | Import only with an accepted implementation capability. |
| `scripts` (3) | No equivalent Community/dependency validator. | Baseline validator plus three-root dependency traversal/regressions and VEF-install regression. | HOLA requirement | `origin/hola/main:scripts/validate_repo.py:11-82`; `scripts/test_validate_repo.py:9-95`; `scripts/test_accountant_install_hook.py:12-30`; PRs #13/#14 | Accepted for current roots; no full-root inference. |

## Enterprise dependency trace

The banned names are `account_reports`, `account_accountant`, `currency_rate_live`, `iot`, `pos_iot`, `web_enterprise`, and `hr_payroll`. Recomputed manifest edges at both current refs reproduce the prior shortest paths. The moved ranges changed manifest versions/data/hooks but no `depends` edge, so the closure itself is unchanged.

### HOLA direct paths

- `l10n_binaural -> account_accountant` (`origin/hola/main:l10n_binaural/__manifest__.py:6`).
- `l10n_ve_currency_rate_live -> currency_rate_live` (`origin/hola/main:l10n_ve_currency_rate_live/__manifest__.py:9`).
- `l10n_ve_fiscal_lock_days -> account_accountant` (`origin/hola/main:l10n_ve_fiscal_lock_days/__manifest__.py:9-13`).
- `l10n_ve_iot_mf -> iot` (`origin/hola/main:l10n_ve_iot_mf/__manifest__.py:14-20`).
- `l10n_ve_pos_mf -> pos_iot` (`origin/hola/main:l10n_ve_pos_mf/__manifest__.py:11-16`).

### HOLA transitive paths

- `l10n_ve_invoice_digital -> l10n_ve_iot_mf -> iot`.
- `l10n_ve_pos_mf -> l10n_ve_iot_mf -> iot`.

No HOLA manifest contains `account_reports`, `web_enterprise`, or `hr_payroll`; optional repository modules still have the direct banned paths above.

### Upstream direct paths

- `l10n_binaural -> account_accountant` (`upstream/19.0:l10n_binaural/__manifest__.py:6`).
- `l10n_ve_accountant -> account_reports` (`upstream/19.0:l10n_ve_accountant/__manifest__.py:11-23`).
- `l10n_ve_currency_rate_live -> currency_rate_live` (`upstream/19.0:l10n_ve_currency_rate_live/__manifest__.py:9`).
- `l10n_ve_fiscal_lock_days -> account_accountant` (`upstream/19.0:l10n_ve_fiscal_lock_days/__manifest__.py:9-13`).
- `l10n_ve_iot_mf -> iot` (`upstream/19.0:l10n_ve_iot_mf/__manifest__.py:14-20`).

No upstream manifest contains `pos_iot`, `web_enterprise`, or `hr_payroll` at this ref.

### Upstream transitive paths

Every path in this first group terminates in `l10n_ve_accountant -> account_reports`:

- Direct dependents: `l10n_ve_account_mf`, `l10n_ve_auditlog`, `l10n_ve_crm_foreign_currency`, `l10n_ve_donation`, `l10n_ve_fiscal_lock_days`, `l10n_ve_igtf`, `l10n_ve_invoice`, `l10n_ve_payment_extension`, `l10n_ve_pos`, `l10n_ve_stock_account`, `l10n_ve_suggested_amount`, and `l10n_ve_tax_payer`.
- `l10n_ve_invoice_digital -> l10n_ve_igtf -> l10n_ve_accountant -> account_reports`.
- `l10n_ve_invoice_loyalty -> l10n_ve_invoice -> l10n_ve_accountant -> account_reports`.
- `l10n_ve_iot_mf -> l10n_ve_invoice -> l10n_ve_accountant -> account_reports`.
- `l10n_ve_pos_igtf -> l10n_ve_pos -> l10n_ve_accountant -> account_reports`.
- `l10n_ve_pos_mf -> l10n_ve_pos -> l10n_ve_accountant -> account_reports`.
- `l10n_ve_ref_bank -> l10n_ve_invoice -> l10n_ve_accountant -> account_reports`.
- `l10n_ve_sale -> l10n_ve_invoice -> l10n_ve_accountant -> account_reports`.
- `l10n_ve_price_list -> l10n_ve_sale -> l10n_ve_invoice -> l10n_ve_accountant -> account_reports`.
- Additional IoT path: `l10n_ve_invoice_digital -> l10n_ve_iot_mf -> iot`.

### Deployable-set authority

**Verified repository evidence.** `README.md:47-117` is descriptive and mixes Community-safe modules with modules that reach banned dependencies. `scripts/validate_repo.py` now establishes only `DEPLOYABLE_MODULES = ("l10n_ve_contact", "l10n_ve_sale", "l10n_ve_stock")` (`origin/hola/main:scripts/validate_repo.py:11`). No tracked authority names later roots.

**Current explicit authority.** The first-batch roots are exactly contact, sale, and stock. Their HOLA manifest closure has no banned path, and the merged validator enforces that fact. This does not authorize any other repository module for deployment.

**Material unknown.** The full HOLA deployable set for later batches remains a human decision: name each later root or add a reviewed tracked root authority.

## Open upstream PR context, excluded from HEAD behavior

At retrieval GitHub reported 82 open PRs: 15 target `19.0`, 15 target `maintenance-19.0`, 32 target `maintenance-17.0`, 15 target `17.0`, and 5 target other bases. The 15 direct `19.0` PRs below are open context and are not part of `57dafc3300aedf0985d159981adf2cc42a24a36a`.

| PR | Head | Snapshot state | Title |
|---|---|---|---|
| [#1192](https://github.com/binaural-dev/odoo-venezuela/pull/1192) | `9b07e3d60891` | open | accountant purchase-journal uniqueness |
| [#1186](https://github.com/binaural-dev/odoo-venezuela/pull/1186) | `f96a926413f1` | draft/open | stable retention UT reference |
| [#1168](https://github.com/binaural-dev/odoo-venezuela/pull/1168) | `98f698ee46ce` | open | invoice-digital migration |
| [#1161](https://github.com/binaural-dev/odoo-venezuela/pull/1161) | `9900c2c4a6dc` | open | POS kiosk foreign total |
| [#1152](https://github.com/binaural-dev/odoo-venezuela/pull/1152) | `abdbde029555` | open | configurable IGTF debit-note flow |
| [#1145](https://github.com/binaural-dev/odoo-venezuela/pull/1145) | `a21e14b272da` | open | missing foreign-currency singleton guard |
| [#1104](https://github.com/binaural-dev/odoo-venezuela/pull/1104) | `fcd1a250a463` | open | sale rate on pricelist change |
| [#1097](https://github.com/binaural-dev/odoo-venezuela/pull/1097) | `b0f833a4b18b` | open | hide sending account on payment receipt |
| [#959](https://github.com/binaural-dev/odoo-venezuela/pull/959) | `dd35bbe75815` | open | sale company rounding |
| [#901](https://github.com/binaural-dev/odoo-venezuela/pull/901) | `8eed277852db` | open | stock-account/donation dependency reversal |
| [#832](https://github.com/binaural-dev/odoo-venezuela/pull/832) | `f7c61372727f` | open | Python 3.11 nested f-string compatibility |
| [#758](https://github.com/binaural-dev/odoo-venezuela/pull/758) | `21219c3fe65c` | open | purchase order line update |
| [#736](https://github.com/binaural-dev/odoo-venezuela/pull/736) | `f7cd4d8ab396` | open | staging branch proposal |
| [#710](https://github.com/binaural-dev/odoo-venezuela/pull/710) | `2d626f155041` | open | stock-account fix |
| [#662](https://github.com/binaural-dev/odoo-venezuela/pull/662) | `bf9a9d249ace` | open | older POS 19 migration proposal |

## Exactly one next independent capability

**Recommendation: implement a hardened `l10n_ve_invoice` draft-document print boundary using upstream's intent, not upstream's current trust boundary.**

Why this one: the capability is finite, security-relevant, independent of the unresolved full deployable set and fiscal-rate interpretation, and requires no production mutation or broad refactor. Upstream HEAD is explicitly **not accepted**: its HTML path trusts caller-controlled context and can skip both guards.

Finite coder acceptance criteria:

1. Reconcile only the minimum `ir.actions.report` model/import/test/translation or manifest-version files required for this capability; no unrelated invoice behavior.
2. Derive the protected model only from server-authoritative `report.model` and the records only from server-authoritative method `docids`/`res_ids`. `data.context.active_model` and `active_ids` must not decide whether the guard applies or substitute another record set.
3. For `account.move`, PDF and HTML print only posted records; draft/cancelled-only selections raise; mixed selections pass only posted IDs downstream.
4. For `sale.order`, PDF and HTML reject draft-only selections; mixed selections pass only non-draft IDs downstream.
5. Focused regressions must cover absent context, honest context, hostile mismatched `active_model`, substituted `active_ids`, mixed valid/invalid IDs, and the exact IDs/model reaching the downstream super call.
6. Preserve HOLA Community dependencies and VES. Run focused Odoo tests, repository validator, independent review, exact-SHA CI, and isolated CT125 accounting/fiscal validation before merge. Never mutate CT123.

## Contradictions, limitations, and material unknowns

- **Source conflict:** upstream code/comments/tests describe an HTML bypass fix, but control flow proves a remaining bypass: lines 35-36 accept serializable model/IDs and line 55 falls through if `active_model` is hostile. The code path outranks the intent label.
- This research card performed no Odoo runtime, CT125, CT123, database, or fiscal-printer execution. The PR #14 CT125 result is quoted only from the exact program-card landing record.
- Contact/sale/stock acceptance is final-source/history/manifest acceptance with their stated prior gates; it is not a claim that every dependent fiscal flow is runtime-equivalent.
- The full deployable-root set beyond the explicit three roots is unknown.
- Fiscal meaning and operational acceptance remain unresolved for accountant behavior beyond VEF removal, invoice beyond the print boundary, IGTF, retentions, stock-account, POS, and fiscal-machine capabilities.
- Hardware behavior of Web Serial/TFHKA modules remains unknown.
- Open PR state is a retrieval-time snapshot and must be refreshed before any later decision.

## Reusable lesson proposal

Trigger: a fork reconciliation or security review finds a guard that reads protected model/record identity from caller-serializable context.

Evidence: upstream HTML reporting starts from `report.model`/`docids`, overwrites both from `data.context`, and existing tests cover only honest context; a mismatched model skips both state guards. The same reconciliation also contains merge/revert history that differs from final behavior.

Minimum procedure: freeze refs; separately reconcile history and final tree; identify server-authoritative model and record identifiers at every guard; test absent, honest, mismatched, substituted, and mixed-ID contexts; inspect the final fall-through/super call; never let client context select whether a guard applies.

Limits: static control-flow establishes the bypass path but not every Odoo transport/ACL precondition. Focused runtime regression and the risk-appropriate CT125 gate remain required. Top-level Git grouping is an audit index, not behavioral equivalence.

Scope: Odoo report/render guards and other RPC entry points during long-diverged fork reconciliation.

Verification: appendix sets equal `git rev-list` with no duplicates; matrix paths equal top-level `git diff`; a focused hostile-context test must prove downstream receives only server-authorized model IDs.

## Appendix A — HOLA-only commit map (11/11)

```text
.github+scripts: db16f90a22bc
l10n_ve_accountant: c31247dc2368
l10n_ve_accountant+scripts: 58474ac6329d
l10n_ve_contact: 5437294bdd3a
l10n_ve_payment_extension: 0106121d29fb
l10n_ve_pos_igtf: ab4902633d31
l10n_ve_sale: 60417435a7a1 8208fcd88a51
l10n_ve_stock: 3432950dca9e 59661a88eeca
scripts: 9c889eed3011
```

## Appendix B — upstream-only commit map (331/331)

Each 12-character SHA appears exactly once. Subjects remain available through `git show <sha>`; omission keeps the audit index compact.

```text
history/no-tree-change: 789a0fe0c1eb 7e16c67a19c2
l10n_ve_account_mf: 4a0f0b36d313
l10n_ve_accountant: 07f87479433f 09f4c7824bd7 0cdc74346c88 20a7611ca103 212d13998490 4ae01cfe9685 54813a1c02f2 5bfc8d351898 6274f06c43e8 6d518388c22e 74a750accb85 76c4d6829351 7d98c461f17f 83d8d380cf90 9a6515e1064e 9e1832e51572 9fcf13a955fe a407aba87eeb a7922a0eb736 ab24f92e5bbd cda40dbcd8ee d028ff31d983 e3e9ac55ae00 e506dff3550a f09ba91d6a41
l10n_ve_accountant+l10n_ve_igtf: 6ed4acc0d0df
l10n_ve_accountant+l10n_ve_igtf+l10n_ve_invoice: 9ef03545d9c5 d269ef1bc2c5
l10n_ve_accountant+l10n_ve_invoice: 4e39460da288 8672e4ad8662
l10n_ve_accountant+l10n_ve_invoice+l10n_ve_iot_mf: 81fd7a1031b8
l10n_ve_accountant+l10n_ve_payment_extension: bc416498fd3f
l10n_ve_contact: ce23a665540d d7118d25a653
l10n_ve_crm: 334b13609af3 36ca1f91d57a 421c1d696fa1 4be8373eebd8 53ff41d640bc 543f3629ccd2 557ca6f320d8 6e37ee55243c 707346d3fe47 7c2c89ded824 83bcf4aaf2f3 aacad502f9c0 b799ddc99cd9 c2ee99866483
l10n_ve_crm+l10n_ve_crm_foreign_currency: 250b8e9e1216
l10n_ve_crm_foreign_currency: 1d07847b8c17 256ec6745411 3156bebf5ea5 38b96fa8558f 65645c6f2c98 8292e30adf69 b14215a6d67e bfc66a28585d d03907e9a337 d275d757334a d78cc030536f e1864b4acad0 f66a3bcdbda5
l10n_ve_igtf: 22057ab8e91e 295934b211a1 4798841ddefa 7c95a4073e8f 97307e911904 c7438bdb212e d7bcafa626a8 f16062c05cf0 f3d9ec6558b8 f7abecccd63a
l10n_ve_igtf+l10n_ve_invoice+l10n_ve_iot_mf+l10n_ve_pos_igtf+l10n_ve_pos_mf: e6f463d4fbd9
l10n_ve_igtf+l10n_ve_invoice+l10n_ve_stock_account: b3f25ca46887
l10n_ve_invoice: 02ca30d8591a 032f12cccb22 0aa8ceac7f5d 1a68c45e7dae 2568f165a5e4 27e1d1707c01 77092283bbcb 78e01d50bdd3 7b1c248e55dc 84e513b11882 899cf68394e1 9588de5f2eed beb7886a942f c276250a27aa ca7d2bd09ac0 ce26aeb7e81d e249a6c6aca1
l10n_ve_invoice+l10n_ve_payment_extension: f7d317be1360
l10n_ve_mf_base: 7ce6f01cbe10 dff918656b8f fcbc0a319d3c
l10n_ve_mf_base+l10n_ve_pos_mf+module-specs: 261f0912ba1b
l10n_ve_payment_extension: 0bf464c178b6 12582355b814 245583ac50ee 39b9e68a8f32 411173f3f470 46f67467b3e4 4c21c1c9e205 7b10b754fa62 7dc7660ea8b2 842453e0ea88 ad27689f521b c73bed54f51e df1db1ee684d ea5427e79951
l10n_ve_pos: 00be18fcc77b 06a9e6e40af5 0b6c9afb5c79 0c2ae2fe2f2c 0dfbb7013fb0 0e47d3332237 0f3fcdea0626 13729e536d1d 176982633486 19b87f23cae2 19d547dddd81 1eb5226ba0ed 1ee3277c1d68 1f251813430c 225a8094dd64 24a320041794 2b6c958aa8d1 2f785e0f6896 2fbf9d79b786 34e34aea5d70 3bb9876622a5 3d0683f61644 440d9f7fe2a7 464e098f6b4e 4a17693b39cb 4c8f04a828fd 4e818d47f975 543889d16695 557401085cd0 55b1f2701e5d 577284e59ea2 581dbd9cd8f5 5c86f77d3c03 5ca94532f3a9 5cbef8c1bebd 5e477e2caee0 6550fe04c937 694e671d0db3 6ccd28da9aae 6deb21710a6d 6df2acdc2d50 6ed3af6a936f 70752aa284da 718ad789934f 71b9676611d8 7369bf229727 74e0b68c131f 776fc22643ca 78d45e01c520 7a8725cc60a1 7ca0e6b7dc0c 7dc54954d005 8078f0315aa7 80be32c3fad3 810089e20ec3 8768f65d7130 8845a925ef0c 88c9d34c12e4 8c6e5a9fdda7 8f7fe08e06b5 906a394fbe5b 93c2eb97385c 942a5740c757 9482da2ffc0b 978cbbe2200f 9d82687b0e3d a133e08ac270 a4131fe8b16b a9f460d044cc ac3c0eac49ac b16e12592652 b62fd00379e6 b9975725d305 b9e3abb1357a ba222638ac4b bc675ee3715e bd6fee7e9896 be7fd6b53d1b c0554149e671 c393dc09cbda c3ad074c6ca8 c6b8cff90330 c8d6820fdadc c91297970af8 c93eb6005e1b cab9942894da cc8e92216a7e cedead22b614 d731aeb8e2c4 d75110c711d8 da7c63ba9033 de1cbf86a73a e3e24d331a0c e4e84d8e6baf e90cbcf0f247 e9c57b489c69 ed5c523eb5a7 ef3a6c40eb1c f1c7664bf1c0 f94086697ed5 f9bb592d97d0 fe9673548f06 ffa955016a35 fff5a1172299
l10n_ve_pos+l10n_ve_pos_igtf: 49305585688e a2c40c39ff28
l10n_ve_pos+l10n_ve_pos_mf: c08bf20cd349
l10n_ve_pos_igtf: 102206aa3687 4c665a47f7ad bcec34e55c42 dbb7d67f4c5a f2e44f433fb7 f6ab3ef591d8
l10n_ve_pos_mf: 3c50a2dd2c72 7927a85771ea 8df494f3f770 991dfc862561 9abd345ac339 a5b83276db68 a7976bf9f83a
l10n_ve_sale: 006193edee2d 12758bee32ed 90d4281a7c08
l10n_ve_stock: 5dc6eb7ea5d4 839e3bb11fd4 aaabb3553a8b ede635c5e8a1
l10n_ve_stock+l10n_ve_stock_account: 52770c0a74b3
merge/history: 0099ef83c267 024223eb43f1 03995f5131c4 06268f0ebcae 067e2efbd01b 06a720a0337c 124e9fe02fd9 136bfc3cf678 18cfa4182560 1de7e367c37b 2086ff03e88b 2c8fde84cdab 2fb89dd8c39e 3025dd035e40 32f899c91981 33388427652e 3396d349db7e 34fdc072dab7 37910d5700e0 37e55e72b35c 389e80b04b6c 3918044fe776 3a83846e6978 3d19f38b79a9 408b4c23a913 4182735faff7 426e45e91f1e 4282b752135a 49e684859d64 4c5d6f642277 4ed0ba31f57e 50679fe60ce3 5227f6ceb8bf 5322a907890b 53912bf22252 55d324d7bb47 5604c305a567 57dafc3300ae 5a08879c8362 5d228d91b703 6485d77a6291 660ffd72689c 6bfd8014a0bd 75052f8e3327 7972221984d4 7bb95de32d1d 7ca34a961801 7ec7a2effe21 82266ee31be7 82f5ad93dd5f 8ab63832b404 8ffc42b48040 9a7912b827c9 9a8f2f53607e 9d506fb77e90 9e6f8b0a4443 a21a7e1edbbc a425a59e2b56 a61ac11b8dc4 ae8ddad49071 aedd2632b67b b1cd7b403089 b1f58037d36d b56c646856b9 b814c890f22a bb8bd983efd3 c2a218eabf37 c4bf4863631e c7061fee00dc cbfc1392ec54 d3530ca716a1 d527a4246964 d6f278c1b144 d84c6ea9af96 da18c93c60ad dfac7359011b e65b1b04bfd4 e96729e63868 e9f3a1e21b52 ea2b47a99c50 ee33b1c1ffae f0776bd9fd4c f142cdfffe92 f6644e286a7b f7204e8e0ba5 f9a4d8a147b3 faaabc51a786 fd31cd9a07a9 fd345bda6a20 fdc2621d6fbe
```
