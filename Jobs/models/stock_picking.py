# -*- coding: utf-8 -*-

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Project', copy=False, ondelete='set null')

    @api.model
    def create(self, values):
        record = super(StockPicking, self).create(values)
        job_order = self.env['job.order']
        if values.get('analytic_account_id'):
            job_order |= self.env['job.order'].search([('analytic_account_id', '=', values.get('analytic_account_id')),
                                                       ('state', 'not in', ['draft', 'waiting', 'approved', 'cancel'])])
            job_order.write({'picking_ids': [(4, record.id)]})
        if job_order and not all([line.job_order_line_id for line in record.move_ids_without_package]) and not record.purchase_id:
            job_line = job_order.material_lines.filtered(
                lambda line: line.remaining_qty != 0 or line.order_qty == 0) | job_order.equipment_lines.filtered(
                lambda line: line.remaining_qty != 0 or line.order_qty == 0)
            for line in record.move_ids_without_package:
                purchase_job_line = job_line.filtered(
                    lambda rec: rec.product_id.id == line.product_id.id)
                purchase_job_line and line.write({'job_order_line_id': purchase_job_line[0].id})
        return record

    def write(self, values):
        result = super(StockPicking, self).write(values)
        for record in self:
            job_order = self.env['job.order'].search(
                [('analytic_account_id', '=', values.get('analytic_account_id') or record.analytic_account_id.id),
                 ('state', 'not in', ['draft', 'waiting', 'approved', 'cancel'])])
            if values.get('analytic_account_id') and job_order:
                if record.id not in job_order.picking_ids.ids:
                    job_order.write({'picking_ids': [(4, record.id)]})
            if job_order and not all([line.job_order_line_id for line in record.move_ids_without_package]) and not record.purchase_id:
                job_line = job_order.material_lines.filtered(
                    lambda line: line.remaining_qty != 0 or line.order_qty == 0) | job_order.equipment_lines.filtered(
                    lambda line: line.remaining_qty != 0 or line.order_qty == 0)

                for line in record.move_ids_without_package:
                    purchase_job_line = job_line.filtered(
                        lambda rec: rec.product_id.id == line.product_id.id)
                    purchase_job_line and line.write({'job_order_line_id': purchase_job_line[0].id})
        return result


StockPicking()
