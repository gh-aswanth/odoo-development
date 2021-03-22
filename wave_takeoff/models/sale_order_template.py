# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    is_takeoff = fields.Boolean()

class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    takeoff_qty = fields.Float(default=0.00)