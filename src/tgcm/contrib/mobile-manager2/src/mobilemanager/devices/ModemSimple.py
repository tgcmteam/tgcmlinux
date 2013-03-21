#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2010, Telefonica Móviles España S.A.U.
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
from mobilemanager.mmdbus.service import method, signal
from mobilemanager.Logging import debug, info, warning, error, register_at_command
import time

MM_URI='org.freedesktop.ModemManager.Modem.Simple'

class ModemSimple(object):

    @method(MM_URI,
            in_signature = 'a{sv}', out_signature = '',
            method_name="Connect")
    def ms_connect(self, properties):
        #dbus.Dictionary({dbus.String(u'username'):
        #  dbus.String(u'MOVISTAR', variant_level=1),
        #  dbus.String(u'number'): dbus.String(u'*99***1#', variant_level=1),
        #  dbus.String(u'network_mode'): dbus.UInt32(0L, variant_level=1),
        #  dbus.String(u'allowed_mode'): dbus.UInt32(0L, variant_level=1),
        #  dbus.String(u'apn'): dbus.String(u'movistar.es', variant_level=1),
        #  dbus.String(u'password'): dbus.String(u'MOVISTAR', variant_level=1)},
        #  signature=dbus.Signature('sv'))

        def function(task):
            self.io.enable_modem_port(True)

            cmd = "AT+CGDCONT=1,\"IP\",\"%s\"" % properties["apn"]
            res = self.io.modem.send_query({"type" : "simple",
                                      "cmd"  : cmd,
                                      "task" : task})
            register_at_command(cmd, res)

            cmd = "ATD%s" % properties["number"]
            res = self.io.modem.send_query({"type" : "simple",
                                      "cmd"  : cmd,
                                      "task" : task})
            register_at_command(cmd, res)

        task_msg = "Modem, Simple Connecting to %s " % properties["number"]
        self.io.task_pool.exec_task(function, timeout=10, timeout_waiting=10, task_msg=task_msg)

    @method(MM_URI,
            in_signature = '', out_signature = 'a{sv}',
            method_name="GetStatus")
    def ms_get_status(self):
        pass

