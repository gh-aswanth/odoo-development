# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    budgetary_expense_position_id = fields.Many2one(
        'account.budget.post',
        string="Budgetary Expense",
        company_dependent=True
    )
    budgetary_income_position_id = fields.Many2one(
        'account.budget.post',
        string="Budgetary Income",
        company_dependent=True
    )
    is_takeoff = fields.Boolean(company_dependent=True)

    @api.onchange('budgetary_income_position_id', 'budgetary_expense_position_id', 'property_account_income_categ_id', 'property_account_expense_categ_id', 'property_stock_valuation_account_id')
    def _onchange_account_budgetary_position(self):
        msg = ''
        if self.budgetary_income_position_id:
            if self.property_account_income_categ_id not in self.budgetary_income_position_id.account_ids:
                self.property_account_income_categ_id = False
                msg += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝐢𝐧𝐜𝐨𝐦𝐞 𝗮𝗰𝗰𝗼𝘂𝗻𝘁 𝗶𝗻 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻\n"
            if self.property_stock_valuation_account_id not in self.budgetary_income_position_id.account_ids:
                self.property_stock_valuation_account_id = False
                msg += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝘀𝘁𝗼𝗰𝗸 𝘃𝗮𝗹𝘂𝗮𝘁𝗶𝗼𝗻 𝗮𝗰𝗰𝗼𝘂𝗻𝘁 𝗶𝗻 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻\n"
            if msg:
                msg += '\n'
                msg += f"\t𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐚𝐜𝐜𝐨𝐮𝐧𝐭𝐬 𝐢𝐧 {self.budgetary_income_position_id.name}\n"
                for i, act in enumerate(self.budgetary_income_position_id.account_ids, 1):
                    msg += f'\t\t{i}. {act.code} {act.name}\n'
                msg += '\n'
        if self.budgetary_expense_position_id:
            if self.property_account_expense_categ_id not in self.budgetary_expense_position_id.account_ids:
                self.property_account_expense_categ_id = False
                msg += "⚠ 𝐜𝐚𝐧'𝐭 𝐟𝐢𝐧𝐝 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐚𝐜𝐜𝐨𝐮𝐧𝐭 𝐢𝐧 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧\n"
                msg += '\n'
                msg += f"\t𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐚𝐜𝐜𝐨𝐮𝐧𝐭𝐬 𝐢𝐧 {self.budgetary_expense_position_id.name}\n"
                for i, act in enumerate(self.budgetary_expense_position_id.account_ids, 1):
                    msg += f'\t\t{i}. {act.code} {act.name}\n'

        if msg:
            return {'warning': {'title': _('𝐖𝐫𝐨𝐧𝐠 𝐕𝐚𝐥𝐮𝐞𝐬'), 'message': _(msg)}}


ProductCategory()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

