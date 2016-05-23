##############################################################################
#
#    GNU Condo: The Free Management Condominium System
#    Copyright (C) 2016- M. Alonso <port02.server@gmail.com>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from trytond.pool import Pool
from trytond.report import Report


__all__ = ['AddressList']


class AddressList(Report):
    __name__ = 'condo.address_list'

    @classmethod
    def get_context(cls, records, data):
        report_context = super(AddressList, cls).get_context(records, data)

        #records:
        #[Pool().get('company.company')(4), Pool().get('company.company')(6)]
        #data:
        #{u'model': u'company.company', u'action_id': 69, u'ids': [4, 6], u'id': 4}

        pool = Pool()
        CondoParty = pool.get('condo.party')
        CondoUnit = pool.get('condo.unit')

        units = CondoUnit.search_read([
                    'OR', [
                            ('company', 'in', data['ids']),
                        ],[
                            ('company.parent', 'child_of', data['ids']),
                        ],
                ], fields_names=['id'])

        condoparties = CondoParty.search([
                ('unit', 'in', [ x['id'] for x in units ]),
                ('mail', '=', True),
                ('active', '=', True),
                ], order=[('unit.company', 'ASC'), ('unit.name', 'ASC')])

        report = []
        for condoparty in condoparties:
            item = {
                'party': condoparty.party,
                'address': condoparty.address
                }
            #append only if distinct (party, address)
            if not (item in report):
                report.append(item)

        report_context['records'] = report

        return report_context
