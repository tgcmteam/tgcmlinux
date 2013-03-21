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
import dbus.service
import _dbus_bindings
from connection import Connection
from freedesktopnet.networkmanager.applet import USER_SERVICE, SYSTEM_SERVICE

def service_pid(name):
    bus = dbus.SystemBus()
    DBS = 'org.freedesktop.DBus'
    DBI = DBS
    dbo = bus.get_object(DBS, '/')
    dbi = dbus.Interface(dbo, DBI)
    owner = dbi.GetNameOwner(name)
    pid = dbi.GetConnectionUnixProcessID(owner)
    return pid

# server analog of cApplet
class NetworkManagerSettings(dbus.service.Object):
    # conmaps is a list
    def __init__(self, conmaps, requested_name = None):
        bus = dbus.SystemBus()
        opath = "/org/freedesktop/NetworkManager/Settings"
        bus_name = None
        if requested_name != None:
            NEE = dbus.exceptions.NameExistsException
            try:
                bus_name = dbus.service.BusName(requested_name, bus,
                                                replace_existing=True,
                                                do_not_queue=True)
            except NEE:
                raise  NEE("%s (pid %d)" % (requested_name, service_pid(requested_name)))
        dbus.service.Object.__init__(self, bus, opath, bus_name)
        #print "CONMAPS:", conmaps
        self.conns = map(self.newCon, conmaps)

    def addCon(self, conmap):
        c = self.newCon(conmap)
        self.conns.append(c)
        return c

    counter = 1
    def newCon(self, conmap):
        cpath = "/MyConnection/%d" % self.counter
        self.counter = self.counter + 1
        c = Connection(cpath, conmap)
        self.NewConnection(cpath) # announce it
        return c

    @dbus.service.method(dbus_interface='org.freedesktop.NetworkManager.Settings',
                             in_signature='', out_signature='ao')
    def ListConnections(self):
        return [c.__dbus_object_path__ for c in self.conns]

    #this is for EMITTING a signal, not receiving it
    @dbus.service.signal(dbus_interface='org.freedesktop.NetworkManager.Settings',
                             signature='o')
    def NewConnection(self, opath):
        pass
        #print "signalling newconn:", opath

    def GetByNet(self, net_name):
        "Returns connection, or None"
        for c in self.conns:
            if c.isNet(net_name):
                return c
        return None

class NetworkManagerUserSettings(NetworkManagerSettings):
    def __init__(self, conmaps):
        super(NetworkManagerUserSettings, self).__init__(conmaps, USER_SERVICE)

# probably does not make sense to reimplement system settings
# but anyway, just for symmetry
class NetworkManagerSystemSettings(NetworkManagerSettings):
    def __init__(self, conmaps):
        super(NetworkManagerSystemSettings, self).__init__(conmaps, SYSTEM_SERVICE)

Applet = NetworkManagerSettings
UserApplet = NetworkManagerUserSettings
SystemApplet = NetworkManagerSystemSettings
