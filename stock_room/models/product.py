from odoo import models, fields, api

class StockroomProduct(models.Model):
    _name = "stockroom.product"
    _description = "Stockroom Product"

    outlet_id = fields.Many2one(
        "stockroom.outlet",
        string="Outlet",
        required=True,
        help="Which outlet this product belongs to"
    )

    name = fields.Char(
        string="Product Name",
        required=True,
        help="Name of the product (e.g., Milk, Bread, Chicken Wings)"
    )

    brand = fields.Char(
        string="Brand",
        help="Brand of the product (e.g., Maple Leaf, Nestle)"
    )

    location_id = fields.Many2one(
        "stockroom.location",
        string="Location",
        required=True,
        help="Where this product is stored in the stock room"
    )

    uom = fields.Selection(
        [
            ('unit', 'Unit'),
            ('kg', 'Kilogram'),
            ('litre', 'Litre'),
            ('pack', 'Pack'),
            ('box', 'Box'),
        ],
        string="Unit of Measure",
        required=True,
        default="unit",
        help="How this product is measured"
    )

    reorder_level = fields.Integer(
        string="Reorder Level",
        default=0,
        help="Minimum quantity before reordering is needed"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, this product will be hidden without deleting it."
    )
