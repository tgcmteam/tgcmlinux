#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
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

def main():
    window = gtk.Window()

    box = gtk.VBox()
    window.add(box)

    eventbox = gtk.EventBox()
    eventbox.set_visible_window(False)
    box.add(eventbox)

    image = gtk.Image()
    image.set_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_DIALOG)
    eventbox.add(image)

    box.set_has_tooltip(True)
    box.connect('query-tooltip', __on_query_tooltip)
    box.connect("expose_event", __on_expose)
    eventbox.connect("enter_notify_event", __on_enter_notify_event)
    eventbox.connect("leave_notify_event", __on_leave_notify_event)
    eventbox.connect("button_press_event", __on_button_press_event)
    eventbox.connect("button_release_event", __on_button_release_event)

    box.show()
    eventbox.show()
    image.show()
    window.show()

def __on_query_tooltip(item, x, y, keyboard_mode, tooltip):
#    print 'on query tooltip', x, y, keyboard_mode, tooltip
    tooltip.set_text('esto es una prueba')
    return True

def __on_expose(widget, event, params=None):
    print 'on expose', widget, event, params
    pass

def __on_enter_notify_event(widget, event):
    print 'on enter notify event', widget, event
    pass

def __on_leave_notify_event(widget, event):
    print 'on leave notify event', widget, event
    pass

def __on_button_press_event(widget, event):
    print 'on button press event', widget, event
    pass

def __on_button_release_event(widget, event):
    print 'on button release event', widget, event
    pass

if __name__ == '__main__':
    main()

    gtk.main()
