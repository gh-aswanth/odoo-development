# -*- coding : utf-8 -*-
from odoo import models, fields, api,_
import base64

from odoo.exceptions import ValidationError

class ProjectEmployeeSign(models.TransientModel):
    _name = 'project.employee.sign'
    _description = 'Project Agreement Wizard'

    proposal_file = fields.Many2one('ir.attachment')

    @api.model
    def default_get(self,fields):
        res = super(ProjectEmployeeSign,self).default_get(fields)
        project_id =self.env['project.project'].browse(self.env.context.get('default_project_id', False))
        proposal_version = project_id.customer_accepted_proposal_id
        if self._context.get('active_model') == 'project.project':
            res.update({'proposal_file' : proposal_version.attachment_ids.id})
        return res


    def send_request(self):
        for proposal in self:
            str_data = str(proposal.proposal_file.datas)
            pdf_data_url = "data:application/pdf;base64,"+str(str_data[2:len(str_data)-1])
            project_ctx =self._context.copy()
            sign_template_obj = self.env['sign.template']
            data = sign_template_obj.with_context(project_ctx).upload_template(name=str(proposal.proposal_file.datas_fname),dataURL=str(pdf_data_url),active=False)
   
            return {
                    'type': "ir.actions.client",
                    'tag': 'sign.Template',
                    'name': _("New Template"),
                    'context': {
                                'id': data['template'],
                                'to_send_to_user': True
                               }
                   }


