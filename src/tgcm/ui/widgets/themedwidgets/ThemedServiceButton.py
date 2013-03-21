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
import gobject
import math

import tgcm
import tgcm.core.XMLTheme

from tgcm.ui.widgets.themedwidgets import ThemedButton
from tgcm.ui.MSD.MSDUtils import HTMLColorToRGB

class ThemedServiceButton (ThemedButton):
    __gsignals__ = {
        'clicked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'pressed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__ (self, params):
        super (ThemedServiceButton, self).__init__(params)

        self.__alt_text = False
        self.bottom_padding = 2

        self.alt_image = params ['alt_image'] if params.has_key ('alt_image') else None
        self.alt_left = params ['alt_left'] if params.has_key ('alt_left') else None
        self.alt_top = params ['alt_top'] if params.has_key ('alt_top') else None
        self.alt_width = params ['alt_width'] if params.has_key ('alt_width') else None
        self.alt_height = params ['alt_height'] if params.has_key ('alt_height') else None
        self.alt_font = params ['alt_font'] if params.has_key ('alt_font') else None
        self.alt_color = params ['alt_color'] if params.has_key ('alt_color') else None

        self.__set_more_menu_image()

        self.set_no_resizable ()
        self.connect ('button_press_event', self.__on_button_press)
        self.connect ('button_release_event', self.__on_button_release)
        self.connect_after ('expose_event', self.__on_expose)

    def check_vars (self):
        ThemedButton.check_vars(self)
        self.container.set_tooltip_text(self.text_to_show)

    def __set_more_menu_image(self):
        xml_theme = tgcm.core.XMLTheme.XMLTheme()
        pixbuf = xml_theme.get_pixbuf(self.id)
        self.more_menu_image = pixbuf

    def set_title (self, text):
        self.text = text
        self.check_vars()

    def set_alt_text (self, alt_text):
        self.__alt_text = alt_text

    def __on_button_press (self, widget, event, params=None):
        if event.button == 1:
            self.pressed = True

            if self.on_down:
                self.emit ('pressed')
        return False


    def __on_button_release (self, widget, event, params=None):
        if self.pressed and event.button == 1:
            self.pressed = False

            if self.on_click:
                self.emit ('clicked')
        return False

    def __on_expose (self, widget, event, params=None):
        if self.__alt_text:
            width = int (self.alt_width)
            height = int (self.alt_height)
            left = int (self.alt_left)
            top = int (self.alt_top)

            context = widget.window.cairo_create ()

            abs_left = float(widget.allocation.x + left)
            abs_top = widget.allocation.y + top

            # Instead of using the bitmap provided by the TGCM/Win theme,
            # I'll draw our own notifier with Cairo. It will allow us to
            # have antialiased images
            radius = float(width) / 2
            xc = abs_left + radius
            yc = abs_top + radius
            context.set_source_rgb(1.0, 1.0, 1.0)
            context.arc(xc, yc, radius, 0, 2 * math.pi)
            context.fill()

            # Warning colors here are hardcoded! so if TGCM/Win changes
            # it would be necessary to update them here too
            radius = radius - 1
            context.set_source_rgb(float(81)/255, float(198)/255, float(217)/255)
            context.arc(xc, yc, radius, 0, 2 * math.pi)
            context.fill()

            if self.alt_color:
                r, g, b = HTMLColorToRGB (self.alt_color)
            else:
                r, g, b = (0, 0, 0)
            context.set_source_rgb (float(r)/255, float(g)/255, float(b)/255)

            if self.alt_font:
                context.set_font_size (float(self.alt_font['height']))

                if self.alt_font['italic']:
                    slant = cairo.FONT_SLANT_ITALIC
                else:
                    slant = cairo.FONT_SLANT_NORMAL

                if int(self.alt_font['weight']) > 500:
                    weight = cairo.FONT_WEIGHT_BOLD
                else:
                    weight = cairo.FONT_WEIGHT_NORMAL

                context.select_font_face (self.alt_font['face'], slant, weight)

            x_bearing, y_bearing, text_width, text_height = context.text_extents(self.__alt_text)[0:4]
            align_horizontal = abs_left + (float(width - text_width) / 2) - x_bearing
            align_vertical = abs_top + (float(height + text_height) / 2)

            context.move_to (align_horizontal, align_vertical)
            context.show_text (self.__alt_text)

            if self.alt_font['underline']:
                context.set_antialias (cairo.ANTIALIAS_NONE)
                context.move_to (align_horizontal, align_vertical + 2)
                context.line_to(align_horizontal + text_width, align_vertical + 2)
                context.set_line_width(1)
                context.stroke()
