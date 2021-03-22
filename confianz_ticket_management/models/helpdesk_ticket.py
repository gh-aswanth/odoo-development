# -*- coding:utf-8 -*-

import re

from odoo import models, fields, api,tools, _


class HelpdeskTickets(models.Model):
    _inherit = 'helpdesk.ticket'

    priority = fields.Selection(selection_add=[('4', 'Extreme')])
    reported_time = fields.Datetime(string='Reported Time')
    fix = fields.Text()
    reason = fields.Text()
    issue_reference_1 = fields.Selection([('product','Product'), ('project','Project'), ('account','Account')], string="Reference 1")
    issue_ref1_product_id = fields.Many2one('product.product', string='Reference Product')
    issue_ref1_invoice = fields.Many2one('account.invoice', string='Reference Invoice')
    issue_ref1_project = fields.Many2one('project.project', string='Reference Project')
    issue_reference_2 = fields.Selection([('invoice_line','Invoice Line')], string="Reference 2")
    issue_ref2_invoice_line = fields.Many2one('account.invoice.line', string='Reference Invoice Line')
    stage_active = fields.Boolean(related="stage_id.is_close")
    date_of_incident = fields.Datetime(string='Date of Incident')
    reported_by = fields.Many2one('res.partner', string='Reported By')
    contact_ids = fields.Many2many('res.partner', string='Contacts')
    action_taken_id = fields.Many2one('ticket.action.taken', string='Action Taken')
    technician_id = fields.Many2one('res.partner', string='Technician')
    reported_by_phone = fields.Char(related='reported_by.phone', string='Contact Phone')
    manager_id = fields.Many2one('res.partner', string='Manager')
    internal_follow_up = fields.Text(string='Internal Follow Up')
    external_follow_up = fields.Text(string='External follow up')
    close_date = fields.Datetime(string="Close date", compute="_compute_close_date", store=True)

    @api.onchange('issue_reference_1','issue_reference_2','issue_ref1_invoice')
    def _onchange_date_clear(self):
        if self.issue_reference_1 in ['product', 'project']:
            self.issue_ref1_product_id = self.issue_ref1_project = None
            self.issue_reference_2 = None
            self.issue_ref1_invoice = self.issue_ref2_invoice_line = None
        
        elif self.issue_reference_1 == 'account':
            self.issue_ref1_product_id = self.issue_ref1_project = None
            self.issue_reference_2 = 'invoice_line'
            self.issue_ref2_invoice_line = None

    @api.multi
    def ticket_get_restored(self):
        self.ensure_one()
        initial_stage = self.env['helpdesk.stage'].search([('team_ids', 'in', self.team_id.ids)], order="sequence asc", limit=1)
        for ticket in self:
            ticket.write({'stage_active': False, 'stage_id': initial_stage.id, 'kanban_state':'normal'})

    @api.depends('stage_id.is_close')
    def _compute_close_date(self):
        for rec in self:
            if rec.stage_id.is_close:
                rec.close_date = fields.Datetime.now()

    @api.model
    def create(self, vals):
        ticket = super(HelpdeskTickets, self).create(vals)
        if ticket.manager_id:
            ticket.message_subscribe(partner_ids=ticket.manager_id.ids)
        return ticket

    @api.multi
    def write(self, vals):
        if vals.get('manager_id'):
            self.message_subscribe([vals['manager_id']])
        res = super(HelpdeskTickets, self).write(vals)
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        body = tools.html2plaintext(msg.get('body'))
        re_match = re.match(r"(.*)^-- *$", body, re.MULTILINE | re.DOTALL | re.UNICODE)
        desc = re_match.group(1) if re_match else None
        parent_customer = self.env['res.partner'].browse([msg.get('author_id')]).commercial_partner_id
        email_split = tools.email_split(msg.get('email_from'))
        
        values = dict(custom_values or {},
                      reported_time = msg.get('date'),
                      reported_by = msg.get('author_id'),
                      description = desc or body)

        create_context = dict(self.env.context or {})

        ticket = super(HelpdeskTickets, self.with_context(create_context)).message_new(msg, custom_values=values)
        partner_ids = [x for x in ticket._find_partner_from_emails(tools.email_split(msg.get('cc') or '')) if x]
        ticket_contacts = [i for i in partner_ids if i in parent_customer.child_ids.ids]
        
        ticket.write({'partner_id': parent_customer.id,
                      'partner_name':msg.get('email_from').split('<')[0],
                      'partner_email':email_split[0] if email_split else parent_customer.email,
                      'contact_ids':[(6,0, ticket_contacts)]})
        
        if partner_ids:
            ticket.message_subscribe(partner_ids)
        return ticket

    @api.model
    def get_stage_ids(self):
        result = self.env['helpdesk.stage'].search([('team_ids','in',self.team_id.ids)])
        return result