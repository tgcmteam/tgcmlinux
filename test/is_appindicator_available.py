#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
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

UNITY_URI = 'com.canonical.Unity'
UNITY_LAUNCHER_PATH = '/com/canonical/Unity/Launcher'

def is_unity():
    is_unity = False
    try:
        bus = dbus.SessionBus()
        bus.get_object(UNITY_URI, UNITY_LAUNCHER_PATH)
        is_unity = True
    except dbus.exceptions.DBusException:
        pass
    return is_unity

def is_appindicator_available():
    is_appindicator_available = False
    try:
        import appindicator
        is_appindicator_available = True
    except ImportError:
        pass
    return is_appindicator_available

if __name__ == '__main__':
    print 'Is Unity:', is_unity()
    print 'Is AppIndicator available:', is_appindicator_available()
