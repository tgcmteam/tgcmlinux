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

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import os
import datetime
import sqlite3

from dateutil.relativedelta import relativedelta

import emtraffic

SYNC_EVERY_N_UPDATES = 30

class TrafficStorage:
    def __init__(self, config, db_file):
        self._conf = config
        self._db_file = db_file

        # The module emtraffic has a really really WEIRD behavior. It will NOT save any data
        # expense update to the physical sqlite file if you don't EXPLICITELY order it to do it.
        # Traditionally it only do it when a connection is closed, but this is difficult to
        # guarantee because TGCM or the OS could crash, power loss, etc.
        #
        # This counter attempts to palliate it, because it stores the number of data updates has
        # been done, and every time it reaches SYNC_EVERY_N_UPDATES it will order emtraffic to
        # write its changes to the disk
        self._num_updates = 0

        # emtraffic initialization
        emtraffic.global_init()
        emtraffic.set_db_file(self._db_file)
        emtraffic.set_version(int(self._conf.get_version().split(".")[0]), \
                int(self._conf.get_version().split(".")[1]), 0, \
                self._conf.get_version() + ".0")

        self._traffics = {}
        for is_roaming in (False, True):
            tag = self.__get_tag(is_roaming)
            traffic = emtraffic.Traffic()
            traffic.set_type(tag)
            self._traffics[is_roaming] = traffic

        emtraffic.update_traffic_history()

    def __del__(self):
        emtraffic.global_end()

    def get_history(self, imsi, is_roaming):
        traffic = self._traffics[is_roaming]
        tag = self.__get_tag(is_roaming)
        device = self.__get_device(imsi)
        billing_day = self.__get_billing_day(imsi)

        emtraffic.set_invoice_day(billing_day)
        traffic.set_device(device)
        return emtraffic.get_traffic_history(tag, device)

    def get_history_date_interval(self, imsi):
        outputs = []
        for is_roaming in (True, False):
            outputs.append(self.get_history(imsi, is_roaming))

        lower_interval = None
        upper_interval = datetime.date.today()

        # Look for the month of the oldest register we have in the history data
        for output in outputs:
            if len(output) > 0:
                start = datetime.date(output[0][0][1], output[0][0][0], 1)
                if (lower_interval is None) or (start < lower_interval):
                    lower_interval = start

        # Only show the last 6 months in history data
        if lower_interval is not None:
            six_months_before_today = datetime.date.today() - relativedelta(months = 5)
            if six_months_before_today > lower_interval:
                lower_interval = six_months_before_today

        # If there is no history data, consider that it started the first day of current
        # billing period
        else:
            if self._conf.is_last_imsi_seen_valid():
                current_billing_period = self._conf.get_imsi_based_billing_period(imsi)
            else:
                current_billing_period = self._conf.get_default_billing_period()
            lower_interval = current_billing_period[0]

        return (lower_interval, upper_interval)

    def get_pending(self, imsi, is_roaming):
        traffic = self._traffics[is_roaming]
        device = self.__get_device(imsi)
        billing_day = self.__get_billing_day(imsi)

        emtraffic.set_invoice_day(billing_day)
        traffic.set_device(device)
        return traffic.get_pending_traffic_history()

    def get_accumulated(self, imsi, first_day, last_day, is_roaming):
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()

        tag = self.__get_tag(is_roaming)
        device = self.__get_device(imsi)

        if first_day.month == last_day.month:
            consult = 'SELECT SUM(up), SUM(down), SUM(up + down) FROM DAILY ' + \
                    'WHERE tag=? AND device=? AND ' + \
                    '((year=? AND month=? and day>=?) AND (year=? AND month=? and day<=?))'
        else:
            consult = 'SELECT SUM(up), SUM(down), SUM(up + down) FROM DAILY ' + \
                    'WHERE tag=? AND device=? AND ' + \
                    '((year=? AND month=? and day>=?) OR (year=? AND month=? and day<=?))'
        cursor.execute(consult, (tag, device, \
                first_day.year, first_day.month, first_day.day, \
                last_day.year, last_day.month, last_day.day))
        row = cursor.fetchone()

        expenses = {}
        expenses['sent'] = row[0] if row[0] is not None else 0
        expenses['received'] = row[1] if row[1] is not None else 0
        expenses['total'] = row[2] if row[2] is not None else 0
        return expenses

    def update(self, imsi, sent_delta, recv_delta, is_roaming, suggest_sync = False):
        traffic = self._traffics[is_roaming]
        device = self.__get_device(imsi)
        billing_day = self.__get_billing_day(imsi)

        perform_sync = False
        self._num_updates += 1
        if suggest_sync or (self._num_updates == SYNC_EVERY_N_UPDATES):
            perform_sync = True
            self._num_updates = 0

        emtraffic.set_invoice_day(billing_day)
        traffic.set_device(device)
        traffic.process_history_traffic(sent_delta, recv_delta, \
                int(os.times()[4] * 1000.0), perform_sync)

    def do_sync(self, imsi, is_roaming):
        self.update(imsi, 0, 0, is_roaming, suggest_sync = True)

    def reset(self, imsi, is_roaming):
        tag = self.__get_tag(is_roaming)
        device = self.__get_device(imsi)
        emtraffic.reset_traffic_history(tag, device)

    def __get_billing_day(self, imsi):
        if (imsi is not None) and (len(imsi) > 0):
            return self._conf.get_imsi_based_billing_day(imsi)
        else:
            return self._conf.get_default_billing_day()

    def __get_device(self, imsi):
        return 'IMSI:%s' % imsi

    def __get_tag(self, is_roaming):
        if not is_roaming:
            return 'DUN'
        else:
            return 'DUNR'

