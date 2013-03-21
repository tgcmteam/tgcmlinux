#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
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

def create_window(text):
    window = gtk.Window()

    vbox = gtk.VBox()
    vbox.set_border_width(10)
    vbox.set_spacing(6)
    window.add(vbox)

    label = gtk.Label(text)
    vbox.add(label)

    button = gtk.Button('foo')
    vbox.add(button)

    window.show_all()

    button.connect('clicked', button_callback, window)

    return window

def button_callback(widget, parent=None):
    dialog = gtk.MessageDialog(parent=parent, flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_OK)
    dialog.set_markup('Lorem ipsum alea jacta est')
    dialog.run()

def main():
    window_group = gtk.WindowGroup()

    main_window = create_window('main_window')
    window_group.add_window(main_window)

    for i in range(0, 3):
        child_window = create_window('child window #%d' % i)
        child_window.set_transient_for(main_window)
        window_group.add_window(child_window)

    gtk.main()

if __name__ == '__main__':
    main()
