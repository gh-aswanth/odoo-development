# -*- coding: utf-8 -*-

from lxml import etree
from lxml.html import builder as html
from lxml.builder import E

from werkzeug.urls import url_encode
from odoo import _, api, fields, models


class Invites(models.TransientModel):
    """ Wizard to invite partners (or channels) and make them followers. """
    _inherit = 'mail.wizard.invite'
    _description = 'Invite wizard'

    @api.model
    def default_get(self, fields):
        result = super(Invites, self).default_get(fields)
        if 'message' not in fields:
            return result
        user_name = self.env.user.name_get()[0][1]
        model = result.get('res_model')
        res_id = result.get('res_id')
        if model and res_id:
            document = self.env['ir.model']._get(model).display_name
            title = self.env[model].browse(res_id).display_name
            layout = self.env.ref('mail_extension.mail_post')
            web_root_url = self.env['ir.config_parameter'].get_param('web.base.url')
            url = '%s/mail/view?%s' % (web_root_url,url_encode({'model':model,'res_id':res_id}))
            mbody = layout.render({'user_name':user_name,
                                   'model_description': self.env['ir.model']._get(model).display_name,
                                   'document_name':document,
                                   'title':title,
                                   'url':url}, engine='ir.qweb', minimal_qcontext=True)
            result['message'] = mbody
            return result
        else:
            msg_fmt = _('%(user_name)s invited you to follow a new document.')
            text = msg_fmt % locals()
            message = html.DIV(
                html.P(_('Hello,')),
                html.P(text)
            )
            result['message'] = etree.tostring(message)
            return result

