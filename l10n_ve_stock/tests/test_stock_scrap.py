from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged("post_install", "-at_install", "l10n_ve_stock")
class TestStockScrapActionValidate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        self.product = self.env["product.product"].create({
            "name": "Scrap Test Prod",
            "type": "consu",
            "is_storable": True,
        })
        self.env["stock.quant"].create({
            "product_id": self.product.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "quantity": 50,
        })

    def create_production(self, quantity=10):
        if "mrp.production" not in self.env.registry.models:
            self.skipTest("mrp is not installed")
        production = self.env["mrp.production"].create({
            "product_id": self.product.id,
            "product_qty": quantity,
            "product_uom_id": self.product.uom_id.id,
            "location_src_id": self.warehouse.lot_stock_id.id,
            "location_dest_id": self.warehouse.lot_stock_id.id,
        })
        finished_move = production.move_finished_ids.filtered(
            lambda move: move.product_id == production.product_id
        )
        self.assertTrue(finished_move)
        finished_move.quantity = quantity
        finished_move.picked = True
        self.assertEqual(production.qty_produced, quantity)
        return production

    def create_production_scrap(self, production, quantity, state=None):
        scrap = self.env["stock.scrap"].create({
            "product_id": self.product.id,
            "scrap_qty": quantity,
            "location_id": self.warehouse.lot_stock_id.id,
            "production_id": production.id,
        })
        if state:
            scrap.state = state
        return scrap

    def test_action_validate_allow_scrap_more_than_available(self):
        self.env.company.allow_scrap_more_than_available = True
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = False
        scrap = self.env["stock.scrap"].create({
            "product_id": self.product.id,
            "scrap_qty": 5,
            "location_id": self.warehouse.lot_stock_id.id,
        })
        scrap.action_validate()
        self.assertEqual(scrap.state, "done")

    def test_action_validate_not_allow_scrap_check_available(self):
        self.env.company.allow_scrap_more_than_available = False
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = False
        scrap = self.env["stock.scrap"].create({
            "product_id": self.product.id,
            "scrap_qty": 5,
            "location_id": self.warehouse.lot_stock_id.id,
        })
        scrap.action_validate()
        self.assertEqual(scrap.state, "done")

    def test_action_validate_not_allow_scrap_insufficient_qty(self):
        self.env.company.allow_scrap_more_than_available = False
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = False
        scrap = self.env["stock.scrap"].create({
            "product_id": self.product.id,
            "scrap_qty": 99999,
            "location_id": self.warehouse.lot_stock_id.id,
        })
        with self.assertRaises(ValidationError):
            scrap.action_validate()

    def test_action_validate_not_allow_manufactured_no_production(self):
        self.env.company.allow_scrap_more_than_available = True
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = True
        scrap = self.env["stock.scrap"].create({
            "product_id": self.product.id,
            "scrap_qty": 5,
            "location_id": self.warehouse.lot_stock_id.id,
        })
        scrap.action_validate()
        self.assertEqual(scrap.state, "done")

    def test_action_validate_production_no_scraps(self):
        self.env.company.allow_scrap_more_than_available = True
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = True
        production = self.create_production()
        scrap = self.create_production_scrap(production, 5)
        scrap.action_validate()
        self.assertEqual(scrap.state, "done")

    def test_action_validate_production_exceeds_qty_produced(self):
        self.env.company.allow_scrap_more_than_available = True
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = True
        production = self.create_production()
        scrap = self.create_production_scrap(production, 15)
        with self.assertRaises(ValidationError):
            scrap.action_validate()

    def test_action_validate_production_sum_exceeds(self):
        self.env.company.allow_scrap_more_than_available = True
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = True
        production = self.create_production()
        self.create_production_scrap(production, 5, state="done")
        scrap = self.create_production_scrap(production, 6)
        with self.assertRaises(ValidationError):
            scrap.action_validate()

    def test_action_validate_production_within_limit(self):
        self.env.company.allow_scrap_more_than_available = True
        self.env.company.not_allow_scrap_more_than_what_was_manufactured = True
        production = self.create_production()
        self.create_production_scrap(production, 5, state="done")
        scrap = self.create_production_scrap(production, 3)
        scrap.action_validate()
        self.assertEqual(scrap.state, "done")


@tagged("post_install", "-at_install", "l10n_ve_stock")
class TestStockScrapChangeWeight(TransactionCase):
    def test_change_weight_field(self):
        self.env.company.change_weight = True
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        picking = self.env["stock.picking"].create({
            "picking_type_id": warehouse.out_type_id.id,
            "location_id": warehouse.lot_stock_id.id,
            "location_dest_id": self.env.ref("stock.stock_location_customers").id,
        })
        self.assertTrue(picking.change_weight)
