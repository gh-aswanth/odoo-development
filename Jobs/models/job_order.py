# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class JobOrder(models.Model):
    _name = 'job.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Job Order Creation'

    name = fields.Char(string="Order Reference", required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string="Customer", tracking=True)
    partner_contact_id = fields.Many2one('res.partner', string="Contact", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting For Approval'),
        ('approved', 'Verified'),
        ('sent', 'Sent to customer'),
        ('job', 'Job'),
        ('inprogress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], default='draft', string="State", tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Project', copy=False,
                                          ondelete='set null', readonly=True, tracking=True)
    material_lines = fields.One2many('job.order.line', 'mat_job_id', string='Material Lines')
    equipment_lines = fields.One2many('job.order.line', 'equ_job_id', string='Equipement Lines')
    labour_lines = fields.One2many('job.order.line', 'lab_job_id', string='Labour Lines')
    date_order = fields.Date(string="Order Date", tracking=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string="Responsible", tracking=True)
    amount_total = fields.Float(compute="_compute_amount_total", string="Amount Total", store=True)
    sale_count = fields.Integer(string="Sale Count", compute='_compute_resource_count', store=True)
    material_sub_total = fields.Float(compute="_compute_amount_total", string="Material Total", store=True)
    equipment_sub_total = fields.Float(compute="_compute_amount_total", string="Equipment Total", store=True)
    machinery_sub_total = fields.Float(compute="_compute_amount_total", string="Machinery Total", store=True)
    labour_sub_total = fields.Float(compute="_compute_amount_total", string="Labour Total", store=True)
    purchase_count = fields.Integer(string="Purchase Count", compute='_compute_resource_count', store=True)
    sub_contract_ids = fields.One2many('job.sub.contract', 'job_id', string="Contract")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True)
    schedule_date = fields.Date(string="Schedule Date", tracking=True)
    close_date = fields.Date(string="Expected Closing date", tracking=True)
    date_create = fields.Date(string='Date', default=lambda self: fields.Datetime.now())
    job_start_date = fields.Date(string="Start Date", tracking=True)
    job_end_date = fields.Date(string="End Date", tracking=True)
    budget = fields.Float(string="Budget", tracking=True)
    invoice_count = fields.Integer(string="Invoice Count", compute='_compute_resource_count', store=True)
    bill_count = fields.Integer(string="Bill Count", compute='_compute_resource_count', store=True)
    picking_in_count = fields.Integer(string="Receipt Count", compute='_compute_resource_count', store=True)
    picking_out_count = fields.Integer(string="Delivery Count", compute='_compute_resource_count', store=True)
    website = fields.Char('Website', index=True, help="Website of the contact")
    contact_name = fields.Char('Contact Name', tracking=30)
    customer_email = fields.Char('Email', placeholder="Email address of the customer..", tracking=40, index=True)
    contact_email = fields.Char('Email', placeholder="Email address of the contact..", tracking=50, index=True)
    partner_name = fields.Char("Company Name", tracking=20, index=True,
                               help='The name of the future partner company that will be created while converting the Estimation into Job')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', change_default=True)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    customer_phone = fields.Char('Phone', placeholder="Customer phone number..", tracking=60)
    contact_phone = fields.Char('Phone', placeholder="Contact phone number..", tracking=70)
    function = fields.Char('Job Position')
    title = fields.Many2one('res.partner.title')
    contact_title = fields.Many2one('res.partner.title')
    contract_est_total = fields.Float(compute="_compute_amount_total", string="Sub Contract Total", store=True)
    contract_cost_total = fields.Float(compute="_compute_amount_total", string="Sub Contract Cost Total", store=True)
    sale_order_ids = fields.Many2many('sale.order', string="Sale Orders", copy=False)
    purchase_order_ids = fields.Many2many('purchase.order', string="Purchase Orders", copy=False)
    move_ids = fields.Many2many('account.move', string='Invoices', copy=False)
    picking_ids = fields.Many2many('stock.picking', copy=False)
    stock_move_count = fields.Integer(string="StockMove Count", compute='_compute_resource_count', store=True)
    customer_type = fields.Selection([('new', 'New Customer'), ('existing', 'Existing customer')], default='new')
    ordered_amount = fields.Float(compute='_compute_tracking_vals', store=True)
    invoiced_amount = fields.Float(compute='_compute_tracking_vals', store=True)
    paid_amount = fields.Float(compute='_compute_tracking_vals', store=True)
    bill_amount = fields.Float(compute='_compute_tracking_vals', store=True)
    bill_paid = fields.Float(compute='_compute_tracking_vals', store=True)
    purchase_amount = fields.Float(compute='_compute_tracking_vals', store=True)
    contract_bill_amount = fields.Float(compute='_compute_tracking_vals', store=True)
    contract_bill_paid = fields.Float(compute='_compute_tracking_vals', store=True)

    @api.onchange('customer_type')
    def _onchange_customer_type(self):
        return {'value': dict().fromkeys(
            ['partner_name', 'customer_email', 'customer_phone', 'street', 'street2', 'function', 'title',
             'contact_name', 'contact_email', 'contact_phone', 'zip', 'city', 'state_id', 'country_id', 'website',
             'partner_id', 'partner_contact_id', 'contact_title'], False)}

    @api.depends('sale_order_ids.amount_total', 'sale_order_ids.state', 'move_ids.amount_total', 'move_ids.state',
                 'purchase_order_ids.amount_total', 'purchase_order_ids.state')
    def _compute_tracking_vals(self):
        for order in self:
            invoices = order.move_ids.filtered(lambda move: move.state == 'posted' and move.type == 'out_invoice')
            purchase_bills = order.move_ids.filtered(lambda move: move.state == 'posted' and move.type == 'in_invoice' and not move.is_contract_bill)
            contract_bills = order.move_ids.filtered(lambda move: move.state == 'posted' and move.type == 'in_invoice' and move.is_contract_bill)
            invoice_sum = sum(invoices.mapped('amount_total'))
            purchase_bill_sum = sum(purchase_bills.mapped('amount_total'))
            contract_bill_sum = sum(contract_bills.mapped('amount_total'))
            order.ordered_amount = sum(
                order.sale_order_ids.filtered(lambda sale: sale.state != 'cancel').mapped('amount_untaxed'))
            order.invoiced_amount = invoice_sum
            order.paid_amount = invoice_sum - sum(invoices.mapped('amount_residual'))
            order.bill_amount = purchase_bill_sum
            order.bill_paid = purchase_bill_sum - sum(purchase_bills.mapped('amount_residual'))
            order.purchase_amount = sum(order.purchase_order_ids.mapped('amount_total'))
            order.contract_bill_amount = contract_bill_sum
            order.contract_bill_paid = contract_bill_sum - sum(contract_bills.mapped('amount_residual'))

    @api.depends('sale_order_ids', 'sale_order_ids.state', 'purchase_order_ids', 'purchase_order_ids.state',
                 'move_ids', 'move_ids.state', 'picking_ids', 'picking_ids.state')
    def _compute_resource_count(self):
        for order in self:
            order.sale_count = len(
                order.sale_order_ids.filtered(
                    lambda sale: sale.state != 'cancel'))
            order.purchase_count = len(
                order.purchase_order_ids.filtered(
                    lambda purchase: purchase.state != 'cancel'))
            order.invoice_count = len(
                order.move_ids.filtered(
                    lambda move: move.state != 'cancel' and move.type == 'out_invoice'))
            order.bill_count = len(
                order.move_ids.filtered(
                    lambda move: move.state != 'cancel' and move.type == 'in_invoice'))
            order.picking_in_count = len(
                order.picking_ids.filtered(
                    lambda picking: picking.state != 'cancel' and picking.picking_type_code == 'incoming'))
            order.picking_out_count = len(
                order.picking_ids.filtered(
                    lambda picking: picking.state != 'cancel' and picking.picking_type_code == 'outgoing'))
            if order.analytic_account_id:
                order.stock_move_count = self.env['stock.move'].search_count([
                    ('analytic_account_id', '=', order.analytic_account_id.id),
                    ('state', '!=', 'cancel')
                ])

    @api.depends('material_lines.amount_total', 'equipment_lines.amount_total', 'labour_lines.amount_total',
                 'sub_contract_ids.estimated_price', 'sub_contract_ids.cost_price')
    def _compute_amount_total(self):
        for order in self:
            material_sub_total = sum(order.material_lines.mapped('amount_total'))
            equipment_sub_total = sum(order.equipment_lines.mapped('amount_total'))
            labour_sub_total = sum(order.labour_lines.mapped('amount_total'))
            contract_est_total = sum(order.sub_contract_ids.mapped('estimated_price'))
            contract_cost_total = sum(order.sub_contract_ids.mapped('cost_price'))
            amount_total = sum([material_sub_total, equipment_sub_total, labour_sub_total, contract_est_total])
            order.update({
                'material_sub_total': material_sub_total,
                'equipment_sub_total': equipment_sub_total,
                'labour_sub_total': labour_sub_total,
                'amount_total': amount_total,
                'contract_est_total': contract_est_total,
                'contract_cost_total': contract_cost_total
            })

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'job.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('job.order') or _('New')
        result = super(JobOrder, self).create(vals)
        return result

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_es_as_sent'):
            self.filtered(lambda o: o.state == 'approved').with_context(tracking_disable=True).write({'state': 'sent'})
        return super(JobOrder, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def action_view_stock_move(self):
        self.ensure_one()
        action = self.env.ref('stock.stock_move_action').read()[0]
        action['domain'] = [('analytic_account_id.id', '=', self.analytic_account_id.id)]
        action['context'] = {'search_default_groupby_location_id': 1}
        return action

    def action_view_records(self):
        action = orders = form_view = None
        ctx = {}
        if self._context.get('view_sale_order', False):
            action = self.env.ref('sale.action_orders').read()[0]
            orders = self.sale_order_ids.filtered(lambda rec: rec.state != 'cancel')
            ctx = {'default_partner_id': self.partner_id.id}
            if len(orders) == 1:
                form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
        elif self._context.get('view_invoice', False):
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            orders = self.move_ids.filtered(lambda rec: rec.type == 'out_invoice' and rec.state != 'cancel')
            ctx = {'default_type': 'out_invoice'}
            if len(orders) == 1:
                form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        elif self._context.get('view_purchase_order', False):
            action = self.env.ref('purchase.purchase_rfq').read()[0]
            orders = self.purchase_order_ids.filtered(lambda rec: rec.state != 'cancel')
            if len(orders) == 1:
                form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        elif self._context.get('view_bill', False):
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            orders = self.move_ids.filtered(lambda rec: rec.type == 'in_invoice' and rec.state != 'cancel')
            ctx = {'default_type': 'in_invoice'}
            if len(orders) == 1:
                form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        elif self._context.get('view_delivery_order', False):
            action = self.env.ref('stock.stock_picking_action_picking_type').read()[0]
            orders = self.picking_ids.filtered(
                lambda rec: rec.picking_type_code == 'outgoing' and rec.state != 'cancel')
            if len(orders) == 1:
                form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
        elif self._context.get('view_receipt', False):
            action = self.env.ref('stock.stock_picking_action_picking_type').read()[0]
            orders = self.picking_ids.filtered(
                lambda rec: rec.picking_type_code == 'incoming' and rec.state != 'cancel')
            if len(orders) == 1:
                form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
        if action and orders and len(orders) > 1:
            action['domain'] = [('id', 'in', orders.ids)]
        elif action and orders and len(orders) == 1:
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = orders.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = dict(ctx, default_analytic_account_id = self.analytic_account_id.id, create = True)
        action['context'] = context
        return action

    def _create_analytic_account(self):
        for order in self:
            analytic_account = self.env['account.analytic.account'].create({
                'name': order.name + ':' + order.partner_id.name,
                'partner_id': order.partner_id.id,
                'company_id': order.company_id.id,
                'active': True,
            })
            return order.write({'analytic_account_id': analytic_account.id})

    def print_document(self):
        return self.env.ref('Jobs.action_report_joborder').report_action(self)

    def set_to_approved(self):
        for order in self:
            order.state = 'approved'
            order.name = self.env['ir.sequence'].search([('prefix', '=', 'JOB-')])._next()

    def set_to_waiting_approval(self):
        for order in self:
            order.state = 'waiting'

    def move_to_provision(self):
        for order in self:
            order.state = 'inprogress'
            order.job_start_date = fields.Date.today()

    def make_as_done(self):
        for order in self:
            order.write({'state': 'done'})
            order.job_end_date = fields.Date.today()

    def action_create_order(self):
        self.ensure_one()
        values = {}
        partner = False
        if not self.partner_id and not self.partner_contact_id:
            partner = self.create_job_partner()
            values.setdefault('partner_contact_id', partner.id if partner.parent_id else False)
            values.setdefault('partner_id', partner.id if not partner.parent_id else partner.parent_id)
        values.setdefault('state', 'job')
        values.setdefault('date_order', fields.Date.today())
        values.setdefault('customer_type', 'existing')
        self.write(values)
        if not self.analytic_account_id:
            self._create_analytic_account()
        sale_object = self.env['sale.order']
        product = self.env.ref('Jobs.job_service_product')
        sale_object.create({
            'partner_id': self.partner_id.id,
            'partner_contact_id': self.partner_contact_id.id if self.partner_contact_id else False,
            'analytic_account_id': self.analytic_account_id.id,
            'date_order': fields.Datetime.now(),
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': product.get_product_multiline_description_sale(),
                'product_uom_qty': 1,
                'price_unit': self.amount_total,
                'product_uom': product.uom_id.id
            })]
        })
        self.message_subscribe(partner_ids=[self.partner_id.id, self.partner_contact_id.id])
        job_action = self.env.ref('Jobs.job_order_action').read()[0]
        form_view_id = self.env.ref('Jobs.job_order_primary_view_form').id
        job_action.update({
            'res_id': self.id,
            'views': [[form_view_id, 'form']],
            'target': 'current'
        })
        return job_action

    def send_to_customer(self):
        self.ensure_one()
        template_id = self.env['ir.model.data'].xmlid_to_res_id('Jobs.email_template_job_order',
                                                                raise_if_not_found=False)
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_template(template.lang, 'job.order', self.ids[0])

        ctx = {
            'default_model': 'job.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_es_as_sent': True,
            'mail_with_cc': True,
            'custom_layout': "mail.mail_notification_light",
            'model_description': self.with_context(lang=lang).name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _create_job_partner_data(self, name, is_company, parent_id=False):
        return {
            'name': name,
            'parent_id': parent_id,
            'phone': self.customer_phone if not parent_id else self.contact_phone,
            'email': self.customer_email if not parent_id else self.contact_email,
            'title': self.title.id if not parent_id else self.contact_title.id,
            'function': self.function if not parent_id else False,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'website': self.website,
            'is_company': is_company,
            'type': 'contact'
        }

    def create_job_partner(self):
        Partner = self.env['res.partner']
        contact_name = self.contact_name
        if self.partner_name:
            partner_company = Partner.create(self._create_job_partner_data(self.partner_name, True))
        else:
            partner_company = None

        if contact_name:
            return Partner.create(
                self._create_job_partner_data(contact_name, False, partner_company.id if partner_company else False))

        if partner_company:
            return partner_company


JobOrder()


class JobOrderLine(models.Model):
    _name = 'job.order.line'
    _description = 'Job Order Line Creation'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text("Description")
    mat_job_id = fields.Many2one('job.order', 'Material Job Order', ondelete='cascade')
    equ_job_id = fields.Many2one('job.order', 'Equipment Job Order', ondelete='cascade')
    lab_job_id = fields.Many2one('job.order', 'Labour Job Order', ondelete='cascade')
    order_qty = fields.Integer('Quantity')
    unit_cost = fields.Float(string="Cost")
    amount_total = fields.Float(string='Amount Total', compute='_compute_amount_total', store=True)
    is_material = fields.Boolean('Material')
    is_equipment = fields.Boolean('Equipment')
    is_labour = fields.Boolean('Labour')
    purchase_line_ids = fields.One2many('purchase.order.line', 'job_order_line_id')
    purchase_qty = fields.Integer('Purchase Qty', compute='_compute_tracking_values', store=True)
    purchase_unit_price = fields.Float('Purchase Unit Price', compute='_compute_tracking_values', store=True)
    margin = fields.Float('Margin', compute='_compute_margin', store=True)
    purchase_amount_total = fields.Float('Purchase SubTotal', compute='_compute_tracking_values', store=True)
    in_stock_qty = fields.Integer('In Stock', compute='_compute_instock_qty', store=True)
    is_rental = fields.Boolean('Rental')
    rule_type = fields.Selection([
        ('hour', 'Hourly'),
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
        ('year', 'Yearly')
    ], string='Billing Period')
    consumed_qty = fields.Float(string="Consumed Quantity")
    unit_price = fields.Float(string="Price")
    stock_move_ids = fields.One2many('stock.move', 'job_order_line_id', string="Stock Transfer")
    remaining_qty = fields.Integer(string="Remaining", default=0, compute='_compute_tracking_values', store=True)
    actual_qty = fields.Integer(string="Actual Qty", default=0, compute='_compute_tracking_values', store=True)
    internal_transfer_qty = fields.Integer(string="Internal Qty", default=0, compute='_compute_tracking_values',
                                           store=True)
    currency_id = fields.Many2one('res.currency', string="Company Currency",
                                          default=_get_default_currency_id)

    @api.depends('unit_cost', 'unit_price')
    def _compute_margin(self):
        for line in self:
            line.margin = ((line.unit_price - line.unit_cost) / line.unit_price) * 100 if line.unit_price else 0

    @api.depends('product_id.qty_available')
    def _compute_instock_qty(self):
        for line in self:
            line.in_stock_qty = line.product_id.qty_available

    @api.depends('purchase_line_ids.product_qty', 'purchase_line_ids.price_unit', 'purchase_line_ids.state',
                 'stock_move_ids.product_uom_qty')
    def _compute_tracking_values(self):
        for line in self:
            purchase_lines = line.purchase_line_ids.filtered(lambda rec: rec.state != 'cancel')
            move_lines = line.stock_move_ids.filtered(lambda rec: rec.state != 'cancel')
            purchase_qty = purchase_lines and sum(purchase_lines.mapped('product_qty')) or 0
            purchase_unit_price = purchase_lines and purchase_lines[0].price_unit
            purchase_amount_total = purchase_lines and sum(purchase_lines.mapped('price_subtotal'))
            move_qty = move_lines and sum(move_lines.mapped('product_uom_qty')) or 0
            actual_purchase_qty = purchase_qty + move_qty
            remaining_qty = line.order_qty - actual_purchase_qty
            line.update({
                'purchase_qty': purchase_qty,
                'purchase_unit_price': purchase_unit_price,
                'purchase_amount_total': purchase_amount_total,
                'actual_qty': actual_purchase_qty,
                'internal_transfer_qty': move_qty,
                'remaining_qty': remaining_qty if line.order_qty and remaining_qty > 0 else 0
            })

    @api.onchange('product_id')
    def _onchange_product(self):
        for line in self:
            order = line.mat_job_id or line.equ_job_id
            description = line.product_id.get_product_multiline_description_sale()
            line.name = description
            line.unit_price = line.product_id.lst_price
            line.unit_cost = line.product_id.standard_price
            line.order_qty = 0 if order and order.state not in ['draft', 'waiting', 'approved', 'sent'] else 1

    @api.depends('order_qty', 'unit_price', 'purchase_qty')
    def _compute_amount_total(self):
        for line in self:
            line.amount_total = line.order_qty * line.unit_price if line.order_qty > 0 else line.unit_price if line.purchase_qty == 0 else line.unit_price * line.purchase_qty


JobOrderLine()
