# -*- coding: utf-8 -*-

{
    'name': 'Wave Takeoff',
    'version': '1.0',
    'category': 'Inventory',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Wave.
=================================================================
have the functionality to send products from stock or purchase products from vendors and have them shipped to
the client without having to put them on a sale.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
        'security/takeoff_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_data.xml',
        'views/product_category.xml',
        'views/stock_picking.xml',
        'views/takeoff_request.xml',
        'views/sale_order_views.xml',
        'views/stock_view.xml',
        'views/purchase_view.xml',
        'views/product_view.xml',
        'views/account_budget_view.xml',
        'views/project_view.xml',
        'views/res_config_settings_views.xml',
        'wizard/takeoff_request_validator.xml'
    ],

    'depends': [
        'account_budget',
        'sale_margin',
        'stock_account',
        'sale_stock',
        'purchase_stock',
        'wave_sale_revision',
        'sale_purchase',
        'project'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
