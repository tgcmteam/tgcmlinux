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
import sys

from freedesktopnet.modemmanager.utils.tool import Command, make_option
from freedesktopnet.modemmanager.modemmanager import ModemManager

class Info(Command):

    def config_cmd(self):
        self.name = "info"
        self.description = "Show information about MManager"
        self.description_full = "Show information about MManager"
        
        self.options_list = [
            make_option("-v", "--verbose",
                        action="store_true", dest="verbose", default=False)
            ]

    def run_cmd(self):
        print "  "
        print "  Modems Availables"
        print "  -----------------"
        mm = ModemManager()

        try:
            modems = mm.EnumerateDevices()
        except:
            print "Are you sure that MManager is running ??"
            sys.exit(0)

        if len(modems) == 0:
            print "  No modems availables"


	if self.options.verbose == False:
            for m in modems :
                print "  * %s" % m
        else:
            for m in modems :
                print "  * %s" % m 
                for prop in ["Device", "Driver", "Type", "UnlockRequired", "UnLockRetries"]:
                    print "      - %s -> %s" % (prop, m[prop])
                print "      - Imsi -> %s" % m.iface["gsm.card"].GetImsi()
                print "      - Imei -> %s" % m.iface["gsm.card"].GetImei()
                print ""
        

        print ""
