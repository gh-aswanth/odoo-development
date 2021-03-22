# -*- coding: utf-8 -*-

from odoo import fields, models, api


class JobSubContract(models.Model):
    _name = 'job.sub.contract'
    _description = 'Sub Contract'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    name = fields.Text(string="Description")
    vendor_id = fields.Many2one('res.partner', string="Vendor", required=True)
    estimated_price = fields.Float(string="Estimated Price", required=True)
    cost_price = fields.Float()
    job_id = fields.Many2one('job.order', ondelete='cascade')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Project', copy=False, ondelete='set null')
    margin = fields.Float('Margin', compute='_compute_margin', store=True)
    currency_id = fields.Many2one('res.currency', string="Company Currency",
                                        default=_get_default_currency_id)

    @api.depends('cost_price', 'estimated_price')
    def _compute_margin(self):
        for line in self:
            line.margin = ((line.estimated_price - line.cost_price) / line.estimated_price) * 100 if line.estimated_price else 0

    def create_vendor_bill(self):
        """
        return vendor bill values for contract line
        :rtype: dict
        """
        bill = self.env['account.move'].create({
            'partner_id': self.vendor_id.id,
            'type': 'in_invoice',
            'is_contract_bill': True,
            'analytic_account_id': self.job_id.analytic_account_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'quantity': 1,
                'price_unit': self.cost_price})]
        })
        form_view_id = self.env.ref('account.view_move_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [[form_view_id, 'form']],
            'res_id': bill.id,
            'target': 'current',
        }


JobSubContract()
