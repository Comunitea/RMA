# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from lxml import etree
from openerp.tools.translate import _


class equivalent_products_wizard(orm.TransientModel):

    _name = "equivalent.products.wizard"
    _description = "Wizard for change products in claim."

    def _get_products(self, cr, uid, ids, field_name, arg, context=None,
                      tag_ids=None, onchange=None):
        res = {}
        product_obj = self.pool.get('product.product')
        tag_obj = self.pool.get('product.tag')
        tag_wiz_obj = self.pool.get('equivalent.tag.wizard')
        for wiz in self.browse(cr, uid, ids, context):
            if not onchange:
                tag_ids = [x.id for x in wiz.tag_ids]
            product_ids = set(product_obj.search(cr, uid,
                                                 [('sale_ok', '=', True)],
                                                 context=context))
            # se buscan todos los product.tag que coincidan con los del wiz
            for tag in tag_wiz_obj.browse(cr, uid, tag_ids, context):
                tag_ids = tag_obj.search(cr, uid,
                                         [('name', '=', tag.name)],
                                         context=context)
                products = product_obj.search(cr, uid,
                                              [('tag_ids', 'in', tag_ids),
                                               ('sale_ok', '=', True)],
                                              context=context)
                product_ids = product_ids & set(products)
            res[wiz.id] = list(product_ids)
        return res

    _columns = {
        'tag_ids': fields.one2many('equivalent.tag.wizard', 'wiz_id', 'Tags'),
        'product_ids': fields.function(_get_products, type='one2many',
                                       relation='product.product',
                                       string='Products'),
        'product_id': fields.many2one('product.product', 'Product selected'),
        'line_id': fields.many2one('claim.line', 'Line'),
        'real_stock': fields.float('Real Stock'),
        'virtual_stock': fields.float('Virtual Stock'),
        'real_stock': fields.float("Real Stock", readonly=True),
        'virtual_stock': fields.float("Virtual Stock", readonly=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(equivalent_products_wizard, self).default_get(cr, uid, fields, context=context)
        if context.get('line_id'):
            claim_line_id = self.pool.get('claim.line').browse(cr, uid, context['line_id'])
            res['product_id'] = claim_line_id.product_id.id
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
            se añade domain al campo product_id.
        """
        product_obj = self.pool.get('product.product')
        if context is None:
            context = {}
        line_id = context.get('line_id', False)
        res = super(equivalent_products_wizard, self).fields_view_get(cr, uid,
                                                                      view_id,
                                                                      view_type,
                                                                      context,
                                                                      toolbar,
                                                                      submenu)
        if line_id:
            # se buscan productos con los mismos tags que el de la linea
            product_ids = set(product_obj.search(cr, uid,
                                                 [('sale_ok', '=', True)],
                                                 context=context))
            line = self.pool.get('claim.line').browse(cr, uid, line_id,
                                                      context)
            product = line.product_id
            for tag in product.tag_ids:
                products = product_obj.search(cr, uid,
                                              [('tag_ids', 'in', [tag.id]),
                                               ('sale_ok', '=', True)],
                                              context=context)
                product_ids = product_ids & set(products)

            # se añade a la vista el domain
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='product_id']"):
                node.set('domain', "[('id', 'in', " +
                         str(list(product_ids)) + ")]")
            res['arch'] = etree.tostring(doc)

        return res

    def onchange_tags(self, cr, uid, ids, tag_ids=False, context=None):
        if not tag_ids:
            return True
        tag_ids = tag_ids[0][2]
        product_ids = self._get_products(cr, uid, ids,
                                         "product_ids", "",
                                         context, tag_ids,
                                         True)[ids[0]]
        return {'value': {'product_ids': product_ids},
                'domain': {'product_id': [('id', 'in', product_ids)]}}

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        wiz = self.browse(cr, uid, ids[0])
        prod_eq = [x.id for x in wiz.product_ids]
        if product_id not in prod_eq:
            raise orm.except_orm(_('Error'),
                                 _('El producto no es equivalente'))
        prod_obj = self.pool.get('product.product')
        prod_id = prod_obj.browse(cr, uid, product_id)
        virtual_stock = prod_id.virtual_available
        real_stock = prod_id.qty_available
        return {
            'value': {'virtual_stock': virtual_stock,
                      'real_stock': real_stock}
        }

    def select_product(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0], context)

        if wiz.product_id.id not in [x.id for x in wiz.product_ids]:
            raise orm.except_orm(_('Error'),
                                 _('El producto no es equivalente'))
        order_line_obj = self.pool.get('claim.line')
        order_line_obj.write(cr, uid,
                             [wiz.line_id.id],
                             {'equivalent_product_id': wiz.product_id.id},
                             context)


class equivalent_tag_wizard(orm.TransientModel):

    _name = "equivalent.tag.wizard"
    _description = "Tags for equivalent products wizard"

    _columns = {
        'wiz_id': fields.many2one('equivalent.products.wizard', 'Wizard'),
        'name': fields.char('Name', size=64),
    }
