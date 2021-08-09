# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'SPS Integration',
    'version': '1.0',
    'category': 'Sales',
    'author'  : "Confianz Global",
    'sequence': 1500,
    'summary': 'The module that manages the SPSIntegration ',
    'description': """
The module that manages the order generated via SPSIntegration
    """,
    'website': 'https://www.confianzit.com',
    'depends': ['sale', 'stock', 'delivery'],
    'data': [
        'views/edi_sftp_config_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
