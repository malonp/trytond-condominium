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


from sql import Null
from trytond.pool import Pool, PoolMeta


__all__ = ['CondoAddress']
__metaclass__ = PoolMeta


class CondoAddress:
    "Address"
    __name__ = 'party.address'

    @classmethod
    def __setup__(cls):
        super(CondoAddress, cls).__setup__()
        cls._history = True

    def get_rec_name(self, name):
        return "; ".join(x for x in [self.name,
                self.street, self.zip, self.city] if x)

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('street',) + tuple(clause[1:]),
            ('zip',) + tuple(clause[1:]),
            ('city',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
            ]

    @classmethod
    def validate(cls, addresses):
        super(CondoAddress, cls).validate(addresses)
        for address in addresses:
            address.validate_active()

    def validate_active(self):
        #Deactivate address as mail address of unit's party
        if (self.id > 0) and not self.active:
            CondoParty = Pool().get('condo.party')
            condoparties = CondoParty.search([('address', '=', self.id),('isactive', '=', True),])
            if len(condoparties):
                self.raise_user_warning('warn_deactive_party_address',
                    'This address will be deactivate as mail address in all units/apartments!', self.rec_name)
                for condoparty in condoparties:
                    condoparty.mail = False
                    condoparty.address = Null
                    condoparty.save()
