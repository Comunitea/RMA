# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields,osv
from openerp import tools

AVAILABLE_PRIORITIES = [
   ('0', 'Low'),
   ('1', 'Normal'),
   ('2', 'High')
]


class crm_claim_report(osv.osv):
    """ CRM Claim Report"""

    _name = "crm.claim.cost.report"
    _auto = False
    _description = "CRM Claim cost Report"

    _columns = {
        'user_id':fields.many2one('res.users', 'User', readonly=True),
        'section_id':fields.many2one('crm.case.section', 'Section', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'create_date': fields.datetime('Create Date', readonly=True, select=True),
        'claim_date': fields.datetime('Claim Date', readonly=True),
        'delay_close': fields.float('Delay to close', digits=(16,2),readonly=True, group_operator="avg",help="Number of Days to close the case"),
        'stage_id': fields.many2one ('crm.claim.stage', 'Stage', readonly=True),
        'categ_id': fields.many2one('crm.case.categ', 'Category', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'priority': fields.selection(AVAILABLE_PRIORITIES, 'Priority'),
        'type_action': fields.selection([('correction','Corrective Action'),('prevention','Preventive Action')], 'Action Type'),
        'date_closed': fields.datetime('Close Date', readonly=True, select=True),
        'date_deadline': fields.date('Deadline', readonly=True, select=True),
        'delay_expected': fields.float('Overpassed Deadline',digits=(16,2),readonly=True, group_operator="avg"),
        'email': fields.integer('# Emails', size=128, readonly=True),
        'subject': fields.char('Claim Subject', readonly=True),
        'nbr': fields.float('RMA cost', readonly=True),
        'claim_type': fields.selection([('customer', 'Customer'),
                                        ('supplier', 'Supplier')],
                                       string='Claim type', readonly=True),
    }

    def init(self, cr):

        """ Display Number of cases And Section Name
        @param cr: the current row, from the database cursor,
         """

        tools.drop_view_if_exists(cr, 'crm_claim_cost_report')
        cr.execute("""
            create or replace view crm_claim_cost_report as (
                select
                    min(c.id) as id,
                    c.date as claim_date,
                    c.date_closed as date_closed,
                    c.date_deadline as date_deadline,
                    c.user_id,
                    c.stage_id,
                    c.section_id,
                    c.partner_id,
                    c.company_id,
                    c.categ_id,
                    c.claim_type,
                    c.name as subject,
                    c.priority as priority,
                    c.type_action as type_action,
                    c.create_date as create_date,
                    avg(extract('epoch' from (c.date_closed-c.create_date)))/(3600*24) as  delay_close,
                    (SELECT count(id) FROM mail_message WHERE model='crm.claim' AND res_id=c.id) AS email,
                    extract('epoch' from (c.date_deadline - c.date_closed))/(3600*24) as  delay_expected,
                    c.rma_cost as nbr
                from
                    crm_claim c
                group by c.date,\
                        c.user_id,c.section_id, c.stage_id,c.claim_type,\
                        c.categ_id,c.partner_id,c.company_id,c.create_date,
                        c.priority,c.type_action,c.date_deadline,c.date_closed,c.id
            )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
