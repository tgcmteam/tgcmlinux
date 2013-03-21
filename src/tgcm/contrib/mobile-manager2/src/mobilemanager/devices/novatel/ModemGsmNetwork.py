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

allowed_modes = [ (0,  ALLOWED_MODE_ANY),
                  (1,  ALLOWED_MODE_2G_ONLY),
                  (2,  ALLOWED_MODE_3G_ONLY),
                  ]

class ModemGsmNetwork(object):
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetAllowedMode")
    def mgn_get_allowed_mode(self):
        def function(task):
            cmd = 'AT$NWRAT?'
            regex = "\$NWRAT:\ +(?P<mode>\d+),+(?P<domain>\d+)"
            r_values = ["mode", "domain"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            if res != None :
                for i, ret in allowed_modes :
                    if i == int(res["mode"]) :
                        return ret

            return ALLOWED_MODE_ANY
            
        task_msg = "[Novatel] Get Allowed Mode"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetAllowedMode")
    def mgn_set_allowed_mode(self, mode):
        def function(task):
            cmd = 'AT$NWRAT?'
            regex = "\$NWRAT:\ +(?P<mode>\d+),+(?P<domain>\d+)"
            r_values = ["mode", "domain"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            if res != None :
                if mode == ALLOWED_MODE_ANY:
                    rmode = 0
                elif mode == ALLOWED_MODE_2G_PREFERRED:
                    rmode = 1
                elif mode == ALLOWED_MODE_3G_PREFERRED:
                    rmode = 2  
                elif mode == ALLOWED_MODE_2G_ONLY:
                    rmode = 1
                elif mode == ALLOWED_MODE_3G_ONLY:
                    rmode = 2

                cmd = "AT$NWRAT=%s,%s" % (rmode, res["domain"])
                self.io.com.send_query({"cmd" : cmd,
                                        "task" : task})
        
        task_msg = "[Novatel] Set Allowed Mode"
        self.io.task_pool.exec_task(function, task_msg=task_msg)

    
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetDomain")    
    def mgn_get_domain(self):
         def function(task):
            cmd = 'AT$NWRAT?'
            regex = "\$NWRAT:\ +(?P<mode>\d+),+(?P<domain>\d+)"
            r_values = ["mode", "domain"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            

            if res != None :
                return int(res["domain"])

            return DOMAIN_CS_PS
         
         task_msg = "[Novatel] Get Domain"
         return self.io.task_pool.exec_task(function, task_msg=task_msg)


    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetDomain")
    def mgn_set_domain(self, domain):
        def function(task):
            cmd = 'AT$NWRAT?'
            regex = "\$NWRAT:\ +(?P<mode>\d+),+(?P<domain>\d+)"
            r_values = ["mode", "domain"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            
            if res != None :
                cmd = "AT$NWRAT=%s,%s" % (res["mode"], domain)
                self.io.com.send_query({"cmd" : cmd,
                                        "task" : task})

        task_msg = "[Novatel] Set Domain"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)


    @method(MM_URI, 
            in_signature = '', out_signature = 'aa{ss}',
            method_name="Scan")
    def mgn_scan(self):
        def function(task):
            cmd = "AT+COPS=?"
            regex = "\+COPS:\ +(?P<list>.*)"
            r_values = ['list']

            res = self.io.com.send_query({"type" : "mregex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            return res

        
        task_msg = "[Novatel] Scan for networks"
        res = self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=100)

        response = self.__mgn_novatel_transform_scan_list(res)
        
        return response

    def __mgn_novatel_transform_scan_list(self, orig):
        response = []
        for r in orig :
            try:
                exec("tmp = %s" % r["list"])
                d = {u'access-tech': unicode(tmp[4]),
                     u'operator-long': unicode(tmp[1]),
                     u'operator-num': unicode(tmp[3]),
                     u'operator-short': unicode(tmp[2]),
                     u'status': unicode(tmp[0])}
                
                response.append(d)
            except:
                pass
        
        return response

    def mgn_get_tech_in_use(self):
        def function(task):
            res = self.io.com.send_query({"cmd" : "AT$CNTI=0",
                                              "task" : task,})
            tech = res[1][0]
                    
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
        
        task_msg = "[Novatel] Get Access Tech"
        self.cache["access-tech"] = self.io.task_pool.exec_task(function, task_msg=task_msg)
        
        return self.cache["access-tech"]
