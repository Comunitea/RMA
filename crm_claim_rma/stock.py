# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, orm
from openerp import api

class stock_picking(orm.Model):

    _inherit = "stock.picking"

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }


# This part concern the case of a wrong picking out. We need to create a new
# stock_move in a picking already open.
# In order to don't have to confirm the stock_move we override the create and
# confirm it at the creation only for this case
class stock_move(orm.Model):

    _inherit = "stock.move"

    def create(self, cr, uid, vals, context=None):
        move_id = super(stock_move, self
                        ).create(cr, uid, vals, context=context)
        if vals.get('picking_id'):
            picking_obj = self.pool.get('stock.picking')
            picking = picking_obj.browse(cr, uid, vals['picking_id'],
                                         context=context)
            if picking.claim_id and picking.picking_type_code == u'incoming':
                self.write(cr, uid, move_id, {'state': 'confirmed'},
                           context=context)
        return move_id


    @api.multi
    def write(self, vals):
        for pick in self:
            if pick.picking_type_id.code == 'incoming':
                if 'date_expected' in vals.keys():
                    reservations = self.env['stock.reservation'].search(
                        [('product_id', '=', pick.product_id.id),
                         ('state', '=', 'confirmed')])
                    # no se necesita hacer browse.
                    # reservations = self.env['stock.reservation'].browse(reservation_ids)
                    for reservation in reservations:
                        reservation.date_planned = pick.date_expected
                        if not reservation.claim_id:
                            continue
                        followers = reservation.claim_id.message_follower_ids
                        sale.message_post(body="The date planned was changed.",
                                          subtype='mt_comment',
                                          partner_ids=followers)
        return super(stock_move, self).write(vals)

