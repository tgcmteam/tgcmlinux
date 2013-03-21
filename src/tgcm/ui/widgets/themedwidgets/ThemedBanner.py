#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2003-2012, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk

import tgcm.core.XMLTheme

import tgcm.ui.widgets.themedwidgets

class ThemedBanner (gtk.Fixed):
    def __init__ (self, layout):
        gtk.Fixed.__init__(self)
        self.__layout_loader = tgcm.ui.widgets.themedwidgets.LayoutLoader (layout)
        self.__orig_width, self.__orig_height = self.__layout_loader.get_size ()

        self.connect ("size_allocate", self.__on_size_allocate)
        self.connect ("size_request", self.__on_size_request)

        self.__widgets = {}

        self.__load_background ()
        self.__load_widgets ()
        self.__notify_widgets ()

        self.show_all ()

    def __load_background (self):
        self.XMLTheme = tgcm.core.XMLTheme.XMLTheme ()
        background = self.__layout_loader.get_background (self.XMLTheme.pixbufs)
        if background:
            self.background = background
            self.put (self.background, 0, 0)

    def __load_widgets (self):
        widgets = self.__layout_loader.get_widgets ()
        for widget in widgets:
            self.put (widget, widget.left, widget.top)
            widget.show_all()
            self.__widgets [widget.id] = widget

    def __notify_widgets (self):
        for widget_id in self.__widgets:
            widget = self.__widgets[widget_id]
            widget.check_vars ()

    def __on_size_allocate (self, widget, allocation, data=None):
        window_width = allocation.width
        window_height = self.__orig_height

        self.allocation = gtk.gdk.Rectangle (allocation.x, allocation.y, window_width, window_height)
        self.background.size_allocate (gtk.gdk.Rectangle (allocation.x, allocation.y, window_width, window_height))

        try:
            width_diff = abs (window_width - self.__orig_width)
            height_diff = abs (window_height - self.__orig_height)
        except:
            width_diff = 0
            height_diff = 0

        for widget_name in self.__widgets:
            widget = self.__widgets[widget_name]

            left = widget.left + width_diff*widget.anchor_tl[0]/100
            top = widget.top + height_diff*widget.anchor_tl[1]/100

            widget.size_allocate (gtk.gdk.Rectangle (left, top, widget.width, widget.height))

        return True

    def __on_size_request (self, widget, request, data=None):
        request.height = self.__orig_height
