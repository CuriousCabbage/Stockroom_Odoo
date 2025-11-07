from odoo import models, fields

class StockroomVendor(models.Model):
    _name = "stockroom.vendor"
    _description = "Stockroom Vendor"

    name = fields.Char(
        string="Vendor Name",
        required=True,
        help="Name of the supplier/vendor"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, this vendor will be archived but past deliveries remain."
    )
