# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import AccessError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Project', copy=False, ondelete='set null')

    @api.model
    def create(self, values):
        record = super(PurchaseOrder, self).create(values)
        job_order = self.env['job.order']
        if values.get('analytic_account_id'):
            job_order |= self.env['job.order'].search([('analytic_account_id', '=', values.get('analytic_account_id')),
                                                       ('state', 'not in', ['draft', 'waiting', 'approved', 'cancel'])])
            job_order.write({'purchase_order_ids': [(4, record.id)]})
        if job_order and not all([line.job_order_line_id for line in record.order_line]):
            job_line = job_order.material_lines.filtered(
                lambda line: line.remaining_qty != 0 or line.order_qty == 0) | job_order.equipment_lines.filtered(
                lambda line: line.remaining_qty != 0 or line.order_qty == 0)
            for line in record.order_line:
                purchase_job_line = job_line.filtered(lambda rec: rec.product_id.id == line.product_id.id)[0]
                line.write({'job_order_line_id': purchase_job_line.id})
        return record

    def write(self, values):
        result = super(PurchaseOrder, self).write(values)
        for record in self:
            job_order = self.env['job.order'].search(
                [('analytic_account_id', '=', values.get('analytic_account_id') or record.analytic_account_id.id),
                 ('state', 'not in', ['draft', 'waiting', 'approved', 'cancel'])])
            if values.get('analytic_account_id'):
                if record.id not in job_order.purchase_order_ids.ids:
                    job_order.write({'purchase_order_ids': [(4, record.id)]})
            if job_order and not all([line.job_order_line_id for line in record.order_line]):
                job_line = job_order.material_lines.filtered(
                    lambda line: line.remaining_qty != 0 or line.order_qty == 0) | job_order.equipment_lines.filtered(
                    lambda line: line.remaining_qty != 0 or line.order_qty == 0)
                for line in record.order_line:
                    purchase_job_line = job_line.filtered(lambda rec: rec.product_id.id == line.product_id.id)[0]
                    line.write({'job_order_line_id': purchase_job_line.id})
        return result

    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        result['context']['default_analytic_account_id'] = self.analytic_account_id.id
        return result

    @api.model
    def _prepare_picking(self):
        result = super(PurchaseOrder, self)._prepare_picking()
        result['analytic_account_id'] = self.analytic_account_id.id
        return result

    def _add_supplier_to_product(self):

        for line in self.order_line:

            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if line.product_id and partner not in line.product_id.seller_ids.mapped('name') and len(line.product_id.seller_ids) <= 10:

                currency = partner.property_purchase_currency_id or self.env.company.currency_id
                price = self.currency_id._convert(line.price_unit, currency, line.company_id, line.date_order or fields.Date.today(), round=False)

                if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)

                supplierinfo = {
                    'name': partner.id,
                    'sequence': max(line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
                    'min_qty': 0.0,
                    'price': price,
                    'product_id': line.product_id.id,
                    'currency_id': currency.id,
                    'delay': 0,
                }

                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:
                    break

PurchaseOrder()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    job_order_line_id = fields.Many2one('job.order.line', ondelete='set null')
    account_analytic_id = fields.Many2one(
        related='order_id.analytic_account_id', string='Project', readonly=True, store=True, ondelete='set null')


PurchaseOrderLine()
