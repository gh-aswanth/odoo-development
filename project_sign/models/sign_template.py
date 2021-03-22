# -*- coding:utf-8 -*-

from odoo import models, fields, api, _

class SignTemplate(models.Model):
    _inherit = 'sign.template'
     
    project_id = fields.Many2one('project.project')
