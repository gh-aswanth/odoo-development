# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import requests
import odoo
from odoo import api, models, fields
from odoo.addons import base

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    force_oauth = fields.Boolean(string='Disable local Authentication',
                            help='Use this if you want to force the user to use external authentication, such as Azure')

    # @api.model
    # def _auth_oauth_validate(self, provider, access_token):
    #     """ return the validation data corresponding to the access token """
    #     oauth_provider = self.env['auth.oauth.provider'].browse(provider)
    #     if provider.is_linkedin:
    #         user = self
    #         try:
    #             url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
    #             headers = {
    #                 'Authorization': 'Bearer %s' % access_token,
    #             }
    #             response = requests.request("GET", url, headers=headers, data={}).json()
    #             user = self.search([('active', '=', True), ('login', '=', response['elements']['handle~']['emailAddress'])])
    #         except Exception as e:
    #             pass
    #         if not user:
    #             raise Exception('Token Error')
    #         return {'user_id': user.id}
    #     return super(ResUsers, self)._auth_oauth_validate(provider, access_token)

    @api.model
    def auth_oauth(self, provider, params):
        provider_obj = self.env['auth.oauth.provider']
        provider_id = provider_obj.sudo().browse(provider)
        if provider_id.is_linkedin:
            access_token = params.get('access_token')
            if not access_token:
                return super(ResUsers, self).auth_oauth(provider, params)

            validation = params
            # retrieve and sign in user
            login = self._auth_oauth_signin(provider, validation, params)
            if not login:
                raise odoo.exceptions.AccessDenied()
            # return user credentials
            return (self.env.cr.dbname, login, access_token)
        return super(ResUsers, self).auth_oauth(provider, params)





