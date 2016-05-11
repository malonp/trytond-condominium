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

from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pool import Pool
from trytond.pyson import Eval, If, Not, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateTransition, StateView, Button


__all__ = ['CondoFactors', 'CondoParty', 'Unit', 'UnitFactor',
    'CheckAddressingList', 'CheckUnitMailAddress']


class CondoFactors(ModelSQL, ModelView):
    'Condominium Factors'
    __name__ = 'condo.factor'
    company = fields.Many2One('company.company', 'Condominium',
        domain=[('is_Condominium', '=', True)],
        ondelete='CASCADE', required=True, select=True)
    name = fields.Char('Factor', help='Short name for this parameter',
        required=True)
    total = fields.Numeric('Total', help='Sum of values for all the units/apartments in the condominium',
        digits=(3, 5))
    notes = fields.Char('Description', help='Short description of this parameter')

    @classmethod
    def __setup__(cls):
        super(CondoFactors, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('condo_factors_uniq', Unique(t,t.company, t.name),
                'This factor name is already in use!'),
        ]
        cls._history = True

    @classmethod
    def validate(cls, factors):
        super(CondoFactors, cls).validate(factors)
        for factor in factors:
            factor.bigger_or_equal_zero()

    def bigger_or_equal_zero(self):
        if self.total and (self.total < 0):
            self.raise_user_error(
                "The value must be equal or bigger than 0")


class CondoParty(ModelSQL, ModelView):
    'Condominium Party'
    __name__ = 'condo.party'
    unit = fields.Many2One('condo.unit', 'Unit',
        depends=['isactive', 'id'], ondelete='CASCADE', required=True,
        select=True, states={
            'readonly': If(~Eval('isactive'), True, Eval('id', 0) > 0),
            })
    company = fields.Function(fields.Many2One('company.company', 'Company'),
        getter='get_company', searcher='search_company')
    unit_name=fields.Function(fields.Char('Unit'),
        getter='get_unit_name', searcher='search_unit_name')
    role = fields.Selection([
            (None, ''),
            ('owner', 'Owner'),
            ('tenant', 'Tenant'),
            ], 'Role',
        depends=['isactive'], states={
            'readonly': If(~Eval('isactive'), True, Eval('id', 0) > 0),
            })
    party = fields.Many2One('party.party', 'Party',
        depends=['isactive', 'id'], ondelete='CASCADE', required=True,
        select=True, states={
            'readonly': If(~Eval('isactive'), True, Eval('id', 0) > 0),
            })
    mail = fields.Boolean('Mail', help="Check if this party should receive mail",
        depends=['isactive'], states={
            'readonly': ~Eval('isactive'),
            })
    address = fields.Many2One('party.address', 'Address', help="Mail address for this party",
        depends=['isactive', 'mail', 'party'], domain=[('party', '=', Eval('party')),('active', '=', True)],
        ondelete='SET NULL', states={
            'readonly': ~Eval('isactive'),
            'invisible': Not(Bool(Eval('mail')))
            })
    # if the object has a field named 'active', trytond filter out all inactive (model/modelstorage.py)
    # we call this field 'isactive' so inactive registers aren't filtered
    isactive = fields.Boolean('Active', select=True)

    def get_rec_name(self, name):
        return ", ".join(x for x in [self.party.name,
                self.unit.name] if x)

    @classmethod
    def __setup__(cls):
        super(CondoParty, cls).__setup__()
        cls._order.insert(0, ('unit', 'ASC'))
        t = cls.__table__()
        cls._sql_constraints += [
            ('party_uniq', Unique(t,t.unit, t.party),
                'Party must be unique in each apartment/unit!'),
        ]
        cls._history = True

    @staticmethod
    def default_mail():
        return True

    @staticmethod
    def default_isactive():
        return True

    @classmethod
    def get_unit_name(cls, condoparties, name):
         return dict([ (p.id, p.unit.name) for p in condoparties if p.unit ])

    @classmethod
    def search_unit_name(cls, name, domain):
        _, operator, value = domain
        Operator = fields.SQL_OPERATORS[operator]

        pool = Pool()
        table1 = pool.get('condo.unit').__table__()
        table2 = cls.__table__()

        query = table1.join(table2,
                        condition=table1.id == table2.unit).select(
                             table2.id,
                             where=Operator(table1.name, value))

        return [('id', 'in', query)]

    @classmethod
    def order_unit_name(cls, tables):
        return chain.from_iterable([cls.unit.convert_order('unit', tables, cls),
                cls.company.convert_order('company', tables, cls)])

    @classmethod
    def get_company(cls, condoparties, name):
         return dict([ (p.id, p.unit.company.id) for p in condoparties if p.unit ])

    @fields.depends('unit')
    def on_change_with_company(self):
        if self.unit:
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

        query = table1.join(table2,
                        condition=table1.id == table2.party).join(table3,
                        condition=table2.id == table3.company).join(table4,
                        condition=table3.id == table4.unit).select(
                             table4.id,
                             where=Operator(table1.name, value))

        return [('id', 'in', query)]

    @staticmethod
    def order_company(tables):
        pool = Pool()
        Unit = pool.get('condo.unit')

        field1 = Unit._fields['company']
        field2 = Unit._fields['name']
        table, _ = tables[None]
        unit = Unit.__table__()

        order_tables = tables.get('unit')
        if order_tables is None:
            order_tables = {
                    None: (unit, unit.id == table.unit),
                    }
            tables['unit'] = order_tables
            return chain.from_iterable([field1.convert_order('company', order_tables, Unit),
                                        field2.convert_order('name', order_tables, Unit)])
        return field1.convert_order('company', order_tables, Unit)

    @classmethod
    def validate(cls, condoparties):
        super(CondoParty, cls).validate(condoparties)
        for condoparty in condoparties:
            condoparty.party_is_active()
            condoparty.address_when_mail()

    def party_is_active(self):
        if not self.party.active and self.isactive:
            self.raise_user_error(
                "This party isn't active!")

    def address_when_mail(self):
        #Constraint to set address if mail is true
        if self.mail and not self.address:
            self.raise_user_error(
                "Set address or uncheck mail")


class Unit(ModelSQL, ModelView):
    'Unit'
    __name__ = 'condo.unit'
    company = fields.Many2One('company.company', 'Condominium',
        domain=[('is_Condominium', '=', True)],
        ondelete='CASCADE', required=True, select=True,
        states={
            'readonly': Eval('id', 0) > 0
            })
    name = fields.Char('Unit', size=12,
        states={
            'readonly': Eval('id', 0) > 0
            })
    parties = fields.One2Many('condo.party', 'unit', 'Parties')
    factors = fields.One2Many('condo.unit-factor', 'unit', 'Factors')

    def get_rec_name(self, name):
        return ", ".join(x for x in [self.name,
                self.company.rec_name] if x)

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('name',) + tuple(clause[1:]),
            ('company',) + tuple(clause[1:]),
            ]

    @classmethod
    def __setup__(cls):
        super(Unit, cls).__setup__()
        cls._order.insert(0, ('company', 'ASC'))
        cls._order.insert(1, ('name', 'ASC'))
        t = cls.__table__()
        cls._sql_constraints += [
            ('unit_unique', Unique(t,t.company, t.name),
                'The apartment/unit must be unique in each condominium!'),
        ]
        cls._history = True

class UnitFactor(ModelSQL, ModelView):
    'Unit Factor'
    __name__ = 'condo.unit-factor'
    unit = fields.Many2One('condo.unit', 'Unit',
        ondelete='CASCADE', required=True, select=True)
    factor = fields.Many2One('condo.factor', 'Factor',
        depends=['unit'], domain=[('company.condo_units', '=', Eval('unit'))],
        ondelete='CASCADE', required=True, select=True)
    value = fields.Numeric('Value', help='Value of factor for this unit/apartment',
        digits=(3, 5))

    @classmethod
    def __setup__(cls):
        super(UnitFactor, cls).__setup__()
        cls._order.insert(0, ('unit', 'ASC'))
        t = cls.__table__()
        cls._sql_constraints += [
            ('unit_factor_uniq', Unique(t,t.unit, t.factor),
                'This factor is already defined for this apartment/unit!'),
        ]
        cls._history = True

    @classmethod
    def validate(cls, factors):
        super(UnitFactor, cls).validate(factors)
        for factor in factors:
            factor.bigger_or_equal_zero()
            factor.validate_total_sum()

    def bigger_or_equal_zero(self):
        if self.value and (self.value < 0):
            self.raise_user_error(
                "The value of factor must be equal or bigger than 0")

    def validate_total_sum(self):
        #Sum of factor's unit must be less than total's factor of condominium
        UnitFactor = Pool().get('condo.unit-factor')
        search_records = UnitFactor.search_read(
            [('unit', 'in', self.unit.company.condo_units),
            ('factor', '=', self.factor)],)
        total = sum(x.get('value') for x in search_records if x.get('value'))

        CondoFactors = Pool().get('condo.factor')
        condofactor = CondoFactors.search([('id', '=', self.factor.id),])
#        print "Total Sum   " + self.factor.name + " :" + str(total)
#        print "Total Condo " + self.factor.name + " :" + str(condofactor[0].total)
        if total > condofactor[0].total:
            self.raise_user_error(
                "Sum of factor's units is bigger than factor's total")


class CheckAddressingList(ModelView):
    'Check Addressing List'
    __name__ = 'condo.check_units_addressing.result'
    units_orphan = fields.Many2Many('condo.unit', None, None,
        'Units without mail', readonly=True)
    units_unsure = fields.Many2Many('condo.unit', None, None,
        'Units to check', readonly=True)


class CheckUnitMailAddress(Wizard):
    'Check Addressing List'
    __name__ = 'condo.check_units_addressing'
    start_state = 'check'

    check = StateTransition()
    result = StateView('condo.check_units_addressing.result',
        'condominium.check_units_addressing_result', [
            Button('OK', 'end', 'tryton-ok', True),
            ])

    def transition_check(self):

        pool = Pool()
        CondoParty = pool.get('condo.party')
        CondoUnit = pool.get('condo.unit')

        units_succeed = []
        units_failed = []

        #All UNITS that BELONGS TO SELETED CONDOMINIUM and/or his childrens
        units = CondoUnit.search_read([
                    'OR', [
                            ('company', 'in', Transaction().context.get('active_ids')),
                        ],[
                            ('company.parent', 'child_of', Transaction().context.get('active_ids')),
                        ],
                ], fields_names=['id'])

        #All ACTIVE CONDOPARTIES of the unit refered above that HAVE MAIL DEFINED
        condoparties = CondoParty.search([
                ('unit', 'in', [ x['id'] for x in units ]),
                ('mail', '=', True),
                ('isactive', '=', True),
                ], order=[('unit.company', 'ASC'), ('unit.name', 'ASC')])

        #All UNITS WITH PARTIES THAT HAVE MAIL defined (in the unit itself or other selected units)
        units_party_with_mail = CondoUnit.search_read([
                    ('id', 'in', [ x['id'] for x in units ]),
                    ('parties.party', 'in', [ x.party for x in condoparties ]),
                ], fields_names=['id'])

        units_condoparty_with_mail = CondoUnit.search_read([
                    ('id', 'in', [ x['id'] for x in units ]),
                    ('parties', 'in', [ x.id for x in condoparties ]),
                ], fields_names=['id'])

        units_orphan = []
        units_unsure = []

        units_orphaned_count = len(units) - len(units_party_with_mail)
        if units_orphaned_count>0:
            units_orphan = [obj['id'] for obj in units if obj not in units_party_with_mail]

        units_unsure_count = len(units_party_with_mail) - len(units_condoparty_with_mail)
        if units_unsure_count>0:
            units_unsure = [obj['id'] for obj in units_party_with_mail if obj not in units_condoparty_with_mail]

        self.result.units_orphan = units_orphan
        self.result.units_unsure = units_unsure
        return 'result'

    def default_result(self, fields):
        return {
            'units_orphan': [p.id for p in self.result.units_orphan],
            'units_unsure': [p.id for p in self.result.units_unsure],
            }
