# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_contact_id = fields.Many2one('res.partner', string="Contact")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Project', copy=False, ondelete='set null')

    @api.model
    def create(self, vals):
        record = super(SaleOrder, self).create(vals)
        if vals.get('analytic_account_id'):
            job_order = self.env['job.order'].search([('analytic_account_id', '=', vals.get('analytic_account_id'))])
            job_order.write({'sale_order_ids': [(4, record.id)]})
        return record

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        if vals.get('analytic_account_id'):
            for record in self:
                job_order = self.env['job.order'].search(
                    [('analytic_account_id', '=', vals.get('analytic_account_id'))])
                if record.id not in job_order.sale_order_ids.ids:
                    job_order.write({'sale_order_ids': [(4, record.id)]})
        return result

    @api.onchange('analytic_account_id')
    def _onchange_analytic_account(self):
        if self.analytic_account_id:
            job = self.env['job.order'].search([('analytic_account_id', '=', self.analytic_account_id.id)])
            amount = job.amount_total - job.ordered_amount
            product = self.env.ref('Jobs.job_service_product')
            return {
                'value': {
                    'partner_id': job.partner_id.id,
                    'order_line': [(0, 0, {
                        'product_id': product.id,
                        'name': product.get_product_multiline_description_sale(),
                        'product_uom_qty': 1,
                        'price_unit': amount,
                        'product_uom': product.uom_id.id
                    })]
                }
            }

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.analytic_account_id:
            invoice_vals['analytic_account_id'] = self.analytic_account_id.id
        return invoice_vals


SaleOrder()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    analytic_account_id = fields.Many2one(
        related='order_id.analytic_account_id', string='Project', store=True, readonly=True)


SaleOrderLine()
