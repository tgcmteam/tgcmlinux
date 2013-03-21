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

from mobilemanager.mmdbus.service import method
from mobilemanager.devices.ModemGsmExceptions import IncorrectPassword

MM_URI     = 'org.freedesktop.ModemManager.Modem'
MM_URI_DBG = 'org.freedesktop.ModemManager.Debug'


class Modem(object):

    @method(MM_URI,
            in_signature='', out_signature='b',
            method_name='IsOperatorLocked')
    def m_is_operator_locked(self):
        def function(task):
            cmd = 'AT+ZSEC?'
            regex = '\+ZSEC: (?P<unlock_status>.+)'
            r_values = ['unlock_status']

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})

            is_operator_locked = False
            if (res is not None) and (res['unlock_status'] == '2,1'):
                is_operator_locked = True

            return is_operator_locked

        task_msg = "[ZTE] Is Device Operator Locked?"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)


    @method(MM_URI,
            in_signature='s', out_signature='',
            method_name='UnlockOperator')
    def m_unlock_operator(self, unlock_code):
        def function(task):
            cmd = 'AT+ZNCK="%s"' % unlock_code
            regex = '(?P<output>.+)'
            r_values = ['output']

            res = self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})

            if res == True:
                # Modem uses to keep at status +CFUN=5, and the radio is
                # needed to be restarted after that
                cmd = 'AT+CFUN?'
                regex = '\+CFUN:\ +(?P<status>\d*)'
                r_values = ["status"]

                res = self.io.com.send_query({"type"     : "regex",
                                              "cmd"      : cmd,
                                              "task"     : task,
                                              "regex"    : regex,
                                              "r_values" : r_values})

                if (res is not None) and (int(res["status"]) != 1):
                    self.io.com.send_query({"cmd" : "AT+CFUN=1" , "task" : task})
            else:
                raise IncorrectPassword

        task_msg = "[ZTE] Device Operator Unlock"
        self.io.task_pool.exec_task(function, task_msg=task_msg)
