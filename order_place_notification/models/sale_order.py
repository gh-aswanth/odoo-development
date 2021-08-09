
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.model
    def create(self, vals):
        saleOb = super(SaleOrder, self).create(vals)
        bus_message = {
            'message': "New Order Placed (%s)"% len(saleOb),
            'title': "New Order",
            'sticky': False
        }
        self.env['bus.bus'].sendmany([('notify_info_%s' % record.user_id.id, bus_message) for record in saleOb])
        return saleOb