#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Luis Galdos <luisgaldos@gmail.com>
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
import dbus
import gudev
import re

from mobilemanager.mmdbus.service import method, signal
from mobilemanager.mmdbus.properties import prop
from mobilemanager.devices.ModemGsmExceptions import IncorrectPassword

MM_URI     = 'org.freedesktop.ModemManager.Modem'
MM_URI_DBG = 'org.freedesktop.ModemManager.Debug'

class Modem(object):

    @method(MM_URI,
            in_signature = 's', out_signature = '',
            method_name="Connect")
    def m_connect(self, number):
        pass

    @method(MM_URI,
            in_signature = '', out_signature = '',
            method_name="Disconnect")
    def m_disconnect(self):
        self.io.enable_modem_port(False)

    @method(MM_URI,
            in_signature = 'b', out_signature = '',
            method_name="Enable")
    def m_enable(self, enable):
        if "enabled" not in self.cache :
            return

        if self.cache["enabled"] == enable :
            return

        if enable == True :
            self.io.resume()
            self.st_m.resume()
            self.cache["enabled"] = True
        else:
            self.st_m.pause()
            self.io.pause()
            self.cache["enabled"] = False

    @method(MM_URI,
            in_signature = 's', out_signature = '',
            method_name="FactoryReset")
    def m_factory_reset(self, code):
        pass

    @method(MM_URI,
            in_signature = '', out_signature = '(uuuu)',
            method_name="GetIPV4Config")
    def m_get_ipv4_config(self):
        return (1,1,1,1)

    @method(MM_URI,
            in_signature = '', out_signature = '(sss)',
            method_name="GetInfo")
    def m_get_info(self):
        def function(task):
            cmd = 'ATI'
            res = self.io.com.send_query({"cmd"  : cmd,
                                          "task" : task})

            if res[2] != 'OK' :
                return ('', '', '')

            ret = ['', '', '']
            pattern = re.compile('(?P<key>.*):\ +(?P<value>.*)$')
            for entry in res[1]:
                match = pattern.match(entry.strip())
                try:
                    key   = match.group('key')
                    value = match.group('value')
                    if key.lower() == 'manufacturer' :
                        ret[0] = value.strip(" ")
                    elif key.lower() == 'model' :
                        ret[1] = value.strip(" ")
                    elif key.lower() == 'revision':
                        ret[2] = value.strip(" ")

                    # -- Stop if we have all the three device values to return
                    if '' not in ret:
                        break

                except Exception, err:
                    print "@FIXME: Exception in GetInfo() parsing %s, %s" % (repr(res[1]), err)

            return ret

        task_msg = "Get Info about device"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @prop(MM_URI, signature='b', property_name='Enabled', perms="r")
    def m_enable_prop():
        def fget(self):
            if "enabled" not in self.cache :
                self.cache["enabled"] = True
                return True
            else:
                return self.cache["enabled"]

        def fset(self, enable):
            pass

    @prop(MM_URI, signature='s', property_name='Device', perms="r")
    def m_device_prop():
        def fget(self):
            return os.path.basename(self.io.modem_path)

        def fset(self, device):
            pass

    @prop(MM_URI, signature='s', property_name='Driver', perms="r")
    def m_driver_prop():
        def fget(self):
            try:
                c = gudev.Client(["tty"])
                return c.query_by_device_file(self.io.modem_path).get_parent().get_driver()
            except:
                return ''

        def fset(self, driver):
            pass

    @prop(MM_URI, signature='s', property_name='EquipmantIdentifier', perms="r")
    def m_equipament_indentifier_prop():
        def fget(self):
            return self.mgc_get_imei()

        def fset(self, eid):
            pass

    @prop(MM_URI, signature='s', property_name='MasterDevice', perms="r")
    def m_master_device_prop():
        def fget(self):
            try:
                c = gudev.Client(["tty"])
                parent = c.query_by_device_file(self.io.modem_path).get_parent()
                for x in range(0,3):
                    if parent.get_subsystem() == "usb":
                        return parent.get_parent().get_sysfs_path()
                    else:
                        parent = parent.get_parent()

                return ''
            except:
                return ''

        def fset(self, eid):
            pass

    @prop(MM_URI, signature='s', property_name='UnlockRequired', perms="r")
    def m_unlock_required_prop():
        def fget(self):
            return self.mgc_get_unlock_status()

        def fset(self, unlockrequired):
            pass

    @prop(MM_URI, signature='u', property_name='IpMethod', perms="r")
    def m_ip_method_prop():
        def fget(self):
            # PPP = 0
            # STATIC = 1
            # DHCP = 2
            return dbus.UInt32(0)

        def fset(self, ip_method):
            pass

    @prop(MM_URI, signature='u', property_name='Type', perms="r")
    def m_type_prop():
        def fget(self):
            # TYPE GSM = 1
            # TYPE CDMA = 2
            return dbus.UInt32(1)

        def fset(self, type):
            pass

    @prop(MM_URI, signature='u', property_name='UnLockRetries', perms="r")
    def m_unlock_retries_prop():
        def fget(self):
            return dbus.UInt32(999)

        def fset(self, unlockretries):
            pass

    def m_emit_disable_status_st_m_pre_pause(self):
        self.dp_mm_properties_changed(MM_URI, {"Enable" : False})

    def m_emit_enable_status_st_m_pre_resume(self):
        self.dp_mm_properties_changed(MM_URI, {"Enable" : True})

    # -- Returns the Vendor name
    @prop(MM_URI, signature='s', property_name='Vendor', perms="r")
    def m_usb_vendor_prop():
        def fget(self):
            vendor = self.driver.vendor()
            return dbus.String(vendor.name())

    # -- Returns the USB VID of the device
    @prop(MM_URI, signature='u', property_name='VID', perms="r")
    def m_usb_vid_prop():
        def fget(self):
            vid = self.driver.vid()
            if type(vid) == type(""):
                vid = int(vid, 16)

            return dbus.UInt16(vid)

    # -- Returns the USB PID of the device
    @prop(MM_URI, signature='u', property_name='PID', perms="r")
    def m_usb_pid_prop():
        def fget(self):
            pid = self.driver.pid()
            if type(pid) == type(""):
                pid = int(pid, 16)

            return dbus.UInt16(pid)

    @method(MM_URI_DBG,
            method_name='FiltersEnable', in_signature='i', out_signature='')
    def filters_enable(self, value):
        self.io.task_pool.filters_enable(value)

    @method(MM_URI_DBG,
            method_name='FiltersSet', in_signature='as', out_signature='')
    def filters_set(self, filters):
        self.io.task_pool.filters_set(list(filters))

    @method(MM_URI_DBG,
            method_name='FiltersGet', in_signature='', out_signature='as')
    def filters_get(self):
        return self.io.task_pool.filters_set()

    @method(MM_URI,
            in_signature='', out_signature='b',
            method_name='IsOperatorLocked')
    def m_is_operator_locked(self):
        def function(task):
            cmd = 'AT+CLCK="PN",2'
            regex = '\+CLCK: (?P<unlock_status>.+)'
            r_values = ['unlock_status']

            res = self.io.com.send_query({"type"     : "regex",
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values})

            is_operator_locked = False
            if (res is not None) and (res['unlock_status'] == '1'):
                is_operator_locked = True

            return is_operator_locked

        task_msg = "Is Device Operator Locked?"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI,
            in_signature='s', out_signature='',
            method_name='UnlockOperator')
    def m_unlock_operator(self, unlock_code):
        def function(task):
            cmd = 'AT+CLCK="PN",0,"%s"' % unlock_code

            res = self.io.com.send_query({"type" : "simple",
                                          "cmd"  : cmd,
                                          "task" : task })

            if res is not True:
                raise IncorrectPassword

        task_msg = "Device Operator Unlock"
        self.io.task_pool.exec_task(function, task_msg=task_msg)
