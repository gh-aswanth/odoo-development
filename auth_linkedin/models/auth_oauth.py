# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AuthOauthProvider(models.Model):
    """Class defining the configuration values of an OAuth2 provider"""

    _inherit = 'auth.oauth.provider'
    _order = 'name'

    is_linkedin = fields.Boolean(string='Use Linkedin Authorization Code Flow', default=False, help="If you want Linkedin Oauth forcefully then tick on check box")
    client_secret = fields.Char(string='Client Secret Password')
