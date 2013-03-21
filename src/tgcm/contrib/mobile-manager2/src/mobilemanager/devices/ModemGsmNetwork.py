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
import time
import gobject

from mobilemanager.mmdbus.service import method, signal
from mobilemanager.mmdbus.properties import prop
from mobilemanager.Logging import debug, info, warning, error


from dbus.exceptions import DBusException

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
ACCESS_TECH_HSPA_PLUS   = 9

class ModemGsmNetwork(object):
            
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetBand")
    def mgn_get_band(self):
        #Must be implementated for each device manufacturer
        pass

    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetNetworkMode")
    def mgn_get_network_mode(self):
        # DEPRECATED 
        # ------------------------------------------------
        #Must be implementated for each device manufacturer
        return 0

    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetAllowedMode")
    def mgn_get_allowed_mode(self):
        #Must be implementated for each device manufacturer
        return 0
    

    #ADDED-TO-STANDARD
    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetDomain")
    def mgn_get_domain(self):
        #Must be implementated for each device manufacturer
        return 0

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetBand")
    def mgn_set_band(self, band):
        #Must be implementated for each device manufacturer
        pass

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetNetworkMode")
    def mgn_set_network_mode(self, mode):
        # DEPRECATED 
        # ------------------------------------------------
        #Must be implementated for each device manufacturer
        pass

    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetAllowedMode")
    def mgn_set_allowed_mode(self, mode):
        #Must be implementated for each device manufacturer
        pass

    #ADDED-TO-STANDARD
    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="SetDomain")
    def mgn_set_domain(self, domain):
        #Must be implementated for each device manufacturer
        pass

    @method(MM_URI, 
            in_signature = '', out_signature = '(uss)',
            method_name="GetRegistrationInfo")
    def mgn_get_registration_info(self):
        if self.cache.has_key("registration_info") :
            t = self.cache["registration_info"][0]
            
            if time.time() - t <= 5 :
                return self.cache["registration_info"][1]

        reg_status = self.mgn_get_registration_status()
        operator_code = self.mgn_get_carrier_code()
        operator_name = self.mgn_get_carrier_name()

        self.cache["registration_info"] = [time.time(),
                                           (reg_status,
                                            operator_code,
                                            operator_name)]

        return (reg_status, operator_code, operator_name)

    @method(MM_URI, 
            in_signature = '', out_signature = 'u',
            method_name="GetSignalQuality")
    def mgn_get_signal_quality(self):
        def function(task):
            cmd = 'AT+CSQ'
            regex = '\+CSQ:\ +(?P<signal>\d{1,2})'
            r_values = ["signal"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})
            if res == None :
                return 0
            else :
                try:
                    signal = int(res["signal"])
                    if 0 <= signal <= 31 :
                        return signal * 100 / 31
                    else:
                        return 0
                except:
                    return 0

        task_msg = "Get Signal Quality ()"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 's', out_signature = '',
            method_name="Register")
    def mgn_register(self, network_id):
        def function(task):
            cmd = 'AT+COPS=1,2,"%s"' % network_id
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})
            return True

        task_msg = "Register Network (%s)" % (network_id)
        self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=20)

    #ADDED-TO-STANDARD
    @method(MM_URI, 
            in_signature = 'su', out_signature = '',
            method_name="RegisterWithTech")
    def mgn_register_with_tech(self, network_id, tech):
        def function(task):
            cmd = 'AT+COPS=1,2,"%s",%u' % (network_id,tech)
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})
            return True

        task_msg = "Register Network Tgcm (%s - %d)" % (network_id, tech)
        self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=20)

    
    @method(MM_URI, 
            in_signature = '', out_signature = 'b',
            method_name="AutoRegistration")
    def mgn_auto_registration(self):
        def function(task):
            cmd = 'AT+COPS=0'
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})
            return True

        task_msg = "Set AutoRegistration Mode" 
        self.io.task_pool.exec_task(function, task_msg=task_msg)
        

    #ADDED-TO-STANDARD
    @method(MM_URI, 
            in_signature = '', out_signature = 'b',
            method_name="IsAutoRegistrationMode")
    def mgn_is_auto_registration_mode(self):
        def function(task):
            cmd = 'AT+COPS?'
            regex = '\+COPS:\ +(?P<mode>\d+)'
            r_values = ["mode"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})
            try:
                if int(res["mode"]) == 0 :
                    return True
                else:
                    return False
            except:
                return True

        task_msg = "Check AutoRegistration Mode" 
        return self.io.task_pool.exec_task(function, task_msg=task_msg)
                

    @method(MM_URI, 
            in_signature = '', out_signature = 'aa{ss}',
            method_name="Scan")
    def mgn_scan(self):  
        def function(task):
            cmd = "AT+COPS=?"
            regex = "\+COPS:\ +(?P<list>.*)(,,|,$)"
            r_values = ["list"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})
            
            scan_response = self.__mgn_transform_scan_list(res["list"])
            return scan_response
        
        task_msg = "Scan for networks"
        return self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=100)

    def __mgn_transform_scan_list(self, orig):
        scan_response = []
        try:
            exec("list = [%s]" % orig)
        except:
            list = []

        for status, oplong, opshort, opnum, at in list :
            d = {u'access-tech': unicode(at),
                 u'operator-long': unicode(oplong),
                 u'operator-num': unicode(opnum),
                 u'operator-short': unicode(opshort),
                 u'status': unicode(status)}
            scan_response.append(d)

        return scan_response

    
    @method(MM_URI, 
            in_signature = 's', out_signature = '',
            method_name="SetApn")
    def mgn_set_apn(self, apn):
        
        info("************* APNNNNNNNN*************** ")        
        def function(task):
            cmd = "AT+CGDCONT=1,\"IP\",\"%s\"" %apn            
            self.io.com.send_query({"type" : "simple",
                                      "cmd" : cmd, 
                                      "task" : task})
            
            
        task_msg = "Modifying APN"
        self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=60)
        
        pass                
    
    @signal(MM_URI, 
            signature = 'u',
            signal_name = 'NetworkMode')
    def mgn_network_mode_signal(self, mode):
        pass

    @signal(MM_URI, 
            signature = 'uss',
            signal_name = 'RegistrationInfo')
    def mgn_registration_info_signal(self, id, a, b):
        pass

    @signal(MM_URI, 
            signature = 'u',
            signal_name = 'SignalQuality')
    def mgn_signal_quality_signal(self, quality):
        pass
    
    @prop(MM_URI, signature='u', property_name='AccessTechnology', perms="r")
    def mgn_access_technology_prop():
        def fget(self):
            if not self.cache.has_key("access-tech"):
                return 0
            else:
                return self.cache["access-tech"]
        
        def fset(self, access_technology):
            pass

    @prop(MM_URI, signature='u', property_name='AllowedMode', perms="r")
    def mgn_allowed_mode_prop():
        def fget(self):
            return self.mgn_get_allowed_mode()
        
        def fset(self, allowed_mode):
            pass

    def mgn_get_tech_in_use(self):
        def function(task):
            cmd = 'AT+COPS?'
            regex = "\+COPS:.*,.*,.*,.*(?P<tech>\d+)"
            r_values = ["tech"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd,
                                          "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})

            try:
                t = int(res["tech"])
            except:
                t = -1

            if t == 0 :
                return ACCESS_TECH_GSM
            elif t == 1 :
                return ACCESS_TECH_GSM_COMPACT
            elif t == 2 :
                return ACCESS_TECH_UMTS
            else:
                return ACCESS_TECH_UNKNOWN
            
        
        task_msg = "Get Access Tech"
        self.cache["access-tech"] = self.io.task_pool.exec_task(function, task_msg=task_msg)
        
        return self.cache["access-tech"]

    # -- Expected response: +CREG: <enable>,<stat>,[,<lac>,<ci>[,<AcT>]] | +CME ERROR
    def mgn_get_registration_status(self):
        def function(task):
            cmd = 'AT+CREG?'
            regex = "\+CREG:\s+(?P<enable>\d+),(?P<state>\d+)($|,.*)"
            r_values = ["state"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})

            if res == None:
                cmd = 'AT+CGREG?'
                regex = "\+CGREG:.*,(?P<state>\d+)"
                r_values = ["state"]

                res = self.io.com.send_query({"type"     : "regex",
                                              "cmd"      : cmd,
                                              "task"     : task,
                                              "regex"    : regex,
                                              "r_values" : r_values})
            if res != None:
                return int(res["state"])
            return 0
        
        task_msg = "Check Registration Status"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    def mgn_get_carrier_code(self):
        def function(task):
            cmd = 'AT+COPS=3,2'
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task })

            cmd = "AT+COPS?"
            regex = '\+COPS:\ +(?P<carrier_selection_mode>\d*),(?P<carrier_format>\d*),"(?P<carrier>.*)"'
            r_values = ["carrier"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task" : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})

        
            if res != None :
                return res["carrier"]
            return ''

        task_msg = "Check Carrier Code"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)


    def mgn_get_carrier_name(self):
        def function(task):
            cmd = 'AT+COPS=3,0'
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd,
                                    "task" : task})

            cmd = "AT+COPS?"
            regex = '\+COPS:\ +(?P<carrier_selection_mode>\d*),(?P<carrier_format>\d*),"(?P<carrier>.*)"'
            r_values = ["carrier"]

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})

        
            if res != None :
                return res["carrier"]
            return ''

        task_msg = "Check Carrier Name"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    #Watchers , jose borrar comentarios
    #----------------------
    
    def mgn_init_st_m_watchers(self):
        self.st_m.register_watcher(range(0,60,20), self.mgn_main_watcher)
        self.st_m.register_watcher(range(0,60, 10), self.mgn_refresh_access_tech)
        pass
        
    
    def mgn_main_watcher(self):
        if self.mgc_get_unlock_status() == '' :
            ri = self.mgn_get_registration_info()
            self.mgn_registration_info_signal(ri[0], ri[1], ri[2])
            if ri[0] == 1 or ri[0] == 5 :
                sq = self.mgn_get_signal_quality()
                self.mgn_signal_quality_signal(sq)
                
                nm = self.mgn_get_allowed_mode()
                self.mgn_network_mode_signal(nm)

                tech = self.mgn_get_tech_in_use()

    def mgn_refresh_access_tech(self):
        if self.mgc_get_unlock_status() == '' :
            tech = self.mgn_get_tech_in_use()
