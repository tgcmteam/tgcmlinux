#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
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

import tgcm
import tgcm.core.Config
import tgcm.core.FreeDesktop
import tgcm.core.Singleton

class MessagingManager():
    __metaclass__ = tgcm.core.Singleton.Singleton

    def __init__ (self):
        self.conf = tgcm.core.Config.Config()
        self.mcontroller = tgcm.core.FreeDesktop.DeviceManager()

    def is_messaging_available (self, connecting=False):
        return True
