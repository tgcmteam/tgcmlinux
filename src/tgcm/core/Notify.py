#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2003-2012, Telefonica Móviles España S.A.U.
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
import gobject
import pynotify

import tgcm
import Config
import Singleton
import XMLTheme

class Notify(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    def __init__(self) :
        gobject.GObject.__init__(self)

        config = Config.Config(tgcm.country_support)
        pynotify.init(config.get_app_name())

        xml_theme = XMLTheme.XMLTheme()
        self._notify_icon = xml_theme.get_window_icon()


    def send(self, summary, body, icon=None):
        if icon != None :
            notify_icon = gtk.gdk.pixbuf_new_from_file(icon)
        else:
            notify_icon = self._notify_icon

        notification = pynotify.Notification(summary, body)
        notification.set_icon_from_pixbuf(notify_icon)
        notification.show()

if __name__ == '__main__':
    tgcm.country_support="uk"
    notify=Notify()
    notify.send("Hola", "Hola caracola")
