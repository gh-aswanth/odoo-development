# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one("account.analytic.account", string='Project', store=True, copy=False,
                                          compute='_compute_analytic_account')
    job_order_line_id = fields.Many2one("job.order.line", ondelete='set null')

    @api.depends('picking_id')
    def _compute_analytic_account(self):
        for move in self:
            move.analytic_account_id = move.picking_id.analytic_account_id

    def _get_new_picking_values(self):
        result = super(StockMove, self)._get_new_picking_values()
        if self.mapped('sale_line_id'):
            result['analytic_account_id'] = self.mapped('sale_line_id.analytic_account_id').id
        elif self.mapped('purchase_line_id'):
            result['analytic_account_id'] = self.mapped('purchase_line_id.account_analytic_id').id
        return result


StockMove()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    analytic_account_id = fields.Many2one(related="move_id.analytic_account_id", string='Project', readonly=True,
                                          store=True)


StockMoveLine()
