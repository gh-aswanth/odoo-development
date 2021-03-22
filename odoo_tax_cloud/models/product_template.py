# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    taxcloud_tic_ctg = fields.Many2one('taxcloud.tic', string="TaxCloud Category")
