#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           Roberto Majadas <roberto.majadas@openshine.com>
#           David Castellanos Serrano <dcastellanos@indra.es>
#
# Copyright (c) 2012, Telefonica Móviles España S.A.U.
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


class ThemedBackgroundWithAds(ThemedWidget):
    def __init__ (self):
        super (ThemedBackgroundWithAds, self).__init__(None)

        self.XMLTheme = tgcm.core.XMLTheme.XMLTheme()
        dock_layout = self.XMLTheme.get_layout('dock.layout')

        # Calculate some needed measures in order to correctly draw a
        # transparent mask in the dock
        self.dock_height = dock_layout['size']['orig_height']
        self.ads_width = 0
        self.ads_right_margin = 0

        ad_widgetex = None
        for widget in dock_layout['widgets']:
            if widget['type'] == 'widgetex':
                ad_widgetex = widget

        if ad_widgetex is not None:
            dock_width = dock_layout['size']['width']
            self.ads_width = int(ad_widgetex['width'])
            ads_left = int(ad_widgetex['left'])
            self.ads_right_margin = dock_width - ads_left - self.ads_width

        if dock_layout.has_key('shape'):
            if dock_layout['shape']['type'] == 'roundrect':
                self.roundrect_width = dock_layout['shape']['width']
                self.roundrect_height = dock_layout['shape']['height']
            if dock_layout['shape']['type'] == 'rect':
                self.roundrect_width = 0
                self.roundrect_height = 0
            self.image.connect_after("expose_event", self.__on_expose)

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
        self.roundedrec(cr, 0.0, 0.0, widget_width, widget_height, \
                self.dock_height, self.ads_width, self.ads_right_margin, \
                self.roundrect_width)
        cr.fill()

        # Set the window shape
        if self.get_parent():
            self.get_parent().get_parent().get_parent().shape_combine_mask(bitmap, 0, 0)

        return False

    def roundedrec(self, context, x, y, w, h, dh, aw, al, r=10):
        #   A************************BQ
        #  N                          C
        #  *                          *
        #  M                          D
        #   L*************K      F***E
        #                 J      G
        #                  I****H

        context.move_to(x+r, y)     # Move to A

        context.line_to(x+w-r, y)                    # Straight line to B
        context.curve_to(x+w, y, x+w, y, x+w, y+r)   # Curve to C, Control points are both at Q

        context.line_to(x+w, y+dh-r)   # Straight line to D
        context.curve_to(x+w, y+dh, x+w, y+dh, x+w-r, y+dh)  # Curve to E

        context.line_to(x+w-al, y+dh)   # Straight line to F
        context.line_to(x+w-al, y+h-r)  # Straight line to G

        context.curve_to(x+w-al, y+h, x+w-al, y+h, x+w-al-r, y+h)   # Curve to H
        context.line_to(x+w-al-aw+r, y+h)  # Straight line to I

        context.curve_to(x+w-al-aw, y+h, x+w-al-aw, y+h, x+w-al-aw, y+h-r)  # Curve to J
        context.line_to(x+w-al-aw, y+dh)  # Straight line to K

        context.line_to(x+r, y+dh)                      # Straight line to L
        context.curve_to(x, y+dh, x, y+dh, x, y+dh-r)   # Curve to M

        context.line_to(x, y+r)                 # Line to N
        context.curve_to(x, y, x, y, x+r, y)    # Curve to A
