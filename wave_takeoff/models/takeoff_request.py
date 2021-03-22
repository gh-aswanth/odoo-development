# -*- coding: utf-8 -*-

from datetime import timedelta
from collections import defaultdict
from itertools import groupby

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class TakeoffRequest(models.Model):
    _name = 'takeoff.request'
    _inherit = ['mail.thread']
    _description = 'Wave Takeoff Request'

    @api.model
    def _default_warehouse_id(self):
        company = self.env.company.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    name = fields.Char(
        default="New",
        readonly=True
    )
    order_id = fields.Many2one(
        'sale.order',
        'Sale Order',
        required=True,
        domain=[('analytic_account_id', '!=', False)]
    )
    analytic_account_id = fields.Many2one(
        related="order_id.analytic_account_id",
        readonly=True,
        store=True
    )
    request_line_ids = fields.One2many(
        'takeoff.request.line',
        'request_id'
    )
    request_template_id = fields.Many2one(
        'sale.order.template',
        domain=[('is_takeoff', '=', True)]
    )
    inventory_users_ids = fields.Many2many(
        'res.users',
        'takeoff_request_res_users_rel',
        'takeoff_request_id',
        'user_id',
        string="Inventory Users",
        track_visibility='onchange'
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        default=_default_warehouse_id
    )
    user_id = fields.Many2one(
        'res.users',
        string='Requested Person',
        default=lambda self: self.env.uid
    )
    process_date = fields.Datetime(
        default=fields.Datetime.now(),
        string='Request date',
        readonly=True)
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
        string='Currency',
        readonly=True
    )
    commitment_date = fields.Datetime(
        'Delivery Date',
        copy=False,
        help="This is the delivery date promised to the customer. "
           "If set, the delivery order will be scheduled based on "
           "this date rather than product lead times."
    )
    expected_date = fields.Datetime(
        help="Delivery date you can promise to the customer, computed from the minimum lead time of "
             "the order lines in case of Service products. In case of shipping, the shipping policy of "
             "the order will be taken into account to either use the minimum or maximum lead time of "
             "the order lines.",
        compute='_compute_expected_date',
        store=False
    )
    picking_policy = fields.Selection([
        ('direct', 'As soon as possible'),
        ('one', 'When all products are ready')],
        string='Shipping Policy',
        required=True,
        readonly=True,
        default='direct',
        help="If you deliver all products at once, the delivery order will be scheduled based on the greatest "
            "product lead time. Otherwise, it will be based on the shortest."
    )
    qty_fully_available = fields.Many2one(
        'stock.location.route',
        string='Quantity Fully Available'
    )
    qty_partially_available = fields.Many2one(
        'stock.location.route',
        string='Quantity partially Available'
    )
    qty_not_available = fields.Many2one(
        'stock.location.route',
        string='Quantity Not Available'
    )
    group_id = fields.Many2one('procurement.group')
    picking_ids = fields.One2many(
        'stock.picking',
        'takeoff_id'
    )
    purchase_ids = fields.One2many(
        'purchase.order',
        'takeoff_id'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed')
    ], default='draft')
    ctg_total = fields.Html(compute="_compute_takeoff_total")
    takeoff_total = fields.Float(compute="_compute_takeoff_total")

    @api.depends('request_line_ids.price_subtotal')
    def _compute_takeoff_total(self):
        for rec in self:
            r = ''
            total = 0
            for line, grp in groupby(rec.request_line_ids, key=lambda k: k.budgetary_position_id):
                line_total = sum([i.price_subtotal for i in grp])
                if line and line_total:
                    r += '''
                    <tr><td><b>%s</b></td><td> :</td><td>&nbsp;&nbsp;&nbsp;&nbsp;$&nbsp;%s</td></tr>
                    ''' % (line.name, float_round(line_total, precision_digits=2))
                    total += line_total
            rec.ctg_total = '''<table>%s</table>''' % r
            rec.takeoff_total = total


    @api.depends('request_line_ids.customer_lead', 'picking_policy')
    def _compute_expected_date(self):
        """ For service and consumable, we only take the min dates. This method is extended in sale_stock to
            take the picking_policy of SO into account.
        """
        for order in self:
            dates_list = []
            for line in order.request_line_ids.filtered(lambda x: not x.display_type):
                dt = line._expected_date()
                dates_list.append(dt)
            if dates_list:
                expected_date = min(dates_list) if order.picking_policy == 'direct' else max(dates_list)
                order.expected_date = fields.Datetime.to_string(expected_date)
            else:
                order.expected_date = False

    @api.onchange('commitment_date')
    def _onchange_commitment_date(self):
        """ Warn if the commitment dates is sooner than the expected date """
        if (self.commitment_date and self.expected_date and self.commitment_date < self.expected_date):
            return {
                'warning': {
                    'title': _('Requested date is too soon.'),
                    'message': _("The delivery date is sooner than the expected date."
                                 "You may be unable to honor the delivery date.")
                }
            }

    def post(self):
        for rec in self:
            if rec.inventory_users_ids:
                values = {
                    'object': rec,
                    'model_description': rec.display_name
                }
                rec.message_post_with_view(
                    'wave_takeoff.takeoff_assigned',
                    values=values,
                    subtype_id=self.env.ref('mail.mt_note').id,
                    email_layout_xmlid='mail.mail_notification_light',
                    subject=_("You are invited to access %s" % rec.display_name),
                    partner_ids=[(6, 0, rec.inventory_users_ids.mapped('partner_id').ids)])
            rec.state = 'requested'

    def _compute_line_data_for_template_change(self, line):
        return {
            'display_type': line.display_type,
            'name': line.name,
        }

    @api.onchange('request_template_id')
    def onchange_request_template_id(self):
        template = self.request_template_id.with_context(lang=self.order_id.partner_id.lang)
        order_lines = []

        self.request_line_ids = [(5, 0, 0)]

        def get_customer_lead(product):
            if product.sale_delay:
                return product.sale_delay
            elif product.product_tmpl_id.sale_delay:
                return product.product_tmpl_id.sale_delay
            else:
                return False

        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            if line.product_id:
                data.update({
                    'product_uom_qty': line.takeoff_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_id.id,
                    'customer_lead': get_customer_lead(line.product_id)
                })
            order_lines.append((0, 0, data))
        self.request_line_ids = order_lines

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('takeoff.request') or 'New'
        record = super(TakeoffRequest, self).create(vals)
        section = False
        for sequence, line in enumerate(record.request_line_ids, 10):
            if line.display_type in ['line_section']:
                section = line.name
            line.write({'section': section, 'sequence': sequence})

        if record.inventory_users_ids:
            record.message_subscribe(partner_ids=record.inventory_users_ids.mapped('partner_id').ids)
        return record

    def write(self, vals):
        res = super(TakeoffRequest, self).write(vals)
        section = False
        for rec in self:
            for sequence, line in enumerate(rec.request_line_ids, 10):
                if line.display_type in ['line_section']:
                    section = line.name
                line.write({'section': section, 'sequence': sequence})
            section = False
            if vals.get('inventory_users_ids'):
                self.message_subscribe(partner_ids=rec.inventory_users_ids.mapped('partner_id').ids)
        return res

    def button_request_lines(self):
        action_id = self.env.ref("wave_takeoff.takeoff_request_line_act_window")
        action_data = action_id.read()[0]
        action_data.update({
            'domain': [('id', 'in', self.request_line_ids.filtered(lambda r: not r.display_type).ids)],
            'context': {
                'search_default_group_by_section': 1 if not self._context.get('takeoff_change') and len(
                    self.request_line_ids) else 0 if self._context.get('takeoff_change') else 1,
                'search_default_group_by_budgetary_position': 1 if self._context.get('takeoff_change') else 0,
                'default_request_id': self.id
            }
        })
        if self._context.get('takeoff_change'):
            changes = self.request_line_ids.filtered(lambda r: r.budgetary_position_id and r.product_uom_qty)
            if changes:
                action_data['domain'] = [('id', 'in', changes.ids)]
        return action_data

    def initiate_request(self):
        changes = self.request_line_ids.filtered(lambda r: r.budgetary_position_id and r.product_uom_qty and not r.mark_as_done)
        changes.auto_set_route()
        wiz = self.env['takeoff.request.validator'].create({
            'takeoff_line_ids': [(6, 0, changes.ids)]
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Routing Summary'),
            'res_model': 'takeoff.request.validator',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new'
        }


TakeoffRequest()


class TakeoffRequestLine(models.Model):
    _name = 'takeoff.request.line'
    _description = 'Wave Takeoff Request Line'
    _order = 'sequence'

    name = fields.Char()
    product_id = fields.Many2one(
        'product.product',
        domain=['|', ('is_takeoff', '=', True), ('categ_id.is_takeoff', '=', True)]
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        domain="[('category_id', '=', product_uom_category_id)]"
    )
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id',
        readonly=True
    )
    request_id = fields.Many2one(
        'takeoff.request',
        auto_join=True,
        ondelete="cascade"
    )
    product_category_id = fields.Many2one(
        related='product_id.categ_id',
        readonly=True
    )
    budgetary_position_id = fields.Many2one(
        related='product_category_id.budgetary_expense_position_id',
        readonly=True,
        store=True
    )
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")],
        default=False, help="Technical field for UX purpose."
    )
    product_uom_qty = fields.Float(string='Quantity')
    sequence = fields.Integer(default=10)
    section = fields.Char()
    route_id = fields.Many2one(
        'stock.location.route',
        string='Route',
        domain=[('takeoff_selectable', '=', True)],
        ondelete='restrict', check_company=True
    )
    currency_id = fields.Many2one(
        related='request_id.currency_id',
        store=True, string='Currency',
        readonly=True
    )
    purchase_price = fields.Float(
        string='Cost',
        digits='Product Price',
        compute='_compute_purchase_price'
    )
    price_subtotal = fields.Monetary(
        compute='_compute_amount',
        string='Subtotal',
        currency_field='currency_id',
        readonly=True,
        store=True
    )
    customer_lead = fields.Float(
        'Lead Time',
        required=True,
        default=0.0,
        help="Number of days between the order confirmation and the shipping of the products to the customer"
    )
    move_ids = fields.One2many(
        'stock.move',
        'takeoff_line_id',
        string='Stock Moves'
    )
    virtual_available_at_date = fields.Float(compute='_compute_qty_at_date')
    scheduled_date = fields.Datetime(compute='_compute_qty_at_date')
    free_qty_today = fields.Float(compute='_compute_qty_at_date')
    qty_available_today = fields.Float(compute='_compute_qty_at_date')
    is_mto = fields.Boolean(compute='_compute_is_mto')
    display_qty_widget = fields.Boolean(compute='_compute_qty_to_deliver')
    qty_to_deliver = fields.Float(compute='_compute_qty_to_deliver')
    qty_delivered = fields.Float(compute='_compute_qty_delivered')
    mark_as_done = fields.Boolean()

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        for line in self:
            qty = 0.0
            for move in line.move_ids:
                if move.location_dest_id.usage != 'customer' or move.state != 'done':
                    continue
                qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
            line.qty_delivered = qty


    @api.depends('product_id', 'product_uom_qty', 'product_uom', 'qty_delivered')
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
            if line.product_id.type == 'product' and line.product_uom and line.qty_to_deliver > 0:
                line.display_qty_widget = True
            else:
                line.display_qty_widget = False

    def auto_set_route(self):
        for line in self:
            if line.virtual_available_at_date >= line.qty_to_deliver:
                line.route_id = line.request_id.qty_fully_available
            elif 0 < line.virtual_available_at_date <= line.qty_to_deliver:
                line.route_id = line.request_id.qty_partially_available
            else:
                line.route_id = line.request_id.qty_not_available

    @api.depends('product_id', 'route_id', 'request_id.warehouse_id', 'product_id.route_ids')
    def _compute_is_mto(self):
        self.is_mto = False
        for line in self:
            product = line.product_id
            product_routes = line.route_id or (product.route_ids + product.categ_id.total_route_ids)
            mto_route = line.request_id.warehouse_id.mto_pull_id.route_id
            if not mto_route:
                try:
                    mto_route = self.env['stock.warehouse']._find_global_route('stock.route_warehouse0_mto',
                                                                               _('Make To Order'))
                except UserError:
                    pass
            if mto_route and mto_route in product_routes:
                line.is_mto = True
            else:
                line.is_mto = False

    @api.depends('product_id', 'request_id.commitment_date', 'request_id.expected_date', 'product_uom_qty', 'product_uom', 'request_id.warehouse_id')
    def _compute_qty_at_date(self):

        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env['takeoff.request.line'])

        for line in self:
            if not line.product_id:
                continue
            warehouse_id = line.request_id.warehouse_id
            if line.request_id.commitment_date:
                date = line.request_id.commitment_date
            else:
                date = line.request_id.expected_date
            grouped_lines[(warehouse_id.id, date)] |= line

        treated = self.browse()
        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            qties_per_product = {
                product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
                line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
                line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
                line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[
                    line.product_id.id]
                if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
                    line.qty_available_today = line.product_id.uom_id. \
                        _compute_quantity(line.qty_available_today, line.product_uom)
                    line.free_qty_today = line.product_id.uom_id. \
                        _compute_quantity(line.free_qty_today, line.product_uom)
                    line.virtual_available_at_date = line.product_id.uom_id. \
                        _compute_quantity(line.virtual_available_at_date, line.product_uom)
                qty_processed_per_product[line.product_id.id] += line.product_uom_qty

            treated |= lines

        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False
        remaining.warehouse_id = False

    @api.depends('product_uom_qty', 'purchase_price')
    def _compute_amount(self):
        for line in self:
            line.update({
                'price_subtotal': line.product_uom_qty * line.purchase_price,
            })

    @api.onchange('route_id')
    def _onchange_route_id(self):
        routes = self.request_id.qty_not_available | self.request_id.qty_partially_available | self.request_id.qty_fully_available
        return {
            'domain': {
                'route_id': [('id', 'in', routes.ids)]
            }
        }

    @api.depends('request_id.order_id', 'product_id.standard_price', 'currency_id', 'product_id.uom_id', 'product_uom')
    def _compute_purchase_price(self):
        for line in self:
            frm_cur = line.currency_id
            to_cur = line.request_id.order_id.pricelist_id.currency_id
            purchase_price = line.product_id.standard_price
            if line.product_uom != line.product_id.uom_id:
                purchase_price = line.product_id.uom_id._compute_price(purchase_price, line.product_uom)
            price = purchase_price
            if to_cur and frm_cur:
                price = frm_cur._convert(
                    purchase_price,
                    to_cur,
                    self.env.user.company_id,
                    fields.Date.today(),
                    round=False
                )
            line.purchase_price = price



    def _expected_date(self):
        self.ensure_one()
        order_date = fields.Datetime.from_string(fields.Datetime.now())
        return order_date + timedelta(days=self.customer_lead or 0.0)

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = {}
        self.ensure_one()
        date_planned = self.scheduled_date
        values.update({
            'group_id': group_id,
            'takeoff_line_id': self.id,
            'date_planned': date_planned,
            'route_ids': self.route_id,
            'warehouse_id': self.request_id.warehouse_id or False,
            'partner_id': self.request_id.order_id.partner_shipping_id.id,
            'company_id': self.request_id.order_id.company_id,
        })
        return values

    def _prepare_procurement_group_vals(self):
        return {
            'name': self.request_id.name,
            'move_type': self.request_id.picking_policy,
            'partner_id': self.request_id.order_id.partner_shipping_id.id,
            'takeoff_id': self.request_id.id
        }
    def _get_procurement_group(self):
        return self.request_id.group_id

    def _action_launch_stock_rule(self):
        procurements = []
        PG = self.env['procurement.group']
        for line in self:
            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.request_id.group_id = group_id
            else:
                updated_vals = {}
                if group_id.partner_id != line.request_id.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.request_id.order_id.partner_shipping_id.id})
                if group_id.move_type != line.request_id.picking_policy:
                    updated_vals.update({'move_type': line.request_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(
                PG.Procurement(
                    line.product_id,
                    product_qty,
                    procurement_uom,
                    line.request_id.order_id.partner_shipping_id.property_stock_customer,
                    line.name, line.request_id.name,
                    line.request_id.order_id.company_id,
                    values
                )
            )
            line.mark_as_done = True

        if procurements:
            PG.run(procurements)
        return True


TakeoffRequestLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
