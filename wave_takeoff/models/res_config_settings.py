# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_request_template_id = fields.Many2one(
        'sale.order.template',
        default_model='takeoff.request',
        string='Default Template'
    )
    default_qty_fully_available = fields.Many2one(
        'stock.location.route',
        default_model='takeoff.request',
        string='Quantity Fully Available'
    )
    default_qty_partially_available = fields.Many2one(
        'stock.location.route',
        default_model='takeoff.request',
        string='Quantity partially Available'
    )
    default_qty_not_available = fields.Many2one(
        'stock.location.route',
        default_model='takeoff.request',
        string='Quantity Not Available'
    )
    default_inventory_users_ids = fields.Many2many(
        'res.users',
        default_model='takeoff.request',
        string='Inventory Users'
    )

ResConfigSettings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: