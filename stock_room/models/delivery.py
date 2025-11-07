# stock_room/models/delivery.py
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockroomDelivery(models.Model):
    _name = "stockroom.delivery"
    _description = "Stockroom Delivery"

    date_received = fields.Date(
        string="Date Received",
        required=True,
        default=fields.Date.context_today,
        help="Date when the delivery was received"
    )
    vendor_id = fields.Many2one(
        "stockroom.vendor",
        string="Vendor",
        required=True,
        help="Vendor who supplied this delivery"
    )
    reference = fields.Char(string="Reference", help="Invoice number or delivery note reference")
    note = fields.Text(string="Notes", help="Additional details about this delivery")
    line_ids = fields.One2many("stockroom.delivery.line", "delivery_id", string="Delivery Lines")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')],
        string='Status', default='draft', required=True, tracking=True
    )

    # open confirm wizard (review page) for this delivery
    def action_open_confirm_wizard(self):
        self.ensure_one()
        wizard = self.env['stockroom.delivery.confirm.wizard'].create({'delivery_id': self.id})
        # populate wizard lines from delivery lines
        wizard._populate_lines()
        return {
            'name': 'Confirm Delivery',
            'type': 'ir.actions.act_window',
            'res_model': 'stockroom.delivery.confirm.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # open cancel wizard
    def action_open_cancel_wizard(self):
        self.ensure_one()
        wizard = self.env['stockroom.delivery.cancel.wizard'].create({'delivery_id': self.id})
        return {
            'name': 'Cancel Delivery',
            'type': 'ir.actions.act_window',
            'res_model': 'stockroom.delivery.cancel.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # Prevent editing a confirmed delivery (you can adjust allowed fields)
    def write(self, vals):
        for rec in self:
            if rec.state == 'confirmed':
                # If anything other than non-business UI-only fields is changing, block it
                raise ValidationError("Confirmed deliveries cannot be edited. Create a reverse/correction delivery instead.")
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'confirmed':
                raise ValidationError("Confirmed deliveries cannot be deleted. Cancel or reverse them instead.")
        return super().unlink()


class StockroomDeliveryLine(models.Model):
    _name = "stockroom.delivery.line"
    _description = "Stockroom Delivery Line"

    product_id = fields.Many2one("stockroom.product", string="Product", required=True)
    outlet_id = fields.Many2one("stockroom.outlet", string="Outlet", required=True)
    location_id = fields.Many2one("stockroom.location", string="Storage Location", required=True)
    delivery_id = fields.Many2one("stockroom.delivery", string="Delivery", required=True, ondelete="cascade")
    quantity = fields.Float(string="Quantity", required=True)
    expiry_date = fields.Date(string="Expiry Date")

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            # fill UI and default values from product
            self.outlet_id = self.product_id.outlet_id.id
            self.location_id = self.product_id.location_id.id

    # block creation on confirmed parent (defensive)
    @api.model_create_multi
    def create(self, vals_list):
        # If the parent delivery is confirmed, prevent adding lines
        for vals in vals_list:
            delivery_id = vals.get('delivery_id')
            if delivery_id:
                delivery = self.env['stockroom.delivery'].browse(delivery_id)
                if delivery and delivery.state == 'confirmed':
                    raise ValidationError("Cannot add lines to a confirmed delivery.")
        # do normal creation; inventory update happens only at delivery confirm
        return super().create(vals_list)

    def write(self, vals):
        # block edits if parent confirmed
        for rec in self:
            if rec.delivery_id.state == 'confirmed':
                raise ValidationError("Cannot modify lines of a confirmed delivery.")
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.delivery_id.state == 'confirmed':
                raise ValidationError("Cannot delete lines of a confirmed delivery.")
        return super().unlink()


# --- Confirm Wizard (transient) ---
class StockroomDeliveryConfirmWizard(models.TransientModel):
    _name = "stockroom.delivery.confirm.wizard"
    _description = "Confirm Delivery Wizard"

    delivery_id = fields.Many2one('stockroom.delivery', string='Delivery', required=True)
    line_ids = fields.One2many('stockroom.delivery.confirm.wizard.line', 'wizard_id', string='Lines')

    def _populate_lines(self):
        """Fill the transient wizard lines from the delivery (for user review)."""
        self.line_ids.unlink()  # clear if any
        lines = []
        for dl in self.delivery_id.line_ids:
            lines.append({
                'wizard_id': self.id,
                'product_name': dl.product_id.name,
                'product_id': dl.product_id.id,
                'outlet_id': dl.outlet_id.id,
                'location_id': dl.location_id.id,
                'quantity': dl.quantity,
                'expiry_date': dl.expiry_date,
                'delivery_line_id': dl.id,
            })
        if lines:
            self.env['stockroom.delivery.confirm.wizard.line'].create(lines)
        # reload self lines
        self.invalidate_recordset()

    def action_confirm(self):
        """Apply the delivery to inventory: create/merge batches and mark delivery confirmed."""
        self.ensure_one()
        delivery = self.delivery_id
        if delivery.state != 'draft':
            raise ValidationError("Only draft deliveries can be confirmed.")
        # Use the real delivery lines to update inventory (fresh values)
        for dl in delivery.line_ids:
            self.env['stockroom.inventory'].add_stock(
                product=dl.product_id,
                outlet=dl.outlet_id,
                location=dl.location_id,
                quantity=dl.quantity,
                expiry_date=dl.expiry_date,
                delivery_line=dl
            )
        delivery.state = 'confirmed'
        return {'type': 'ir.actions.act_window_close'}


class StockroomDeliveryConfirmWizardLine(models.TransientModel):
    _name = "stockroom.delivery.confirm.wizard.line"
    _description = "Confirm Delivery Wizard Line"

    wizard_id = fields.Many2one('stockroom.delivery.confirm.wizard', ondelete='cascade')
    delivery_line_id = fields.Many2one('stockroom.delivery.line', string='Delivery Line')
    product_id = fields.Many2one('stockroom.product', string='Product')
    product_name = fields.Char(string='Product Name')
    outlet_id = fields.Many2one('stockroom.outlet', string='Outlet')
    location_id = fields.Many2one('stockroom.location', string='Location')
    quantity = fields.Float(string='Quantity')
    expiry_date = fields.Date(string='Expiry')


# --- Cancel Wizard (simple confirmation) ---
class StockroomDeliveryCancelWizard(models.TransientModel):
    _name = "stockroom.delivery.cancel.wizard"
    _description = "Cancel Delivery Wizard"

    delivery_id = fields.Many2one('stockroom.delivery', string='Delivery', required=True)

    def action_cancel(self):
        self.ensure_one()
        delivery = self.delivery_id
        if delivery.state == 'confirmed':
            # if you want to allow cancelling confirmed deliveries, you'd need reverse logic.
            raise ValidationError("Cannot cancel a confirmed delivery. Use reverse workflow.")
        delivery.state = 'cancelled'
        return {'type': 'ir.actions.act_window_close'}
