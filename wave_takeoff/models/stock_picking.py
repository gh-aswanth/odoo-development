# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    is_need_takeoff = fields.Boolean()
    count_takeoff = fields.Integer(
        string="Number of Take Off Orders",
        compute='_get_takeoff_count'
    )

    def _get_takeoff_count(self):
        data = self.env['stock.picking'].read_group([
            ('is_takeoff', '=', True), ('state', 'not in', ['done', 'cancel'])],
            ['picking_type_id'], ['picking_type_id'])

        count = {x['picking_type_id'][0]: x['picking_type_id_count'] for x in data if x['picking_type_id']}
        for record in self:
            record['count_takeoff'] = count.get(record.id, 0)

    def _get_action(self, action_xmlid):
        action = super(PickingType, self)._get_action(action_xmlid)
        if self._context.get('takeoff_source', False):
            action['context'].pop('search_default_available')
            action['domain'] = [('is_takeoff', '=', True)]
            action['display_name'] += ' [Take Off]'
        return action

PickingType()

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    takeoff_id = fields.Many2one('takeoff.request')


ProcurementGroup()


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['takeoff_line_id']
        return fields

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(StockRule, self)._prepare_purchase_order(company_id, origins, values)
        group = values[0]['group_id'] if res.get('group_id') else False
        if group and group.takeoff_id:
            res['sale_id'] = group.takeoff_id.order_id.id
            res['is_takeoff'] = True
            res['takeoff_id'] = group.takeoff_id.id
        return res

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super(StockRule, self)._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, values, po)
        if po and po.is_takeoff:
            res['takeoff_line_id'] = values.get('takeoff_line_id')
        return res

StockRule()


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_takeoff = fields.Boolean(copy=False)
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        copy=False
    )
    analytic_account_id = fields.Many2one(
        related='sale_order_id.analytic_account_id',
        string='Analytic Account'
    )
    can_create_takeoff = fields.Boolean(related='picking_type_id.is_need_takeoff', readonly=True)
    takeoff_id = fields.Many2one('takeoff.request', copy=False)

    def check_budgetary_position(self, moves):
        message = ''
        if moves.filtered(lambda r: not r.product_id.categ_id.budgetary_income_position_id).ids:
            message += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻"
        if moves.filtered(lambda r: not r.product_id.categ_id.budgetary_expense_position_id).ids:
            message += "\n⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧" if message else "⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧"
        return message

    def check_takeoff_validation(self):
        for pick in self:
            if pick.move_ids_without_package and pick.is_takeoff:
                if pick.move_ids_without_package.filtered(lambda r: not r.product_id.is_takeoff and not r.product_id.categ_id.is_takeoff).ids:
                    raise UserError(_("Stock move contains products that are not takeoffs, please revise and try again"))
                msg = pick.check_budgetary_position(pick.move_ids_without_package)
                if msg:
                    raise UserError(_(msg))
            if pick.move_line_ids_without_package and pick.is_takeoff:
                if pick.move_line_ids_without_package.filtered(lambda r: not r.product_id.is_takeoff and not r.product_id.categ_id.is_takeoff).ids:
                    raise UserError(_("Stock move contains products that are not takeoffs, please revise and try again"))
                msg = pick.check_budgetary_position(pick.move_line_ids_without_package)
                if msg:
                    raise UserError(_(msg))
        return True

    def action_confirm(self):
        self.check_takeoff_validation()
        return super(StockPicking, self).action_confirm()

    def button_validate(self):
        self.check_takeoff_validation()
        return super(StockPicking, self).button_validate()

    @api.onchange('is_takeoff')
    def _onchange_is_takeoff(self):
        if not self.is_takeoff:
            self.sale_order_id = False


StockPicking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
