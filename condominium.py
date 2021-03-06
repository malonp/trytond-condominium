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


from decimal import Decimal
from itertools import chain

from sql import Column

from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pool import Pool
from trytond.pyson import Eval, If, Not, Bool, And
from trytond.transaction import Transaction


__all__ = ['CondoFactors', 'CondoParty', 'Factor', 'Unit']


class CondoFactors(ModelSQL, ModelView):
    'Condominium Factors'
    __name__ = 'condo.factor'
    company = fields.Many2One(
        'company.company',
        'Condominium',
        domain=[('is_condo', '=', True)],
        ondelete='CASCADE',
        required=True,
        select=True,
    )
    name = fields.Char('Name', help='Short name for this parameter', required=True)
    total = fields.Function(
        fields.Numeric('Total', help='Sum of values for all the units/apartments in the condominium', digits=(3, 5)),
        getter='get_total',
    )
    notes = fields.Char('Description', help='Short description of this parameter')

    @classmethod
    def __setup__(cls):
        super(CondoFactors, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('condofactors_uniq', Unique(t, t.company, t.name), 'This factor name is already in use!')
        ]

    def get_total(self, name):
        return sum(f.value for unit in self.company.units for f in unit.factors if f.condofactor.id == self.id)


class CondoParty(ModelSQL, ModelView):
    'Condominium Party'
    __name__ = 'condo.party'
    unit = fields.Many2One('condo.unit', 'Unit', ondelete='CASCADE', required=True, select=True)
    company = fields.Function(
        fields.Many2One('company.company', 'Company'), getter='get_company', searcher='search_company'
    )
    unit_name = fields.Function(fields.Char('Unit'), getter='get_unit_name', searcher='search_unit_name')
    role = fields.Selection([(None, ''), ('owner', 'Owner'), ('tenant', 'Tenant')], 'Role')
    party = fields.Many2One('party.party', 'Party', ondelete='CASCADE', required=True, select=True)

    def get_rec_name(self, name):
        return ", ".join(x for x in [self.party.name, self.unit.name] if x)

    @classmethod
    def __setup__(cls):
        super(CondoParty, cls).__setup__()
        cls._order.insert(0, ('unit', 'ASC'))
        t = cls.__table__()
        cls._sql_constraints += [
            ('party_uniq', Unique(t, t.unit, t.party), 'Party must be unique in each apartment/unit!')
        ]

    @classmethod
    def get_unit_name(cls, condoparties, name):
        return dict([(p.id, p.unit.name) for p in condoparties if p.unit])

    @classmethod
    def search_unit_name(cls, name, domain):
        _, operator, value = domain
        Operator = fields.SQL_OPERATORS[operator]

        pool = Pool()
        table1 = pool.get('condo.unit').__table__()
        table2 = cls.__table__()

        query = table1.join(table2, condition=table1.id == table2.unit).select(
            table2.id, where=Operator(table1.name, value)
        )

        return [('id', 'in', query)]

    @classmethod
    def order_unit_name(cls, tables):
        return chain.from_iterable(
            [
                cls.unit.convert_order('unit.name', tables, cls),
                cls.unit.convert_order('unit.company.party.name', tables, cls),
            ]
        )

    @classmethod
    def get_company(cls, condoparties, name):
        return dict([(p.id, p.unit.company.id) for p in condoparties if p.unit])

    @fields.depends('unit')
    def on_change_with_company(self):
        if self.unit and self.unit.company:
            return self.unit.company.id

    @classmethod
    def search_company(cls, name, domain):
        _, operator, value = domain
        Operator = fields.SQL_OPERATORS[operator]

        pool = Pool()
        table1 = pool.get('party.party').__table__()
        table2 = pool.get('company.company').__table__()
        table3 = pool.get('condo.unit').__table__()
        table4 = cls.__table__()

        query = (
            table1.join(table2, condition=table1.id == table2.party)
            .join(table3, condition=table2.id == table3.company)
            .join(table4, condition=table3.id == table4.unit)
            .select(table4.id, where=Operator(table1.name, value))
        )

        return [('id', 'in', query)]

    @classmethod
    def order_company(cls, tables):
        return chain.from_iterable(
            [
                cls.unit.convert_order('unit.company.party.name', tables, cls),
                cls.unit.convert_order('unit.name', tables, cls),
            ]
        )

    @classmethod
    def validate(cls, condoparties):
        super(CondoParty, cls).validate(condoparties)
        for condoparty in condoparties:
            condoparty.party_is_active()
            # condoparty.change_role()

    def party_is_active(self):
        if not self.party.active:
            self.raise_user_error("This party isn't active!")

    def change_role(self):
        table = Pool().get('condo.party').__table__()
        with Transaction().new_cursor(readonly=True):
            cursor = Transaction().connection.cursor()
            cursor.execute(*table.select(table.role, where=table.id == self.id))

            role = cursor.fetchone()
            if role and bool(role[0]):
                self.raise_user_error("This role can not be change!")


class Unit(ModelSQL, ModelView):
    'Unit'
    __name__ = 'condo.unit'
    company = fields.Many2One(
        'company.company',
        'Condominium',
        domain=[('is_condo', '=', True)],
        ondelete='CASCADE',
        required=True,
        select=True,
        states={'readonly': Eval('id', 0) > 0},
    )
    name = fields.Char('Unit', select=True, size=12, states={'readonly': Eval('id', 0) > 0})
    condoparties = fields.One2Many('condo.party', 'unit', 'Parties')
    factors = fields.One2Many('condo.unit-factor', 'unit', 'Factors')

    def get_rec_name(self, name):
        return ", ".join(x for x in [self.name, self.company.rec_name] if x)

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op, ('name',) + tuple(clause[1:]), ('company',) + tuple(clause[1:])]

    @classmethod
    def __setup__(cls):
        super(Unit, cls).__setup__()
        cls._order.insert(0, ('company', 'ASC'))
        cls._order.insert(1, ('name', 'ASC'))
        t = cls.__table__()
        cls._sql_constraints += [
            ('unit_unique', Unique(t, t.company, t.name), 'The apartment/unit must be unique in each condominium!')
        ]

    @classmethod
    def order_company(cls, tables):
        table, _ = tables[None]
        return chain.from_iterable(
            [cls.company.convert_order('company.party.name', tables, cls), [Column(table, 'name')]]
        )

    @classmethod
    def order_name(cls, tables):
        table, _ = tables[None]
        return chain.from_iterable(
            [[Column(table, 'name')], cls.company.convert_order('company.party.name', tables, cls)]
        )


class Factor(ModelSQL, ModelView):
    'Unit Factor'
    __name__ = 'condo.unit-factor'
    unit = fields.Many2One('condo.unit', 'Unit', ondelete='CASCADE', required=True, select=True)
    condofactor = fields.Many2One(
        'condo.factor',
        'Factor',
        depends=['unit'],
        domain=[('company.units', '=', Eval('unit'))],
        ondelete='CASCADE',
        required=True,
        select=True,
    )
    value = fields.Numeric('Value', help='Value of factor for this unit/apartment', digits=(3, 5))

    @classmethod
    def __setup__(cls):
        super(Factor, cls).__setup__()
        cls._order.insert(0, ('unit', 'ASC'))
        t = cls.__table__()
        cls._sql_constraints += [
            ('factor_uniq', Unique(t, t.unit, t.condofactor), 'This factor is already defined for this apartment/unit!')
        ]

    @classmethod
    def validate(cls, factors):
        super(Factor, cls).validate(factors)
        for factor in factors:
            factor.bigger_or_equal_zero()

    def bigger_or_equal_zero(self):
        if self.value and (self.value < 0):
            self.raise_user_error("The value of factor must be equal or bigger than 0")
