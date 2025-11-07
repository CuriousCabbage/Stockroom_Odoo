from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockroomUsage(models.Model):
    _name = "stockroom.usage"
    _description = "Stockroom Usage"

    outlet_id = fields.Many2one("stockroom.outlet", string="Outlet", required=True)
    date = fields.Date(string="Usage Date", default=fields.Date.today, required=True)
    line_ids = fields.One2many("stockroom.usage.line", "usage_id", string="Usage Lines")


class StockroomUsageLine(models.Model):
    _name = "stockroom.usage.line"
    _description = "Usage Lines"

    usage_id = fields.Many2one("stockroom.usage", string="Usage", required=True, ondelete="cascade")

    product_id = fields.Many2one(
        "stockroom.product",
        string="Product",
        required=True,
        domain="[('outlet_id', '=', parent.outlet_id)]",
    )
    inventory_id = fields.Many2one(
        "stockroom.inventory",
        string="Batch",
        required=True,
        domain="[('product_id', '=', product_id)]",  # only batches of selected product
    )

    available_qty = fields.Float(
        string="Available Qty",
        compute="_compute_available_qty",
        store=False,
    )

    quantity_used = fields.Float(string="Quantity Used", required=True, default=0.0)

    @api.depends("inventory_id")
    def _compute_available_qty(self):
        for rec in self:
            rec.available_qty = rec.inventory_id.quantity if rec.inventory_id else 0.0

    # --- Inline warning when user enters too much ---
    @api.onchange("quantity_used", "inventory_id")
    def _onchange_quantity_or_inventory(self):
        for rec in self:
            if rec.inventory_id and rec.quantity_used:
                available = rec.inventory_id.quantity or 0.0
                if rec.quantity_used > available:
                    return {
                        "warning": {
                            "title": "Quantity exceeds available",
                            "message": f"Batch has {available}, but you entered {rec.quantity_used}.",
                        }
                    }

    # --- Decrement stock when a line is created ---
    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.inventory_id and line.quantity_used > 0:
                available = line.inventory_id.quantity or 0.0
                if line.quantity_used > available:
                    raise ValidationError(
                        f"Insufficient stock for {line.product_id.name}: "
                        f"requested {line.quantity_used}, available {available}."
                    )
                line.inventory_id.remove_stock(line.quantity_used)
        return lines
