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

"A crude signal monitor for NetworkManager."

import dbus
import freedesktopnet.dbusclient.monitor
import networkmanager
import device

class Monitor(freedesktopnet.dbusclient.monitor.Monitor):
    """A crude signal monitor for NetworkManager.

    It was done before the rest of the library
    and should be replaced with something more fitting the rest.
    """

    def __init__(self):
        super(Monitor, self).__init__(dbus.SystemBus())

        self.watch(
            self.propc_h,
            dbus_interface="org.freedesktop.NetworkManager.Device.Wireless",
            signal_name="PropertiesChanged")
        self.watch(
            self.propc_h,
            dbus_interface="org.freedesktop.NetworkManager.AccessPoint",
            signal_name="PropertiesChanged")

        self.ignore("org.freedesktop.Hal.Device", "PropertyModified")
        self.ignore("fi.epitest.hostap.WPASupplicant.Interface", "ScanResultsAvailable")
        self.ignore("com.redhat.PrinterSpooler", "QueueChanged")
        self.ignore("org.freedesktop.NetworkManager", "StateChange") # deprecated
        self.watch(self.nm_sc_h, "org.freedesktop.NetworkManager", "StateChanged")
        self.watch(self.wpas_isc_h, "fi.epitest.hostap.WPASupplicant.Interface", "StateChange")
        self.watch(self.nmd_sc_h, "org.freedesktop.NetworkManager.Device", "StateChanged")
        self.watch(self.bus_noc_h, "org.freedesktop.DBus", "NameOwnerChanged")

    def bus_noc_h(self, *args, **kwargs):
        (name, old, new) = args
        if new == "":
            new = "gone"
        else:
            new = "at " + new
        print "\tBUS NOC\t%s %s" % (name, new)

    def wpas_isc_h(self, *args, **kwargs):
        opath = kwargs["path"]
        (new, old) = args
        print "\tWPAS %s\t(%s, was %s)" % (new, opath, old.lower())

    def nmd_sc_h(self, *args, **kwargs):
        opath = kwargs["path"]
        (new, old, reason) = args
        news = device.Device.State(new)
        olds = device.Device.State(old)
        reasons = ""
        if reason != 0:
            reasons = " reason %d" % reason
        print "\tDevice State %s\t(%s, was %s%s)" % (news, opath, olds, reasons)

    def nm_sc_h(self, *args, **kwargs):
        s = args[0]
        ss = networkmanager.NetworkManager.State(s)
        print "\tNM State:", ss

    def propc_h(self, *args, **kwargs):
        opath = kwargs["path"]
        props = args[0]
        for k, v in props.iteritems():
            if k == "Strength":
                v = "%u" % v
            line = "\tPROP\t%s\t%s\t(%s)" % (k, v, opath)
            print line
