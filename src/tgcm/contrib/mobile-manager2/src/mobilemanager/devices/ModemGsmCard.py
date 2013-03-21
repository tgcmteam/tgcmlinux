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
from time import sleep

from mobilemanager.mmdbus.service import method, signal
from mobilemanager.mmdbus.properties import prop
from mobilemanager.Logging import debug, info, warning, error

from mobilemanager.devices.ModemGsmExceptions import SimPinRequired, \
    SimPukRequired, SimFailure

from dbus.exceptions import DBusException
from mobilemanager.Logging import debug, info, warning, error

MM_URI = 'org.freedesktop.ModemManager.Modem.Gsm.Card'

from ModemGsm import MODE_UNKNOWN, BAND_UNKNOWN

class ModemGsmCard(object):

    @method(MM_URI,
            in_signature = 'ss', out_signature = '',
            method_name = "ChangePin")
    def mgc_change_pin(self, old_pin, new_pin):
        def function(task):
            cmd = 'AT+CPWD="SC", "%s", "%s"'  % (old_pin, new_pin)
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})
            return True

        try:
            task_msg = "Change Pin (%s -> %s)" % (old_pin, new_pin)
            self.io.task_pool.exec_task(function, task_msg=task_msg)
            self.cache["unlock_status"] = ''
        except DBusException as e:
            sleep(1)
            self.mgc_refresh_unlock_status()
            self.mgc_emit_unlock_state_info()
            raise e

    @method(MM_URI,
            in_signature = 'sb', out_signature = '',
            method_name = "EnablePin")
    def mgc_enable_pin(self, pin, enabled):
        def function(task):
            cmd = 'AT+CLCK="SC",%s,"%s"' % (int(enabled), pin)
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})
            return True

        try:
            task_msg = "Enable Pin (%s, %s)" % (pin, enabled)
            self.io.task_pool.exec_task(function, task_msg=task_msg)
            self.cache["is_pin_enabled"] = enabled
            self.cache["unlock_status"] = ''
        except DBusException as e:
            sleep(1)
            self.mgc_refresh_unlock_status()
            self.mgc_emit_unlock_state_info()
            raise e

    @method(MM_URI,
            in_signature = '', out_signature = 's',
            method_name = "GetImei")
    def mgc_get_imei(self):
        def function(task):
            cmd = 'AT+CGSN'
            regex = '^(?P<imei>.+)'
            r_values = ["imei"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            if res == None :
                return None
            else :
                self.cache["imei"] = res["imei"]
                return self.cache["imei"]

        if self.cache.has_key("imei") and self.cache["imei"] != '':
            return self.cache["imei"]
        else:
            task_msg = "GetImei ()"
            return self.io.task_pool.exec_task(function, task_msg=task_msg)


    @method(MM_URI,
            in_signature = '', out_signature = 's',
            method_name = "GetImsi")
    def mgc_get_imsi(self):
        def function(task):
            cmd = 'AT+CIMI'
            regex = '^(\+CIMI:\ +|)(?P<cimi>.+)'
            r_values = ["cimi"]

            for i in range(0, 3):
                res = self.io.com.send_query({"type" : "regex",
                                              "cmd" : cmd, "task" : task,
                                              "regex" : regex,
                                              "r_values" : r_values})
                if res == None:
                    return ""

                try:
                    # Test it is a valid integer number
                    int(res["cimi"])

                    # If the IMSI seems valid store it in a cache
                    self.cache["imsi"] = res["cimi"]
                    return self.cache["imsi"]
                except ValueError:
                    warning("Got erroneous IMSI, trying again")

            error("Got erroneous IMSI for three times, desisting")

        if self.cache.has_key("imsi") and self.cache["imsi"] != '':
            return self.cache["imsi"]
        else:
            task_msg = "GetImsi ()"
            return self.io.task_pool.exec_task(function, task_msg=task_msg)


    #ADDED-TO-STANDARD
    @method(MM_URI,
            in_signature = '', out_signature = 's',
            method_name = "GetMSISDN")
    def mgc_get_msisdn(self):
        def function(task):
            cmd = 'AT+CSIM=18,"00A40804047F106F40"'
            regex = '\+CSIM:.*4,\"(?P<file>.+)\"'
            r_values =  ["file"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})

            if res == None :
                return ''
            else:
                if res["file"].startswith("61") or res["file"] == "9000" :
                    cmd = 'AT+CSIM=10,"00B2010400"'
                    regex = '\+CSIM:.*,\"(?P<file>.+)\"'
                    r_values =  ["file"]

                    res2 = self.io.com.send_query({"type" : "regex",
                                                   "cmd" : cmd, "task" : task,
                                                   "regex" : regex,
                                                   "r_values" : r_values})

                    if res2 == None:
                        return ''
                    else:
                        try:
                            code = '70' + res2["file"].split("70",1)[1][:10]
                            ret = ''
                            for i in [1,0,3,2,5,4,7,6,9,8,11] :
                                ret = ret + str(code[i])
                            return ret
                        except:
                            return ''

            return ''

        task_msg = "GetMSISD ()"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI,
            in_signature='', out_signature='s',
            method_name='GetICCID')
    def mgc_get_iccid(self):
        def function(task):
            cmd =  'AT+CRSM=176,12258,0,0,10'
            regex = '\+CRSM:.*,\"(?P<file>.+)\"'
            r_values = ['file']

            res = self.io.com.send_query({'type': 'regex',
                                          'cmd': cmd,
                                          'task': task,
                                          'regex': regex,
                                          'r_values': r_values})

            if res == None:
                return ''
            else:
                # Ignore first 6 characters of the output
#                s = res['file'][6:]
                s = res['file']

                # swap the characters pair by pair
                s = [ s[x:x+2][::-1] for x in range(0, len(s), 2) ]

                # profit!
                iccid = ''.join(s)

                return iccid[:-1]

        if self.cache.has_key('iccid') and self.cache['iccid'] != '':
            return self.cache['iccid']
        else:
            task_msg = 'GetICCID()'
            return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI,
            in_signature = '', out_signature = 's',
            method_name = "GetOperatorId")
    def mgc_get_operator_id(self):
        return self.mgn_get_carrier_code()

    @method(MM_URI,
            in_signature = 's', out_signature = '',
            method_name = "SendPin")
    def mgc_send_pin(self, pin):
        def function(task):
            cmd = 'AT+CPIN="%s"' % pin
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})

        try:
            task_msg = "Send Pin (%s)" % (pin)
            self.io.task_pool.exec_task(function, task_msg=task_msg)
            self.cache["unlock_status"] = ''
            self.device_unlocked(self)
        except DBusException as e:
            sleep(1)
            self.mgc_refresh_unlock_status()
            self.mgc_emit_unlock_state_info()
            raise e

    @method(MM_URI,
            in_signature = 'ss', out_signature = '',
            method_name = "SendPuk")
    def mgc_send_puk(self, puk, pin):
        def function(task):
            cmd = 'AT+CPIN="%s", "%s"'  % (puk, pin)
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})
            return True

        try:
            task_msg = "Send Puk (%s,%s)" % (puk, pin)
            self.io.task_pool.exec_task(function, task_msg=task_msg)
            self.cache["unlock_status"] = ''
        except DBusException as e:
            sleep(1)
            self.mgc_refresh_unlock_status()
            self.mgc_emit_unlock_state_info()
            raise e


    @method(MM_URI,
            in_signature = 'ss', out_signature = '',
            method_name = "SetPin")
    def mgc_set_pin(self, old_pin, new_pin):
        def function(task):
            cmd = 'AT+CPWD="SC", "%s", "%s"'  % (old_pin, new_pin)
            self.io.com.send_query({"type" : "simple",
                                    "cmd" : cmd, "task" : task})
            return True

        try:
            task_msg = "Set Pin (%s,%s)" % (old_pin, new_pin)
            self.io.task_pool.exec_task(function, task_msg=task_msg)
            self.cache["unlock_status"] = ''
            self.device_unlocked(self)
        except DBusException as e:
            sleep(1)
            self.mgc_refresh_unlock_status()
            self.mgc_emit_unlock_state_info()
            raise e

    def mgc_refresh_unlock_status(self):
        def function(task):
            cmd = 'AT+CPIN?'
            regex = "\+CPIN: (?P<unlock_status>.+)"
            r_values = ["unlock_status"]

            # -- By some modems it's required to wait some time before the first read
            if self.cache.has_key("unlock_status") is False:
                vendor = self.driver.vendor()
                if vendor.is_huawei():
                    sleep(4)
                elif vendor.is_novatel():
                    sleep(1)
                elif vendor.is_zte():
                    sleep(2)

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})

            if res == None :
                self.cache["unlock_status"] = ''
            else:
                if res["unlock_status"] == "READY":
                    self.cache["unlock_status"] = ''
                elif res["unlock_status"] == "SIM PIN":
                    self.cache["unlock_status"] = 'sim-pin'
                elif res["unlock_status"] == "SIM PUK":
                    self.cache["unlock_status"] = 'sim-puk'
                elif res["unlock_status"] == "PH-NET PIN":
                    self.cache["unlock_status"] = 'ph-net-pin'
                elif res["unlock_status"] == "PH-NET PUK":
                    self.cache["unlock_status"] = 'ph-net-puk'

            # -- Return False by operation failures
            return (res != None)

        try:
            task_msg = "Refreshing unlock status"
            return self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=10, timeout_waiting=10)
        except Exception, err:
            print "Exception '%s' while refreshing unlock status" % err
            raise Exception, err

    def mgc_get_unlock_status(self):
        if "unlock_status" not in self.cache :
            self.mgc_refresh_unlock_status()

        return self.cache["unlock_status"]

    @prop(MM_URI, signature = 'u',
          property_name = 'SupportedBands', perms = "r")
    def mgc_supported_bands_prop():
        def fget(self):
            return BAND_UNKNOWN

        def fset(self, supported_bands):
            pass

    @prop(MM_URI, signature = 'u',
          property_name = 'SupportedModes', perms = "r")
    def mgc_supported_modes_prop():
        def fget(self):
            return MODE_UNKNOWN

        def fset(self, supported_modes):
            pass

    #ADDED-TO-STANDARD
    @method(MM_URI,
            in_signature = '', out_signature = 'b',
            method_name = "IsPinEnabled")
    def mgc_is_pin_enabled(self):
        def function(task):
            cmd = 'AT+CLCK="SC",2'
            regex = "\+CLCK:\ +(?P<enabled>[01])"
            r_values = ["enabled"]

            res = self.io.com.send_query({"type" : "regex",
                                          "cmd" : cmd, "task" : task,
                                          "regex" : regex,
                                          "r_values" : r_values})
            if res != None :
                if res["enabled"] == '1' :
                    self.cache["is_pin_enabled"] = True
                    return True
                else:
                    self.cache["is_pin_enabled"] = False
                    return False


        if "is_pin_enabled" not in self.cache :
            task_msg = "Asking if is Pin enabled"
            return self.io.task_pool.exec_task(function, task_msg=task_msg)
        else:
            return self.cache["is_pin_enabled"]

    def mgc_emit_unlock_state_info(self):
        if self.cache.has_key("unlock_status"):
            if self.cache["unlock_status"] in ['', 'sim-pin', 'sim-puk', 'ph-net-pin', 'ph-net-puk']:
                self.dp_mm_properties_changed(MM_URI, { \
                        "UnlockRequired" : self.cache["unlock_status"],
                        "UnlockRetries" : self.m_unlock_retries_prop})

    @signal(MM_URI,
            signature = 'o',
            signal_name = 'DeviceUnlocked')
    def device_unlocked(self, object):
        info("Unlocked sending signal")
        '''
        [DBUS signal exported]
        The object path of the newly added device.

        '''
        pass
