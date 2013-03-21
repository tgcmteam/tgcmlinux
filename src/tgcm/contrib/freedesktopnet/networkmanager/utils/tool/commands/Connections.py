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

import os
import dbus
import sys

from freedesktopnet.networkmanager.utils.tool import Command, make_option
from freedesktopnet.networkmanager.networkmanager import NetworkManager
from freedesktopnet.networkmanager.applet import NetworkManagerSettings, SYSTEM_SERVICE, USER_SERVICE
from freedesktopnet.networkmanager.applet.service import NetworkManagerUserSettings

class Connections(Command):

    def config_cmd(self):
        self.name = "connections"
        self.description = "List connections availables"
        self.description_full = "List connections availables"
        
        self.options_list = [
            make_option("-u", "--user",
                        action="store_true", dest="user", default=True),
            make_option("-s", "--system",
                        action="store_true", dest="system", default=False)
            ]

    def run_cmd(self):
        nm = NetworkManager()

        conn_type = USER_SERVICE

        if self.options.system == True:
            conn_type = SYSTEM_SERVICE

        acs = nm["ActiveConnections"]
        acos = map(lambda a: a["Connection"].object_path, acs)
        
        try:
            applet = NetworkManagerSettings(conn_type)
        except dbus.exceptions.DBusException, e:
            print e
            return
        d_conn = {}

        for conn in applet.ListConnections():
            cs = conn.GetSettings()
            active = True if conn.object_path in acos else False
            if cs["connection"]["type"] not in d_conn.keys():
                d_conn[cs["connection"]["type"]] = []
            
            d_conn[cs["connection"]["type"]].append((active, cs["connection"]["id"]))
        
        
        for t in d_conn.keys():
            print "%s |" % t
            print "-" * len(t) + "-+"
            for active, name in d_conn[t]:
                p_active = " "
                if active == True:
                    p_active = "*"
                print "%s|%s" % (p_active, name)
            print "\n"

        
       
