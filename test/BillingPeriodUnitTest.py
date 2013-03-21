#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import datetime
import unittest
import gconf

import tgcm.core.Config as Config

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class BillingPeriodTest(unittest.TestCase):
    config = Config.Config('es')

    def setUp(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def tearDown(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def test_billing_period_start_end_same_month(self):
        datapool = (
            {'billing_day' : 1, 'today' : (2011, 1, 18), 'result' : ((2011, 1, 1), (2011, 1, 31))}, \
            {'billing_day' : 1, 'today' : (2011, 2, 18), 'result' : ((2011, 2, 1), (2011, 2, 28))}, \
            {'billing_day' : 1, 'today' : (2011, 3, 18), 'result' : ((2011, 3, 1), (2011, 3, 31))}, \
            {'billing_day' : 1, 'today' : (2011, 4, 18), 'result' : ((2011, 4, 1), (2011, 4, 30))}, \
            {'billing_day' : 1, 'today' : (2011, 5, 18), 'result' : ((2011, 5, 1), (2011, 5, 31))}, \
            {'billing_day' : 1, 'today' : (2011, 6, 18), 'result' : ((2011, 6, 1), (2011, 6, 30))}, \
            {'billing_day' : 1, 'today' : (2011, 7, 18), 'result' : ((2011, 7, 1), (2011, 7, 31))}, \
            {'billing_day' : 1, 'today' : (2011, 8, 18), 'result' : ((2011, 8, 1), (2011, 8, 31))}, \
            {'billing_day' : 1, 'today' : (2011, 9, 18), 'result' : ((2011, 9, 1), (2011, 9, 30))}, \
            {'billing_day' : 1, 'today' : (2011, 10, 18), 'result' : ((2011, 10, 1), (2011, 10, 31))}, \
            {'billing_day' : 1, 'today' : (2011, 11, 18), 'result' : ((2011, 11, 1), (2011, 11, 30))}, \
            {'billing_day' : 1, 'today' : (2011, 12, 18), 'result' : ((2011, 12, 1), (2011, 12, 31))}, \
        )
        self.__tc_helper(datapool)

    def test_billing_day_is_last_day_of_month(self):
        datapool = (
            {'billing_day' : 31, 'today' : (2011, 1, 18), 'result' : ((2010, 12, 31), (2011, 1, 30))}, \
            {'billing_day' : 31, 'today' : (2011, 2, 18), 'result' : ((2011, 1, 31), (2011, 2, 27))}, \
            {'billing_day' : 31, 'today' : (2011, 3, 18), 'result' : ((2011, 2, 28), (2011, 3, 30))}, \
            {'billing_day' : 31, 'today' : (2011, 4, 18), 'result' : ((2011, 3, 31), (2011, 4, 29))}, \
            {'billing_day' : 31, 'today' : (2011, 5, 18), 'result' : ((2011, 4, 30), (2011, 5, 30))}, \
            {'billing_day' : 31, 'today' : (2011, 6, 18), 'result' : ((2011, 5, 31), (2011, 6, 29))}, \
            {'billing_day' : 31, 'today' : (2011, 7, 18), 'result' : ((2011, 6, 30), (2011, 7, 30))}, \
            {'billing_day' : 31, 'today' : (2011, 8, 18), 'result' : ((2011, 7, 31), (2011, 8, 30))}, \
            {'billing_day' : 31, 'today' : (2011, 9, 18), 'result' : ((2011, 8, 31), (2011, 9, 29))}, \
            {'billing_day' : 31, 'today' : (2011, 10, 18), 'result' : ((2011, 9, 30), (2011, 10, 30))}, \
            {'billing_day' : 31, 'today' : (2011, 11, 18), 'result' : ((2011, 10, 31), (2011, 11, 29))}, \
            {'billing_day' : 31, 'today' : (2011, 12, 18), 'result' : ((2011, 11, 30), (2011, 12, 30))}, \
        )
        self.__tc_helper(datapool)

    def test_billing_period_ends_in_this_month(self):
        datapool = (
            {'billing_day' : 18, 'today' : (2011, 1, 14), 'result' : ((2010, 12, 18), (2011, 1, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 2, 14), 'result' : ((2011, 1, 18), (2011, 2, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 3, 14), 'result' : ((2011, 2, 18), (2011, 3, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 4, 14), 'result' : ((2011, 3, 18), (2011, 4, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 5, 14), 'result' : ((2011, 4, 18), (2011, 5, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 6, 14), 'result' : ((2011, 5, 18), (2011, 6, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 7, 14), 'result' : ((2011, 6, 18), (2011, 7, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 8, 14), 'result' : ((2011, 7, 18), (2011, 8, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 9, 14), 'result' : ((2011, 8, 18), (2011, 9, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 10, 14), 'result' : ((2011, 9, 18), (2011, 10, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 11, 14), 'result' : ((2011, 10, 18), (2011, 11, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 12, 14), 'result' : ((2011, 11, 18), (2011, 12, 17))}, \
        )
        self.__tc_helper(datapool)

    def test_billing_period_ends_in_next_month(self):
        datapool = (
            {'billing_day' : 18, 'today' : (2011, 1, 22), 'result' : ((2011, 1, 18), (2011, 2, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 2, 22), 'result' : ((2011, 2, 18), (2011, 3, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 3, 22), 'result' : ((2011, 3, 18), (2011, 4, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 4, 22), 'result' : ((2011, 4, 18), (2011, 5, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 5, 22), 'result' : ((2011, 5, 18), (2011, 6, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 6, 22), 'result' : ((2011, 6, 18), (2011, 7, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 7, 22), 'result' : ((2011, 7, 18), (2011, 8, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 8, 22), 'result' : ((2011, 8, 18), (2011, 9, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 9, 22), 'result' : ((2011, 9, 18), (2011, 10, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 10, 22), 'result' : ((2011, 10, 18), (2011, 11, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 11, 22), 'result' : ((2011, 11, 18), (2011, 12, 17))}, \
            {'billing_day' : 18, 'today' : (2011, 12, 22), 'result' : ((2011, 12, 18), (2012, 1, 17))}, \
        )
        self.__tc_helper(datapool)

    def test_billing_period_start_end_same_month_and_leap_year(self):
        datapool = (
            {'billing_day' : 1, 'today' : (2012, 1, 22), 'result' : ((2012, 1, 1), (2012, 1, 31))}, \
            {'billing_day' : 1, 'today' : (2012, 2, 22), 'result' : ((2012, 2, 1), (2012, 2, 29))}, \
            {'billing_day' : 1, 'today' : (2012, 3, 22), 'result' : ((2012, 3, 1), (2012, 3, 31))}, \
        )
        self.__tc_helper(datapool)

    def test_billing_day_is_last_day_of_month_and_leap_year(self):
        datapool = (
            {'billing_day' : 31, 'today' : (2012, 1, 22), 'result' : ((2011, 12, 31), (2012, 1, 30))}, \
            {'billing_day' : 31, 'today' : (2012, 2, 22), 'result' : ((2012, 1, 31), (2012, 2, 28))}, \
            {'billing_day' : 31, 'today' : (2012, 3, 22), 'result' : ((2012, 2, 29), (2012, 3, 30))}, \
        )
        self.__tc_helper(datapool)

    def test_today_is_billing_day(self):
        datapool = (
            {'billing_day' : 18, 'today' : (2011, 1, 18), 'result' : ((2011, 1, 18), (2011, 2, 17))}, \
            {'billing_day' : 25, 'today' : (2011, 12, 25), 'result' : ((2011, 12, 25), (2012, 1, 24))}, \
            {'billing_day' : 1, 'today' : (2011, 1, 1), 'result' : ((2011, 1, 1), (2011, 1, 31))}, \
            {'billing_day' : 31, 'today' : (2011, 12, 31), 'result' : ((2011, 12, 31), (2012, 1, 30))}, \
            {'billing_day' : 31, 'today' : (2011, 12, 31), 'result' : ((2011, 12, 31), (2012, 1, 30))}, \

            {'billing_day' : 28, 'today' : (2011, 1, 28), 'result' : ((2011, 1, 28), (2011, 2, 27))}, \
            {'billing_day' : 28, 'today' : (2012, 1, 28), 'result' : ((2012, 1, 28), (2012, 2, 27))}, \
            {'billing_day' : 29, 'today' : (2011, 1, 29), 'result' : ((2011, 1, 29), (2011, 2, 27))}, \
            {'billing_day' : 29, 'today' : (2012, 1, 29), 'result' : ((2012, 1, 29), (2012, 2, 28))}, \
            {'billing_day' : 30, 'today' : (2011, 1, 30), 'result' : ((2011, 1, 30), (2011, 2, 27))}, \
            {'billing_day' : 30, 'today' : (2012, 1, 30), 'result' : ((2012, 1, 30), (2012, 2, 28))}, \
            {'billing_day' : 31, 'today' : (2011, 1, 31), 'result' : ((2011, 1, 31), (2011, 2, 27))}, \
            {'billing_day' : 31, 'today' : (2012, 1, 31), 'result' : ((2012, 1, 31), (2012, 2, 28))}, \

            {'billing_day' : 28, 'today' : (2011, 2, 28), 'result' : ((2011, 2, 28), (2011, 3, 27))}, \
            {'billing_day' : 28, 'today' : (2012, 2, 28), 'result' : ((2012, 2, 28), (2012, 3, 27))}, \
            {'billing_day' : 28, 'today' : (2012, 2, 29), 'result' : ((2012, 2, 28), (2012, 3, 27))}, \
            {'billing_day' : 29, 'today' : (2011, 2, 28), 'result' : ((2011, 2, 28), (2011, 3, 28))}, \
            {'billing_day' : 29, 'today' : (2012, 2, 28), 'result' : ((2012, 1, 29), (2012, 2, 28))}, \
            {'billing_day' : 29, 'today' : (2012, 2, 29), 'result' : ((2012, 2, 29), (2012, 3, 28))}, \
            {'billing_day' : 30, 'today' : (2011, 2, 28), 'result' : ((2011, 2, 28), (2011, 3, 29))}, \
            {'billing_day' : 30, 'today' : (2012, 2, 28), 'result' : ((2012, 1, 30), (2012, 2, 28))}, \
            {'billing_day' : 30, 'today' : (2012, 2, 29), 'result' : ((2012, 2, 29), (2012, 3, 29))}, \
            {'billing_day' : 31, 'today' : (2011, 2, 28), 'result' : ((2011, 2, 28), (2011, 3, 30))}, \
            {'billing_day' : 31, 'today' : (2012, 2, 28), 'result' : ((2012, 1, 31), (2012, 2, 28))}, \
            {'billing_day' : 31, 'today' : (2012, 2, 29), 'result' : ((2012, 2, 29), (2012, 3, 30))}, \
        )
        self.__tc_helper(datapool)

    def __tc_helper(self, datapool):
        for entry in datapool:
            billing_day = entry['billing_day']
            self.config.set_default_billing_day(billing_day)

            year = entry['today'][0]
            month = entry['today'][1]
            day = entry['today'][2]
            today = datetime.date(year, month, day)

            year = entry['result'][0][0]
            month = entry['result'][0][1]
            day = entry['result'][0][2]
            start = datetime.date(year, month, day)

            year = entry['result'][1][0]
            month = entry['result'][1][1]
            day = entry['result'][1][2]
            end = datetime.date(year, month, day)

            billing_period = (start, end)
            result = self.config.get_default_billing_period(day = today)

            self.assertEqual(billing_period, result, \
                '\n\nBilling day: %d\nToday: %s\nExpected:\t%s - %s\nResult:\t\t%s - %s' % ( \
                    billing_day, today.isoformat(), \
                    start.isoformat(), end.isoformat(), \
                    result[0].isoformat(), result[1].isoformat()))


    def test_invalid_date_type(self):
        invalid_dates = (False, 11, 'foo')

        for day in invalid_dates:
            self.assertRaises(TypeError, self.config.get_default_billing_period, day)

if __name__ == '__main__':
    unittest.main()
