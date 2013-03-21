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

import gtk
import os
import webbrowser

import tgcm
import tgcm.core.DeviceManager
import tgcm.core.FreeDesktop


class LinkButton (gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()

        label_text = "<span font='8' color='#ffffff' weight='bold' underline='single'>%s</span>" % _("View usage &amp; buy access")

        label = gtk.Label ()
        label.set_markup (label_text)
        label.set_use_markup (True)

        event_box = gtk.EventBox ()
        event_box.set_visible_window (False)
        event_box.add (label)
        event_box.connect ("button-press-event", self.__on_click)

        self.add (event_box)
        self.show_all()

    def __on_click (self, widget, data=None):
        dev = self.device_manager.get_main_device()
        if dev != None and dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            msisdn = dev.get_MSISDN()
            if msisdn != '' :
                webbrowser.open("https://mobilebroadbandaccess.o2.co.uk/?DMPN=%s" % msisdn)
            else:
                webbrowser.open("http://mobilebroadbandaccess.o2.co.uk")
        else:
            webbrowser.open("http://mobilebroadbandaccess.o2.co.uk")


