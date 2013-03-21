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


import dbus
from freedesktopnet.dbusclient import DBusClient, object_path
from freedesktopnet.dbusclient.func import *

class ModemSimple(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    IFACE = "org.freedesktop.ModemManager.Modem.Simple"

    def __init__(self, opath):
        super(ModemSimple, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface = self.IFACE)

class ModemGsmSms(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    IFACE = "org.freedesktop.ModemManager.Modem.Gsm.SMS"

    def __init__(self, opath):
        super(ModemGsmSms, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface = self.IFACE)

        # -- For this class we provide the method Get() from the interface "Modem.Gsm.SMS". Otherwise the
        # -- method Get() from other inherited class may be provided and this would lead to a failure
        self.Get = self.get_dbus_method("Get", dbus_interface=self.IFACE)

        # -- The application calls the method Delete() from the "Modem.Gsm.Contacts" without the below line
        self.Delete = self.get_dbus_method("Delete", dbus_interface=self.IFACE)

class ModemGsmNetwork(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    IFACE = "org.freedesktop.ModemManager.Modem.Gsm.Network"

    def __init__(self, opath):
        super(ModemGsmNetwork, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface = self.IFACE)

class ModemGsmCard(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    IFACE = "org.freedesktop.ModemManager.Modem.Gsm.Card"

    def __init__(self, opath):
        super(ModemGsmCard, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface = self.IFACE)

class ModemGsmUssd(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    IFACE = "org.freedesktop.ModemManager.Modem.Gsm.Ussd"

    def __init__(self, opath):
        super(ModemGsmUssd, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface = self.IFACE)

class ModemGsmContacts(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    IFACE = "org.freedesktop.ModemManager.Modem.Gsm.Contacts"

    def __init__(self, opath):
        super(ModemGsmContacts, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface = self.IFACE)

        # -- Set the method to the correct DBus interface
        self.List = self.get_dbus_method("List", dbus_interface=self.IFACE)

class Modem(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    IFACE = "org.freedesktop.ModemManager.Modem"

    def __init__(self, opath):
        self.iface = {}
        super(Modem, self).__init__(dbus.SystemBus(), self.SERVICE, opath, default_interface = self.IFACE)

    @staticmethod
    def _create(opath):
        m = Modem(opath)
        m.iface["gsm.card"] = ModemGsmCard(opath)

        try:
            m.iface["gsm.network"] = ModemGsmNetwork(opath)
        except:
            pass

        try:
            m.iface["gsm.ussd"] = ModemGsmUssd(opath)
        except:
            pass
        
        try:
            m.iface["gsm.contacts"] = ModemGsmContacts(opath)
        except:
            pass

        try:
            m.iface["gsm.sms"] = ModemGsmSms(opath)
        except:
            pass

        try:
            m.iface["simple"] = ModemSimple(opath)
        except:
            pass
        
        return m

class ModemManager(DBusClient):
    SERVICE = "org.freedesktop.ModemManager"
    OPATH = "/org/freedesktop/ModemManager"
    IFACE = "org.freedesktop.ModemManager"

    def __init__(self):
        super(ModemManager, self).__init__(dbus.SystemBus(), self.SERVICE, self.OPATH, default_interface=self.IFACE)

ModemManager._add_adaptors(
    EnumerateDevices = MA(seq_adaptor(Modem._create)),
    )

