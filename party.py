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


from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.tools import reduce_ids, grouped_slice
from trytond.transaction import Transaction


__all__ = ['Party']


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'
    units = fields.One2Many('condo.party', 'party', 'Units/Apartments')

    @classmethod
    def validate(cls, parties):
        super(Party, cls).validate(parties)
        for party in parties:
            party.validate_active()

    def validate_active(self):
        #Deactivate party as unit owner on party deactivate
        if (self.id > 0) and not self.active:
            condoparties = Pool().get('condo.party').__table__()
            cursor = Transaction().connection.cursor()

            cursor.execute(*condoparties.select(condoparties.id,
                                        where=(condoparties.party == self.id) &
                                              (condoparties.active == True)))

            ids = [ids for (ids,) in cursor.fetchall()]
            if len(ids):
                self.raise_user_warning('warn_deactive_condos_of_party.%d' % self.id,
                    'This party will be deactivate in %d unit(s)/apartment(s)!', len(ids))

                for sub_ids in grouped_slice(ids):
                    red_sql = reduce_ids(condoparties.id, sub_ids)
                    # Use SQL to prevent double validate loop
                    cursor.execute(*condoparties.update(
                            columns=[condoparties.active],
                            values=[False],
                            where=red_sql))
