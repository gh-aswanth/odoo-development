# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_show_materials = fields.Boolean(string='Show Materials', implied_group='Jobs.group_show_materials',
                                          default=True)
    group_show_equipments = fields.Boolean(string="Show Equipments", implied_group='Jobs.group_show_equipments',
                                           default=True)
    group_show_labours = fields.Boolean(string="Show Labours", implied_group='Jobs.group_show_labours', default=True)
    group_show_sub_contracts = fields.Boolean(string="Show Sub-Contract", implied_group='Jobs.group_show_sub_contracts',
                                              default=True)


ResConfigSettings()
