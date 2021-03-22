# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Project', copy=False, ondelete='set null')
    is_contract_bill = fields.Boolean(string='Contract')

    @api.model
    def create(self, vals):
        record = super(AccountMove, self).create(vals)
        if vals.get('analytic_account_id'):
            job_order = self.env['job.order'].search([('analytic_account_id', '=', vals.get('analytic_account_id'))])
            job_order.write({'move_ids': [(4, record.id)]})
        return record

    def write(self, vals):
        result = super(AccountMove, self).write(vals)
        if vals.get('analytic_account_id'):
            job_order = self.env['job.order'].search([('analytic_account_id', '=', vals.get('analytic_account_id'))])
            for record in self:
                if record.id not in job_order.move_ids.ids:
                    job_order.write({'move_ids': [(4, record.id)]})
        return result


AccountMove()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_account_id = fields.Many2one(related="move_id.analytic_account_id", string='Project', readonly=True,
                                          store=True)


AccountMoveLine()