#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#
# Copyright (c) 2003-2007, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import os
import os.path

import tgcm
from Singleton import *

class DocManager (gobject.GObject):
    __metaclass__ = Singleton

    def __init__(self) :
        gobject.GObject.__init__(self)
        self.path = os.path.join (tgcm.doc_path, tgcm.country_support)
        self.configured_lang = os.environ['LANG'].split('_')[0]

    def get_doc_path (self, file):
        doc_path = os.path.join (self.path, self.configured_lang, file)
        if os.path.exists (doc_path):
            return doc_path

        doc_path = os.path.join (self.path, self.configured_lang.lower(), file)
        if os.path.exists (doc_path):
            return doc_path

        doc_path = os.path.join (self.path, "C", file)
        if os.path.exists (doc_path):
            return doc_path

        return False
