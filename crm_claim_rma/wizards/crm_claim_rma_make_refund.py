# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
from odoo.tools.safe_eval import safe_eval


class CrmClaimRmaMakeRefund(models.TransientModel):

    _name = 'crm.claim.rma.make.refund'

    def _default_description(self):
        return self.env.context.get('description', '')

    description = fields.Char(default=_default_description, required=True)
    invoice_date = fields.Date()


    @api.multi
    def make_refund(self):
        self.ensure_one()
        claim = self.env['crm.claim'].browse(self._context.get('claim_id'))
        invoice = self.env['account.invoice'].new({
            'partner_id': claim.partner_id.id,
            'type': ('out_refund'),
            'date_invoice': self.invoice_date,
            'company_id': self.env.user.company_id.id,
            'state': 'draft',
            'claim_id': claim.id
        })
        # Get other invoice values from partner onchange
        invoice._onchange_partner_id()
        invoice_vals = invoice._convert_to_write(invoice._cache)
        new_invoice = self.env['account.invoice'].create(invoice_vals)
        for line in claim.claim_line_ids:
            invoice_line = self.env['account.invoice.line'].new(
                {'product_id': line.product_id.id,
                 'name': line.name,
                 'quantity': line.product_returned_quantity,
                 'price_unit': line.unit_sale_price,
                 'invoice_id': new_invoice.id})
            invoice_line._onchange_product_id()
            invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)
            new_line = self.env['account.invoice.line'].create(invoice_line_vals)
            new_line.write({'price_unit': line.unit_sale_price, 'name': line.name})

        result = self.env.ref('account.action_invoice_tree1').read()[0]
        invoice_domain = safe_eval(result['domain'])
        invoice_domain.append(('id', '=', new_invoice.id))
        result['domain'] = invoice_domain
        return result
