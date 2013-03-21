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

class ScanCarriers(Command):

    def config_cmd(self):
        self.name = "scan_carriers"
        self.category = "network"
        self.description = "Scan availables carriers with a modem"
        self.description_full = "Scan availables carriers with a modem"
        
        self.options_list = [
            make_option("-m", "--modem",
                        type="int", dest="modem", default=0)
            ]
    
    def run_cmd(self):
        mm = ModemManager()
        if len(self.args) == 1 :
            c = mm.EnumerateDevices()[self.options.modem].iface["gsm.network"]
            if c != None:
                list = []
                from pprint import pprint
                print "Please wait ...."
                list = c.Scan(timeout=20000)
                for item in list :
                    print "[%s]" % item["operator-num"]
                    for x in item.keys():
                        print "   %s: %s" % (x, item[x])
                    
                sys.exit(0)

        self.parser.print_usage()
