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
from freedesktopnet.dbusclient import DBusClient
from freedesktopnet.dbusclient.func import *
import util

class Mode(util.Enum):
    "Mode of a wireless device or access point."
    UNKNOWN = 0
    ADHOC = 1
    INFRA = 2

class AccessPoint(DBusClient):
    """
    
     Signals:
    PropertiesChanged ( a{sv}: properties )
    
     Properties:
    Flags - u - (read) (NM_802_11_AP_FLAGS)
    WpaFlags - u - (read) (NM_802_11_AP_SEC)
    RsnFlags - u - (read) (NM_802_11_AP_SEC)
    Ssid - ay - (read)
    Frequency - u - (read)
    HwAddress - s - (read)
    Mode - u - (read) (NM_802_11_MODE)
    MaxBitrate - u - (read)
    Strength - y - (read)
    
     Sets of flags:
    NM_802_11_AP_FLAGS
    NM_802_11_AP_SEC
    """

    class Flags(util.Flags):
        NONE = 0x0
        PRIVACY = 0x1

    class Sec(util.Flags):
        NONE = 0x0
        PAIR_WEP40 = 0x1
        PAIR_WEP104 = 0x2
        PAIR_TKIP = 0x4
        PAIR_CCMP = 0x8
        GROUP_WEP40 = 0x10
        GROUP_WEP104 = 0x20
        GROUP_TKIP = 0x40
        GROUP_CCMP = 0x80
        KEY_MGMT_PSK = 0x100
        KEY_MGMT_802_1X = 0x200

    SERVICE = "org.freedesktop.NetworkManager"
    IFACE = "org.freedesktop.NetworkManager.AccessPoint"

    def __init__(self, opath):
        super(AccessPoint, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface=self.IFACE)

AccessPoint._add_adaptors(
#    PropertiesChanged = SA(identity),
    Flags = PA(AccessPoint.Flags),
    WpaFlags = PA(AccessPoint.Sec),
    RsnFlags = PA(AccessPoint.Sec),
#    Ssid = PA(identity),
#    Frequency = PA(identity),
#    HwAddress = PA(identity),
    Mode = PA(Mode),
#    MaxBitrate = PA(identity),
    Strength = PA(int),
    )
