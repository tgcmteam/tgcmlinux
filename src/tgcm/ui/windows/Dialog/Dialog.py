#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
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
import gtk

import tgcm
import tgcm.core.Config
import tgcm.core.Theme

import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic


class Dialog (gtk.Dialog):
    def __init__(self, title=None, parent=None, flags=0, buttons=None):
        gtk.Dialog.__init__(self, title=title, parent=parent, flags=flags, buttons=buttons)
        self.set_has_separator(False)
        self.set_modal (True)
        self.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        self.set_border_width(5)
        self.vbox.set_spacing(1)

        self.conf = tgcm.core.Config.Config()
        self._theme_manager = tgcm.core.Theme.ThemeManager()

        self.windows_dir = os.path.join(tgcm.windows_dir , self.__class__.__name__)

        gtk_builder_magic(self, \
            filename=os.path.join(self.windows_dir, 'Dialog.ui'), \
            prefix='d')

        self.standard_banner_area.hide()

        self.get_content_area().add(self.main_widget)

        # Connect some signals
        self.preferences_button.connect('clicked', self.on_preferences_button_clicked)
        self.help_button.connect('clicked', self.on_help_button_clicked)

    def add(self, widget) :
        self.dialog_area.add(widget)

    def on_preferences_button_clicked(self, widget, data=None):
        preferences_dialog = tgcm.ui.windows.Settings()
        preferences_dialog.run(self.settings_section)

    def on_help_button_clicked(self, widget, data=None):
        pass
