# -*- coding: utf-8 -*- 
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'
   
    @api.model
    def invoice_project_milestones(self):
        today_uninvoiced_rec = self.search([('start_date', '=', fields.Date.today()),\
                        ('invoiced', '=', False), ('active', '=', True),\
                        ('project_id.state', '=', 'proposal_accepted'),\
                        ('project_id.signed_state', '=', 'signed')])
        for rec in today_uninvoiced_rec:
            invoice = rec.create_milestone_invoice(cron_mode='on')
            project_id = rec.project_id
            project_id.send_invoice_alerts(invoice_id=invoice, \
                            invoice_alert_ids=project_id.invoice_alert_ids)
        return True
        
        
        
        
        
        
        
        
        
