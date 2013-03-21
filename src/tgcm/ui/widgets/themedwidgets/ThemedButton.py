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

class ThemedButton (ThemedWidget):
    def __init__ (self, params):
        super (ThemedButton, self).__init__(params)

        self.text_to_show = ""
        self.pressed = False
        self.bottom_padding = 4

        self.previous_enabled = False    # Save the previous widget enable status

        self.id = params['id']
        self.image_normal = params['image_normal']
        self.image_hot = params['image_hot']
        self.image_down = params['image_down']
        self.image_disable = params['image_disable']
        self.text = params['text'] if params.has_key ('text') else ""
        self.tooltip = params['tooltip'] if params.has_key ('tooltip') else ""
        self.text_align_horizontal, self.text_align_vertical = params['text_align'].split ('-')
        self.text_left = int (params['text_left']) if params.has_key ('text_left') else 0
        self.text_right = int (params['text_right']) if params.has_key ('text_right') else 0
        self.text_top = int (params['text_top']) if params.has_key ('text_top') else 0
        self.text_bottom = int (params['text_bottom']) if params.has_key ('text_bottom') else 0
        self.multiline = params['multiline']
        self.ellipsis = params['ellipsis']
        self.font_normal = params['font_normal']
        self.font_hot = params['font_hot']
        self.font_down = params['font_down']
        self.font_disable = params['font_disable']
        self.color_normal = params['color_normal']
        self.color_hot = params['color_hot']
        self.color_down = params['color_down']
        self.color_disable = params['color_disable']
        self.cursor = params['cursor']

        self.on_down = params['on_down'] if params.has_key ('on_down') else None
        self.on_click = params['on_click'] if params.has_key ('on_click') else None

        self.visible = params['visible'] if params.has_key ('visible') else True
        self.enable = params['enable'] if params.has_key ('enable') else True

        self.set_hot_images (self.image_normal, self.image_hot, self.image_down, self.image_disable)

        self.connect_after ('expose_event', self.__on_expose)
        self.connect_after ('button_press_event', self.__on_button_press)
        self.connect_after ('button_release_event', self.__on_button_release)

        self.set_resizable (5, 5, 5, 5)

    def set_visible (self, visible):
        self.visible = visible
        self.check_vars ()

    def check_vars (self):
        try:
            exec ("visible = %s" % self.parse_var_string (self.visible))
        except:
            visible = False
        if visible:
            self.show_all ()
        else:
            self.hide_all ()
            return

        try:
            exec ("enabled = %s" % self.parse_var_string (self.enable))
        except:
            enabled = False

        # Only enable or disable this button if current state differs from the previous
        if enabled and not self.previous_enabled:
            self.previous_enabled = True
            self.enable_w ()
        elif not enabled and self.previous_enabled:
            self.previous_enabled = False
            self.disable_w ()

        exec ("text = '%s'" % self.parse_text_string (self.text))
        if text != self.text_to_show:
            self.text_to_show = text

        exec ("tooltip = '%s'" % self.parse_text_string (self.tooltip))
        self.container.set_tooltip_text (tooltip)

    def __on_button_press (self, widget, event, params=None):
        if event.button == 1:
            self.pressed = True

            if self.on_down:
                self.set_sensitive(False)
                self.call_dock_function (self.on_down, event)
                self.set_sensitive(True)
        return False

    def __on_button_release (self, widget, event, params=None):
        if self.pressed and event.button == 1:
            self.pressed = False

            if self.on_click:
                self.set_sensitive(False)
                self.call_dock_function (self.on_click)
                self.set_sensitive(True)
        return False

    def __on_expose (self, widget, event, params=None):
        if self.text_to_show:
            left = widget.allocation.x
            top = widget.allocation.y
            width = widget.allocation.width
            height = widget.allocation.height

            context = widget.window.cairo_create ()

            if self.widget_state == 0:
                r, g, b = HTMLColorToRGB (self.color_normal)
                font = self.font_normal
            elif self.widget_state == 1:
                r, g, b = HTMLColorToRGB (self.color_hot)
                font = self.font_hot if self.font_hot else self.font_normal
            elif self.widget_state == 2:
                r, g, b = HTMLColorToRGB (self.color_down)
                font = self.font_down if self.font_down else self.font_normal
            elif self.widget_state == 3:
                r, g, b = HTMLColorToRGB (self.color_disable)
                font = self.font_disable if self.font_disable else self.font_normal
            context.set_source_rgb (float(r)/255, float(g)/255, float(b)/255)

            if font:
                context.set_font_size (float(font['height']))

                if font['italic']:
                    slant = cairo.FONT_SLANT_ITALIC
                else:
                    slant = cairo.FONT_SLANT_NORMAL

                if int(font['weight']) > 500:
                    weight = cairo.FONT_WEIGHT_BOLD
                else:
                    weight = cairo.FONT_WEIGHT_NORMAL

                context.select_font_face (font['face'], slant, weight)

            text = self.text_to_show
            text_width = context.text_extents(text)[2]
            lines = [text]

            if text_width > width and self.multiline:
                lines_count = 1
                while text_width > width and lines_count<10:
                    if " " in text:
                        lines = text.split (" ", lines_count)
                        longest_line = max(lines, key=len)
                        text_width = context.text_extents(longest_line)[2]
                        lines_count += 1
                    else:
                        break

            remaining_lines = len (lines)
            drawed_lines = 0
            space_between_lines = 3
            for line in lines:
                text_width = context.text_extents(line)[2]

                if self.text_align_horizontal == 'center':
                    align_horizontal = left + (width - text_width) / 2
                elif self.text_align_horizontal == 'left':
                    align_horizontal = left + self.text_left
                elif self.text_align_horizontal == 'right':
                    align_horizontal = left + width - text_width - self.text_right

                # Not all texts have the same height, so it is virtually impossible
                # to have two different texts aligned vertically if the height is
                # calculated differently. Additionally, if the text of a widget changes
                # it will change the vertical position of the text too.
                #
                # Instead of using the real height of the text, we will use the height
                # of an example text so the vertical position is now deterministic.
                text_height = context.text_extents('ZZZZ')[3]

                if self.text_align_vertical == 'center':
                    # TODO: CENTER MULTI-LINED STRINGS IS NOT DONE
                    align_vertical = top + (height + text_height) / 2
                elif self.text_align_vertical == 'top':
                    align_vertical = top + self.text_top + \
                            (text_height + space_between_lines) * drawed_lines
                elif self.text_align_vertical == 'bottom':
                    align_vertical = top + height - self.bottom_padding - self.text_bottom - \
                            (text_height + space_between_lines) * (remaining_lines - 1)

                context.move_to (align_horizontal, align_vertical)
                context.show_text (line)

                if font['underline']:
                    context.set_antialias (cairo.ANTIALIAS_NONE)
                    context.move_to (align_horizontal, align_vertical + 2)
                    context.line_to(align_horizontal + text_width, align_vertical + 2)
                    context.set_line_width(1)
                    context.stroke()

                remaining_lines -= 1
                drawed_lines += 1

        return False
