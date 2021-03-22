# -*- coding: utf-8 -*-

import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    email_to = fields.Char('To', help='Message recipients (emails)')
    email_cc = fields.Char('Cc', help='Carbon copy message recipients')

    def action_send_mail(self):
        if self._context.get('mail_with_cc'):
            self.send_with_cc()
            return {'type': 'ir.actions.act_window_close', 'infos': 'mail_sent'}
        return super(MailComposer, self).action_send_mail()

    @api.model
    def default_get(self, fields):
        result = super(MailComposer, self).default_get(fields)
        record = self.env[self._context.get('default_model')].browse(self._context.get('default_res_id'))
        if hasattr(record, 'contact_email') and hasattr(record, 'customer_email') and hasattr(record,
                                                                                              'partner_id') and hasattr(
                record, 'partner_contact_id'):
            if record.contact_email or record.partner_contact_id:
                result['email_to'] = record.contact_email or record.partner_contact_id.email
                result['email_cc'] = record.customer_email or record.partner_id.email
            else:
                result['email_to'] = record.customer_email or record.partner_id.email
        return result

    def send_with_cc(self):
        self.ensure_one()
        Mail = self.env['mail.mail']
        values = {}
        values['recipient_ids'] = [(4, pid.id) for pid in self.partner_ids]
        values['attachment_ids'] = [(4, aid.id) for aid in self.attachment_ids]
        values['subject'] = self.subject
        notif_layout = self._context.get('custom_layout')
        if notif_layout:
            try:
                template = self.env.ref(notif_layout, raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template %s not found when sending template %s. Sending without layouting.' % (
                    notif_layout, self.template_id.name))
            else:
                record = self.env[self.model].browse(self.res_id)
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(
                        dict(body=self.body, record_name=record.display_name)),
                    'model_description': self.env['ir.model']._get(record._name).display_name,
                    'company': 'company_id' in record and record['company_id'] or self.env.company,
                    'record': record,
                }
                body = template.render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                values['body_html'] = self.env['mail.thread']._replace_local_links(body)
                values['email_to'] = self.email_to
                values['email_cc'] = self.email_cc
                values['reply_to'] = self.email_from
                values['auto_delete'] = self.template_id.auto_delete
        mail = Mail.create(values)
        if self._context.get('force_send'):
            mail.send()
        email_to = [*self.partner_ids.mapped('email')]
        if self.email_to:
            email_to.append(self.email_to)
        bodys = f"""<div style="margin:0px;padding: 0px;">
                    <p style="padding: 0px; font-size: 12px;line-height: 1.4;">
                        <b>from:</b> {mail.email_from.replace('"', '')}<br/>
                        <b>replay-to:</b> {mail.reply_to.replace('"', '')}<br/>
                        <b>to:</b> {', '.join(email_to)}<br/>
                        <b>cc:</b> {mail.email_cc}<br/>
                        <b>subject:</b> {mail.subject}<br/>
                    </p>
                  </div>
                <br/>""" + self.body + "<br/>"
        record.message_post(body=bodys)


MailComposer()
