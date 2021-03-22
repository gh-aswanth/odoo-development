# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        compute='_compute_analytic_account',
        store=True
    )

    @api.depends('crossovered_budget_line.analytic_account_id')
    def _compute_analytic_account(self):
        for budget in self:
            account = budget.crossovered_budget_line.mapped('analytic_account_id')
            budget.analytic_account_id = account and account[0]


CrossoveredBudget()


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    sale_line_ids = fields.Many2many(
        'sale.order.line',
        'sale_line_budget_rel',
        'budget_line_id',
        'sale_line_id'
    )
    is_revenue = fields.Boolean()
    is_expense = fields.Boolean()


CrossoveredBudgetLines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
