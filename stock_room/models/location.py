from odoo import models, fields, api

class StockroomLocation(models.Model):
    _name = "stockroom.location"
    _description = "Stockroom Location"

    name = fields.Char(
        string="Location Name",
        required=True,
        help="Name of the location (e.g., Freezer 1, Grill Shelf)"
    )
    type = fields.Selection(
        [
            ('freezer1', 'Freezer 1'),
            ('freezer2', 'Freezer 2'),
            ('subway', 'Subway'),
            ('starbucks', 'Starbucks'),
            ('pop', 'Pop'),
        ],
        string="Type",
        required=True,
        help="section in the stock room"
    )
    description = fields.Text(
        string="Description",
        help="Additional details about this storage location"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, this location will be hidden without deleting it."
    )


