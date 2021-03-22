# -*- coding:utf-8 -*-

from odoo import models, fields, api, _
from pprint import pprint

class TicketActionTaken(models.Model):
    _name = 'ticket.action.taken'
    _description = 'Helpdesk ticket Action taken'

    name = fields.Char(string = 'Action Name')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Action name already exists !"),
    ]