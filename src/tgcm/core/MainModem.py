#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2011-2012, Telefonica Móviles España S.A.U.
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

import Singleton
import Signals
import FreeDesktop
import DeviceManager
from NetworkManagerDbus import *
import freedesktopnet
from freedesktopnet.modemmanager import modemmanager

class MainModemError(Exception):
    pass

class MainModem(gobject.GObject):
    """
    Class that provides access to the main modem selected by the application.

    This class emits the signals related to the MainModem. It takes care
    that some events (like connected or disconnected) are coming from the main
    modem and not from other devices (wifi, ethernet, etc.).
    Available signals:
        - main-modem-removed      : The main modem was removed from the system
        - main-modem-disconnected : The connection of the main modem was stopped
        - main-modem-connected    : A connection with the main modem was started
        - main-modem-connecting   : The main modem is establishing a connection
        - main-modem-changed      : A new modem has been selected as main modem and the modem has an unlocked SIM card!
        - main-modem-candidate    : New modem detected but is not switched as main modem
    """

    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'main-modem-removed'           : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_STRING, )) ,
        'main-modem-disconnected'      : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, gobject.TYPE_STRING )) ,
        'main-modem-connected'         : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, gobject.TYPE_STRING )),
        'main-modem-connecting'        : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )) ,
        'main-modem-changed'           : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT )),
        'main-modem-candidate-added'   : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )),
        'main-modem-candidate-removed' : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )),
    }

    class Debug():
        GLOBAL_DISABLE = 0

        def __init__(self, debug):
            self.__debug = debug

        def __call__(self, func):
            def newf(*args, **kwargs):
                if self.__debug and not self.GLOBAL_DISABLE:
                    if func.__name__ == "__emit":
                        print "  >>>> MainModem : Emiting '%s'" % args[1]
                    else:
                        print "  >>>> MainModem : Calling '%s()'" % func.__name__
                func(*args, **kwargs)
            return newf

    class _Candidate():
        def __init__(self, controller, device):
            self.__nm_obj     = device
            self.__mm_obj     = device.modem
            self.__controller = controller

            iface         = 'org.freedesktop.ModemManager.Modem'
            mdev_iface    = dbus.Interface(device.modem, 'org.freedesktop.DBus.Properties')
            self.__pid    = mdev_iface.Get(iface, 'PID')
            self.__vid    = mdev_iface.Get(iface, 'VID')
            self.__vendor = mdev_iface.Get(iface, 'Vendor')

        def pid(self):
            return self.__pid

        def vid(self):
            return self.__vid

        def vendor(self):
            return self.__vendor

        # -- Return the Mobile Manager path
        def mm_path(self):
            return self.__mm_obj.object_path

        # -- Return the Network Manager path
        def nm_path(self):
            return self.__nm_obj.object_path

        def controller(self):
            return self.__controller

        # -- Return the Network Manager object
        def nm_obj(self):
            return self.__nm_obj

        # -- Return the Mobile Manager object
        def mm_obj(self):
            return self.__mm_obj

    def __init__(self, device_manager):
        gobject.GObject.__init__(self)

        self.device_manager     = device_manager
        self.device_dialer      = FreeDesktop.DeviceDialer(self.device_manager)
        self.__candidate        = None
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
            if str(nm_dev["DeviceType"]) == "GSM":
                self.__trigger_state_change = True
                break

        # -- These are the signals to be connected to Gobjects
        _signals = [
            [ 'main-changed' , self.device_manager , "main-device-changed" , self.__main_device_changed_cb ],
            [ 'dev-removed'  , self.device_manager , "device-removed"      , self.__device_removed_cb ],
        ]
        self.__signals = Signals.GobjectSignals(_signals)

    def is_on(self):
        if self.__current_device is not None:
            self.__current_device.is_on()

    def is_card_ready(self):
        if self.__current_device is not None:
            self.__current_device.is_card_ready()

    def turn_off(self):
        self.__turn(0)

    def turn_on(self):
        self.__turn(1)

    def __turn(self, on_off):
        if self.__current_device is not None:
            if on_off:
                self.__current_device.turn_on()
            else:
                self.__current_device.turn_off()

    def current_modem(self):
        return (None if self.__current_device is None else self.__current_device.modem)

    def current_device(self):
        return self.__current_device

    def candidate(self):
        return self.__candidate

    def candidate_modem(self):
        return (None if self.__candidate is None else self.__candidate.mm_obj())

    def candidate_device(self):
        return (None if self.__candidate is None else self.__candidate.nm_obj())

    # -- Return True if a main modem is available and connected
    def is_connected(self):
        retval = False
        if self.__current_device is not None:
            state = self.__current_device.nm_dev.Get(NM_DEVICE_IFACE, 'State')
            retval = True if (state == NM_DEVICE_STATE_ACTIVATED) else False

        return retval

    # -- @FIXME: Here we need the object instance instead of the object path as the modem has two paths,
    # -- for the NetworkManager and MobileManager
    def __check_main_device(self, objpath):
        return True if ( (self.__main_device_path is not None) and (self.__main_device_path == objpath) ) else False

    @Debug(1)
    def __emit(self, *args):
        self.emit(*args)

    # -- The second parameter is the path of the removed object
    # -- IMPORTANT: When the modem is connected and removed, the signal 'main-modem-disconnected' will be emitted first
    @Debug(0)
    def __device_removed_cb(self, device_manager, objpath):
        if self.__check_main_device(objpath):

            if self.__is_connected is True:
                self.__is_connected = False
                self.__emit("main-modem-disconnected", self.__current_device, self.__current_device.object_path)

            self.__main_device_path = None
            self.__current_device   = None
            self.__dbus_disconnect()
            self.__emit("main-modem-removed", objpath)

        if (self.__candidate is not None) and (self.__candidate.nm_path() == objpath):
            self.__emit("main-modem-candidate-removed", self.__candidate)
            self.__candidate = None

    @Debug(0)
    def __main_device_changed_cb(self, mcontroller, device):
        if (device is not None) and (device.get_type() == DeviceManager.DEVICE_MODEM):
            self.__candidate = self._Candidate(mcontroller, device)
            self.__emit('main-modem-candidate-added', self.__candidate)

    @Debug(0)
    def emit_main_modem_changed(self, modem):
        if self.__candidate is None:
            raise MainModemError, "No candidate available for emitting 'main-modem-changed'"

        self.__main_device_path = self.__candidate.nm_path()
        self.__emit_main_modem_changed(self.__candidate.controller(), self.__candidate.nm_obj())
        self.__candidate        = None

    def is_main_device(self, device):
        return str(self.__main_device_path) == str(device.object_path)

    @Debug(0)
    def set_main_device(self, device):
        self.__main_device_path = device.object_path
        self.__emit_main_modem_changed(self.device_manager, device)

    @Debug(0)
    def __nm_state_changed_cb(self, new_state, old_state, reason):

        if new_state == NM_DEVICE_STATE_ACTIVATED:
            self.__is_connected = True
            self.__emit("main-modem-connected", self.__current_device, self.__current_device.object_path)

        elif new_state == NM_DEVICE_STATE_DISCONNECTED:
            self.__is_connected = False
            self.__emit("main-modem-disconnected", self.__current_device, self.__current_device.object_path)

        elif new_state in range(NM_DEVICE_STATE_DISCONNECTED, NM_DEVICE_STATE_ACTIVATED):

            # -- Assure that this signal is emitted only one time
            if old_state not in range(NM_DEVICE_STATE_PREPARE, NM_DEVICE_STATE_SECONDARIES):
                self.__emit("main-modem-connecting", self.device_dialer)

        elif new_state in (NM_DEVICE_STATE_FAILED, NM_DEVICE_STATE_UNMANAGED, NM_DEVICE_STATE_UNAVAILABLE):

            if old_state == NM_DEVICE_STATE_ACTIVATED:
                self.__is_connected = False
                self.__emit("main-modem-disconnected", self.__current_device, self.__current_device.object_path)

        else:
            print "@FIXME: Unhandled main modem state change to %i (old %i)" % (new_state, old_state)

    def __emit_main_modem_changed(self, device_manager, device):

        self.__dbus_disconnect()

        # -- Connect our internal callback to the NM signal of this new object
        _signals = [
            [ 'state-changed' , device.nm_dev, "StateChanged", self.__nm_state_changed_cb ]
        ]
        self.__dbus_signals = Signals.DBusSignals(_signals)

        self.__current_device = device
        self.__emit("main-modem-changed", device_manager, device)

        if self.__trigger_state_change is True:
            self.__trigger_state_change = False
            self.__nm_state_changed_cb(int(device.nm_dev["State"]), NM_DEVICE_STATE_UNKNOWN, 0)

    def __dbus_disconnect(self):
        if self.__dbus_signals is not None:
            self.__dbus_signals.disconnect_all()
            self.__dbus_signals = None

gobject.type_register(MainModem)
