#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Martin Vidner
# 
# 
# Authors:
#   Martin Vidner <martin at vidnet.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import dbus
from freedesktopnet.dbusclient import DBusClient, object_path
from freedesktopnet.dbusclient.func import *
from device import Device
from activeconnection import ActiveConnection
from util import Enum

# gratuitous convertor to test writable properties
def english_to_bool(v):
    if v == "yes":
        return True
    elif v == "no":
        return False
    return v

class NetworkManager(DBusClient):
    """networkmanager
    
    The NM client library
    
     Methods:
    GetDevices ( ) → ao
    ActivateConnection ( o: connection, o: device, o: specific_object ) → o
    DeactivateConnection ( o: active_connection ) → nothing
    Sleep ( b: sleep ) → nothing
    
     Signals:
    StateChanged ( u: state )
    PropertiesChanged ( a{sv}: properties )
    DeviceAdded ( o: device_path )
    DeviceRemoved ( o: device_path )
    
     Properties:
    WirelessEnabled - b - (readwrite)
    WirelessHardwareEnabled - b - (read)
    ActiveConnections - ao - (read)
    State - u - (read) (NM_STATE)
    
     Enumerated types:
    NM_STATE
    """

    SERVICE = "org.freedesktop.NetworkManager"
    OPATH = "/org/freedesktop/NetworkManager"
    IFACE = "org.freedesktop.NetworkManager"

    def __init__(self):
        super(NetworkManager, self).__init__(dbus.SystemBus(), self.SERVICE, self.OPATH, default_interface=self.IFACE)


    class State(Enum):
        UNKNOWN = 0     
        ASLEEP = 10 
        DISCONNECTED = 20
        DISCONNECTING = 30
        CONNECTING = 40
        CONNECTED_LOCAL = 50
        CONNECTED_SITE = 60
        CONNECTED_GLOBAL = 70
        CONNECTED = 70 #Maintained for compatibility reasons

    "TODO find a good term for 'adaptor'"

#from freedesktopnet.dbusclient.adaptors import *

NetworkManager._add_adaptors(
    GetDevices = MA(seq_adaptor(Device._create)),
    ActivateConnection = MA(ActiveConnection, object_path, object_path, object_path),
    DeactivateConnection = MA(void, object_path),

    State = PA(NetworkManager.State),
    WirelessEnabled = PA(bool, english_to_bool),
    WirelessHardwareEnabled = PA(bool),
    ActiveConnections = PA(seq_adaptor(ActiveConnection)),

    StateChanged = SA(NetworkManager.State),
    )

