# -*- coding: utf-8 -*-


from odoo import fields, models


class TakeOffRequestValidator(models.TransientModel):
    _name = 'takeoff.request.validator'

    takeoff_line_ids = fields.Many2many('takeoff.request.line')

    def make_process(self):
        self.takeoff_line_ids._action_launch_stock_rule()
        if all([line.mark_as_done for line in self.takeoff_line_ids]):
            self.takeoff_line_ids.mapped('request_id').write({'state': 'confirmed'})
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }
        #



TakeOffRequestValidator()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
