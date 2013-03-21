#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Luis Galdos <luisgaldos@gmail.com>
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
import tgcm.ui.widgets.themedwidgets

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

class ServiceWindow(gtk.Window):
    def __init__(self, banner, name, buttons=None):
        gtk.Window.__init__(self)

        self.conf = tgcm.core.Config.Config()
        self._theme_manager = tgcm.core.Theme.ThemeManager()

        self.windows_dir = os.path.join(tgcm.windows_dir, 'Generic')
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'Windows.ui'), \
                prefix='d')

        self.standard_banner_area.hide()

        # -- Replace the main parent
        super(gtk.Window, self).add(self.main_widget)

        # -- Dont skip the taskbar and set destroy with parent
        self.set_skip_taskbar_hint(False)
        self.set_destroy_with_parent(True)

        title = "%s - %s" % (self.conf.get_caption(), name)
        self.set_title(title)

        # -- Create the window banner
        xml_theme = tgcm.core.XMLTheme.XMLTheme()
        layout = xml_theme.get_layout(banner)
        if layout is not None:
            banner = tgcm.ui.widgets.themedwidgets.ThemedBanner(layout)
            self.themed_banner_area.pack_end(banner)

        # Connect some signals
        self.preferences_button.connect('clicked', self.on_preferences_button_clicked)
        self.help_button.connect('clicked', self.on_help_button_clicked)

    def add(self, widget):
        self.dialog_area.add(widget)

    def remove(self, widget):
        self.dialog_area.remove(widget)

    def show(self):
        super(gtk.Window, self).show()
        self.deiconify()

    def on_preferences_button_clicked(self, widget, data=None):
        preferences_dialog = tgcm.ui.windows.Settings()
        preferences_dialog.run(self.settings_section)

    def on_help_button_clicked(self, widget, data=None):
        pass
