# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_takeoff = fields.Boolean(company_dependent=True)


ProductTemplate()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if self._context.get('takeoff_order', False):
            args = args or []
            sale_order = self._context.get('takeoff_order')
            so_lines = self.env['sale.order.line'].search([('order_id', '=', sale_order)])
            category_list = so_lines.mapped('product_id.categ_id').filtered(lambda r: r.budgetary_expense_position_id).ids
            domain = ['&', ('default_code', operator, name), ('categ_id', 'in', category_list)]
            ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
            return self.browse(ids).name_get()
        return super(ProductProduct, self)._name_search(name, args, operator, limit, name_get_uid)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
