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

class ModemGsmNetwork(object):
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetAllowedMode")
    def mgn_get_allowed_mode(self):
        def function(task):
            cmd = "AT+ZSNT?"
            regex = "\+ZSNT:\ +(?P<cm_mode>\d*),(?P<net_sel_mode>\d*),(?P<acqorder>\d*)"
            r_values = ["cm_mode", "net_sel_mode", "acqorder"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})
            if res != None :
                cm_mode = int(res["cm_mode"])
                net_sel_mode = int(res["net_sel_mode"])
                acqorder = int(res["acqorder"])

                if cm_mode == 0 and acqorder == 0:
                    return ALLOWED_MODE_ANY
                elif cm_mode == 2:
                    return ALLOWED_MODE_3G_ONLY
                elif cm_mode == 1:
                    return ALLOWED_MODE_2G_ONLY
                elif cm_mode == 0 and acqorder == 2:
                    return ALLOWED_MODE_3G_PREFERRED
                elif cm_mode == 0 and acqorder == 1:
                    return ALLOWED_MODE_2G_PREFERRED

            return ALLOWED_MODE_ANY             

        task_msg = "[ZTE] Get Allowed Mode" 
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetAllowedMode")
    def mgn_set_allowed_mode(self, mode):
        def function(task):
            if mode == ALLOWED_MODE_ANY:
                cmd = "AT+ZSNT=0,0,0"
                self.io.com.send_query({"cmd"  : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_3G_ONLY:
                cmd = "AT+ZSNT=2,0,0"
                self.io.com.send_query({"cmd"  : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_2G_ONLY:
                cmd = "AT+ZSNT=1,0,0"
                self.io.com.send_query({"cmd"  : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_2G_PREFERRED:
                cmd = "AT+ZSNT=0,0,1"
                self.io.com.send_query({"cmd"  : cmd,
                                        "task" : task})
            elif mode == ALLOWED_MODE_3G_PREFERRED:
                cmd = "AT+ZSNT=0,0,2"
                self.io.com.send_query({"cmd"  : cmd,
                                        "task" : task})
                

        task_msg = "[ZTE] Set Allowed Mode (mode %i)" % mode 
        self.io.task_pool.exec_task(function, task_msg=task_msg)

        
    
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetDomain")    
    def mgn_get_domain(self):
        def function(task):
            cmd = 'AT+ZCSPS?'
            regex = '\+ZCSPS:\ +(?P<domain>\d*)'
            r_values = ["domain"]
            
            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd, 
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})
            
            if res != None:
                try:
                    return int(res["domain"])
                except:
                    pass
                
            return DOMAIN_ANY

        task_msg = "[ZTE] Get Domain" 
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
                return

            cmd = "AT+ZCSPS=%s" % rdomain
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})
            
        task_msg = "[ZTE] Set Domain"
        self.io.task_pool.exec_task(function, task_msg=task_msg)


    def mgn_get_carrier_code(self):
        def function(task):
            cmd = 'AT+COPS=3,2'
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})

            cmd = "AT+COPS?"
            regex = '\+COPS:\ +(?P<carrier_selection_mode>\d*),(?P<carrier_format>\d*),"(?P<carrier>.*)",'
            r_values = ["carrier"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})

        
            if res != None :
                return res["carrier"]
            return ''

        task_msg = "[ZTE] Check Carrier Code"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    def mgn_get_carrier_name(self):
        def function(task):
            cmd = 'AT+COPS=3,0'
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})

            cmd = "AT+COPS?"
            regex = '\+COPS:\ +(?P<carrier_selection_mode>\d*),(?P<carrier_format>\d*),"(?P<carrier>.*)",'
            r_values = ["carrier"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})

        
            if res != None :
                return res["carrier"]
            return ''

        task_msg = "[ZTE] Check Carrier Name"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    def mgn_get_tech_in_use(self):
        def function(task):
            res = self.io.com.send_query({"cmd" : "AT+ZPAS?", "task" : task})
            try:
                tech = res[1][0]
            except Exception, err:
                raise IndexError, "Invalid response from modem: %s" % repr(res)
                    
            if res[2] == 'OK' :
                if "GPRS" in tech :
                    return ACCESS_TECH_GPRS
                elif "EDGE" in tech :
                    return ACCESS_TECH_EDGE
                elif "UMTS" in tech :
                    return ACCESS_TECH_UMTS            
                elif "HSDPA" in tech :
                    return ACCESS_TECH_HSDPA
                elif "HSUPA" in tech :
                    return ACCESS_TECH_HSUPA
                elif "HSPA+" in tech :
                    return ACCESS_TECH_HSPA_PLUS
                else :
                    return ACCESS_TECH_UNKNOWN
            else:
                return ACCESS_TECH_UNKNOWN
        
        task_msg = "[ZTE] Get Access Tech"
        self.cache["access-tech"] = self.io.task_pool.exec_task(function, task_msg=task_msg)
        
        return self.cache["access-tech"]
