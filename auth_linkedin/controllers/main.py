# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import logging

import urllib.parse
import werkzeug.utils
import json

from odoo import api, http, SUPERUSER_ID, _
from odoo import registry as registry_get
from odoo.http import request

from odoo.addons.portal.controllers.web import Home
from odoo.addons.auth_oauth.controllers.main import OAuthLogin, OAuthController

_logger = logging.getLogger(__name__)




# class Website(Home):

    # @http.route(website=True, auth="public")
    # def web_login(self, redirect=None, *args, **kw):
    #     values = request.params.copy()
    #     if request.httprequest.method == 'POST':
    #         user_id = request.env['res.users'].sudo().search([('login','=', request.params['login'])])
    #         if user_id and user_id.force_oauth:
    #             values['warning'] = _("Unable to login here. Login through this portal is not allowed for user '%s'"%(request.params['login']))
    #             values.pop('password')
    #             oauth_login = OAuthLogin()
    #             values['providers'] = oauth_login.list_providers()
    #             response = request.render('web.login', values)
    #             response.headers['X-Frame-Options'] = 'DENY'
    #             return response
    #     response = super(Website, self).web_login(redirect=redirect, *args, **kw)
    #     return response

#----------------------------------------------------------
# Controller
#----------------------------------------------------------
class AzureOAuthLogin(OAuthLogin):
    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return_url = urllib.parse.urljoin(base_url, 'auth_oauth/signin')
            state = self.get_state(provider)
            params = dict(
                response_type=provider['is_linkedin'] and 'code' or 'token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.url_encode(params))
        return providers


class AzureOAuthController(OAuthController):

    @http.route()
    def signin(self, **kw):
        if kw.get('code'):
            state = json.loads(kw.get('state'))
            dbname = state['d']
            context = state.get('c', {'no_user_creation': True})
            provider_id = state['p']
            registry = registry_get(dbname)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, context)
                provider_obj = env['auth.oauth.provider']
                provider = provider_obj.sudo().browse(provider_id)
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                return_url = urllib.parse.urljoin(base_url, 'auth_oauth/signin')
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                ms_params = dict(
                        client_id=provider.client_id,
                        redirect_uri=return_url,
                        scope=provider.scope,
                        state=json.dumps(state),
                        code=kw.get('code'),
                        grant_type='authorization_code',
                        client_secret=provider.client_secret,
                    )
                req = requests.post(provider.validation_endpoint, headers=headers, data=werkzeug.url_encode(ms_params))
                response = req.json()
                _logger.info('Linkedin callback......')
                _logger.info(response)

                if response:
                    access_token = response['access_token']
                    if provider.is_linkedin:
                        user_id = False
                        email = False
                        try:
                            url = "https://api.linkedin.com/v2/me?projection=(id)"
                            headers = {
                                'Authorization': 'Bearer %s' % access_token,
                            }
                            response = requests.request("GET", url, headers=headers, data={}).json()
                            _logger.info('Auth2.0 user id fetch')
                            _logger.info(response)
                            user_id = response.get('id')
                        except Exception as e:
                            pass
                        try:
                            url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
                            headers = {
                                'Authorization': 'Bearer %s' % access_token,
                            }
                            response = requests.request("GET", url, headers=headers, data={}).json()
                            _logger.info('Auth2.0 user email address fetch')
                            _logger.info(response)
                            email = response.get('elements', [{}])[0].get('handle~', {}).get('emailAddress', False)
                        except Exception as e:
                            pass

                        kw['user_id'] = user_id
                        kw['email'] = email
                        kw['access_token'] = access_token

                        user = env['res.users'].sudo().search([('active', '=', True), ('login', '=', email)])
                        print('Linked User:', user)
                        if user:
                            if not user.oauth_uid and not user.oauth_provider_id.id:
                                user.write({'oauth_uid': kw['user_id'], 'oauth_provider_id': state['p']})

        return super(AzureOAuthController, self).signin(**kw)
