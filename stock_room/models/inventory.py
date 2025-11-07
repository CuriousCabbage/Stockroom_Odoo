from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class StockroomInventory(models.Model):
    _name = "stockroom.inventory"
    _description = "Current Stock in Stockroom"
    _order = "expiry_date asc, id asc"
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    _rec_name = "display_name"


    product_id = fields.Many2one(
        "stockroom.product",
        string="Product",
        required=True,
        help="Product in stock"
    )

    outlet_id = fields.Many2one(
        "stockroom.outlet",
        string="Outlet",
        required=True,
        help="Outlet this stock belongs to"
    )

    location_id = fields.Many2one(
        "stockroom.location",
        string="Storage Location",
        help="Where the stock is stored"
    )

    quantity = fields.Float(
        string="Quantity Available",
        default=0.0,
        help="Quantity available in stock (in smallest unit, e.g., packets, liters)"
    )


    expiry_date = fields.Date(
        string="Expiry Date",
        index=True,
        help="Expiry date of this batch (if applicable)"
    )

    delivery_line_id = fields.Many2one(
        "stockroom.delivery.line",
        string="Delivery Source",
        help="Reference to delivery line from which this stock came"
    )

    reorder_level = fields.Integer(
        related="product_id.reorder_level",
        string="Reorder Level",
        store=True,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, this inventory line will be archived instead of deleted"
    )

    @api.depends('product_id', 'expiry_date', 'quantity', 'location_id', 'outlet_id')
    def _compute_display_name(self):
        for rec in self:
            parts = []
            # product name first
            if rec.product_id and rec.product_id.name:
                parts.append(rec.product_id.name)
            # expiry date, convert safely to date object then format
            if rec.expiry_date:
                try:
                    # fields.Date.to_date handles string or date
                    exp_date = fields.Date.to_date(rec.expiry_date)
                    parts.append("Exp: " + exp_date.strftime('%b %d, %Y'))
                except Exception:
                    # fallback to raw value if formatting fails
                    parts.append("Exp: " + str(rec.expiry_date))
            # location/outlet optional
            if rec.location_id and rec.location_id.name:
                parts.append(str(rec.location_id.name))
            if rec.outlet_id and rec.outlet_id.name:
                parts.append(str(rec.outlet_id.name))
            # quantity last
            qty = rec.quantity or 0.0
            # show int when whole number
            qty_label = str(int(qty)) if float(qty).is_integer() else str(qty)
            parts.append("Qty: " + qty_label)
            rec.display_name = " · ".join(parts) if parts else f"batch {rec.id}"

    def name_get(self):
        result = []
        for record in self:
            if record.expiry_date:
                name = f"Expiring {record.expiry_date.strftime('%b %d, %Y')}"
            else:
                name = record.product_id.name or "Batch"
            result.append((record.id, name))
        return result

    @api.model
    def add_stock(self, product, outlet, location, quantity, expiry_date=None, delivery_line=None):
        """Add stock from a delivery"""
        line = self.search([
            ('product_id', '=', product.id),
            ('outlet_id', '=', outlet.id),
            ('location_id', '=', location.id),
            ('expiry_date', '=', expiry_date),
            ('active', '=', True)
        ], limit=1)
        if line:
            line.write({'quantity': (line.quantity or 0.0) + float(quantity)})
        else:
            self.create({
                'product_id': product.id,
                'outlet_id': outlet.id,
                'location_id': location.id,
                'quantity': quantity,
                'expiry_date': expiry_date,
                'delivery_line_id': delivery_line.id if delivery_line else False,
            })

    def remove_stock(self, quantity):
        """Decrement quantity safely from this batch."""
        for record in self:
            available = record.quantity or 0.0
            if quantity > available:
                raise ValidationError("Cannot remove more than available stock.")
            record.write({"quantity": available - quantity})