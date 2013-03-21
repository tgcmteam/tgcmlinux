#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           Roberto Majadas <telemaco@openshine.com>
#
# Copyright (c) 2003-2010, Telefonica Móviles España S.A.U.
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

import gobject

import tgcm
import tgcm.ui.windows

class TrafficZone(gobject.GObject):
    def __init__(self):
        gobject.GObject.__init__(self)
        self.__traffic = None

    def show_traffic_dialog(self):
        if self.__traffic is None:
            self.__traffic = tgcm.ui.windows.Traffic()
        self.__traffic.run()

    def show_change_billing_day_dialog(self):
        if self.__traffic is not None:
            self.__traffic.show_change_billing_day_dialog()

gobject.type_register(TrafficZone)
