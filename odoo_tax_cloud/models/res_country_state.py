# -*- coding: utf-8 -*-

from odoo import models, api


class res_country(models.Model):
    _inherit = 'res.country.state'

    def name_get(self):
        data = []
        for state in self:
            display_value = ''
            display_value += state.name or ""
            display_value += ' ['
            display_value += state.code or ""
            display_value += ']'
            data.append((state.id, display_value))
        return data

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        return recs.name_get()
