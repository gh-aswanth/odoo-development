# -*- coding: utf-8 -*-

import requests
from collections import namedtuple

API_URL = "https://api.taxcloud.com/1.0/TaxCloud/"


class TaxcloudApi(object):

    def __init__(self, api_login_id, api_key):
        try:
            response = requests.post(API_URL + 'Ping', data={"apiLoginID": api_login_id, "apiKey": api_key}).json()
            if response.get('ResponseType') == 3:
                self.api_login_id = api_login_id
                self.api_key = api_key
                self.error = False
            else:
                self.error = "Invalid apiLoginID and/or apiKey"            
        except requests.exceptions.RequestException as e:
            self.error = 'Failed to Established new connection..!'

    def _verify_address(self, partner):
        addrs_data = {
            "apiLoginID": self.api_login_id,
            "apiKey": self.api_key,
            "Address1": partner.street,
            "Address2": partner.street2,
            "City": partner.city,
            "State": partner.state_id.code,
            "Zip5": partner.zip,
            "Zip4": ""
        }
        res = {}
        try:
            res = requests.post(url=API_URL + "VerifyAddress", data=addrs_data).json()
        except requests.exceptions.RequestException as e:
            self.error = 'Failed to Established new connection..!'

        if int(res.get('ErrNumber', False)):
            res.update(addrs_data)

        return res
 
    def _taxcloud_look_up(self, lookup_data):
        lookup_data.update({
            "apiLoginID": self.api_login_id,
            "apiKey": self.api_key,
            })
        resp_lookup = {}
        from pprint import pprint
        pprint(lookup_data)
        try:
            resp_lookup = requests.post(url=API_URL + "Lookup", json=lookup_data).json()
        except  requests.exceptions.RequestException as e:
            self.error = 'Failed to Established new connection..!'
        tax_resp = resp_lookup.get('CartItemsResponse')
        return tax_resp


    def _get_taxcloud_tics(self):

        tics_data = {}
        try:
            tics_data = requests.post(url=API_URL + "GetTICs", data={"apiLoginID": self.api_login_id, "apiKey": self.api_key}).json()
        except  requests.exceptions.RequestException as e:
            self.error = 'Failed to Established new connection..!'

        return [{'tic_code': i.get('TICID'), 'name': i.get('Description')} for i in tics_data.get('TICs')]
