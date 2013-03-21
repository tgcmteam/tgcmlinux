#!/usr/bin/env python
# Copyright (C) 2010 OpenShine S.L.
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
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

import os
import sys
import inspect
import glob

class CommandDispatcher:
    def __init__(self):
        self.commands_dir = os.path.join(os.path.dirname(inspect.currentframe().f_code.co_filename),
                                         'commands')
        self.command_dict = {}
        cmd_pyfiles = glob.glob(os.path.join(self.commands_dir, "*.py"))
        for cmd_file in cmd_pyfiles :
            self.__inspect_file(cmd_file)

        if len(sys.argv) <= 1:
            self.__show_global_help()
        else:
            if sys.argv[1] in self.command_dict.keys() :
                self.command_dict[sys.argv[1]][1].run(sys.argv[1:])
            else:
                self.__show_global_help()

    def __inspect_file(self, cmd_file):
        if os.path.basename(cmd_file) == "__init__.py" :
            return
        try:
            cmd_name = os.path.basename(cmd_file).replace(".py","")
            exec("from freedesktopnet.modemmanager.utils.tool.commands.%s import %s as command" % (cmd_name, cmd_name))
            c = command()
            c.config()
            if len(c.name) > 0 :
                if not self.command_dict.has_key(c.name) :
                    self.command_dict[c.name] = [c.description, c]
        except:
            pass

    def __show_global_help(self):
        print "usage : %s <subcommand> [options]\n" % os.path.basename(sys.argv[0])
        print "Subcommands availables :"
        print 
        for cat in ["general", "card", "network", "sms"] :
            print "  %s" % cat.upper()
            for k in self.command_dict.keys():
                if self.command_dict[k][1].category == cat :
                    print "    %s - %s" % (k, self.command_dict[k][0])
            print ""
            
        
    
        
