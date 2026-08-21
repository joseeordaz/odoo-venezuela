from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    _order = "priority_location asc"

    product_tag_ids = fields.Many2many(related="product_id.product_tag_ids")

    priority_location = fields.Integer(
        string="Priority", related="product_id.priority_location", store=True
    )
