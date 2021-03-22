# -*- coding:utf-8 -*-

from odoo import models, fields, api, _

class SignRequest(models.Model):
    _inherit = 'sign.request'

    @api.multi
    def action_signed(self):
        super(SignRequest, self).action_signed()
        project_doc = self.template_id.project_id
        project_doc.write({'signed_state':'signed'})
            

    
    
