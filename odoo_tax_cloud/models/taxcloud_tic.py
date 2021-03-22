# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TaxcloudTic(models.Model):
    _name = 'taxcloud.tic'

    name = fields.Char(string="Description")
    tic_code = fields.Char(string="TIC code")

    def name_get(self):
        data = []
        for tic in self:
            display_value = ''
            display_value += '['
            display_value += tic.tic_code or ""
            display_value += ']'
            display_value += ' '
            display_value += tic.name or ""
            data.append((tic.id, display_value))
        return data

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            recs = self.search([('tic_code', operator, name)] + args, limit=limit)
        return recs.name_get()