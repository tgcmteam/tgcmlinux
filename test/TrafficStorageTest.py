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

import os
import datetime
import sqlite3
import unittest

import tgcm.core.Config
import tgcm.core.TrafficStorage

DB_FILE = os.path.expanduser("~/foo.db")
IMSI = '214075527144750'

class EmtrafficTest(unittest.TestCase):
    def setUp(self):
        config = tgcm.core.Config.Config('es')
        self.storage = tgcm.core.TrafficStorage.TrafficStorage(config, DB_FILE)

        for is_roaming in (True, False):
            self.storage.reset(IMSI, is_roaming)

    def tearDown(self):
        pass

    def test_known_billing_periods(self):
        upload_incr = 1024 * 1024 * 10
        download_incr = 1234 * 4321

        first_day = datetime.date(2011, 10, 1)
        last_day = datetime.date(2011, 12, 31)
        for is_roaming in (True, False):
            self.__fill_data(IMSI, first_day, last_day, upload_incr, download_incr, is_roaming)
            self.__fill_data('123456789012345', first_day, last_day, upload_incr, download_incr, is_roaming)
            self.__fill_data('012345678901234', first_day, last_day, upload_incr, download_incr, is_roaming)

        tests = []
        tests.append({'billing_day' : 1, \
                'billing_period' : (datetime.date(2011, 11, 1), datetime.date(2011, 11, 30))})
        tests.append({'billing_day' : 18, \
                'billing_period' : (datetime.date(2011, 11, 18), datetime.date(2011, 12, 17))})
        tests.append({'billing_day' : 24, \
                'billing_period' : (datetime.date(2011, 11, 24), datetime.date(2011, 12, 23))})
        tests.append({'billing_day' : 24, \
                'billing_period' : (datetime.date(2011, 11, 24), datetime.date(2011, 12, 23))})
        tests.append({'billing_day' : 30, \
                'billing_period' : (datetime.date(2011, 11, 30), datetime.date(2011, 12, 29))})
        tests.append({'billing_day' : 31, \
                'billing_period' : (datetime.date(2011, 11, 30), datetime.date(2011, 12, 30))})

        for test in tests:
            first_day = test['billing_period'][0]
            last_day = test['billing_period'][1]

            for is_roaming in (True, False):
                expected = self.__calculate_expected(first_day, last_day, upload_incr, download_incr)
                result = self.storage.get_accumulated(IMSI, first_day, last_day, is_roaming)
                print expected, result

                self.assertEqual(expected, result, \
                    'Problem with billing_day: %d\nExpected:\t%s\nResult:\t\t%s' % \
                    (test['billing_day'], expected, result))

    def __fill_data(self, imsi, first_day, last_day, upload_incr, download_incr, is_roaming):
        tag = 'DUN' if not is_roaming else 'DUNR'
        device = 'IMSI:%s' % imsi

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        foo_day = datetime.date(first_day.year, first_day.month, first_day.day)
        delta = last_day - first_day

        for i in range(0, delta.days + 1):
            sql = 'INSERT INTO daily ("year", "month", "day", "up", "down", "millis", "tag", "device") ' + \
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?);'
            cursor.execute(sql, \
                    (foo_day.year, foo_day.month, foo_day.day, upload_incr, download_incr, 12345, tag, device))
            foo_day += datetime.timedelta(days=1)
        conn.commit()

        cursor.close()
        conn.close()

    def __calculate_expected(self, first_day, last_day, upload_incr, download_incr):
        delta = last_day - first_day

        expenses = {}
        expenses['sent'] = (delta.days + 1) * upload_incr
        expenses['received'] = (delta.days + 1) * download_incr
        expenses['total'] = expenses['sent'] + expenses['received']
        return expenses
