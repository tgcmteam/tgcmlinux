#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
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

from MobileCapabilities import *

MOBILE_MANAGER_CONTROLLER_PATH="/es/movistar/MobileManager/Manager"
MOBILE_MANAGER_CONTROLLER_URI="es.movistar.MobileManager"
MOBILE_MANAGER_CONTROLLER_INTERFACE_URI=MOBILE_MANAGER_CONTROLLER_URI+".Controller"
MOBILE_MANAGER_DIALER_INTERFACE_URI=MOBILE_MANAGER_CONTROLLER_URI+".Dialer"

MOBILE_MANAGER_DEVICE_PATH="/es/movistar/MobileManager/devices/"
MOBILE_MANAGER_DEVICE_URI="es.movistar.MobileManager"
MOBILE_MANAGER_DEVICE_INFO_INTERFACE_URI=MOBILE_MANAGER_DEVICE_URI+".DeviceInfo"
MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI=MOBILE_MANAGER_DEVICE_URI+".DeviceAuth"
MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI=MOBILE_MANAGER_DEVICE_URI+".DeviceState"
MOBILE_MANAGER_DEVICE_XZONE_INTERFACE_URI=MOBILE_MANAGER_DEVICE_URI+".DeviceXZone"
MOBILE_MANAGER_DEVICE_DEBUG_INTERFACE_URI=MOBILE_MANAGER_DEVICE_URI+".DeviceDebug"
MOBILE_MANAGER_DEVICE_SMS_INTERFACE_URI=MOBILE_MANAGER_DEVICE_URI+".DeviceSMS"
MOBILE_MANAGER_DEVICE_ADDRESSBOOK_INTERFACE_URI=MOBILE_MANAGER_DEVICE_URI+".DeviceAddressBook"
MOBILE_MANAGER_DEVICE_NO_OPTIONS_MENU=MOBILE_MANAGER_DEVICE_URI+".NoOptionsMenu"

