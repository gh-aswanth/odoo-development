# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from xml.etree import ElementTree
from xml.dom import minidom
import io
import xmltodict
import re
from odoo import fields, models, _
from paramiko import SSHClient, AutoAddPolicy
import logging


class EdiSftpConfig(models.Model):
    _name = 'edi.sftp.config'
    _description = 'EDI SFTP CONFIGURATION'

    name = fields.Char(string='Site Name', required=True)
    host = fields.Char(string='Host', required=True)
    port = fields.Integer(string="Port", required=True)
    username = fields.Char(string='User Name', required=True)
    password = fields.Char(string='Password', required=True)
    file_path_in = fields.Char(
        string='Path to Read EDI', help='Path for 850 EDI', required=True)
    file_path_out = fields.Char(string='Path to Write EDI', required=True)
    show_warning = fields.Boolean()

    def check_connection(self):
        authenticated = False
        path_error_state = None
        with SSHClient() as client:
            client.set_missing_host_key_policy(AutoAddPolicy())
            try:
                client.connect(self.host, username=self.username,
                               password=self.password, port=self.port)
                if client.get_transport().is_authenticated():
                    authenticated = True
                    try:
                        with client.open_sftp() as sftp:
                            path_error_state = 'in'
                            sftp.chdir(self.file_path_in)
                            sftp.chdir('..')
                            path_error_state = 'out'
                            sftp.chdir(self.file_path_out)
                    except FileNotFoundError as e:
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Warning'),
                                'message': _('Read path NotFound.') if path_error_state == 'in' else _('Write path NotFound.'),
                                'sticky': True,
                            }
                        }
            except Exception as e:
                logging.error(e)
        if authenticated:
            self.show_warning = authenticated


def sps_connect(self, root=None, send=False, receive=False, operation=False, ref=False):
    with SSHClient() as client:
        client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            t = client.connect(self.host, username=self.username,
                               password=self.password, port=self.port)
            print(t)
            with client.open_sftp() as sftp:
                sftp.chdir('IN' if send else 'OUT')
                if receive:
                    for path in sftp.listdir():
                        if path.endswith('.xml'):
                            stream = io.BytesIO()
                            sftp.getfo(path, stream)
                            doc = xmltodict.parse(
                                re.sub(' xmlns="[^"]+"', '', stream.getvalue().decode('utf-8'), count=1))
                            try:
                                pass
                            except Exception as e:
                                self.env.cr.rollback()
                                logging.error(e)
                elif root and send:
                    rough_string = ElementTree.tostring(root)
                    reparsed = minidom.parseString(rough_string).childNodes[0]
                    out = reparsed.toprettyxml(
                        indent='\t', newl='\n', encoding='utf-8')
                    stream = io.BytesIO(out)
                    sftp.putfo(stream, f'{operation}{ref}.xml')
        except FileNotFoundError as e:
            logging.error(e)


EdiSftpConfig()
