#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011, Telefónica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import dbus
import gobject

import tgcm
import Singleton

from NetworkManagerDbus import DBUS_PROPERTIES_IFACE, \
        NM_URI, NM_MAIN_PATH, NM_MAIN_IFACE, NM_CONN_ACTIVE_IFACE, \
        NM_ACTIVE_CONNECTION_STATE_ACTIVATED
from tgcm.core.NetworkManagerDbus import NM_STATE_CONNECTED_GLOBAL

class ConnectionManager(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    def __init__(self):
        gobject.GObject.__init__(self)

        self._bus = dbus.SystemBus()
        self._proxy = self._bus.get_object(NM_URI, NM_MAIN_PATH)

        self._nm_main_iface = dbus.Interface(self._proxy, dbus_interface=NM_MAIN_IFACE)
        self._nm_props_iface = dbus.Interface(self._proxy, dbus_interface=DBUS_PROPERTIES_IFACE)

    def is_connected(self):
        is_connected = self._nm_props_iface.Get(NM_MAIN_IFACE, 'State')
        return is_connected == NM_STATE_CONNECTED_GLOBAL

    def get_related_active_connection(self, conn_settings):
        act_conns = self._nm_props_iface.Get(NM_MAIN_IFACE, 'ActiveConnections')
        related_active_conn = None
        for object_path in act_conns:
            proxy = self._bus.get_object(NM_URI, object_path)
            active_connection = dbus.Interface(proxy, DBUS_PROPERTIES_IFACE)
            try:
                connection = active_connection.Get(NM_CONN_ACTIVE_IFACE, 'Connection')
                if conn_settings.object_path == connection:
                    related_active_conn = active_connection
                    break
            except dbus.exceptions.DBusException:
                pass
        return related_active_conn

    def is_active_connection_connected(self, active_connection):
        return (active_connection is not None) and \
            (active_connection.Get(NM_CONN_ACTIVE_IFACE, 'State') == NM_ACTIVE_CONNECTION_STATE_ACTIVATED)
