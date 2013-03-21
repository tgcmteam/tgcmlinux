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

MM_URI='org.freedesktop.DBus.Properties'

class DeviceProperties(object):
    @method(MM_URI, 
            in_signature = 'ss', out_signature = 'v',
            method_name="Get")
    def dp_get(self, interface, prop_name):
        try:
            return self._dbus_class_table["mobilemanager.DeviceManager.device"][interface][prop_name].fget(self)
        except:
            return []

    @method(MM_URI, 
            in_signature = 'ssv', out_signature = '',
            method_name="Set")
    def dp_set(self, interface, prop_name, value):
        try:
            prop = self._dbus_class_table["mobilemanager.DeviceManager.device"][interface][prop_name]
            self._dbus_class_table["mobilemanager.DeviceManager.device"][interface][prop_name].fset(self, value)
        except:
            pass

    @method(MM_URI, 
            in_signature = 's', out_signature = 'a{sv}',
            method_name="GetAll")
    def dp_get_all(self, interface):
        d = {}
        try:
            for item_name in self._dbus_class_table["mobilemanager.DeviceManager.device"][interface].keys():
                item = self._dbus_class_table["mobilemanager.DeviceManager.device"][interface][item_name]
                if hasattr(item, "_dbus_is_property") and item._dbus_is_property == True:
                    d[item_name] = self._dbus_class_table["mobilemanager.DeviceManager.device"][interface][item_name].fget(self)
        except:
            return {}
        return d

    @signal(MM_URI, 
            signature = 'sa{sv}',
            signal_name = 'MmPropertiesChanged')
    def dp_mm_properties_changed(self, interface, props):
        pass

