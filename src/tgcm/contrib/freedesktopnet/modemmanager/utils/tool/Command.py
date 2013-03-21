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
from optparse import OptionParser

class Command :
    
    def __init__(self):
        self.parser = OptionParser()
        self.name = ''
        self.description = ''
        self.description_full = ''
        self.add_usage = ''
        self.options_list = None
        self.options = None
        self.args = None
        self.category = "general"

    def config(self):
        self.config_cmd()
        self.parser = OptionParser(option_list=self.options_list)

    def config_cmd(self):
        pass

    def run(self, argv):
        self.parser.usage = self.parser.usage.replace("%prog", "%%prog %s" % self.name)
        self.parser.usage = self.parser.usage + self.add_usage

        if self.description_full != '' :
            self.parser.description = self.description_full
        self.options, self.args = self.parser.parse_args(argv)
        self.run_cmd()

    def run_cmd(self):
        pass


