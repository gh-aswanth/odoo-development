# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    is_takeoff = fields.Boolean()

    def write(self, vals):
        res = super(SaleOrderTemplate, self).write(vals)
        for template in self:
            section = False
            for line in template.sale_order_template_line_ids:
                if line.display_type:
                    section = line.name

                line.write({'section': section})
            else:
                section = False
        return res

class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    takeoff_qty = fields.Float(default=0.00)
    section = fields.Char()

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        warning = {}
        message = ''
        popup = {}

        if self.product_id:
            name = self.product_id.display_name
            if self.product_id.description_sale:
                name += '\n' + self.product_id.description_sale
            self.name = name
            self.price_unit = self.product_id.lst_price
            self.product_uom_id = self.product_id.uom_id.id

        if self.sale_order_template_id.is_takeoff and self.product_id:
            if not self.product_id.categ_id.budgetary_income_position_id:
                message += "⚠ 𝗖𝗮𝗻'𝘁 𝗳𝗶𝗻𝗱 𝗯𝘂𝗱𝗴𝗲𝘁𝗮𝗿𝘆 𝗶𝗻𝗰𝗼𝗺𝗲 𝗽𝗼𝘀𝗶𝘁𝗶𝗼𝗻"
            if not self.product_id.categ_id.budgetary_expense_position_id:
                message += "\n⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧" if message \
                    else "⚠ 𝗖𝗮𝗻'𝘁 𝐟𝐢𝐧𝐝 𝐛𝐮𝐝𝐠𝐞𝐭𝐚𝐫𝐲 𝐞𝐱𝐩𝐞𝐧𝐬𝐞 𝐩𝐨𝐬𝐢𝐭𝐢𝐨𝐧"

            if message:
                warning['title'] = _("Warning for %s") % self.product_id.name
                warning['message'] = message

        if self.sale_order_template_id.is_takeoff:
            popup.update(domain={'product_id': ['|', ('is_takeoff', '=', True), ('categ_id.is_takeoff', '=', True)]})
        if warning:
            popup.update(warning=warning)
        return popup