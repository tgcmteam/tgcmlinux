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

'''
ModemManager is the main class of mobile-manager2. 
It creates a dbus interface freedesktop ModemManager.
'''

import gobject
import dbus
from mmdbus.service import Object as DbusObject
from mmdbus.service import method, signal, BusName
import dbus.mainloop.glib

from DeviceManager import DeviceManager

from mobilemanager.Logging import debug, info, warning, error

MM_SERVICE = "org.freedesktop.ModemManager"
MM_PATH = "/org/freedesktop/ModemManager"
MM_URI = MM_PATH.replace("/",".")[1:]

class ModemManager(DbusObject):
    
    '''
    ModemManager is the main class of mobile-manager2. 
    It creates a dbus interface freedesktop ModemManager.
    '''

    def __init__(self, on_system_bus=True):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = gobject.MainLoop()

        if on_system_bus == False :
            self.bus_name = BusName("org.gnome.MobileManager", 
                                    dbus.SessionBus())
        else:
            self.bus_name = BusName(MM_SERVICE, dbus.SystemBus())

        DbusObject.__init__(self, self.bus_name, MM_PATH)

    def run(self):
        '''
        ModemManager.run() starts the ModemManager service
        '''
        self.device_manager = DeviceManager(self.bus_name)
        self.device_manager.connect("device-added", self.__device_added)
        self.device_manager.connect("device-removed", self.__device_removed)
        self.mainloop.run()

    @method(MM_URI, 
            in_signature = '', out_signature = 'ao',
            method_name="EnumerateDevices")
    def enumerate_devices(self):
        '''
        [DBUS Method exported]
        List of object paths of modem devices known to the system.
        '''
        
        return self.device_manager.enumerate_devices()

    @signal(MM_URI,  
            signature = 'o',
            signal_name = 'DeviceAdded')
    def device_added(self, object):
        '''
        [DBUS signal exported]
        The object path of the newly added device.
        
        '''
        pass

    def __device_added(self, dm, obj):
        self.device_added(obj)
        info("DBUS (signal:DeviceAdded:(%s))" % (obj))

    @signal(MM_URI, 
            signature = 'o',
            signal_name = 'DeviceRemoved')
    def device_removed(self, object):
        '''
        [DBUS signal exported]
        A device was removed from the system, and is no longer available.
        '''
        pass

    def __device_removed(self, dm, obj):
        self.device_removed(obj)
        info("DBUS (signal:DeviceRemoved:(%s))" % (obj))


   
