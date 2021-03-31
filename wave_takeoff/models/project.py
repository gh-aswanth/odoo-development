from odoo import fields, models, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    takeoff_count = fields.Integer(compute='_compute_takeoff_count')

    def _compute_takeoff_count(self):
        for project in self:
            if project.analytic_account_id:
                project.takeoff_count = self.env['takeoff.request'].search_count([('analytic_account_id', '=', project.analytic_account_id.id)])

    def takeoff_tree_view(self):
        self.ensure_one()
        action = self.env.ref('wave_takeoff.takeoff_request_act_window').read()[0]
        takeoff_ids = self.env['takeoff.request'].search([('analytic_account_id', '=', self.analytic_account_id.id)])
        action['domain'] = [('id', 'in', takeoff_ids.ids)]
        return action
