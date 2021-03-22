# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import ValidationError
from .api import TaxcloudApi

class ResDiscountSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_tax_cloud = fields.Boolean(related="company_id.tax_cloud_act", readonly=False)
    tax_cloud_id = fields.Char(config_parameter='tax_cloud_id')
    tax_cloud_key = fields.Char(config_parameter='tax_cloud_key')

    def set_values(self):
        super(ResDiscountSettings, self).set_values()
        if not self.so_tax_cloud:
            self.env['taxcloud.tic'].search([]).sudo().unlink()

    def sync_taxcloud_category(self):
        config_parm = self.env['ir.config_parameter']
        Api = TaxcloudApi(api_login_id=config_parm.get_param('tax_cloud_id'), api_key=config_parm.get_param('tax_cloud_key'))
        if Api.error:
            raise ValidationError(Api.error)
        tic_category_data = Api._get_taxcloud_tics()
        tic_object = self.env['taxcloud.tic'].sudo()
        tic_object.create(tic_category_data)
        return True
