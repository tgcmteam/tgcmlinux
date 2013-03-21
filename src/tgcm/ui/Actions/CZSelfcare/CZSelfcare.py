#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
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
import webbrowser

import tgcm
import tgcm.core.FreeDesktop

import tgcm.ui
import tgcm.ui.MSD

class CZSelfcare(tgcm.ui.MSD.MSDAction):
    def __init__(self):
        tgcm.info ("Init CZSelfcare")

        tgcm.ui.MSD.MSDAction.__init__(self, "selfcare")

        theme_manager = tgcm.core.Theme.ThemeManager()
        self.taskbar_icon_name = 'selfcare_taskbar.png'
        self.window_icon_path = theme_manager.get_icon('icons', self.taskbar_icon_name)

        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.security_manager = tgcm.ui.MSD.MSDSecurityManager()
        self.action_dir = os.path.join(tgcm.actions_data_dir , self.codename)
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()


    def launch_action(self, params=None):
        if self.device_dialer.apn == None or self.device_dialer.apn not in self._get_conf_key_value("apn_list"):
            parent = tgcm.ui.ThemedDock().get_main_window()
            dlg = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK)
            dlg.set_title (_(u'Service not available'))
            dlg.set_markup(_("<b>Service not available</b>"))
            dlg.format_secondary_markup(_("To access the Selfcare, please connect via O2 GPRS/UMTS network"))
            dlg.set_icon_from_file(self.window_icon_path)
            dlg.run()
            dlg.destroy()
        else:
            webbrowser.open(self._get_conf_key_value("selfcare_url"))

        return True
