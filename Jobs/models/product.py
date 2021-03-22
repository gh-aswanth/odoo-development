# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    boq_type = fields.Selection(
        [('material', "Material"),
         ('equipment', "Equipment / Machinery"),
         ('labour', "Labour")],
        string="BOQ Type")


ProductTemplate()
