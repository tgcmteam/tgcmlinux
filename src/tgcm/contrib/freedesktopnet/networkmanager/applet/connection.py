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
#from freedesktopnet.dbusclient.func import *


class Connection(DBusClient):
    """NetworkManager.Settings.Connection (including Secrets)

     Methods:
    Update ( a{sa{sv}}: properties ) → nothing
    Delete ( ) → nothing
    GetSettings ( ) → a{sa{sv}}
    GetSecrets ( s: setting_name, as: hints, b: request_new ) → a{sa{sv}}
    
     Signals:
    Updated ( a{sa{sv}}: settings )
    Removed ( )
    """

    IFACE = "org.freedesktop.NetworkManager.Settings.Connection"
    # FIXME
    SECRETS_IFACE = "org.freedesktop.NetworkManager.Settings.Connection.Secrets"

    def __init__(self, service, opath):
        super(Connection, self).__init__(dbus.SystemBus(), service, opath, default_interface=self.IFACE)

# no adaptors necessary, it seems
Connection._add_adaptors(
    )
