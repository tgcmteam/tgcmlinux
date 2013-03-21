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

import re
import gtk
import cairo

import tgcm.ui

class ThemedWidget (gtk.VBox):
    def __init__ (self, params, windowless=False):
        gtk.VBox.__init__(self)

        if not windowless:
            eventbox = gtk.EventBox ()
            eventbox.set_visible_window (False)
            self.add (eventbox)
            self.container = eventbox
        else:
            self.container = self

        if params:
            self.left = int (params['left']) if params.has_key ('left') else None
            self.top = int (params['top']) if params.has_key ('top') else None
            self.width = int (params['width']) if params.has_key ('width') else None
            self.height = int (params['height']) if params.has_key ('height') else None
            self.anchor_tl = params['anchor_tl'] if params.has_key ('anchor_tl') else "anchor-none"
            self.anchor_br = params['anchor_br'] if params.has_key ('anchor_br') else "anchor-none"
        else:
            self.left = 0
            self.top = 0
            self.width = 0
            self.height = 0
            self.anchor_tl = "top-left"
            self.anchor_br = "bottom-right"

        self.__check_anchors ()

        self.resizable = False
        self.set_child_visible (True)
        # WIDGET STATES:
        # 0: normal
        # 1: over
        # 2: clicked
        # 3: disabled
        self.widget_state = 0

        self.image = gtk.Image ()
        self.image.hide ()
        self.container.add (self.image)

        self.visible_pixbuf = None

        self.normal_pixbuf = None
        self.over_pixbuf = None
        self.click_pixbuf = None
        self.disabled_pixbuf = None

        self.connect ("expose_event", self.__on_expose)

        self.container.connect ("enter_notify_event", self.__on_enter_notify_event)
        self.container.connect ("leave_notify_event", self.__on_leave_notify_event)
        self.container.connect ("button_press_event", self.__on_button_press_event)
        self.container.connect ("button_release_event", self.__on_button_release_event)

    def set_margins(self, left, top):
        self.left += left
        self.top += top

    def set_fixed_image (self, image):
        if image is not None and isinstance(image, gtk.gdk.Pixbuf):
            self.normal_pixbuf = image
        else:
            self.normal_pixbuf = None
        self.over_pixbuf = self.normal_pixbuf
        self.click_pixbuf = self.normal_pixbuf
        self.disabled_pixbuf = self.normal_pixbuf

        self.__reload(self.normal_pixbuf)

    def set_hot_images (self, normal_image, over_image, click_image, disabled_image):
        if normal_image is not None and isinstance(normal_image, gtk.gdk.Pixbuf):
            self.normal_pixbuf = normal_image
        else:
            self.normal_pixbuf = None
        if over_image is not None and isinstance(over_image, gtk.gdk.Pixbuf):
            self.over_pixbuf = over_image
        else:
            self.over_pixbuf = self.normal_pixbuf
        if click_image is not None and isinstance(click_image, gtk.gdk.Pixbuf):
            self.click_pixbuf = click_image
        else:
            self.click_pixbuf = self.normal_pixbuf
        if disabled_image is not None and isinstance(disabled_image, gtk.gdk.Pixbuf):
            self.disabled_pixbuf = disabled_image
        else:
            self.disabled_pixbuf = self.normal_pixbuf

        self.__reload(self.normal_pixbuf)

    DEFAULT_LENGTH = 5

    def set_resizable (self, left=0, top=0, right=0, bottom=0):
        self.resizable  = True
        self.res_left   = self.DEFAULT_LENGTH if (left == 0) else left
        self.res_top    = self.DEFAULT_LENGTH if (top == 0) else top
        self.res_right  = self.DEFAULT_LENGTH if (right == 0) else right
        self.res_bottom = self.DEFAULT_LENGTH if (bottom == 0) else bottom

    def set_no_resizable (self):
        self.resizable = False

    def parse_var_string (self, string, default_value=True):
        string = str (string)
        if string:
            pieces = re.findall (r"([\(\)]*)([\w\.]+)([\(\)]*)", string)
            pieces_aux = ()
            for piece in pieces:
                pieces_aux += piece

            parsed_string = ""
            for piece in pieces_aux:
                if len(piece) == 0:
                    continue

                if piece in ("and", "or", "not", "(", ")"):
                    parsed_string += " %s " % piece
                elif piece.upper() == "TRUE":
                    parsed_string += "True"
                elif piece.upper() == "FALSE":
                    parsed_string += "False"
                else:
                    dock = tgcm.ui.ThemedDock ()
                    value = dock.get_var(piece)
                    parsed_string += "%s" % value
        else:
            parsed_string = default_value

        return parsed_string

    def parse_text_string (self, string):
        if string:
            try:
                vars = re.findall (r"#\([\w\.]*\)|#[\w\.]*", string)
                dock = tgcm.ui.ThemedDock ()
                for v in vars:
                    var_name = v.replace('#', '')
                    if var_name[0]=='(' and var_name[-1]==')':
                        var_name=var_name[1:-1];

                    value = dock.get_var (var_name)
                    string = string.replace (v, value)
                return string.encode('string-escape')
            except:
                return ""
        else:
            return ""

    def parse_function (self, string):
        string = string.strip()
        regex = r"^([\w.]+)\s*\(([\w\s,]+)?\)$"
        m = re.match (regex, string)

        func_name = m.group(1)
        func_params = m.group(2)
        if func_params:
            params = [param.strip() for param in func_params.split(",")]
            return func_name, params
        else:
            return func_name, func_params

    def call_dock_function (self, func_name, event=None):
        function, params = self.parse_function (func_name)
        dock = tgcm.ui.ThemedDock ()
        if params:
            dock.functions[function](params, event=event)
        else:
            dock.functions[function](event=event)

    def __check_anchors (self):
        try:
            if self.anchor_tl:
                if self.anchor_tl == "top-left":
                    self.anchor_tl = (0,0)
                elif self.anchor_tl == "top-right":
                    self.anchor_tl = (100,0)
                elif self.anchor_tl == "bottom-left":
                    self.anchor_tl = (0,100)
                elif self.anchor_tl == "bottom-right":
                    self.anchor_tl = (100,100)
                elif self.anchor_tl == "anchor-none" or self.anchor_tl == "none":
                    self.anchor_tl = (0,0)
                else:
                    self.anchor_tl = tuple (int (anchor.strip()) for anchor in self.anchor_tl.split(","))
        except:
            self.anchor_tl = (0, 0)

        try:
            if self.anchor_br:
                if self.anchor_br == "top-left":
                    self.anchor_br = (0,0)
                elif self.anchor_br == "top-right":
                    self.anchor_br = (100,0)
                elif self.anchor_br == "bottom-left":
                    self.anchor_br = (0,100)
                elif self.anchor_br == "bottom-right":
                    self.anchor_br = (100,100)
                elif self.anchor_br == "anchor-none" or self.anchor_br == "none":
                    self.anchor_br = (0,0)
                else:
                    self.anchor_br = tuple (int (anchor.strip()) for anchor in self.anchor_br.split(","))
        except:
            self.anchor_br = (0, 0)

    def __reload (self, pixbuf):
        self.visible_pixbuf = pixbuf
        self.queue_resize()

    def enable_w (self):
        self.widget_state = 0
        self.__reload (self.normal_pixbuf)

    def disable_w (self):
        self.widget_state = 3
        self.__reload (self.disabled_pixbuf)

    def __on_enter_notify_event (self, widget, event):
        if self.widget_state != 3:
            self.widget_state = 1
            self.__reload (self.over_pixbuf)
        return False

    def __on_leave_notify_event (self, widget, event):
        if self.widget_state != 3:
            self.widget_state = 0
            self.__reload (self.normal_pixbuf)
        return False

    def __on_button_press_event (self, widget, event):
        if self.widget_state != 3:
            if event.button == 1:
                self.widget_state = 2
                self.__reload (self.click_pixbuf)
        return False

    def __on_button_release_event (self, widget, event):
        if self.widget_state != 3:
            if self.widget_state == 2 and event.button == 1:
                self.widget_state = 0
                self.__reload (self.normal_pixbuf)
        return False

    @staticmethod
    def __normalize_length(base, diff):
        retval = base - diff
        return (retval if (retval > 0) else self.DEFAULT_HEIGHT)

    def __on_expose (self, widget, event, params=None):
        if self.visible_pixbuf is None:
            return False

        main_pixbuf = self.visible_pixbuf
        format = cairo.FORMAT_RGB24
        if main_pixbuf.get_has_alpha():
            format = cairo.FORMAT_ARGB32

        widget_width = widget.allocation.width
        widget_height = widget.allocation.height

        context = widget.window.cairo_create ()

        surface = cairo.ImageSurface(format, main_pixbuf.get_width(), main_pixbuf.get_height())
        image_width = surface.get_width ()
        image_height = surface.get_height ()

        context2 = cairo.Context (surface)
        gdkcontext = gtk.gdk.CairoContext (context2)
        gdkcontext.set_source_pixbuf (main_pixbuf, 0, 0)
        gdkcontext.paint ()

        if not self.resizable:
            context.set_source_surface (surface, widget.allocation.x, widget.allocation.y)
            context.rectangle (widget.allocation.x, widget.allocation.y, image_width, image_height)
            context.fill ()
        else:
            box11 = [0, 0 , self.res_left, self.res_top]
            box12 = [0, self.res_top, self.res_left, widget_height-self.res_top-self.res_bottom]
            box13 = [0, widget_height - self.res_bottom, self.res_left, widget_height]

            box21 = [box11[2], box11[1], widget_width - self.res_right-self.res_left, box11[3]]
            box22 = [box12[2], box12[1], widget_width-self.res_right-self.res_left, box12[3]]
            box23 = [box13[2], box13[1], widget_width-self.res_right-self.res_left, box13[3]]

            box31 = [widget_width-self.res_right, box21[1], self.res_right, box21[3]]
            box32 = [widget_width-self.res_right, box22[1], self.res_right, box22[3]]
            box33 = [widget_width-self.res_right, box23[1], self.res_right, box23[3]]


            #BOX11 - TOP Left
            try:
                pixbuf = main_pixbuf.subpixbuf(0, 0, self.res_left, self.res_top)
                box11_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box11_context = cairo.Context(box11_surface)
                gdkcontext = gtk.gdk.CairoContext(box11_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box11_surface, widget.allocation.x + box11[0], widget.allocation.y + box11[1])
                context.rectangle (widget.allocation.x + box11[0], widget.allocation.y + box11[1], box11[2], box11[3])
                context.fill ()
            except:
                pass

            #BOX12
            try:
                h = self.__normalize_length(image_height, self.res_bottom + self.res_top)
                pixbuf = main_pixbuf.subpixbuf(0, self.res_top, self.res_left, h)

                h = self.__normalize_length(widget_height, self.res_top + self.res_bottom)
                pixbuf = pixbuf.scale_simple(self.res_left, h, gtk.gdk.INTERP_BILINEAR)

                box12_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box12_context = cairo.Context(box12_surface)
                gdkcontext = gtk.gdk.CairoContext(box12_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box12_surface, widget.allocation.x + box12[0], widget.allocation.y + box12[1])
                context.rectangle (widget.allocation.x + box12[0], widget.allocation.y + box12[1], box12[2], box12[3])
                context.fill ()
            except:
                pass

            #BOX13 - Bottom left
            try:
                pixbuf = main_pixbuf.subpixbuf(0, image_height-self.res_bottom, self.res_left, self.res_bottom)
                box13_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box13_context = cairo.Context(box13_surface)
                gdkcontext = gtk.gdk.CairoContext(box13_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box13_surface, widget.allocation.x + box13[0], widget.allocation.y + box13[1])
                context.rectangle (widget.allocation.x + box13[0], widget.allocation.y + box13[1], box13[2], box13[3])
                context.fill ()
            except:
                pass

            #BOX21
            try:
                w = self.__normalize_length(image_width, self.res_right + self.res_left)
                pixbuf = main_pixbuf.subpixbuf(self.res_left, 0, w, self.res_top)
                w = self.__normalize_length(widget_width, self.res_right + self.res_left)
                pixbuf = pixbuf.scale_simple(w, self.res_top, gtk.gdk.INTERP_BILINEAR)

                box21_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box21_context = cairo.Context(box21_surface)
                gdkcontext = gtk.gdk.CairoContext(box21_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box21_surface, widget.allocation.x + box21[0], widget.allocation.y + box21[1])
                context.rectangle (widget.allocation.x + box21[0], widget.allocation.y + box21[1], box21[2], box21[3])
                context.fill ()
            except:
                pass

            #BOX22
            try:
                h = self.__normalize_length(image_height, self.res_top + self.res_bottom)
                w = self.__normalize_length(image_width, self.res_right + self.res_left)
                pixbuf = main_pixbuf.subpixbuf(self.res_left, self.res_top, w, h)
                pixbuf = pixbuf.scale_simple(widget_width-(self.res_left+self.res_right), widget_height-(self.res_top+self.res_bottom), gtk.gdk.INTERP_BILINEAR)

                box22_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box22_context = cairo.Context(box22_surface)
                gdkcontext = gtk.gdk.CairoContext(box22_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box22_surface, widget.allocation.x + box22[0], widget.allocation.y + box22[1])
                context.rectangle (widget.allocation.x + box22[0], widget.allocation.y + box22[1], box22[2], box22[3])
                context.fill ()
            except:
                pass

            #BOX23
            try:
                w = self.__normalize_length(image_width, self.res_right + self.res_left)
                pixbuf = main_pixbuf.subpixbuf(self.res_left, image_height - self.res_bottom, w, self.res_bottom)
                pixbuf = pixbuf.scale_simple(widget_width-(self.res_left+self.res_right), self.res_bottom, gtk.gdk.INTERP_BILINEAR)

                box23_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box23_context = cairo.Context(box23_surface)
                gdkcontext = gtk.gdk.CairoContext(box23_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box23_surface, widget.allocation.x + box23[0], widget.allocation.y + box23[1])
                context.rectangle (widget.allocation.x + box23[0], widget.allocation.y + box23[1], box23[2], box23[3])
                context.fill ()
            except:
                pass

            #BOX31 - Top Right
            try:
                pixbuf = main_pixbuf.subpixbuf(image_width - self.res_right, 0, self.res_right, self.res_top)

                box31_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box31_context = cairo.Context(box31_surface)
                gdkcontext = gtk.gdk.CairoContext(box31_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box31_surface, widget.allocation.x + box31[0], widget.allocation.y + box31[1])
                context.rectangle (widget.allocation.x + box31[0], widget.allocation.y + box31[1], box31[2], box31[3])
                context.fill ()
            except:
                pass

            #BOX32
            try:
                h = self.__normalize_length(image_height, self.res_bottom + self.res_top)
                pixbuf = main_pixbuf.subpixbuf(image_width - self.res_right, self.res_top, self.res_right, h)
                w = self.__normalize_length(widget_height, self.res_top + self.res_bottom)
                pixbuf = pixbuf.scale_simple(self.res_right, w, gtk.gdk.INTERP_BILINEAR)

                box32_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box32_context = cairo.Context(box32_surface)
                gdkcontext = gtk.gdk.CairoContext(box32_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box32_surface, widget.allocation.x + box32[0], widget.allocation.y + box32[1])
                context.rectangle (widget.allocation.x + box32[0], widget.allocation.y + box32[1], box32[2], box32[3])
                context.fill ()
            except:
                pass

            #BOX33 - Bottom right
            try:
                pixbuf = main_pixbuf.subpixbuf(image_width - self.res_right, image_height - self.res_bottom, self.res_right, self.res_bottom)

                box33_surface = cairo.ImageSurface(format, pixbuf.get_width(), pixbuf.get_height())
                box33_context = cairo.Context(box33_surface)
                gdkcontext = gtk.gdk.CairoContext(box33_context)
                gdkcontext.set_source_pixbuf(pixbuf, 0, 0)
                gdkcontext.paint()

                context.set_source_surface (box33_surface, widget.allocation.x + box33[0], widget.allocation.y + box33[1])
                context.rectangle (widget.allocation.x + box33[0], widget.allocation.y + box33[1], box33[2], box33[3])
                context.fill ()
            except:
                pass

        return False
