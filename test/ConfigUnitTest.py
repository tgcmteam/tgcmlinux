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

import gconf
import unittest

import tgcm.core.Config as Config

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)


class BillingDayTest(unittest.TestCase):
    config = Config.Config('es')

    def setUp(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def tearDown(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def testIsFixedDay(self):
        values = (True, False)
        for value in values:
            self.config.set_is_default_fixed_billing_day(value)
            result = self.config.is_default_fixed_billing_day()
            self.assertEqual(value, result)

    def testImsiBasedIsFixed(self):
        imsi = '214075516806795'
        values = range(True, False)
        for value in values:
            self.config.set_is_imsi_based_fixed_billing_day(imsi, value)
            result = self.config.is_imsi_based_fixed_billing_day(imsi)
            self.assertEqual(value, result)

    def testInvalidImsiBasedIsFixed(self):
        imsi = '214075516806795'
        values = ('a', '@', '1', '2', None)
        for value in values:
            self.assertRaises(TypeError, self.config.set_is_imsi_based_fixed_billing_day, imsi, value)

    def testDefaultImsiBasedIsFixed(self):
        imsi = '214075516806795'
        value = True
        self.config.set_is_default_fixed_billing_day(value)
        result = self.config.is_imsi_based_fixed_billing_day(imsi)
        self.assertEqual(value, result)

    def testDefaultBillingDay(self):
        values = range(1, 32)
        for value in values:
            self.config.set_default_billing_day(value)
            result = self.config.get_default_billing_day()
            self.assertEqual(value, result)

    def testInvalidDefaultBillingDay(self):
        values = ('a', '@', '1', '2', None)
        for value in values:
            self.assertRaises(TypeError, self.config.set_default_billing_day, value)

    def testInvalidImsiBillingDay(self):
        imsi = None
        value = 18
        self.assertRaises(AttributeError, self.config.set_imsi_based_billing_day, imsi, value)

    def testImsiBasedBillingDay(self):
        imsi = '214075516806795'
        values = range(1, 32)
        for value in values:
            self.config.set_imsi_based_billing_day(imsi, value)
            result = self.config.get_imsi_based_billing_day(imsi)
            self.assertEqual(value, result)

    def testInvalidImsiBasedBillingDay(self):
        imsi = '214075516806795'
        values = ('a', '@', '1', '2', None)
        for value in values:
            self.assertRaises(TypeError, self.config.set_imsi_based_billing_day, imsi, value)

    def testDefaultForImsiBasedBillingDay(self):
        imsi = '214075516806795'
        default_value = 18
        self.config.set_default_billing_day(default_value)
        result = self.config.get_imsi_based_billing_day(imsi)
        self.assertEqual(default_value, result)


class MonthlyLimitsTest(unittest.TestCase):
    config = Config.Config('es')

    def setUp(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def testGetMonthlyLimits(self):
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            results = self.config.get_monthly_limits(roaming)
            self.assertEqual(limits, results)

    def testInvalidMonthlyLimits(self):
        roaming_values = (False, True)
        limits = ('a', '@', '1', '2', None)
        for roaming in roaming_values:
            self.assertRaises(TypeError, self.config.set_monthly_limits, limits, roaming)

    def testDefaultSelectedMonthlyLimit(self):
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = 200
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.config.set_default_selected_monthly_limit(value, roaming)
            result = self.config.get_default_selected_monthly_limit(roaming)
            self.assertEqual(value, result)

    def testInvalidTypeDefaultSelectedMonthlyLimit(self):
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = '@'
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.assertRaises(TypeError, self.config.set_default_selected_monthly_limit, value, roaming)

    def testDefaultSelectedNotInMonthlyLimits(self):
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = 120
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.assertRaises(AttributeError, self.config.set_default_selected_monthly_limit, value, roaming)

    def testImsiBasedSelectedMonthlyLimit(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = 3072
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.config.set_imsi_based_selected_monthly_limit(imsi, value, roaming)
            result = self.config.get_imsi_based_selected_monthly_limit(imsi, roaming)
            self.assertEqual(value, result)

    def testInvalidImsiMonthlyLimit(self):
        imsi = None
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = 3072
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.assertRaises(AttributeError, self.config.set_imsi_based_selected_monthly_limit, imsi, value, roaming)

    def testInvalidTypeImsiBasedSelectedMonthlyLimit(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = '@'
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.assertRaises(TypeError, self.config.set_imsi_based_selected_monthly_limit, imsi, value, roaming)

    def testImsiBasedSelectedNotInMonthlyLimits(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = '@'
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.assertRaises(TypeError, self.config.set_imsi_based_selected_monthly_limit, imsi, value, roaming)

    def testDefaultForImsiBasedMonthlyLimit(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        limits = [200, 1024, 3072, 5120, 10240, -1]
        value = 3072
        for roaming in roaming_values:
            self.config.set_monthly_limits(limits, roaming)
            self.config.set_default_selected_monthly_limit(value, roaming)
            result = self.config.get_imsi_based_selected_monthly_limit(imsi, roaming)
            self.assertEqual(value, result)

    def testOtherImsiBasedMonthlyLimit(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        value = 666
        for roaming in roaming_values:
            self.config.set_imsi_based_other_monthly_limit(imsi, value, roaming)
            result = self.config.get_imsi_based_other_monthly_limit(imsi, roaming)
            self.assertEqual(value, result)

    def testInvalidTypeOtherImsiBasedMonthlyLimit(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        value = '@'
        for roaming in roaming_values:
            self.assertRaises(TypeError, self.config.set_imsi_based_other_monthly_limit, imsi, value, roaming)

    def testDefaultOtherImsiBasedMonthlyLimit(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        for roaming in roaming_values:
            result = self.config.get_imsi_based_other_monthly_limit(imsi, roaming)
            self.assertIsNotNone(result)


class AlertsTest(unittest.TestCase):
    config = Config.Config('es')

    def setUp(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def testGetAlerts(self):
        roaming_values = (False, True)
        alerts = [100, 90, 75, 50]
        for roaming in roaming_values:
            self.config.set_alerts(alerts, roaming)
            results = self.config.get_alerts(roaming)
            self.assertEqual(alerts, results)

    def testInvalidAlerts(self):
        roaming_values = (False, True)
        alerts = ('a', '@', '1', '2', None)
        for roaming in roaming_values:
            self.assertRaises(TypeError, self.config.set_alerts, alerts, roaming)

    def testGetDefaultEnabledAlerts(self):
        roaming_values = (False, True)
        alerts = (100, 90, 75, 50)
        enabled_alerts = (50, 90, 75)
        for roaming in roaming_values:
            self.config.set_alerts(alerts, roaming)
            for alert in alerts:
                enabled = alert in enabled_alerts
                self.config.enable_default_alert(alert, enabled, roaming)
            result = self.config.get_default_enabled_alerts(roaming)
            self.assertItemsEqual(enabled_alerts, result)

    def testEnabledAlertNotInAlerts(self):
        roaming_values = (False, True)
        alerts = (100, 90, 75, 50)
        enabled_alert = 80
        for roaming in roaming_values:
            self.config.set_alerts(alerts, roaming)
            self.assertRaises(AttributeError, self.config.enable_default_alert, enabled_alert, True, roaming)

    def testInvalidEnabledAlert(self):
        roaming_values = (False, True)
        alerts = (100, 90, 75, 50)
        enabled_alert = '@'
        for roaming in roaming_values:
            self.config.set_alerts(alerts, roaming)
            self.assertRaises(TypeError, self.config.enable_default_alert, enabled_alert, True, roaming)

    def testGetImsiBasedEnabledAlerts(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        alerts = (100, 90, 75, 50)
        enabled_alerts = (50, 75)
        for roaming in roaming_values:
            self.config.set_alerts(alerts, roaming)
            for alert in alerts:
                enabled = alert in enabled_alerts
                self.config.enable_imsi_based_alert(imsi, alert, enabled, roaming)
            result = self.config.get_imsi_based_enabled_alerts(imsi, roaming)
            self.assertItemsEqual(enabled_alerts, result)

    def testImsiBasedEnabledAlertNotInAlerts(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        alerts = (100, 90, 75, 50)
        enabled_alert = 80
        for roaming in roaming_values:
            self.config.set_alerts(alerts, roaming)
            self.assertRaises(AttributeError, self.config.enable_imsi_based_alert, imsi, enabled_alert, True, roaming)

    def testInvalidImsiBasedEnabledAlert(self):
        imsi = '214075516806795'
        roaming_values = (False, True)
        alerts = (100, 90, 75, 50)
        enabled_alert = '@'
        for roaming in roaming_values:
            self.config.set_alerts(alerts, roaming)
            self.assertRaises(TypeError, self.config.enable_imsi_based_alert, imsi, enabled_alert, True, roaming)


class BookmarksTest(unittest.TestCase):
    config = Config.Config('es')

    def setUp(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def tearDown(self):
        client = gconf.client_get_default()
        client.recursive_unset('/apps/tgcm', gconf.UNSET_INCLUDING_SCHEMA_NAMES)
        client.suggest_sync()

    def testAddNewBookmark(self):
        datapool = (
        (
            {
                'name': 'Menéame',
                'url': 'http://meneame.net',
                'connection': '',
                'userdata': 0,
                'readonly': True,
                'overwrite': False,
            },
            {
                'name': 'Menéame',
                'url': 'http://meneame.net',
                'connection': '',
                'userdata': 0,
                'readonly': True,
            }
        ),
        (
            {
                'name': 'Google',
                'url': 'http://www.google.es',
                'connection': 'Movistar Internet',
                'userdata': 1,
                'readonly': True,
                'overwrite': False,
            },
            {
                'name': 'Google',
                'url': 'http://www.google.es',
                'connection': 'Movistar Internet',
                'userdata': 1,
                'readonly': True,
            }
        ),
        (
            {
                'name': 'Barrapunto',
                'url': 'http://barrapunto.com',
                'connection': None,
                'userdata': None,
                'readonly': True,
                'overwrite': False,
            },
            {
                'name': 'Barrapunto',
                'url': 'http://barrapunto.com',
                'connection': '',
                'userdata': 0,
                'readonly': True,
            },
        ))
        for values, expected in datapool:
            self.config.add_bookmark(
                    values['name'],
                    values['url'],
                    values['connection'],
                    values['userdata'],
                    values['readonly'],
                    values['overwrite'])

            result = self.config.get_bookmark(values['name'])
            del result['timestamp']
            self.assertEqual(expected, result)

        expected_list = [expected for values, expected in datapool]
        result_list = self.config.get_bookmarks_list()
        for result in result_list:
            del result['timestamp']

        self.assertEqual(expected_list, result_list)

    def testOverwriteNonExistingBookmark(self):
        values = {
            'name': 'Menéame',
            'url': 'http://meneame.net',
            'connection': '',
            'userdata': 0,
            'readonly': True,
            'overwrite': True,
        }
        expected = {
            'name': 'Menéame',
            'url': 'http://meneame.net',
            'connection': '',
            'userdata': 0,
            'readonly': True,
        }

        self.config.add_bookmark(
                values['name'],
                values['url'],
                values['connection'],
                values['userdata'],
                values['readonly'],
                values['overwrite'])

        result = self.config.get_bookmark(values['name'])
        del result['timestamp']
        self.assertEqual(expected, result)

    def testOverwriteExistingBookmark(self):
        values = {
            'name': 'Menéame',
            'url': 'http://meneame.net',
            'connection': '',
            'userdata': 0,
            'readonly': True,
            'overwrite': False,
        }
        modifications = {
            'name': 'Menéame',
            'url': 'http://meneame2.net',
            'connection': 'moco',
            'userdata': 1,
            'readonly': False,
            'overwrite': True,
        }
        expected = {
            'name': 'Menéame',
            'url': 'http://meneame2.net',
            'connection': 'moco',
            'userdata': 1,
            'readonly': False,
        }

        self.config.add_bookmark(
                values['name'],
                values['url'],
                values['connection'],
                values['userdata'],
                values['readonly'],
                values['overwrite'])

        self.config.add_bookmark(
                modifications['name'],
                modifications['url'],
                modifications['connection'],
                modifications['userdata'],
                modifications['readonly'],
                modifications['overwrite'])

        result = self.config.get_bookmark(values['name'])
        del result['timestamp']
        self.assertEqual(expected, result)

    def testModifyExistingBookmark(self):
        values = {
            'name': 'Menéame',
            'url': 'http://meneame.net',
            'connection': '',
            'userdata': 0,
            'readonly': True,
            'overwrite': False,
        }
        modifications = {
            'name': 'Barrapunto',
            'url': 'http://barrapunto.com',
            'connection': 'moco',
            'userdata': 1,
            'readonly': False,
            'overwrite': True,
        }
        expected = {
            'name': 'Barrapunto',
            'url': 'http://barrapunto.com',
            'connection': 'moco',
            'userdata': 1,
            'readonly': False,
        }

        self.config.add_bookmark(
                values['name'],
                values['url'],
                values['connection'],
                values['userdata'],
                values['readonly'],
                values['overwrite'])

        self.config.modify_bookmark(
                values['name'],
                modifications['name'],
                modifications['url'],
                modifications['connection'],
                modifications['userdata'],
                modifications['readonly'])

        result = self.config.get_bookmark(modifications['name'])
        del result['timestamp']
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()
