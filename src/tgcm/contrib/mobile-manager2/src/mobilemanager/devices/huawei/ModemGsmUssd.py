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
from mobilemanager.mmdbus.properties import prop
from mobilemanager.Logging import debug, info, warning, error

MM_URI = 'org.freedesktop.ModemManager.Modem.Gsm.Ussd'

class ModemGsmUssd(object):

    @method(MM_URI, 
            in_signature = 's', out_signature = 's',
            method_name = "Initiate")
    def mgu_initiate(self, command):
        ussd_cmd = command

        def function(task):
            cmd = 'AT+CUSD=1,"%s",15' % ussd_cmd
            regex = '\+CUSD:.*(?P<code>\d),\"(?P<msg>.+)\",'
            r_values = ["code", "msg"]
            self.io.com.send_query({"cmd" : "AT^PORTSEL=0", 
                                    "task" : task,})

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values,
                                          "alt_ok_value" : "+CUSD",
                                          })

            self.io.com.send_query({"cmd" : "AT^PORTSEL=1", 
                                    "task" : task,})
            
            if res != None:
                return int(res["code"]), res["msg"]
            
            return None

        if self.mgu_state_prop != 'idle' :
            info("ussd system not idle status")
            return ''

        self.cache["ussd_status"] = 'active'
        
        task_msg = "[Huawei] Send USSD msg -> ('%s')'" % (command)
        try:
            r = self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=20)
        except:
            self.cache["ussd_status"] = 'idle'
            return ''
            
        if r == None:
            ussd_cmd = self.mgu_to_gsm7(command)
            task_msg = "[Huawei] Send USSD msg gsm7 encoded -> ('%s')'" % (ussd_cmd)
            r = self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=20)
            
            if r == None :
                self.cache["ussd_status"] = 'idle'
                return ''
            else:
                c = r[0]
                if c == 0 :
                    self.cache["ussd_status"] = 'idle'
                elif c == 1 :
                    self.cache["ussd_status"] = 'user-response'
                else:
                    self.cache["ussd_status"] = 'idle'
            
            return self.mgu_from_gsm7(r[1])

        else:
            c = r[0]
            if c == 0 :
                self.cache["ussd_status"] = 'idle'
            elif c == 1 :
                self.cache["ussd_status"] = 'user-response'
            else:
                self.cache["ussd_status"] = 'idle'
            
            return r[1]

    @method(MM_URI, 
            in_signature = 's', out_signature = 's',
            method_name = "Respond")
    def mgu_respond(self, response):
        ussd_cmd = response

        def function(task):
            cmd = 'AT+CUSD=1,"%s",15' % ussd_cmd
            regex = '\+CUSD:.*(?P<code>\d),\"(?P<msg>.+)\",'
            r_values = ["code", "msg"]

            self.io.com.send_query({"cmd" : "AT^PORTSEL=0", 
                                    "task" : task,})

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values,
                                          "alt_ok_value" : "+CUSD",
                                          })

            self.io.com.send_query({"cmd" : "AT^PORTSEL=1", 
                                    "task" : task,})

            if res != None:
                return int(res["code"]), res["msg"]
            
            return None

        if self.mgu_state_prop != 'user-response' :
            info("[Huawei] USSD session is not in user-response status")
            return ''
        
        task_msg = "[Huawei] Send USSD response -> ('%s')'" % (response)
        try:
            r = self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=20)
        except:
            self.cache["ussd_status"] = 'idle'
            return ''

        if r == None:
            ussd_cmd = self.mgu_to_gsm7(response)
            task_msg = "[Huawei] Send USSD response gsm7 encoded -> ('%s')" % (ussd_cmd)
            r = self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=20)
            
            if r == None :
                self.cache["ussd_status"] = 'idle'
                return ''
            else:
                c = r[0]
                if c == 0 :
                    self.cache["ussd_status"] = 'idle'
                elif c == 1 :
                    self.cache["ussd_status"] = 'user-response'
                else:
                    self.cache["ussd_status"] = 'idle'
            
            return self.mgu_from_gsm7(r[1])
        else:
            c = r[0]
            if c == 0 :
                self.cache["ussd_status"] = 'idle'
            elif c == 1 :
                self.cache["ussd_status"] = 'user-response'
            else:
                self.cache["ussd_status"] = 'idle'
            
            return r[1]

