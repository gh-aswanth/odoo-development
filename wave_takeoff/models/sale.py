# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    takeoff_ids = fields.One2many('takeoff.request', 'order_id')
    takeoff_count = fields.Integer(compute='_compute_takeoff_count')


    def _compute_takeoff_count(self):
        for rec in self:
            rec.takeoff_count = len(rec.takeoff_ids.mapped('picking_ids').mapped('move_line_ids'))

    def open_takeoff_tree_view(self):
        action = self.env.ref('wave_takeoff.takeoff_stock_move_line_action').read()[0]
        moves = self.takeoff_ids.mapped('picking_ids').mapped('move_line_ids')
        action['domain'] = [('id', 'in', moves.ids)]
        return action

    @api.depends('order_line.purchase_line_ids')
    def _compute_purchase_order_count(self):
        purchase_line_data = self.env['purchase.order.line'].\
            read_group([('sale_order_id', 'in', self.ids)],
                       ['sale_order_id', 'purchase_order_count:count_distinct(order_id)'],
                       ['sale_order_id'])

        takeoff_data = self.env['purchase.order'].\
            read_group([('is_takeoff', '=', True),
                        ('state', '!=', 'cancel')], ['sale_id'], ['sale_id'])

        purchase_data = {x['sale_id'][0]: x['sale_id_count'] for x in takeoff_data if x['sale_id']}
        purchase_count_map = {item['sale_order_id'][0]: item['purchase_order_count'] for item in purchase_line_data}

        for order in self:
            order.purchase_order_count = purchase_count_map.get(order.id, 0) + purchase_data.get(order.id, 0)

    def action_view_purchase(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        PO = self.env['purchase.order'].search(['|',
            ('sale_id', 'in', self.ids),
            ('sale_id', 'in', self.ids),
            ('is_takeoff', '=', True)
                                                ])
        PO = PO | self.mapped('order_line.purchase_line_ids.order_id')
        action['domain'] = [('id', 'in', PO.ids)]
        action['context'] = {'default_sale_id': self.id, 'default_origin': self.name}
        return action

    def _create_analytic_account(self, prefix=None):
        super(SaleOrder, self)._create_analytic_account(prefix)
        budget = self.env['crossovered.budget']
        for order in self:
            analytic_account = order.analytic_account_id
            if analytic_account and not budget.search([('name', '=', analytic_account.name)]):
                budget.create({
                    'name': analytic_account.name,
                    'date_from': order.date_order,
                    'date_to': order.commitment_date or fields.Date.today(),
                    'analytic_account_id': analytic_account.id
                })

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        analytic_account = self.analytic_account_id
        if analytic_account:
            budget = self.env['crossovered.budget'].search([
                '|', ('analytic_account_id', '=', analytic_account.id), ('name', '=', analytic_account.name)], limit=1)
            if budget:
                self.order_line.order_line_budget_auto_commit(budget, analytic_account)
        return res

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            takeoff = self.env['stock.picking'].search([
                ('sale_order_id', '=', order.id),
                ('state', '!=', 'cancel'),
                ('picking_type_code', '!=', 'incoming'),
                ('is_takeoff', '=', True)
            ])
            order.delivery_count = len(order.picking_ids.filtered(lambda do: do.picking_type_code != 'incoming') | takeoff)

    def action_view_delivery(self):
        '''
                This function returns an action that display existing delivery orders
                of given sales order ids. It can either be a in a list or in a form
                view, if there is only one delivery order to show.
                '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        takeoff = self.env['stock.picking'].search([
            ('sale_order_id', '=', self.id),
            ('state', '!=', 'cancel'),
            ('picking_type_code', '!=', 'incoming'),
            ('is_takeoff', '=', True)
        ])
        pickings = self.mapped('picking_ids').filtered(lambda do: do.picking_type_code != 'incoming') | takeoff
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(
            self._context, default_partner_id=self.partner_id.id,
            default_origin=self.name,
            default_picking_type_id=picking_id.picking_type_id.id,
            default_group_id=picking_id.group_id.id
        )
        return action


SaleOrder()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_budget = fields.Boolean(copy=False)
    budget_line_ids = fields.Many2many(
        'crossovered.budget.lines',
        'budget_sale_line_rel',
        'sale_line_id',
        'budget_id',
        copy=False
    )
    purchase_sub_total = fields.Float(compute='_compute_purchase_sub_total')

    @api.depends('purchase_price', 'product_uom_qty')
    def _compute_purchase_sub_total(self):
        for line in self:
            line.purchase_sub_total = line.product_uom_qty * line.purchase_price

    def _update_budget_lines(self):
        for line in self:
            for budget_line in line.budget_line_ids:
                if budget_line.is_revenue:
                    if line.original_qty > line.product_uom_qty and line.is_budget:
                        change = line.price_unit * (line.original_qty - line.product_uom_qty)
                        budget_line.write({
                            'planned_amount': budget_line.planned_amount - change
                        })
                    else:
                        change = line.price_unit * (line.product_uom_qty - line.original_qty)
                        budget_line.write({
                            'planned_amount': budget_line.planned_amount + change
                        })
                elif budget_line.is_expense:
                    if line.original_qty > line.product_uom_qty and line.is_budget:
                        change = line.purchase_price * (line.original_qty - line.product_uom_qty)
                        budget_line.write({
                            'planned_amount': budget_line.planned_amount + change
                        })
                    else:
                        change = line.purchase_price * (line.product_uom_qty - line.original_qty)
                        budget_line.write({
                            'planned_amount': budget_line.planned_amount - change
                        })
                budget_line.sale_line_ids |=line
            if not line.is_budget:
                line.write({'is_budget': True})

    def order_line_budget_auto_commit(self, budget, analytic_account):
        for line in self:
            pos_income = line.product_id.categ_id.budgetary_income_position_id
            pos_expense = line.product_id.categ_id.budgetary_expense_position_id
            if pos_expense and pos_income:
                budget_line = budget.crossovered_budget_line.filtered(
                    lambda r: r.general_budget_id.id in [pos_expense.id, pos_income.id]
                )
                if budget_line:
                    line.budget_line_ids |= budget_line
                    line._update_budget_lines()
                else:
                    line.budget_auto_generation(budget, analytic_account, pos_income, pos_expense)

    def budget_auto_generation(self, budget, analytic_account, pos_income, pos_expense):
        for line in self:
            for pos in pos_income | pos_expense:
                is_income = True if line.product_id.categ_id.budgetary_income_position_id.id == pos.id else False
                is_expense = True if line.product_id.categ_id.budgetary_expense_position_id.id == pos.id else False
                amount = line.product_uom_qty * line.price_unit if is_income else -(line.product_uom_qty * line.purchase_price)
                obj = self.env['crossovered.budget.lines'].create({
                    'crossovered_budget_id': budget.id,
                    'general_budget_id': pos.id,
                    'planned_amount': amount,
                    'is_revenue': is_income,
                    'is_expense': is_expense,
                    'analytic_account_id': analytic_account.id,
                    'date_from': budget.date_from,
                    'date_to': budget.date_to
                })
                line.write({'is_budget': True, 'budget_line_ids': [(4, obj.id)]})
                obj.sale_line_ids |= line

SaleOrderLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
