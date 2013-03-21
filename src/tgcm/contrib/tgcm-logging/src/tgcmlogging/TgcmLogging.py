#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2012, Telefonica Móviles España S.A.U.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import os
import sys
import datetime
import signal
import gobject
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from mobilemanager.mmdbus.service import method

import TgcmLoggingConfig

TGCM_LOG_BUS_NAME = 'es.indra.TgcmLogging'
TGCM_LOG_OBJ_PATH = '/es/indra/TgcmLogging'
TGCM_LOG_IFACE = 'es.indra.TgcmLogging'


class TgcmLoggingService(dbus.service.Object):

    def __init__(self, country):
        DBusGMainLoop(set_as_default=True)
        self.mainloop = gobject.MainLoop()

        self.bus_name = dbus.service.BusName(TGCM_LOG_BUS_NAME, dbus.SystemBus())
        dbus.service.Object.__init__(self, self.bus_name, TGCM_LOG_OBJ_PATH)

        self._line_number = 1
        self._conf = TgcmLoggingConfig.TgcmLoggingConfig(country)

        signal.signal(signal.SIGINT, self.__call_exit)

    def run(self):
        self.mainloop.run()

    @method(TGCM_LOG_IFACE,
            in_signature='sb', out_signature='',
            method_name='LogATCommand')
    def LogATCommand(self, command, response):
        entries = []
        entries.append('Sending AT: %s' % command)
        response = 'OK' if response else 'NO OK'
        entries.append('Response AT: %s' % response)
        self.__write_lines(entries)

    @method(TGCM_LOG_IFACE,
            in_signature='as', out_signature='',
            method_name='LogLines')
    def LogLines(self, lines):
        self.__write_lines(lines)

    @method(TGCM_LOG_IFACE, method_name='ResetLog')
    def ResetLog(self):
        self._line_number = 1

    @method(TGCM_LOG_IFACE, method_name='CallExit')
    def CallExit(self):
        self.__call_exit()

    def __write_lines(self, lines):
        # If the log is not enabled just do nothing
        if not self._conf.is_connection_log_enabled():
            return

        # Open connection log file
        connection_log_filepath = self._conf.get_connection_log_filepath()
        fd = open(connection_log_filepath, "a")

        # Write entry lines
        for line in lines:
            time_str = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S.%f')
            log_line = "%08d | %s | %s\n" % (self._line_number, time_str, line)
            self._line_number += 1
            fd.write(log_line)

        # Be sure that everything has been written, and close the file
        fd.flush()
        fd.close()

    def __call_exit(self):
        self.mainloop.quit()

if __name__ == '__main__':
    tgcm_logging = TgcmLoggingService('es')
    tgcm_logging.run()
