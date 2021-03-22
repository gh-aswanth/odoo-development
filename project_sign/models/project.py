#-*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    agreement_sign_ids =fields.Many2many('sign.request.item',string="Signatory", copy=False)
    agreement_id = fields.Many2one('sign.request', string="Agreement", copy=False)
    signed_state = fields.Selection([
                             ('draft', 'Draft'),
                             ('waiting', 'Waiting'),
                             ('signed', 'Signed')
                             ], default='draft', track_visibility='onchange',string="Sign State", copy=False)  
    
    
    @api.multi 
    def action_send_agreement(self):
        return{
                    'type': 'ir.actions.act_window',
                    'name': _('Sign'),
                    'res_model': 'project.employee.sign',
                    'target': 'new',
                    'view_mode': 'form',
                    'view_type': 'form',
                   }
                   
    @api.model
    def create_timesheet_invoice(self):
        projects = self.search([('project_type', '=', 'time_sheet'), ('active', '=', True), ('next_billing_date', '=', fields.Date.today()), ('state', '=', 'proposal_accepted'), ('signed_state', '=', 'signed')])
        customer_ids = projects.mapped(lambda partner: partner.partner_id)
        for customer in customer_ids:
            for project in projects.filtered(lambda project: project.partner_id == customer):
                not_invoiced_timesheets = project.analytic_account_id.line_ids.filtered(lambda line: line.project_id.id == project.id and line.timesheet_invoice_id.id == False and line.billable == True)
                if len(not_invoiced_timesheets) != 0:
                    journal_account_id = project.get_default_sale_jrnl_acc().id
                    invoice_id = self.env['account.invoice'].create({
                                                'partner_id': customer.id,
                                                'project_id': project.id,
                                                'type': 'out_invoice',
                                                'date_invoice': fields.Date.today(),
                                                'origin': project.name,
                                                'move_name': project.get_next_project_sequence_number(),
                                                'invoice_line_ids': [(0,0,{
                                                      'name': project.compute_description(res_id=timesheet),
                                                      'account_id': journal_account_id,
                                                      'quantity': timesheet.unit_amount,
                                                      'price_unit': timesheet.employee_id.employee_rate * timesheet.unit_amount,
                                                      })for timesheet in not_invoiced_timesheets]})
                    project.send_alerts_and_calc_bill_date(invoice_id=invoice_id)
                    for timesheet in not_invoiced_timesheets:
                        timesheet.write({'timesheet_invoice_id': invoice_id.id})
        return True

    @api.model
    def create_fte_invoice(self):
        projects = self.search([('project_type', '=', 'fte'), ('active', '=', True), ('next_billing_date', '=', fields.Date.today()), ('state', '=', 'proposal_accepted'), ('signed_state', '=', 'signed')])
        customer_ids = projects.mapped(lambda partner: partner.partner_id)
        for customer in customer_ids:
            for project in projects.filtered(lambda project: project.partner_id == customer):
                journal_account_id = project.get_default_sale_jrnl_acc().id
                invoice_id = self.env['account.invoice'].create({
                                                            'partner_id': customer.id,
                                                            'project_id': project.id,
                                                            'type': 'out_invoice',
                                                            'date_invoice': fields.Date.today(),
                                                            'origin': project.name,
                                                            'move_name': project.get_next_project_sequence_number(),
                                                            'invoice_line_ids': [(0,0,{
                                                                          'product_id': project.product_id.id,
                                                                          'name': project.compute_description(),
                                                                          'account_id': journal_account_id,
                                                                          'quantity': 1,
                                                                          'price_unit': project.project_cost,
                                                                          })]})
                project.send_alerts_and_calc_bill_date(invoice_id=invoice_id)
        return True
