#!/usr/bin/env python
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
import os
from freedesktopnet.networkmanager.applet.settings import Settings

# server analog of cConnection
class Connection(dbus.service.Object):
    def __init__(self, opath, conmap):
        assert isinstance(conmap, dict)
        bus = dbus.SystemBus()
        dbus.service.Object.__init__(self, bus, opath)
        self.settings = Settings(conmap)

    @dbus.service.method(dbus_interface='org.freedesktop.NetworkManager.Settings.Connection',
                         sender_keyword='sender',
                             in_signature='', out_signature='a{sa{sv}}')
    def GetSettings(self, sender):
        #print "Getting settings:", self. __dbus_object_path__
#        return self.settings.ConMap()
# grr, censoring secrets makes NM complain!?
        # bnc#479566#c3: Until I figure out how to make it work with
        # censored secrets, only pass the settings to the same user.
        sender_uid = self.connection.get_unix_user(sender)
        if sender_uid != 0 and sender_uid != os.geteuid():
            e = "User %u is not permitted to read the settings" % sender_uid
            print e
            raise dbus.exceptions.DBusException(e) # could do NM_SETTINGS_ERROR_* instead
        return self.settings.conmap

    @dbus.service.method(dbus_interface='org.freedesktop.NetworkManager.Settings.Connection.Secrets',
                             in_signature='sasb', out_signature='a{sa{sv}}')
    def GetSecrets(self, tag, hints, ask):
        # FIXME respect args
        print "Getting secrets:", self.__dbus_object_path__
        return self.settings.SecMap()

    @dbus.service.method(dbus_interface='org.freedesktop.NetworkManager.Settings.Connection',
                             in_signature='', out_signature='s')
    def ID(self):
        return self.settings.ID()

    def Ssid(self):
        return self.settings.Ssid()

    def isNet(self, net_name):
        return self.settings.isNet(net_name)

