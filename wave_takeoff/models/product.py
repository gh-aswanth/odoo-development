# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_takeoff = fields.Boolean(company_dependent=True)


ProductTemplate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
