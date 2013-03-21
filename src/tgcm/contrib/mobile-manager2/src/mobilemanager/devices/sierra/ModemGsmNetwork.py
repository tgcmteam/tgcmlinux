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

class ModemGsmNetwork(object):
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetAllowedMode")
    def mgn_get_allowed_mode(self):
        def function(task):
            cmd = 'AT!SELRAT?'
            regex = "\!SELRAT:\ +(?P<mode>\d+)"
            r_values = ["mode"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
   
            if res != None :
                if res["mode"] == "00" :
                    return ALLOWED_MODE_ANY
                elif res["mode"] == "01" :
                    return ALLOWED_MODE_3G_ONLY
                elif res["mode"] == "02" :
                    return ALLOWED_MODE_2G_ONLY
                elif res["mode"] == "03" :
                    return ALLOWED_MODE_2G_PREFERRED
                elif res["mode"] == "04" :
                    return ALLOWED_MODE_3G_PREFERRED

            return ALLOWED_MODE_ANY
        
        task_msg = "[Sierra] Get Allowed Mode"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetAllowedMode")
    def mgn_set_allowed_mode(self, mode):
        def function(task):
            rmode = "00"
            if mode == ALLOWED_MODE_ANY:
                rmode = "00"
            elif mode == ALLOWED_MODE_3G_ONLY:
                rmode = "01"
            elif mode == ALLOWED_MODE_2G_ONLY:
                rmode = "02"
            elif mode == ALLOWED_MODE_2G_PREFERRED:
                rmode = "03"
            elif mode == ALLOWED_MODE_3G_PREFERRED:
                rmode = "04"
                
            cmd = "AT!SELRAT=%s" % rmode
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})

        task_msg = "[Sierra] Set Allowed Mode"
        self.io.task_pool.exec_task(function, task_msg=task_msg)
    
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetDomain")    
    def mgn_get_domain(self):
        def function(task):
            cmd = 'AT!SELMODE?'
            regex = '\!SELMODE:\ +(?P<domain>\d+)'
            r_values = ["domain"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})

            if res != None:
                try:
                    return int(res["domain"])
                except:
                    pass

            return DOMAIN_ANY

        task_msg = "[Sierra] Get Domain"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetDomain")
    def mgn_set_domain(self, domain):
        def function(task):
            if domain == DOMAIN_CS:
                rdomain = "00"
            elif domain == DOMAIN_PS:
                rdomain = "01"
            elif domain == DOMAIN_CS_PS:
                rdomain = "02"
            else:
                return

            cmd = "AT!SELMODE=%s" % rdomain
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})
        
        task_msg = "[Sierra] Set Domain"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)
        

    def mgn_get_tech_in_use(self):
        def function(task):
            res = self.io.com.send_query({"cmd" : "AT*CNTI=0",
                                              "task" : task,})
            tech = res[1][0]
                    
            if res[2] == 'OK' :
                if "GSM" in tech :
                    return ACCESS_TECH_GSM
                elif "GPRS" in tech :
                    return ACCESS_TECH_GPRS
                elif "EDGE" in tech :
                    return ACCESS_TECH_EDGE
                elif "UMTS" in tech :                    
                    return ACCESS_TECH_UMTS
                elif "HSDPA/HSUPA" in tech :
                    return ACCESS_TECH_HSPA            
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
        
        task_msg = "[Sierra] Get Access Tech"
        self.cache["access-tech"] = self.io.task_pool.exec_task(function, task_msg=task_msg)
        
        return self.cache["access-tech"]
