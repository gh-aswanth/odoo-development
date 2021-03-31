# -*- coding: utf-8 -*-


from odoo import fields, models, _
from odoo.exceptions import UserError

class TakeOffRequestValidator(models.TransientModel):
    _name = 'takeoff.request.validator'

    takeoff_line_ids = fields.Many2many('takeoff.request.line')
    route_ids = fields.Many2many('stock.location.route')

    def make_process(self):
        self.takeoff_line_ids.action_launch_stock_rule()
        if all([line.mark_as_done for line in self.takeoff_line_ids]):
            request = self.takeoff_line_ids.mapped('request_id')
            request.write({'state': 'confirmed'})
            if request.request_template_id.mail_template_id:
                request.request_template_id.mail_template_id.send_mail(request.id)
            else:
                request.message_post(
                    body=f'Hey {request.user_id.name},\n your takeoff request {request.name} was confirmed.',
                    partner_ids=request.user_id.partner_id.ids)


TakeOffRequestValidator()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
