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

from mobilemanager.devices.ModemGsm import *

MM_URI='org.freedesktop.ModemManager.Modem.Gsm.Network'

allowed_modes = [ (0, ALLOWED_MODE_2G_ONLY),
                  (1, ALLOWED_MODE_3G_ONLY),
                  (2, ALLOWED_MODE_2G_PREFERRED),
                  (3, ALLOWED_MODE_3G_PREFERRED),
                ]

class ModemGsmNetwork(object):
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetAllowedMode")
    def mgn_get_allowed_mode(self):
        def function(task):
            cmd = "AT_OPSYS?"
            regex = "\+OPSYS:\ +(?P<mode>.*),(?P<domain>.*)"
            r_values = ["mode", "domain"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})

            if res != None :
                try:
                    rmode = int(res["mode"])
                    for m , rm in allowed_modes :
                        if m == rmode:
                            return rm
                except:
                    return ALLOWED_MODE_ANY

            return ALLOWED_MODE_ANY

        task_msg = "[Option] Get Allowed Mode"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)
            

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetAllowedMode")
    def mgn_set_allowed_mode(self, mode):
        def function(task):

            if mode == ALLOWED_MODE_ANY:
                cmd = "AT_OPSYS=5,4"
                self.io.com.send_query({"cmd" : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_3G_ONLY:
                cmd = "AT_OPSYS=1,4"
                self.io.com.send_query({"cmd" : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_2G_ONLY:
                cmd = "AT_OPSYS=0,4"
                self.io.com.send_query({"cmd" : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_2G_PREFERRED:
                cmd = "AT_OPSYS=2,4"
                self.io.com.send_query({"cmd" : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_3G_PREFERRED:
                cmd = "AT_OPSYS=3,4"
                self.io.com.send_query({"cmd" : cmd,
                                        "task" : task})

        task_msg = "[Option] Set Allowed Mode"
        self.io.task_pool.exec_task(function, task_msg=task_msg)
        
    
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetDomain")    
    def mgn_get_domain(self):
        def function(task):
            cmd = "AT_OPSYS?"
            regex = "\+OPSYS:\ +(?P<mode>.*),(?P<domain>.*)"
            r_values = ["mode", "domain"]
            
            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
       
            if res != None :
                try:
                    return int(res["mode"]) if int(res["mode"]) <= DOMAIN_ANY else DOMAIN_ANY
                except:
                    return DOMAIN_ANY

            return DOMAIN_ANY

        task_msg = "[Option] Get Domain"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetDomain")
    def mgn_set_domain(self, domain):
        def function(task):
            if domain == DOMAIN_CS:
                rdomain = "0"
            elif domain == DOMAIN_PS:
                rdomain = "1"
            elif domain == DOMAIN_CS_PS:
                rdomain = "2"
            else:
                rdomain = "3"

            cmd = "AT_OPSYS=4,%s" % rdomain
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})
        
        task_msg = "[Option] Set Domain"
        self.io.task_pool.exec_task(function, task_msg=task_msg)
