#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
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

import gobject
import dbus
import gtk

import Singleton
import Signals
import FreeDesktop
import DeviceManager
from NetworkManagerDbus import *
import freedesktopnet
from freedesktopnet.modemmanager import modemmanager

class MainWifiError(Exception):
    pass

class MainWifi(gobject.GObject):
    """
    Class that provides access to the main wifi selected by the application.

    This class emits the signals related to the MainModem. It takes care
    that some events (like connected or disconnected) are coming from the main
    modem and not from other devices (wifi, ethernet, etc.).
    Available signals:
        - main-wifi-disconnected : The connection of the main wifi was stopped
        - main-wifi-connected    : A connection with the main wifi was started
    """

    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'main-wifi-removed'           : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_STRING, )) ,
        'main-wifi-disconnected'      : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )) ,
        'main-wifi-connected'         : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )),
        'main-wifi-connecting'        : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )) ,
        'main-wifi-changed'           : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )),
    }

    class Debug():
        GLOBAL_DISABLE = 0

        def __init__(self, debug):
            self.__debug = debug

        def __call__(self, func):
            def newf(*args, **kwargs):
                if self.__debug and not self.GLOBAL_DISABLE:
                    if func.__name__ == "__emit":
                        print "  >>>> MainWifi : Emiting '%s'" % args[1]
                    else:
                        print "  >>>> MainWifi : Calling '%s()'" % func.__name__
                func(*args, **kwargs)
            return newf

    def __init__(self, device_manager):
        gobject.GObject.__init__(self)

        self.device_manager     = device_manager
        self.device_dialer      = FreeDesktop.DeviceDialer()
        self.__current_device   = None
        self.__dbus_signals     = None
        self.__main_device_path = None
        self.__is_connected     = False
        self.__trigger_state_change = False

        # -- Schedule this for later as it needs an instance to DeviceManager (our parent)
        gobject.idle_add(self.__init)

    def __init(self):
        # -- Check if a modem is already connected so that we trigger a state check after emitting the main-modem-changed signal
        net_mgr = freedesktopnet.NetworkManager()
        for nm_dev in net_mgr.GetDevices():
            if str(nm_dev["DeviceType"]) == "WIRELESS":
                self.__trigger_state_change = True
                break

        # -- These are the signals to be connected to Gobjects
        _signals = [
            [ 'wifi-changed'   , self.device_manager , 'wifi-device-changed' , self.__wifi_device_changed_cb ],
            [ 'device-removed' , self.device_manager , 'device-removed'      , self.__device_removed_cb ],
        ]
        self.__signals = Signals.GobjectSignals(_signals)

    def current_device(self):
        return self.__current_device

    # -- Return True if a main modem is available and connected
    def is_connected(self):
        retval = False
        if self.__current_device is not None:
            state = self.__current_device.nm_dev.Get(NM_DEVICE_IFACE, 'State')
            retval = True if (state == NM_DEVICE_STATE_ACTIVATED) else False

        return retval

    def ip_interface(self):
        if self.__current_device is not None:
            return self.__current_device.nm_dev.Get(NM_DEVICE_IFACE, 'IpInterface')
        else:
            raise MainWifiError, "MainWifi is not connected or no IP assigned to device"

    # -- @FIXME: Here we need the object instance instead of the object path as the modem has two paths,
    # -- for the NetworkManager and MobileManager
    def __check_main_device(self, objpath):
        return True if ( (self.__main_device_path is not None) and (self.__main_device_path == objpath) ) else False

    @Debug(1)
    def __emit(self, *args):
        self.emit(*args)

    # -- The second parameter is the path of the removed object
    @Debug(0)
    def __device_removed_cb(self, device_manager, objpath):
        if self.__check_main_device(objpath):

            if self.__is_connected is True:
                self.__is_connected = False
                self.__emit("main-wifi-disconnected", self.__current_device)

            self.__main_device_path = None
            self.__current_device   = None
            self.__dbus_disconnect()
            self.__emit("main-wifi-removed", objpath)

    @Debug(0)
    def __wifi_device_changed_cb(self, mcontroller, device):
        if (device is not None) and (device.get_type() == DeviceManager.DEVICE_WLAN):
            self.set_main_device(device)

    def is_main_device(self, device):
        return str(self.__main_device_path) == str(device.object_path)

    @Debug(0)
    def set_main_device(self, device):
        self.__main_device_path = device.object_path
        self.__emit_main_wifi_changed(self.device_manager, device)

    @Debug(0)
    def __nm_state_changed_cb(self, new_state, old_state, reason):

        if new_state == NM_DEVICE_STATE_ACTIVATED:
            self.__is_connected = True
            self.__emit("main-wifi-connected", self.__current_device)

        elif new_state == NM_DEVICE_STATE_DISCONNECTED:
            self.__is_connected = False
            self.__emit("main-wifi-disconnected", self.__current_device)

        elif new_state in range(NM_DEVICE_STATE_DISCONNECTED, NM_DEVICE_STATE_ACTIVATED):

            # -- Assure that this signal is emitted only one time
            if old_state not in range(NM_DEVICE_STATE_PREPARE, NM_DEVICE_STATE_SECONDARIES):
                self.__emit("main-wifi-connecting", self.__current_device)

        elif new_state in (NM_DEVICE_STATE_FAILED, NM_DEVICE_STATE_UNMANAGED, NM_DEVICE_STATE_UNAVAILABLE):

            if old_state == NM_DEVICE_STATE_ACTIVATED:
                self.__is_connected = False
                self.__emit("main-wifi-disconnected", self.__current_device)

        else:
            print "@FIXME: Unhandled main wifi state change to %i (old %i)" % (new_state, old_state)

    def __emit_main_wifi_changed(self, device_manager, device):

        self.__dbus_disconnect()

        # -- Connect our internal callback to the NM signal of this new object
        _signals = [
            [ 'changed', device.nm_dev, 'StateChanged', self.__nm_state_changed_cb ]
        ]
        self.__dbus_signals = Signals.DBusSignals(_signals)

        self.__current_device = device
        self.__emit("main-wifi-changed", self.__current_device)

        if self.__trigger_state_change is True:
            self.__trigger_state_change = False
            self.__nm_state_changed_cb(int(device.nm_dev["State"]), NM_DEVICE_STATE_UNKNOWN, 0)

    def __dbus_disconnect(self):
        if self.__dbus_signals is not None:
            self.__dbus_signals.disconnect_all()
            self.__dbus_signals = None

gobject.type_register(MainWifi)
