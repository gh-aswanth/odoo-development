# -*- coding: utf-8 -*-
import json

from odoo import _, models
from odoo.addons.web.controllers.main import clean_action


class JobOrverview(models.Model):
    _inherit = 'job.order'

    def _qweb_prepare_qcontext(self, view_id, domain):
        values = super()._qweb_prepare_qcontext(view_id, domain)
        if domain:
            jobs = self.search(domain)
        else:
            jobs = self.env['job.order'].browse(self._context.get('active_id'))
        values.update(jobs._job_prepare_values())
        return values

    def _job_prepare_values(self):
        values = {
            'jobs': self,
            'stat_buttons': self._plan_get_stat_button(),
            'budget': self._get_budget_info(),
            'stock_status': self._get_stock_info(),
            'status': self._get_status_info()
        }
        return values

    def _get_status_info(self):
        return [
            {
                'name': _('Sale Order'),
                'amount': self.ordered_amount,
                'total': self.amount_total or 1,
                'label': 'Sale Order',
                'boot_amount': 'o_progress_sale_amount',
                'model': 'sale.order',
                'domain': [('analytic_account_id', '=', self.analytic_account_id.id)]
            },
            {
                'name': _('Customer Invoice'),
                'amount': self.invoiced_amount,
                'total': self.amount_total,
                'label': 'Amount Invoiced',
                'payment_label': 'Amount Paid',
                'residual': self.amount_total - self.paid_amount,
                'amount_paid': self.paid_amount,
                'boot_amount': 'o_progress_invoice_amount',
                'boot_residual': 'o_progress_invoice_residual',
                'model': 'account.move',
                'domain': [('analytic_account_id', '=', self.analytic_account_id.id), ('type', '=', 'out_invoice')],
                'model_residual': 'account.payment',
                'domain_residual': [
                    ('invoice_ids', 'in', self.move_ids.filtered(lambda rec: rec.type == 'out_invoice').ids)]
            },
            {
                'name': _('Purchase Bills'),
                'amount': self.bill_amount,
                'total': self.purchase_amount ,
                'label': 'Amount Billed',
                'payment_label': 'Amount Paid',
                'residual': self.purchase_amount - self.bill_paid,
                'amount_paid': self.bill_paid,
                'boot_amount': 'o_progress_bill_amount',
                'boot_residual': 'o_progress_bill_residual',
                'model': 'account.move',
                'domain': [('analytic_account_id', '=', self.analytic_account_id.id), ('type', '=', 'in_invoice')],
                'model_residual': 'account.payment',
                'domain_residual': [
                    ('invoice_ids', 'in', self.move_ids.filtered(lambda rec: rec.type == 'in_invoice' and not rec.is_contract_bill).ids)]

            },
            {
                'name': _('Contract Bills'),
                'amount': self.contract_bill_amount,
                'total': self.contract_cost_total ,
                'label': 'Amount Billed',
                'payment_label': 'Amount Paid',
                'residual': self.contract_cost_total - self.contract_bill_paid,
                'amount_paid': self.contract_bill_paid,
                'boot_amount': 'o_progress_bill_amount',
                'boot_residual': 'o_progress_bill_residual',
                'model': 'account.move',
                'domain': [('analytic_account_id', '=', self.analytic_account_id.id), ('type', '=', 'in_invoice')],
                'model_residual': 'account.payment',
                'domain_residual': [
                    ('invoice_ids', 'in', self.move_ids.filtered(lambda rec: rec.type == 'in_invoice' and rec.is_contract_bill).ids)]

            }

        ]

    def _get_stock_info(self):
        values = []
        for line in self.material_lines | self.equipment_lines:
            values.append({
                'product': line.product_id.partner_ref,
                'qty': line.order_qty or line.actual_qty,
                'actual_qty': line.actual_qty,
                'purchase_qty': line.purchase_qty,
                'internal_qty': line.internal_transfer_qty,
                'boot_pqty': 'o_progress_purchase_qty',
                'boot_iqty': 'o_progress_bill_internal_qty',
                'special': True if line.order_qty == 0 else False,
                'stock_model': 'stock.move.line',
                'stock_domain': [('analytic_account_id', '=', self.analytic_account_id.id),
                                 ('product_id', '=', line.product_id.id)],
                'purchase_model': 'purchase.order.line',
                'purchase_domain': [('account_analytic_id', '=', self.analytic_account_id.id),
                                    ('product_id', '=', line.product_id.id)]
            })
        return values

    def _get_budget_info(self):
        return {
            'ref': self.name,
            'target': self.budget,
            'record_edit': _to_action_data('job.order', res_id=self.id,
                                           views=[[self.env.ref('Jobs.job_order_primary_view_form').id, 'form']]),
            'current': self.amount_total > self.budget and self.budget or self.amount_total,
            'excess': self.amount_total > self.budget,
            'ex_amount': self.amount_total - self.budget if self.amount_total > self.budget and self.budget else 0,
            'boot_budget': 'o_progress_budget_amount',
            'boot_excess': 'o_progress_budget_excess'
        }

    def _plan_get_stat_button(self):
        stat_buttons = []
        if len(self) == 1:
            stat_buttons.append({
                'name': _('Jobs'),
                'icon': 'fa fa-puzzle-piece',
                'record': self.name,
                'action': _to_action_data('job.order', res_id=self.id,
                                          views=[[self.env.ref('Jobs.job_order_primary_view_form').id, 'form']])
            })
        ts_tree = self.env.ref('sale.view_order_tree')
        ts_form = self.env.ref('sale.view_order_form')
        stat_buttons.append({
            'name': _('Sale Orders'),
            'icon': 'fa-users',
            'count': sum(self.mapped('sale_count')),
            'action': _to_action_data(
                'sale.order',
                domain=[('id', '=', self.sale_order_ids.ids)],
                views=[(ts_tree.id, 'list'), (ts_form.id, 'form')],
                context={'create': False}
            )
        })
        stat_buttons.append({
            'name': _('Customer Invoice'),
            'count': sum(self.mapped('invoice_count')),
            'icon': 'fa-book',
            'action': _to_action_data(
                action=self.env.ref('account.action_move_out_invoice_type'),
                domain=[('id', '=', self.move_ids.ids), ('type', '=', 'out_invoice')],
                context={'create': False}
            )
        })
        stat_buttons.append({
            'name': _('Purchase Orders'),
            'count': sum(self.mapped('purchase_count')),
            'icon': 'fa-shopping-cart',
            'action': _to_action_data(
                action=self.env.ref('purchase.purchase_rfq'),
                domain=[('id', '=', self.purchase_order_ids.ids)],
                context={'create': False}
            )
        })
        stat_buttons.append({
            'name': _('Vendor Bills'),
            'count': sum(self.mapped('bill_count')),
            'icon': 'fa-dollar',
            'action': _to_action_data(
                action=self.env.ref('account.action_move_in_invoice_type'),
                domain=[('id', '=', self.move_ids.ids), ('type', '=', 'in_invoice')],
                context={'create': False}
            )
        })
        stat_buttons.append({
            'name': _('Delivery Orders'),
            'count': sum(self.mapped('picking_out_count')),
            'icon': 'fa-truck',
            'action': _to_action_data(
                action=self.env.ref('stock.stock_picking_action_picking_type'),
                domain=[('id', '=', self.picking_ids.ids), ('picking_type_code', '=', 'outgoing')],
                context={'create': False}
            )
        })
        stat_buttons.append({
            'name': _('Incoming Orders'),
            'count': sum(self.mapped('picking_in_count')),
            'icon': 'fa-truck',
            'action': _to_action_data(
                action=self.env.ref('stock.stock_picking_action_picking_type'),
                domain=[('id', '=', self.picking_ids.ids), ('picking_type_code', '=', 'incoming')],
                context={'create': False}
            )
        })
        stat_buttons.append({
            'name': _('Stock Moves'),
            'count': sum(self.mapped('stock_move_count')),
            'icon': 'fa-exchange',
            'action': _to_action_data(
                action=self.env.ref('stock.stock_move_action'),
                domain=[('analytic_account_id', '=', self.analytic_account_id.id)],
                context={'create': False}
            )
        })

        return stat_buttons

    def action_view_timesheet_plan(self):
        action = self.env.ref('Jobs.job_plan_qweb_view').read()[0]
        action['params'] = {
            'jobs': self.ids,
        }
        action['context'] = {
            'active_id': self.id,
            'active_ids': self.ids,
            'search_default_name': self.name
        }
        return action

def _to_action_data(model=None, *, action=None, views=None, res_id=None, domain=None, context=None):
    # pass in either action or (model, views)
    if action:
        assert model is None and views is None
        act = clean_action(action.read()[0])
        model = act['res_model']
        views = act['views']
    # FIXME: search-view-id, possibly help?
    descr = {
        'data-model': model,
        'data-views': json.dumps(views),
    }
    if context is not None:  # otherwise copy action's?
        descr['data-context'] = json.dumps(context)
    if res_id:
        descr['data-res-id'] = res_id
    elif domain:
        descr['data-domain'] = json.dumps(domain)
    return descr
