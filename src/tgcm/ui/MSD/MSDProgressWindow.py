#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
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

import os
import gobject

import tgcm
import tgcm.ui

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic


class MSDProgressWindow:

    def __init__(self, cancel_callback=None, parent=None):
        filename = os.path.join(tgcm.msd_dir, 'MSDProgressWindow_dialog.ui')
        gtk_builder_magic(self, filename=filename, prefix='prg')

        self.cancel_button.connect("clicked",self.__cancel_button_cb)
        self.progress_dialog.connect("delete_event",self.__close_window_cb)

        self.timer_id = 0
        self.cancel_callback = cancel_callback
        if cancel_callback == None:
            self.show_buttons = False
        else:
            self.show_buttons = True
        self.is_show = False

        # -- Set the Dock as parent for the dialog if None passed
        if parent is None:
            parent = tgcm.ui.ThemedDock().get_main_window()
        self.progress_dialog.set_transient_for(parent)

    def show(self, title=None, message=None, cancel_callback=None):
        self.is_show = True
        if title:
            self.progress_dialog.set_title(title)
        if message:
            self.message_label.set_text(message)
        if cancel_callback:
            self.cancel_callback = cancel_callback

        self.timer_id = gobject.timeout_add(100, self.__timer_cb)

        if self.show_buttons == True:
            self.progress_dialog.set_decorated(True)
            self.progress_dialog.set_modal(False)
            self.progress_dialog.show_all()
            self.cancel_button.show()
        else:
            self.progress_dialog.set_decorated(False)
            self.progress_dialog.set_modal(True)
            self.progress_dialog.show_all()
            self.cancel_button.hide()

    def hide(self):
        self.is_show = False
        self.progress_dialog.hide()

    def destroy(self):
        self.progress_dialog.destroy()

    def set_show_buttons(self, show):
        self.show_buttons = show

    def set_transient_for(self, parent):
        self.progress_dialog.set_transient_for(parent)

    def __timer_cb(self):
        if self.is_show is False:
            self.timer_id = None
            return False
        self.progressbar.pulse()
        return True

    def __cancel_button_cb(self, widget):
        self.hide()
        if self.cancel_callback:
            self.cancel_callback()

    def __close_window_cb(self, widget, event):
        self.__cancel_button_cb(widget)
        return True
