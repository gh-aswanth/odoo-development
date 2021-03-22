{
    'name': 'Confianz Ticket Management',
    'author': 'Confianz IT',
    'licence': 'LGPL-v3',
    'summary': 'Confianz Ticket Management',
    'description': """""",
    'maintainer': 'Confianz IT',
    'category': 'Helpdesk',
    'website': 'www.confianzit.com',
    'depends': ['mail','helpdesk','project','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_views.xml',
        'views/helpdesk_ticket_report.xml',
        'views/report_ticket.xml'
            ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
