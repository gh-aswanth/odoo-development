# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Order Place Notification',
    'summary': """
        Send notification messages to user""",
    'version': '13.0.1.0.0',
    'description': 'Order Place Notification',
    'author': 'Aswanth (Confianz)',
    'depends': [
        'web',
        'bus',
        'sale',
    ],
    'data': [
        'views/web_notify.xml'
    ],
    'installable': True,
}
