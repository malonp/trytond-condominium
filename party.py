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

import datetime

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Not, Bool


__all__ = ['Party']
__metaclass__ = PoolMeta


class Party:
    'Condominium Party'
    __name__ = 'party.party'
    units = fields.One2Many('condo.party', 'party', 'Units/Apartments')

    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
        cls._history = True

    @classmethod
    def validate(cls, condos):
        super(Party, cls).validate(condos)
        for condo in condos:
            condo.validate_name()
            condo.validate_active()

    def validate_name(self):
        #Warn on existing name and constraint non stripped names
        if (self.id > 0):
            if not (self.name == self.name.strip()):
                self.raise_user_error(
                    "Party name should be stripped!")
            else:
                parties = Pool().get('party.party')
                #Must explicitly search on records with active=False
                #otherwise only search on records with active=True
                parties_count = parties.search_count(
                    [('name', '=', self.name), ('active', 'in', (True, False))])
                if (parties_count > 1):
                    self.raise_user_warning('warn_party_with_same_name',
                        'Party name already exists!', self.rec_name)

    def validate_active(self):
        #Deactivate party as unit owner on party deactivate
        if (self.id > 0) and not self.active:
            CondoParty = Pool().get('condo.party')
            condoparties = CondoParty.search([('party', '=', self.id),('isactive', '=', True),])
            if len(condoparties):
                self.raise_user_warning('warn_deactive_party',
                    'This party will be deactivate in all of his units/apartments!', self.rec_name)
                for condoparty in condoparties:
                    condoparty.isactive = False
                    condoparty.save()
