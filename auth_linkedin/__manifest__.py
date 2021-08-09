# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Linkedin OAuth2 Authentication',
    'summary': 'Linkedin OAuth',
    'sequence': 100,
    'license': 'OEEL-1',
    'version': '1.0',
    'author': 'Odoo Inc',
    'description': """
Azure: Allow users to login through OAuth2 Provider.
====================================================
""",
    'category': 'Extra Tools',
    'depends': ['base', 'auth_oauth'],
    'data': [
        'data/auth_oauth_data.xml',
        'views/auth_oauth_views.xml',
        'views/login_templates.xml',
        'views/res_users_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
