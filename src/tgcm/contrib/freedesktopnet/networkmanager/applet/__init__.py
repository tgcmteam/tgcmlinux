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

"""'Applet' is what NM calls NetworkManagerSettings.
It is renamed in this library to reduce confusion with 'Settings'
which is the nested map returned by NMS.Connection.GetSettings"""

import dbus
from freedesktopnet.dbusclient import DBusClient
from freedesktopnet.dbusclient.func import *
from freedesktopnet.networkmanager.applet.connection import Connection

__all__ = ["Applet", "Connection",]

# need better/shorter names? or hide them?
SYSTEM_SERVICE = "org.freedesktop.NetworkManager"
USER_SERVICE = "org.freedesktop.NetworkManager"

# TODO NMS.System, not in spec

class NetworkManagerSettings(DBusClient):
    """NetworkManagerSettings

    The NM Settings client library

     Methods:
    ListConnections ( ) → ao

     Signals:
    NewConnection ( o: connection )
    """

    # FIXME into DBusCLient ctor
    OPATH = "/org/freedesktop/NetworkManager/Settings"
    IFACE = "org.freedesktop.NetworkManager"

    def __init__(self, service="org.freedesktop.NetworkManager"):
        # default_interface because knetworkmanager doesnt provide introspection
        super(NetworkManagerSettings, self).__init__(dbus.SystemBus(), service, self.OPATH, default_interface = self.IFACE)
        # need instance specific adaptors for user/system conn factories
        self._add_adaptor("methods", "ListConnections", MA(seq_adaptor(self._create_connection)))

    def _create_connection(self, opath):
        return Connection(self.bus_name, opath)

NetworkManagerSettings._add_adaptors(
    NewConnection = SA(Connection),
    )

"Alias"
Applet = NetworkManagerSettings
