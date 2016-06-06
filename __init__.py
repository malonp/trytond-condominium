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

from .address import *
from .company import *
from .condominium import *
from .party import *
from .contact_mechanism import *
from report import *


def register():
    Pool.register(
        Unit,
        CondoParty,
        CheckAddressingList,
        Address,
        CondoFactors,
        Party,
        PartyIdentifier,
        ContactMechanism,
        UnitFactor,
        Company,
        module='condominium', type_='model')
    Pool.register(
        AddressList,
        module='condominium', type_='report')
    Pool.register(
        CheckUnitMailAddress,
        module='condominium', type_='wizard')
