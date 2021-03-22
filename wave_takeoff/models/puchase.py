# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_takeoff = fields.Boolean(copy=False)
    sale_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        copy=False
    )
    can_create_takeoff = fields.Boolean(related='picking_type_id.is_need_takeoff', readonly=True)
    takeoff_id = fields.Many2one('takeoff.request')

    @api.onchange('is_takeoff')
    def _onchange_is_takeoff(self):
        if not self.is_takeoff and self.order_line:
            self.sale_id = False
        return {
            'domain': {
                'sale_id': [('analytic_account_id', '!=', False)] if self.is_takeoff else []
            }
        }

    def check_budgetary_position(self, order_lines):
        message = ''
        if order_lines.filtered(lambda r: not r.product_id.categ_id.budgetary_income_position_id).ids:
            message += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻"
        if order_lines.filtered(lambda r: not r.product_id.categ_id.budgetary_expense_position_id).ids:
            message += "\n⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧" if message else "⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧"
        return message

    def check_takeofff_validation(self):
        for order in self:
            if order.is_takeoff:
                if order.order_line.filtered(lambda r: not r.product_id.is_takeoff and not r.product_id.categ_id.is_takeoff).ids:
                    raise UserError(_("Stock move contains products that are not takeoffs, please revise and try again."))
                msg = order.check_budgetary_position(order.order_line)
                if msg:
                    raise UserError(_(msg))

        return True

    def button_confirm(self):
        self.check_takeofff_validation()
        res = super(PurchaseOrder, self).button_confirm()
        for rec in self:
            rec.sale_id._compute_purchase_order_count()
        return res


    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        if self.is_takeoff:
            res['is_takeoff'] = True
            res['sale_order_id'] = self.sale_id.id
            res['takeoff_id'] = self.group_id.takeoff_id.id
        return res


PurchaseOrder()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    takeoff_line_id = fields.Many2one('takeoff.request.line')

    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for line in res:
            line.update({'takeoff_line_id': self.takeoff_line_id.id})
        return res

    @api.onchange('product_id')
    def _onchange_product_id(self):
        warning = {}
        message = ''
        popup = {}
        if self.order_id.is_takeoff and self.product_id:
            if not self.product_id.categ_id.budgetary_income_position_id:
                message += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻"
            if not self.product_id.categ_id.budgetary_expense_position_id:
                message += "\n⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧" if message \
                    else "⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧"

            if message:
                warning['title'] = _("Warning for %s") % self.product_id.name
                warning['message'] = message

        if self.order_id.is_takeoff:
            popup.update(domain={'product_id': ['|', '&', ('is_takeoff', '=', True), ('purchase_ok', '=', True), ('categ_id.is_takeoff', '=', True), ('purchase_ok', '=', True)]})
        if warning:
            popup.update(warning=warning)
        return popup


PurchaseOrderLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
