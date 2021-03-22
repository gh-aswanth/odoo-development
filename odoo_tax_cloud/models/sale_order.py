# -*- coding: utf-8 -*-
from odoo import models, fields, api 
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import ValidationError
from .api import TaxcloudApi


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        if self.fiscal_position_id and self.fiscal_position_id.is_taxcloud or not self.fiscal_position_id:
            config_parm = self.env['ir.config_parameter']
            Api = TaxcloudApi(api_login_id=config_parm.get_param('tax_cloud_id'), api_key=config_parm.get_param('tax_cloud_key'))
            if Api.error:
                raise ValidationError(Api.error)
            for order in self:
                loc = Api._verify_address(order.company_id.partner_id)
                des = Api._verify_address(order.partner_id)
                cart_items = [{
                    "Qty": recrd.product_uom_qty,
                    "Price": recrd.price_unit,
                    "TIC": recrd.product_id.taxcloud_tic_ctg.tic_code,
                    "ItemID": recrd.product_id.name,
                    "Index": index
                    } for index, recrd in enumerate(order.order_line)]

                lookup_data = {
                    "customerID": order.partner_id.name,
                    "deliveredBySeller": False, #use False always if you use any Carrier servies Like UPS, Fedex, etc..
                    "origin": {
                        "Address1": loc.get('Address1'),
                        "Address2": loc.get('Address2'),
                        "City": loc.get('City'),
                        "State": loc.get('State'),
                        "Zip5": loc.get('Zip5'),
                        "Zip4": loc.get('Zip4')
                    },
                    "destination": {
                        "Address1": des.get('Address1'),
                        "Address2": des.get('Address2'),
                        "City": des.get('City'),
                        "State": des.get('State'),
                        "Zip5": des.get('Zip5'),
                        "Zip4": des.get('Zip4')
                    },
                    "cartItems": cart_items
                }

                tax_values = Api._taxcloud_look_up(lookup_data)
                from pprint import pprint
                pprint(tax_values)
                if Api.error:
                    raise ValidationError(Api.error)

                company = order.company_id
                for index, line in enumerate(order.order_line.filtered(lambda l: not l.display_type)):
                    if line.price_unit >= 0.0 and line.product_uom_qty >= 0.0:
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0) * line.product_uom_qty
                    if not price:
                        tax_rate = 0.0
                    else:
                        tax_rate = tax_values[index]['TaxAmount'] / price * 100
                    tax_rate = float_round(tax_rate, precision_digits=3)
                    if not float_is_zero(tax_rate, precision_digits=3):
                        tax = self.env['account.tax'].with_context(active_test=False).sudo().search([
                            ('amount', '=', tax_rate),
                            ('amount_type', '=', 'percent'),
                            ('type_tax_use', '=', 'sale'),
                            ('company_id', '=', company.id),
                            ], limit=1)

                        if not tax:
                            tax = self.env['account.tax'].sudo().create({
                                'name': 'Tax %.3f %%' % (tax_rate),
                                'amount': tax_rate,
                                'amount_type': 'percent',
                                'type_tax_use': 'sale',
                                'description': 'Sales Tax',
                                'company_id': company.id,
                            })

                        line.tax_id = tax
                super(SaleOrder, self).action_confirm()
            return True