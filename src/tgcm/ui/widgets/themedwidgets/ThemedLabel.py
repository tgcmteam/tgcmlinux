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

import cairo

import tgcm
from tgcm.ui.widgets.themedwidgets import ThemedWidget
from tgcm.ui.MSD.MSDUtils import HTMLColorToRGB

class ThemedLabel (ThemedWidget):
    def __init__ (self, params):
        # Only create non-windowless labels when necessary (e.g. it has something to show)
        if ('tooltip' in params) and (params['tooltip'] is not None) and (len(params['tooltip']) > 0):
            super(ThemedLabel, self).__init__(params)

        # Create a single windowless label
        else:
            super(ThemedLabel, self).__init__(params, windowless=True)

        self.__text_to_show = ""

        self.id = params['id']
        self.font = params['font']
        self.color = params['color']
        self.text = params['text']
        self.tooltip = params['tooltip']
        if 'text_align' in params:
            self.text_align_horizontal, self.text_align_vertical = params['align'].split ('-')
        else:
            self.text_align_horizontal = 'left'
            self.text_align_vertical = 'top'
        self.multiline = params['multiline']
        self.ellipsis = params['ellipsis']
        self.shadow = params['shadow']

        self.visible = params['visible']

        self.connect_after ('expose_event', self.__on_expose)

    def check_vars (self):
        exec ("visible = %s" % self.parse_var_string (self.visible))
        if visible:
            self.show_all ()
        else:
            self.hide_all ()

        exec ("text = '%s'" % self.parse_text_string (self.text))
        if text != self.__text_to_show:
            self.__text_to_show = text

        exec ("tooltip = '%s'" % self.parse_text_string (self.tooltip))
        self.container.set_tooltip_text (tooltip)

    def get_text (self):
        return self.__text_to_show

    def __on_expose (self, widget, event, params=None):
        if self.__text_to_show:
            left = widget.allocation.x
            top = widget.allocation.y
            width = widget.allocation.width
            height = widget.allocation.height

            context = widget.window.cairo_create ()

            if self.font:
                context.set_font_size (float(self.font['height']))

                if self.font['italic']:
                    slant = cairo.FONT_SLANT_ITALIC
                else:
                    slant = cairo.FONT_SLANT_NORMAL

                if int(self.font['weight']) > 500:
                    weight = cairo.FONT_WEIGHT_BOLD
                else:
                    weight = cairo.FONT_WEIGHT_NORMAL

                context.select_font_face (self.font['face'], slant, weight)

            if self.color:
                r, g, b = HTMLColorToRGB (self.color)
                context.set_source_rgb (float(r)/255, float(g)/255, float(b)/255)

            text_width = context.text_extents(self.__text_to_show)[2]

            if self.text_align_horizontal == 'center':
                align_horizontal = left + (width - text_width) / 2
            elif self.text_align_horizontal == 'left':
                align_horizontal = left
            elif self.text_align_horizontal == 'right':
                align_horizontal = left + width - text_width

            # Not all texts have the same height, so it is virtually impossible
            # to have two different texts aligned vertically if the height is
            # calculated differently. Additionally, if the text of a widget changes
            # it will change the vertical position of the text too.
            #
            # Instead of using the real height of the text, we will use the height
            # of an example text so the vertical position is now deterministic.
            text_height = context.text_extents('ZZZZ')[3]

            if self.text_align_vertical == 'center':
                align_vertical = top + (height + text_height) / 2
            elif self.text_align_vertical == 'top':
                align_vertical = top + text_height
            elif self.text_align_vertical == 'bottom':
                align_vertical = top + height - text_height

            context.move_to (align_horizontal, align_vertical)
            context.show_text (self.__text_to_show)

            if self.font['underline']:
                context.set_antialias (cairo.ANTIALIAS_NONE)
                context.move_to (align_horizontal, align_vertical + 2)
                context.line_to(align_horizontal + text_width, align_vertical + 2)
                context.set_line_width(1)
                context.stroke()
