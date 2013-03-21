#!/usr/bin/env python
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

DBUS_PROPERTIES_IFACE = 'org.freedesktop.DBus.Properties'

NM_URI = 'org.freedesktop.NetworkManager'

MM_URI = 'org.freedesktop.ModemManager'

NM_MAIN_IFACE = 'org.freedesktop.NetworkManager'
NM_MAIN_PATH = '/org/freedesktop/NetworkManager'

NM_SETTINGS_IFACE = 'org.freedesktop.NetworkManager.Settings'
NM_SETTINGS_PATH = '/org/freedesktop/NetworkManager/Settings'

NM_CONN_ACTIVE_IFACE = 'org.freedesktop.NetworkManager.Connection.Active'

NM_CONN_SETTINGS_IFACE = 'org.freedesktop.NetworkManager.Settings.Connection'

NM_DEVICE_IFACE = 'org.freedesktop.NetworkManager.Device'
NM_DEVICE_ETHERNET_IFACE = 'org.freedesktop.NetworkManager.Device.Wired'
NM_DEVICE_WIFI_IFACE = 'org.freedesktop.NetworkManager.Device.Wireless'


#### Enumerated types ####

## NM_ACTIVE_CONNECTION_STATE ##
NM_ACTIVE_CONNECTION_STATE_UNKNOWN      = 0
''' The active connection is in an unknown state '''
NM_ACTIVE_CONNECTION_STATE_ACTIVATING   = 1
''' The connection is activating '''
NM_ACTIVE_CONNECTION_STATE_ACTIVATED    = 2
''' The connection is activated '''
NM_ACTIVE_CONNECTION_STATE_DEACTIVATING = 3
''' The connection is being torn down and cleaned up '''

## NM_DEVICE_STATE ##
NM_DEVICE_STATE_UNKNOWN      =  0
''' The device is in an unknown state '''
NM_DEVICE_STATE_UNMANAGED    = 10
''' The device is recognized but not managed by NetworkManager '''
NM_DEVICE_STATE_UNAVAILABLE  = 20
''' The device cannot be used (carrier off, rfkill, etc) '''
NM_DEVICE_STATE_DISCONNECTED = 30
''' The device is not connected '''
NM_DEVICE_STATE_PREPARE      = 40
''' The device is preparing to connect '''
NM_DEVICE_STATE_CONFIG       = 50
''' The device is being configured '''
NM_DEVICE_STATE_NEED_AUTH    = 60
''' The device is awaiting secrets necessary to continue connection '''
NM_DEVICE_STATE_IP_CONFIG    = 70
''' The IP settings of the device are being requested and configured '''
NM_DEVICE_STATE_IP_CHECK     = 80
''' The device's IP connectivity ability is being determined '''
NM_DEVICE_STATE_SECONDARIES  = 90
''' The device is waiting for secondary connections to be activated '''
NM_DEVICE_STATE_ACTIVATED    = 100
''' The device is active '''
NM_DEVICE_STATE_REACTIVATING = 110
''' The device's network connection is being torn down '''
NM_DEVICE_STATE_FAILED       = 120
''' The device is in a failure state following an attempt to activate it '''

## NM_STATE ##
NM_STATE_UNKNOWN          = 0
''' Networking state is unknown '''
NM_STATE_ASLEEP           = 10
''' Networking is inactive and all devices are disabled '''
NM_STATE_DISCONNECTED     = 20
''' There is no active network connection '''
NM_STATE_DISCONNECTING    = 30
''' Network connections are being cleaned up '''
NM_STATE_CONNECTING       = 40
''' A network device is connecting to a network and there is no other available network connection '''
NM_STATE_CONNECTED_LOCAL  = 50
''' A network device is connected, but there is only link-local connectivity '''
NM_STATE_CONNECTED_SITE   = 60
''' A network device is connected, but there is only site-local connectivity '''
NM_STATE_CONNECTED_GLOBAL = 70
''' A network device is connected, with global network connectivity '''
