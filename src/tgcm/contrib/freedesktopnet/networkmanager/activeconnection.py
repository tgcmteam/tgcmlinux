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
from applet import Connection
from device import Device
from accesspoint import AccessPoint
from util import Enum

class ActiveConnection(DBusClient):
    """
     Signals:
    PropertiesChanged ( a{sv}: properties )
    
     Properties:
    ServiceName - s - (read)
    Connection - o - (read)
    SpecificObject - o - (read)
    Devices - ao - (read)
    State - u - (read) (NM_ACTIVE_CONNECTION_STATE)
    Default - b - (read)
    
     Enumerated types:
    NM_ACTIVE_CONNECTION_STATE
    """

    SERVICE = "org.freedesktop.NetworkManager"
    IFACE = "org.freedesktop.NetworkManager.Connection.Active"

    def __init__(self, opath):
        super(ActiveConnection, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface=self.IFACE)

    class State(Enum):
        UNKNOWN = 0
        ACTIVATING = 1
        ACTIVATED = 2

    def __getitem__(self, key):
        "Implement Connection by adding the required ServiceName"

        v = super(ActiveConnection, self).__getitem__(key)
        if key == "Connection":     
            sn="org.freedesktop.NetworkManager"       
            v = Connection(sn, v)
        return v

ActiveConnection._add_adaptors(
    PropertiesChanged = SA(identity),
#    ServiceName = PA(identity),
#    Connection = PA(Connection), # implemented in __getitem__
    SpecificObject = PA(AccessPoint), #in most cases. figure out.
    Devices = PA(seq_adaptor(Device._create)),
    State = PA(ActiveConnection.State),
    Default = PA(bool),
    )
