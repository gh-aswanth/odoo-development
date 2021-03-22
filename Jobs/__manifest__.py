# -*- coding: utf-8 -*-

{
    'name': 'Jobs',
    'version': '1.0',
    'summary': 'Jobs',
    'description': """
ERP System for Jobs Management""",
    'category': 'Sales Management',
    'author': 'Confianz Global,Inc.',
    'website': 'http://www.confianzit.com',
    'depends': ['base', 'product', 'sale_management', 
    			'sale_stock', 'stock', 'purchase', 'purchase_stock', 
    			'purchase_stock', 'stock_dropshipping'],
    'data': [
        "security/ir.model.access.csv",
        "security/job_security.xml",
        "data/ir_sequence_data.xml",
        "data/product_data.xml",
        "report/job_report.xml",
        "report/job_report_template.xml",
        "data/mail_template.xml",
        "wizard/procurement_requisition_wizard_view.xml",
        "wizard/mail_compose_message.xml",
        "views/assets.xml",
        "views/stock_view.xml",
        "views/product_view.xml",
        "views/sale_view.xml",
        "views/purchase_view.xml",
        "views/account_move_view.xml",
        "views/job_overview.xml",
        "views/job_order_view.xml",
        "views/job_sub_contract.xml",
        "views/res_config_settings_views.xml"
    ],
    'qweb': [
        "static/src/xml/base.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
