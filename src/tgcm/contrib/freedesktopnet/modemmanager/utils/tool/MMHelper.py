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

import sys, dbus, os

DBUS_INTERFACE_PROPERTIES='org.freedesktop.DBus.Properties'
MM_DBUS_SERVICE='org.freedesktop.ModemManager'
MM_DBUS_PATH='/org/freedesktop/ModemManager'
MM_DBUS_INTERFACE='org.freedesktop.ModemManager'
MM_DBUS_INTERFACE_MODEM='org.freedesktop.ModemManager.Modem'
MM_DBUS_INTERFACE_MODEM_GSM_CARD='org.freedesktop.ModemManager.Modem.Gsm.Card'
MM_DBUS_INTERFACE_MODEM_GSM_SMS='org.freedesktop.ModemManager.Modem.Gsm.SMS'
MM_DBUS_INTERFACE_MODEM_GSM_NETWORK='org.freedesktop.ModemManager.Modem.Gsm.Network'

bus = dbus.SystemBus()

def get_mmanager():
    manager_proxy = bus.get_object(MM_DBUS_SERVICE, MM_DBUS_PATH)
    manager_iface = dbus.Interface(manager_proxy, dbus_interface=MM_DBUS_INTERFACE)
    return manager_iface

def get_modems():
    return get_mmanager().EnumerateDevices()

def get_modem_property(modem, prop_name):
    proxy = bus.get_object(MM_DBUS_SERVICE, modem)
    props_iface = dbus.Interface(proxy, dbus_interface=DBUS_INTERFACE_PROPERTIES)
    return props_iface.Get(MM_DBUS_INTERFACE_MODEM, prop_name)
    
def get_modem_gsm_card_iface(modem_number):
    modems = get_modems()
    for m in modems :
        if int(os.path.basename(m)) == modem_number :
            proxy = bus.get_object(MM_DBUS_SERVICE, m)
            iface = dbus.Interface(proxy, dbus_interface=MM_DBUS_INTERFACE_MODEM_GSM_CARD)
            return iface

    return None

def get_modem_gsm_sms_iface(modem_number):
    modems = get_modems()
    for m in modems :
        if int(os.path.basename(m)) == modem_number :
            proxy = bus.get_object(MM_DBUS_SERVICE, m)
            iface = dbus.Interface(proxy, dbus_interface=MM_DBUS_INTERFACE_MODEM_GSM_SMS)
            return iface

    return None

def get_modem_gsm_network_iface(modem_number):
    modems = get_modems()
    for m in modems :
        if int(os.path.basename(m)) == modem_number :
            proxy = bus.get_object(MM_DBUS_SERVICE, m)
            iface = dbus.Interface(proxy, dbus_interface=MM_DBUS_INTERFACE_MODEM_GSM_NETWORK)
            return iface

    return None
