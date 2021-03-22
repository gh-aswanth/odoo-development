# -*- coding : utf-8 -*-
from odoo import models, fields, api,_

class SignSendRequest(models.TransientModel):
    _inherit = 'sign.send.request'
    
    def send_request(self):
        rec = super(SignSendRequest, self).send_request()
        send_doc = self.template_id.project_id
        signer_ids = self.env['sign.request.item'].search([('sign_request_id','=',rec['res_id'])])
        send_doc.write({
                        'signed_state':'waiting',
                        'agreement_id' : rec['res_id'],
                        'agreement_sign_ids':[(6,0,signer_ids.ids)]
                        })                                       
        return rec
        
    @api.model
    def default_get(self,fields):
        res=super(SignSendRequest,self).default_get(fields)
        project_id = self.env['sign.template'].browse(self.env.context.get('active_id','False')).project_id
        signer = []
        signers = map(lambda rec:rec[2],res['signer_ids'])
        if project_id:
            agreement = project_id.customer_accepted_proposal_id.attachment_ids
            for sg in list(signers):
                role =  self.env['sign.item.role'].browse(sg.get('role_id'))
                if role.name.lower() == 'customer':
                    sg.update({'partner_id': project_id.partner_id.id})
                    signer.append((0, 0, sg))
                elif role.name.lower() == 'employee':
                    employee_id = self.env['hr.employee'].search([('user_id.id', 'in', \
                            [project_id.approval_1_user_id.id, project_id.approval_2_user_id.id])], limit=1)
                    if employee_id and employee_id.address_id:
                        sg.update({'partner_id': employee_id.address_id.id})
                    signer.append((0, 0, sg))
                elif role.name.lower() == 'company':
                    company_partner_id = self.env['res.partner'].search(
                        [('name', 'ilike', self.env.user.company_id.name)])
                    if company_partner_id:
                        sg.update({'partner_id': company_partner_id.id})
                    signer.append((0, 0, sg))
                else:
                    sg.update({'partner_id': False})
                    signer.append((0, 0, sg))
            res.update({'signer_ids':signer,
                        'filename':agreement.name.split('.')[0],
                        'subject':_("MNDA from %s") % (project_id.company_id.name),
                       })
            if not signer:
                res.update({'signer_id': project_id.partner_id.id,
                            'filename': agreement.name.split('.')[0],
                            'subject': _("MNDA from %s") % (project_id.company_id.name),
                            })
        return res

    def sign_directly(self):
        res = self.create_request()
        request = self.env['sign.request'].browse(res['id'])
        user_item = request.request_item_ids.filtered(
            lambda item: item.partner_id == item.env.user.partner_id)[:1]
        if self.template_id.project_id:
            send_doc = self.template_id.project_id
            send_doc.write({
                'signed_state': 'waiting',
                'agreement_id': res['id'],
                'agreement_sign_ids': [(6, 0, request.request_item_ids.ids)]
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'sign.SignableDocument',
            'name': _('Sign'),
            'context': {
                'id': request.id,
                'token': user_item.access_token,
                'sign_token': user_item.access_token,
                'create_uid': request.create_uid.id,
                'state': request.state,
            },
        }
