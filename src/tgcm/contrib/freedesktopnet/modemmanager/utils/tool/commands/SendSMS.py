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

class SendSMS(Command):

    def config_cmd(self):
        self.name = "send_sms"
        self.category = "sms"
        self.description = "Send sms with a modem"
        self.description_full = "Send sms with a modem"
        self.add_usage = " 'phone_numer' 'text'"
        
        self.options_list = [
            make_option("-m", "--modem",
                        type="int", dest="modem", default=0)
            ]
    
    def run_cmd(self):
        mm = ModemManager()
        if len(self.args) == 3 :
            c = mm.EnumerateDevices()[self.options.modem].iface["gsm.sms"]
            if c != None:
                c.Send({ "number" : self.args[1], "text" : self.args[2] })
                sys.exit(0)

        self.parser.print_usage()
