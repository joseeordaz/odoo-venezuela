from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestActionConfirmServiceProducts(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.service_product = self.env['product.product'].create({
            'name': 'Service Product',
            'type': 'service',
            'list_price': 50.0,
        })
        self.storable_product = self.env['product.product'].create({
            'name': 'Storable Product',
            'type': 'consu',
            'list_price': 100.0,
        })

    def test_confirm_service_only(self):
        """T6: SO con solo producto servicio → confirm exitoso, 0 pickings."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.service_product.id,
                'product_uom_qty': 1,
                'price_unit': 50.0,
            })],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(len(sale_order.picking_ids), 0)

    def test_confirm_mixed_products(self):
        """T7: SO con 1 servicio + 1 storable → confirm exitoso, pickings solo para storable."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.service_product.id,
                    'product_uom_qty': 1,
                    'price_unit': 50.0,
                }),
                (0, 0, {
                    'product_id': self.storable_product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(len(sale_order.picking_ids), 1)

    def test_confirm_storable_with_split(self):
        """T8: SO con 5 storable, limit=2 → 3 pickings (2+2+1)."""
        self.company.limit_product_qty_out = 2
        products = self.env['product.product'].create([
            {'name': f'Storable Product {i}', 'type': 'consu', 'list_price': 10.0}
            for i in range(5)
        ])
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': p.id,
                    'product_uom_qty': 1,
                    'price_unit': 10.0,
                })
                for p in products
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(len(sale_order.picking_ids), 3)

    def test_confirm_limit_zero(self):
        """T9: SO con storable, limit=0 → 1 picking sin dividir."""
        self.company.limit_product_qty_out = 0
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.storable_product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(len(sale_order.picking_ids), 1)

    def test_confirm_splits_each_existing_picking_independently(self):
        """Multiple pickings keep their own moves when the limit is applied."""
        products = self.env['product.product'].create([
            {'name': f'Storable Product {i}', 'type': 'consu', 'list_price': 10.0}
            for i in range(3)
        ])
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'price_unit': 10.0,
                })
                for product in products[:2]
            ],
        })
        sale_order.action_confirm()
        first_picking = sale_order.picking_ids
        second_picking = first_picking.copy({'move_ids': []})
        self.env['stock.move'].create({
            'product_id': products[2].id,
            'product_uom_qty': 1,
            'product_uom': products[2].uom_id.id,
            'location_id': second_picking.location_id.id,
            'location_dest_id': second_picking.location_dest_id.id,
            'picking_id': second_picking.id,
            'sale_line_id': sale_order.order_line[0].id,
        })
        self.assertEqual(len(sale_order.picking_ids), 2)

        self.company.limit_product_qty_out = 1
        sale_order._split_pickings_by_product_limit()

        self.assertEqual(len(sale_order.picking_ids), 3)
        self.assertEqual(sorted(sale_order.picking_ids.mapped('move_ids').mapped('product_id').ids), sorted(products.ids))
        self.assertTrue(all(len(picking.move_ids) == 1 for picking in sale_order.picking_ids))
