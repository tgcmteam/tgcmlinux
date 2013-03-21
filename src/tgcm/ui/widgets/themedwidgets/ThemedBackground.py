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
import cairo

import tgcm
import tgcm.core.XMLTheme
from tgcm.ui.widgets.themedwidgets import ThemedWidget

class ThemedBackground (ThemedWidget):
    def __init__ (self):
        super (ThemedBackground, self).__init__(None)

        self.XMLTheme = tgcm.core.XMLTheme.XMLTheme ()

        dock_layout = self.XMLTheme.get_layout ('dock.layout')
        if dock_layout.has_key('shape'):
            if dock_layout['shape']['type'] == 'roundrect':
                self.roundrect_width = dock_layout['shape']['width']
                self.roundrect_height = dock_layout['shape']['height']
                self.image.connect_after ("expose_event", self.__on_expose)

    def __on_expose (self, widget, event, data=None):
        widget_width = widget.allocation.width
        widget_height = widget.allocation.height

        bitmap = gtk.gdk.Pixmap(None, widget_width, widget_height, 1)
        cr = bitmap.cairo_create()

        # Clear the bitmap
        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()

        # Draw our shape into the bitmap using cairo
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        self.roundedrec (cr, 0.0, 0.0, widget_width, widget_height, self.roundrect_width)
        cr.fill()

        # Set the window shape
        if self.get_parent():
            self.get_parent().get_parent().get_parent().shape_combine_mask(bitmap, 0, 0)

        return False

    def roundedrec(self,context,x,y,w,h,r = 10):
        #   A****BQ
        #  H      C
        #  *      *
        #  G      D
        #   F****E

        context.move_to(x+r,y)                      # Move to A
        context.line_to(x+w-r,y)                    # Straight line to B
        context.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
        context.line_to(x+w,y+h-r)                  # Move to D
        context.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
        context.line_to(x+r,y+h)                    # Line to F
        context.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
        context.line_to(x,y+r)                      # Line to H
        context.curve_to(x,y,x,y,x+r,y)             # Curve to A
