# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class ProcurementRequisitionWizard(models.TransientModel):
    _name = 'procurement.requisition.wizard'
    _description = 'Procurement requisition wizard'

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To')
    job_order_id = fields.Many2one('job.order', 'Job')
    material_line_ids = fields.One2many('purchase.requisition.wizard.line', 'wiz_id')
    product_id = fields.Many2one('product.product', string='Equipment')
    move_qty = fields.Integer(string='Quantity', required=True)
    line_id = fields.Many2one('job.order.line')
    procurement_selection = fields.Selection([('purchase', 'Purchase'), ('transfer', 'Stock Transfer')],
                                             default='purchase')
    in_stock = fields.Float(related="product_id.qty_available", readonly=True)
    code = fields.Selection(related="picking_type_id.code", readonly=True)

    @api.model
    def default_get(self, fields_list):
        result = super(ProcurementRequisitionWizard, self).default_get(fields_list)
        lines = []
        job_order = self.env['job.order'].browse(self._context.get('default_job_order_id'))
        line = self.env['job.order.line'].browse(self._context.get('active_id'))
        if self._context.get('mass_order'):
            estimation_lines = job_order.material_lines | job_order.equipment_lines
            if job_order:
                for line in estimation_lines:
                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'order_qty': line.remaining_qty,
                        'unit_cost': line.unit_cost,
                        'job_order_line_id': line.id
                    }))
        elif self._context.get('single_order'):
            if line:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'order_qty': line.remaining_qty,
                    'unit_cost': line.unit_cost,
                    'job_order_line_id': line.id
                }))
                result['product_id'] = line.product_id.id
                result['move_qty'] = line.remaining_qty
                result['line_id'] = self._context.get('active_id')

        result['material_line_ids'] = lines
        return result

    @api.onchange('job_order_id', 'procurement_selection')
    def _onchange_job_id(self):
        if self._context.get('mass_order') or self.procurement_selection == 'purchase':
            return {
                'domain': {
                    'picking_type_id': [('code', '=', 'incoming')]
                }
            }
        return {
            'domain': {
                'picking_type_id': []
            }
        }

    def create_purchase_order(self):
        purchase_dictionary = {}
        partner_dest_addrs = self.job_order_id and self.job_order_id.partner_id or \
                             self.line_id and self.line_id.mat_job_id and self.line_id.mat_job_id.partner_id or \
                             self.line_id.mat_job_id and self.line_id.mat_job_id.partner_id
        for line in self.material_line_ids:
            if not line.partner_id:
                raise UserError('Select Partner in Material line..!')

            purchase_dictionary.setdefault(line.partner_id, []). \
                append({'product_id': line.product_id.id,
                        'name': line.name,
                        'product_qty': line.purchase_qty or line.order_qty,
                        'job_order_line_id': line.job_order_line_id.id,
                        'product_uom': line.product_id.uom_po_id.id,
                        'price_unit': line.unit_cost,
                        'date_planned': fields.Date.from_string(fields.Datetime.now()) + relativedelta(
                            days=int(line.supplier_delay)),
                        })

        order = self.job_order_id or self.line_id.mat_job_id or self.line_id.equ_job_id
        for partner, order_value in purchase_dictionary.items():
            self.env['purchase.order'].create({
                'partner_id': partner.id,
                'analytic_account_id': order.analytic_account_id.id,
                'picking_type_id': self.picking_type_id.id,
                'dest_address_id': partner_dest_addrs.id if self.picking_type_id.sequence_code == 'DS' else False,
                'order_line': [(0, 0, line) for line in order_value]})
        return {'type': 'ir.actions.act_window_close'}

    def action_confirm(self):
        picking_ob = self.env['stock.picking']
        move_ob = self.env['stock.move']
        picking_type = self.picking_type_id
        if not picking_type.default_location_dest_id or not picking_type.default_location_src_id:
            raise UserError('Cannot find locations in picking type:%s.' % (picking_type.name))
        order = self.line_id.mat_job_id or self.line_id.equ_job_id
        if self.picking_type_id.code == 'outgoing' and self.product_id.qty_available < self.move_qty:
            raise UserError('Do not have enough quantity in stock to process this transfer.')

        Picking = picking_ob.create({
            'partner_id': self.line_id.equ_job_id.partner_id.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': 'Equipment Move:' + order.name,
            'picking_type_id': self.picking_type_id.id,
            'analytic_account_id': order.analytic_account_id.id,
        })
        move = move_ob.create({
            'name': "%s Equipment Move: %s" % (order.name, self.product_id.display_name),
            'partner_id': Picking.partner_id.id,
            'location_id': Picking.location_id.id,
            'location_dest_id': Picking.location_dest_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.move_qty,
            'picking_id': Picking.id,
        })
        Picking.action_assign()
        self.line_id.write({'stock_move_ids': [(4, move.id)]})
        for move in Picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
            for move_line in move.move_line_ids:
                move_line.qty_done = move_line.product_uom_qty

        Picking.action_done()


ProcurementRequisitionWizard()


class PurchaseRequisitionWizardLine(models.TransientModel):
    _name = 'purchase.requisition.wizard.line'
    _description = 'Purchase requisition wizard Line'

    name = fields.Text("Description")
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string="Vendor")
    purchase_line_id = fields.Many2one('purchase.order.line')
    wiz_id = fields.Many2one('procurement.requisition.wizard')
    order_qty = fields.Integer(string='Quantity', default=1)
    unit_cost = fields.Float(string="Unit cost")
    amount_total = fields.Float(string='Amount total', compute='_compute_amount_total')
    purchase_qty = fields.Integer('Quantity Ordered')
    job_order_line_id = fields.Many2one('job.order.line')
    supplier_delay = fields.Integer('Delivery Lead time')

    @api.depends('purchase_qty', 'unit_cost')
    def _compute_amount_total(self):
        for line in self:
            line.amount_total = line.order_qty * line.unit_cost

    def get_seller_info_product(self, product, qty):
        seller_infos = product.variant_seller_ids. \
            filtered(lambda rec: rec.product_id.id == product.id).sorted(
            lambda s: (-s.min_qty, s.price))
        purchase_qty_uom = product.uom_id._compute_quantity(qty, product.uom_po_id)
        supplierinfo = self.env['product.supplierinfo']
        if seller_infos:
            for seller in seller_infos:
                info = product._select_seller(
                    partner_id=seller and seller.name,
                    quantity=purchase_qty_uom,
                    date=fields.Date.today(),
                    uom_id=self.product_id.uom_po_id
                )
                if not supplierinfo:
                    supplierinfo |= info
        return supplierinfo

    @api.onchange('purchase_qty')
    def _onchange_order_qty(self):
        qty_required = self.purchase_qty or self.order_qty
        supplierinfo = self.get_seller_info_product(self.product_id, qty_required)
        if supplierinfo:
            return {
                'value': {
                    'unit_cost':  supplierinfo.price or self.job_order_line_id.unit_cost,
                    'supplier_delay': supplierinfo.delay or False,
                    'partner_id': supplierinfo.name.id or False,
                    'amount_total': self.purchase_qty * self.unit_cost
                }
            }
        title = "Warning for %s" % self.product_id.name
        message = "No Supplier Found..."
        warning = {
            'title': title,
            'message': message
        }
        self.update({'amount_total': self.purchase_qty * self.unit_cost})
        if self.purchase_qty and not self.partner_id:
            return {
                'warning': warning
            }


PurchaseRequisitionWizardLine()
