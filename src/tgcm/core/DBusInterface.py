#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2012, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import dbus
import dbus.service

import tgcm

from tgcm.core.NetworkManagerDbus import NM_URI, MM_URI

BUS_NAME = 'es.indra.Tgcm'
OBJECT_PATH = '/es/indra/tgcm'
TGCM_IFACE = 'es.indra.Tgcm'


class DBusInterface(dbus.service.Object):
    def __init__(self):
        self._dock = None
        self._bus = dbus.SessionBus()
        if not self._bus.name_has_owner(BUS_NAME):
            self._bus.request_name(BUS_NAME)
            dbus.service.Object.__init__(self, self._bus, OBJECT_PATH)
        else:
            raise DBusInterfaceAlreadyExistsError()

    def set_dock(self, dock):
        self._dock = dock

    @dbus.service.method(TGCM_IFACE)
    def show(self):
        tgcm.debug('Called "show" through D-Bus')
        if self._dock is not None:
            self._dock.show_main_window()

    @dbus.service.method(TGCM_IFACE)
    def hide(self):
        tgcm.debug('Called "hide" through D-Bus')
        if self._dock is not None:
            self._dock.hide_main_window()

    @staticmethod
    def call_show_main_window():
        bus = dbus.SessionBus()
        service = bus.get_object(BUS_NAME, OBJECT_PATH)
        show = service.get_dbus_method('show', TGCM_IFACE)
        show()

    @staticmethod
    def check_dbus_services():
        required_system_services = (\
                ('Network Manager', NM_URI), \
                ('Mobile Manager', MM_URI))

        bus = dbus.SystemBus()
        for name, uri in required_system_services:
            if not bus.name_has_owner(uri):
                raise Exception(name, uri)


class DBusInterfaceAlreadyExistsError(Exception):
    pass
