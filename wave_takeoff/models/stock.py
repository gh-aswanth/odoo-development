# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    takeoff_selectable = fields.Boolean("Selectable on Take Off")


StockLocationRoute()


class StockMove(models.Model):
    _inherit = 'stock.move'

    analytic_account_id = fields.Many2one(
        related='picking_id.analytic_account_id',
        store=True,
        readonly=True
    )
    is_takeoff = fields.Boolean(
        related='picking_id.is_takeoff',
        store=True,
        readonly=True
    )
    takeoff_line_id = fields.Many2one('takeoff.request.line')

    def _prepare_procurement_values(self):
        self.ensure_one()
        group_id = self.group_id or False
        return {
            'date_planned': self.date_expected,
            'move_dest_ids': self,
            'group_id': group_id,
            'route_ids': self.route_ids,
            'warehouse_id': self.warehouse_id or self.picking_id.picking_type_id.warehouse_id or self.picking_type_id.warehouse_id,
            'priority': self.priority,
            'takeoff_line_id': self.takeoff_line_id.id
        }

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        group = self.mapped('group_id')
        if group.takeoff_id:
            vals['takeoff_id'] = group.takeoff_id.id
            vals['sale_order_id'] = group.takeoff_id.order_id.id
            vals['is_takeoff'] = True
        return vals

    @api.onchange('product_id')
    def _onchange_product_id(self):
        warning = {}
        message = ''
        popup = {}
        if self.picking_id.is_takeoff and self.product_id:
            if not self.product_id.categ_id.budgetary_income_position_id:
                message += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻"
            if not self.product_id.categ_id.budgetary_expense_position_id:
                message += "\n⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧" if message \
                    else "⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧"

            if message:
                warning['title'] = _("Warning for %s") % self.product_id.name
                warning['message'] = message

        if self.picking_id.is_takeoff:
            popup.update(domain={'product_id': ['|', ('is_takeoff', '=', True), ('categ_id.is_takeoff', '=', True)]})
        if warning:
            popup.update(warning=warning)
        return popup

    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        self = self.with_context(force_company=self.company_id.id)
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        position_expense = self.product_id.categ_id.budgetary_expense_position_id
        position_income = self.product_id.categ_id.budgetary_income_position_id
        if self.picking_id.is_takeoff:
            if not position_expense:
                raise UserError(_("User Error !\nPlease set budgetary expense position in product category."))
            if not position_income:
                raise UserError(_("User Error !\nPlease set budgetary income position in product category."))

        if self.picking_id.is_takeoff:
            acc_src = accounts_data['expense'].id
        elif self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id

        if self.picking_id.is_takeoff:
            acc_dest = accounts_data['expense'].id
        elif self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts_data['stock_output'].id

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category,'
                              'check if you have installed a chart of accounts.'))
        if not acc_src:
            raise UserError(_('Cannot find a stock input account for the product %s.'
                              '\nYou must define one on the product category, or on the location,'
                              'before processing this operation.') % (self.product_id.display_name))
        if not acc_dest:
            raise UserError(_('Cannot find a stock output account for the product %s.'
                              '\nYou must define one on the product category, or on the location,'
                              'before processing this operation.') % (self.product_id.display_name))
        if not acc_valuation:
            raise UserError(_('You don\'t have any stock valuation account defined on your product category.'
                              '\nYou must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id

        return journal_id, acc_src, acc_dest, acc_valuation

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        # This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
        self.ensure_one()
        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
        is_return = any(m.origin_returned_move_id for m in self.picking_id.move_ids_without_package)
        product_valuation = self.product_id.categ_id.property_stock_valuation_account_id
        analytic_account = self.picking_id.analytic_account_id
        if self.picking_id.is_takeoff and not is_return:
            if product_valuation.id != debit_account_id:
                rslt['debit_line_vals']['analytic_account_id'] = analytic_account.id
        # if the takeoff is returned from customer then we need to reverse the expense entry from our system.
        if self.picking_id.is_takeoff and is_return:
            if product_valuation.id != credit_account_id:
                rslt['credit_line_vals']['analytic_account_id'] = analytic_account.id
        return rslt


StockMove()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    analytic_account_id = fields.Many2one(
        related='move_id.analytic_account_id',
        readonly=True,
        store=True
    )
    is_takeoff = fields.Boolean(
        related='move_id.is_takeoff',
        readonly=True,
        store=True
    )
    takeoff_request_id = fields.Many2one(
        related='move_id.takeoff_line_id.request_id',
        store=True,
        readonly=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        warning = {}
        message = ''
        popup = {}
        if self.picking_id.is_takeoff and self.product_id:
            if not self.product_id.categ_id.budgetary_income_position_id:
                message += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻"
            if not self.product_id.categ_id.budgetary_expense_position_id:
                message += "\n⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧" if message \
                    else "⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧"

            if message:
                warning['title'] = _("Warning for %s") % self.product_id.name
                warning['message'] = message

        if self.picking_id.is_takeoff:
            popup.update(domain={
                'product_id': ['|', ('is_takeoff', '=', True), ('categ_id.is_takeoff', '=', True)]
            })
        if warning:
            popup.update(warning=warning)
        return popup

StockMoveLine()


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        if self.picking_id and self.picking_id.is_takeoff and not new_picking.is_takeoff:
            if self.picking_id.takeoff_id:
                vals['takeoff_line_id'] = return_line.move_id.takeoff_line_id.id
            new_picking.write({
                'is_takeoff': True,
                'sale_order_id': self.picking_id.sale_order_id.id,
                'takeoff_id': self.picking_id.takeoff_id and self.picking_id.takeoff_id.id
            })
        return vals


ReturnPicking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
