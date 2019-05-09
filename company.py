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


from trytond.model import fields, Unique
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Not, Bool


__all__ = ['Company']


class Company(metaclass=PoolMeta):
    __name__ = 'company.company'
    is_condo = fields.Boolean('Condominium', help='Check if this company is a condominium', select=True)
    units = fields.One2Many(
        'condo.unit',
        'company',
        'Units/Apartments',
        depends=['is_condo'],
        states={'invisible': Not(Bool(Eval('is_condo')))},
    )
    condofactors = fields.One2Many(
        'condo.factor', 'company', 'Factors', depends=['is_condo'], states={'invisible': Not(Bool(Eval('is_condo')))}
    )

    @classmethod
    def __setup__(cls):
        super(Company, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [('company_uniq', Unique(t, t.party), 'This party is already used in another company!')]

    @staticmethod
    def default_is_condo():
        return True
