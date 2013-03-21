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

ACCESS_TECH_UNKNOWN=0
ACCESS_TECH_GSM=1
ACCESS_TECH_GSM_COMPACT=2
ACCESS_TECH_GPRS=3
ACCESS_TECH_EDGE=4
ACCESS_TECH_UMTS=5
ACCESS_TECH_HSDPA=6
ACCESS_TECH_HSUPA=7
ACCESS_TECH_HSPA=8
ACCESS_TECH_HSPA_PLUS=9

class ModemGsmNetwork(object):
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetAllowedMode")
    def mgn_get_allowed_mode(self):
        def function(task):
            cmd = "AT^SYSCFG?"
            regex = "\^SYSCFG:(?P<mode>.*),(?P<acqorder>.*),.*,.*,(?P<domain>.*)"
            r_values = ["mode", "acqorder"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})

            if res != None :
                mode = int(res["mode"])
                acqorder = int(res["acqorder"])

                allowed_modes = [ (13, 1, ALLOWED_MODE_2G_ONLY),
                                  (13, 0, ALLOWED_MODE_2G_ONLY),
                                  (14, 2, ALLOWED_MODE_3G_ONLY),
                                  (14, 0, ALLOWED_MODE_3G_ONLY),
                                  ( 2, 1, ALLOWED_MODE_2G_PREFERRED),
                                  ( 2, 2, ALLOWED_MODE_3G_PREFERRED)
                                  ]

                for m,a,r in allowed_modes :
                    if m == mode and a == acqorder :
                        return r

            return ALLOWED_MODE_ANY

        task_msg = "[Huawei] Get Allowed Mode"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetAllowedMode")
    def mgn_set_allowed_mode(self, mode):
        def function(task):
            a = 2
            b = 0

            if mode == ALLOWED_MODE_2G_ONLY :
                a = 13
                b = 1
            elif mode == ALLOWED_MODE_3G_ONLY :
                a = 14
                b = 2
            elif mode == ALLOWED_MODE_2G_PREFERRED :
                a = 2
                b = 1
            elif mode == ALLOWED_MODE_3G_PREFERRED :
                a = 2
                b = 2

            cmd = "AT^SYSCFG=%d,%d,3FFFFFFF,2,4" % (a, b)
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task })
        
        task_msg = "[Huawei] Set Allowed Mode"
        self.io.task_pool.exec_task(function, task_msg=task_msg)
        

    
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetDomain")    
    def mgn_get_domain(self):
        def function(task):
            cmd = "AT^SYSCFG?"
            regex = "\^SYSCFG:(?P<mode>.*),(?P<acqorder>.*),.*,.*,(?P<domain>.*)"
            r_values = ["domain"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            
            if res != None :
                return int(res["domain"])

            return DOMAIN_ANY

        task_msg = "[Huawei] Get Domain"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)
        
    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetDomain")
    def mgn_set_domain(self, domain):
        mode = self.mgn_get_allowed_mode()

        def function(task):
            real_domain = 2

            if domain == DOMAIN_CS :
                real_domain = 0
            elif domain == DOMAIN_PS :
                real_domain = 1
            elif domain == DOMAIN_CS_PS :
                real_domain = 2
            elif domain == DOMAIN_ANY:
                real_domain = 3

            a = 2
            b = 0

            if mode == ALLOWED_MODE_2G_ONLY :
                a = 13
                b = 1
            elif mode == ALLOWED_MODE_3G_ONLY :
                a = 14
                b = 2
            elif mode == ALLOWED_MODE_2G_PREFERRED :
                a = 2
                b = 1
            elif mode == ALLOWED_MODE_3G_PREFERRED :
                a = 2
                b = 2
        
            cmd = "AT^SYSCFG=%d,%d,3FFFFFFF,1,%d" % (a, b, real_domain)
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})

        task_msg = "[Huawei] Set Domain"
        self.io.task_pool.exec_task(function, task_msg=task_msg)
        
    def mgn_get_tech_in_use(self):
        def function(task):
            
            res = self.io.com.send_query({"cmd" : "AT^SYSINFO",
                                           "task" : task,})
            try :
                tech = int(res[1][0][-1])
                if tech == 0 :
                    return ACCESS_TECH_UNKNOWN
                elif tech == 1 :
                    return ACCESS_TECH_GSM
                elif tech == 2 :
                    return ACCESS_TECH_GPRS
                elif tech == 3 :
                    return ACCESS_TECH_EDGE
                elif tech == 4 :
                    return ACCESS_TECH_UMTS
                elif tech == 5 :
                    return ACCESS_TECH_HSDPA
                elif tech == 6 :
                    return ACCESS_TECH_HSUPA
                elif tech == 7 :
                    return ACCESS_TECH_HSPA
                elif tech == 9 or  tech == 17 or tech == 18 :
                    return ACCESS_TECH_HSPA_PLUS
                else :
                    return ACCESS_TECH_UNKNOWN 
            except:
                return ACCESS_TECH_UNKNOWN

                
        
        task_msg = "[Huawei] Get Access Tech"
        self.cache["access-tech"] = self.io.task_pool.exec_task(function, task_msg=task_msg)
        
        return self.cache["access-tech"]
