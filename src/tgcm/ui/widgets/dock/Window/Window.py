#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
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

import os

import gtk
import cairo
import gobject

import tgcm
import tgcm.core.FreeDesktop
import tgcm.core.Theme
import tgcm.ui.widgets.dock

class Window (gtk.Window):

    __gsignals__ = {
        'close' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()) ,
        'minimize' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()) ,
        'help' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()) ,
        'settings' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()) ,
    }

    def __init__(self):
        gtk.Window.__init__(self)
        self.set_decorated (False)

        self._theme_path = 'dock/Window'

        self.HEADER_HEIGHT = 32
        self.BODY_HEIGHT = 75

        self.conf = tgcm.core.Config.Config()
        self._theme_manager = tgcm.core.Theme.ThemeManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()

        self.widget_dir = os.path.join(tgcm.widgets_dir , 'dock', self.__class__.__name__)

        self.set_title (self.conf.get_app_name())

        self.main_vbox = gtk.VBox ()
        self.body_hbox = gtk.HBox()
        self.header_container_hbox = gtk.HBox ()
        self.header_container_hbox.set_property ('height_request', self.HEADER_HEIGHT)
        self.header_hbox = gtk.HBox ()
        self.header_hbox.set_spacing (15)
        self.control_buttons_hbox = gtk.HBox ()
        self.control_buttons_hbox.set_spacing (5)
        self.control_buttons_hbox.set_border_width (10)

        window_icon = self._theme_manager.get_icon (self._theme_path, 'main_window_icon.png')
        self.set_icon_from_file (window_icon)

        if tgcm.country_support == "uk" or self.conf.get_company_name() == "movistar":
            window_icon = self._theme_manager.get_icon (self._theme_path, 'main_window_icon2.png')

        self.window_icon = gtk.image_new_from_file(window_icon)
        window_icon_align = gtk.Alignment (yalign=0.5)
        window_icon_align.set_padding (0, 0, 15, 0)
        window_icon_align.add (self.window_icon)

        image = self._theme_manager.get_icon (self._theme_path, 'close_button.png')
        self.close_button = tgcm.ui.widgets.dock.ImageButton (image)
        self.close_button.set_tooltip_text (_("Close %s") % self.conf.get_app_name())
        self.close_button.connect("clicked", self.__on_close_button_clicked)
        self.control_buttons_hbox.pack_end (self.close_button, expand=False)

        image = self._theme_manager.get_icon (self._theme_path, 'minimize_button.png')
        self.minimize_button = tgcm.ui.widgets.dock.ImageButton (image)
        self.minimize_button.set_tooltip_text (_("Minimize to system tray"))
        self.minimize_button.connect("clicked", self.__on_minimize_button_clicked)
        self.control_buttons_hbox.pack_end (self.minimize_button, expand=False)

        if self.conf.show_help_on_toolbar():
            image = self._theme_manager.get_icon (self._theme_path, 'help_button.png')
            self.help_button = tgcm.ui.widgets.dock.ImageButton (image)
            self.help_button.set_tooltip_text (_("%s Help") % self.conf.get_app_name())
            self.help_button.connect("clicked", self.__on_help_button_clicked)
            self.control_buttons_hbox.pack_end (self.help_button, expand=False)

        if self.conf.show_settings_on_toolbar():
            image = self._theme_manager.get_icon (self._theme_path, 'settings_button.png')
            self.settings_button = tgcm.ui.widgets.dock.ImageButton (image)
            self.settings_button.set_tooltip_text (_("%s Settings") % self.conf.get_app_name())
            self.settings_button.connect("clicked", self.__on_settings_button_clicked)
            self.control_buttons_hbox.pack_end (self.settings_button, expand=False)

        self.header_container_hbox.connect ("expose-event", self.__expose_header)
        self.body_hbox.connect ("expose-event", self.__expose_body)

        self.header_container_hbox.pack_start (window_icon_align, expand=False)
        self.header_container_hbox.pack_start (self.header_hbox, expand=True, fill=True)
        self.header_container_hbox.pack_end (self.control_buttons_hbox, expand=False)

        header_event_box = gtk.EventBox()
        header_event_box.add (self.header_container_hbox)
        header_event_box.connect ("button-press-event", self.__header_press_event)
        header_event_box.connect ("button-release-event", self.__header_release_event)
        header_event_box.connect ("motion-notify-event", self.__header_motion_event)
        self.is_moving=False

        self.main_vbox.pack_start (header_event_box, expand=False, fill=False)
        self.main_vbox.pack_start (self.body_hbox, expand=True, fill=False)

        event_box = gtk.EventBox ()
        event_box.add (self.main_vbox)

        self.add(event_box)

        self.device_dialer.connect("connected", self.__connected_cb)
        self.device_dialer.connect("disconnected", self.__disconnected_cb)
        self.device_dialer.connect("connecting", self.__connecting_cb)
        self.device_dialer.connect("disconnecting", self.__disconnecting_cb)

        self.device_manager.connect("device-added", self.__device_added_cb)

        self.connect('size-allocate', self._on_size_allocate)
        self.connect("delete-event", self.__on_destroy_window, None)
        self.connect("show", self.__on_show_window, None)

    def __on_show_window (self, widget, data):
        x, y = self.conf.get_window_position ()

        if x == 0 and y == 0:
            width, height = self.get_size()
            screen_width = gtk.gdk.screen_width()
            self.move (screen_width/2 - width/2, 0)
        else:
            self.move (x, y)

    def append (self, widget):
        self.body_hbox.add (widget)
        width, height = self.body_hbox.get_size_request()
        self.body_hbox.set_size_request (width, self.BODY_HEIGHT)
        self.show_all()

    def append_on_header (self, widget, align_left=True):
        if align_left == False:
            alignment = gtk.Alignment(xalign=1.0, yalign=0.5, xscale=0.0, yscale=1.0)
            alignment.add (widget)
            self.header_hbox.pack_start (alignment, True, True, 10)
            alignment.show_all()
        else:
            self.header_hbox.pack_start(widget, False, True, 10)

    def remove_from_header (self, widget):
        if widget.get_parent() == self.header_hbox:
            self.header_hbox.remove (widget)
        else:
            parent = widget.get_parent()
            self.remove_from_header (parent)

    def __on_close_button_clicked (self, widget, data):
        self.emit ("close")

    def __on_minimize_button_clicked (self, widget, data):
        self.emit ("minimize")

    def __on_help_button_clicked (self, widget, data):
        self.emit ("help")

    def __on_settings_button_clicked (self, widget, data):
        self.emit ("settings")

    def __on_destroy_window (self, widget, event, data):
        self.emit ("close")

    def __expose_header (self, widget, event):
        rect = widget.get_allocation()
        context = widget.window.cairo_create()
        context.rectangle (rect.x, rect.y, rect.width, rect.height)
        image = self._theme_manager.get_icon (self._theme_path, 'topbar_bg.png')
        surface = cairo.ImageSurface.create_from_png(image)
        context.set_source_surface (surface)
        context.get_source().set_extend(cairo.EXTEND_REPEAT)
        context.paint()

    def __expose_body (self, widget, event):
        rect = widget.get_allocation()
        context = widget.window.cairo_create()
        image = self._theme_manager.get_icon (self._theme_path, 'downbar_bg.png')
        surface = cairo.ImageSurface.create_from_png(image)
        context.set_source_surface (surface, 0, self.HEADER_HEIGHT)
        context.rectangle (rect.x, rect.y, rect.width, rect.height)
        context.get_source().set_extend(cairo.EXTEND_REPEAT)
        context.clip()
        context.paint()

    def __header_press_event (self, widget, event):
        self.is_moving = True
        self.old_x = event.x_root
        self.old_y = event.y_root

    def __header_release_event (self, widget, event):
        self.is_moving = False

    def __header_motion_event (self, widget, event):
        if self.is_moving:
            if event.state & gtk.gdk.BUTTON1_MASK == gtk.gdk.BUTTON1_MASK:
                x, y = self.get_position ()
                self.move (x + (event.x_root - self.old_x), y + (event.y_root - self.old_y))
                self.old_x = event.x_root
                self.old_y = event.y_root

                self.conf.set_window_position (x, y)

    def __load_fixed_icon (self):
        if tgcm.country_support == "uk" or self.conf.get_company_name() == "movistar":
            window_icon = self._theme_manager.get_icon (self._theme_path, 'main_window_icon2.png')
            self.window_icon.set_from_file (window_icon)

    def __load_animated_icon (self):
        if tgcm.country_support == "uk" or self.conf.get_company_name() == "movistar":
            window_icon = self._theme_manager.get_icon (self._theme_path, 'main_window_icon2.gif')
            if window_icon == None:
                return
            self.window_icon.set_from_file (window_icon)

    def __connected_cb(self, dialer):
        self.__load_fixed_icon ()

    def __disconnected_cb (self, dialer):
        self.__load_fixed_icon ()

    def __connecting_cb (self, dialer):
        self.__load_animated_icon ()

    def __disconnecting_cb (self, dialer):
        self.__load_animated_icon ()

    def __device_added_cb (self, dev_manager, dev):
        self.__load_fixed_icon ()

    def _on_size_allocate(self, win, allocation):
        w,h = allocation.width, allocation.height
        bitmap = gtk.gdk.Pixmap(None, w, h, 1)
        cr = bitmap.cairo_create()

        # Clear the bitmap
        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()

        # Draw our shape into the bitmap using cairo
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        self.roundedrec (cr, 0.0, 0.0, w, h, 20)
#        cr.arc(w / 2, h / 2, min(h, w) / 2, 0, 2 * math.pi)
        cr.fill()

        # Set the window shape
        win.shape_combine_mask(bitmap, 0, 0)

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
        return

