# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class SaleRevision(models.Model):
    _inherit = 'sale.revision'

    def create_sol_with_revision_line(self, line):

        SaleOrderLine = self.env["sale.order.line"]
        order = line.revision_id.order_id
        analytic_account = order.analytic_account_id
        budget = False
        if analytic_account:
            budget = self.env['crossovered.budget'].search([
                '|', ('analytic_account_id', '=', analytic_account.id),
                ('name', '=', analytic_account.name)], limit=1
            )

        if not line.revision_id:
            raise UserError(_("User Error !\nPlease refresh your browser interface and try again."))

        if not line.order_line and line.display_type == 'line_section':
            sale_line = order.order_line.filtered(lambda rec: rec.section == line.section)
            sequence = sale_line and sale_line[0].sequence
            if not line.order_line:
                so_line = SaleOrderLine.create({
                    'sequence': sequence or line.sequence,
                    'name': line.name,
                    'section': line.name,
                    'order_id': order.id,
                    'display_type': line.display_type,
                    'revision_id': line.revision_id.id
                })
                line.change_id.write({'order_line': so_line.id})
        elif not line.order_line:
            orderline = SaleOrderLine.create({
                'name': line.name or line.product_id.description_sale or line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.product_uom_qty,
                'order_id': order.id,
                'sequence': line.sequence,
                'section': line.section,
                'revision_id': line.revision_id.id,
                'price_unit': line.price_unit,
                'purchase_price': line.purchase_price,
                'route_id': line.route_id.id,
                'discount': line.discount
            })
            orderline._compute_tax_id()
            line.change_id.write({'order_line': orderline.id})
            if analytic_account and budget:
                orderline.order_line_budget_auto_commit(budget, analytic_account)

        elif any([line.section_modified, line.line_modified, line.sequence_modified]):
            line.order_line.write({
                'product_uom_qty': line.product_uom_qty,
                'section': line.section,
                'sequence': line.sequence,
                'original_qty': line.order_line.product_uom_qty,
                'is_revised': False if line.display_type == 'line_section' or line.sequence_modified and not line.section_modified and not line.line_modified else True
            })
            line.order_line._compute_tax_id()
            if line.line_modified and analytic_account and budget:
                line.order_line.order_line_budget_auto_commit(budget, analytic_account)


SaleRevision()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
