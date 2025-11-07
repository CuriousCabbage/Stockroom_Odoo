from odoo import models, fields, api

class StockroomOutlet(models.Model):
    _name = "stockroom.outlet"
    _description = "Stockroom Outlet"

    name = fields.Char(
        string="Outlet Name",
        required=True,
        help="Name of the outlet (e.g., Subway, Starbucks, Grill, Pizza Pizza)"
    )
    description = fields.Text(
        string="Description",
        help="Optional details about this outlet"
    )
