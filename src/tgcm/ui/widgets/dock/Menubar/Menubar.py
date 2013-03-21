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

import re
import gtk

import tgcm
import tgcm.core.Config
import tgcm.core.FreeDesktop
import tgcm.ui.ThemedDock


class Menubar():

    def __init__(self):
        self.config = tgcm.core.Config.Config(tgcm.country_support)
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()

        self.accelgroup = gtk.AccelGroup()
        self.menubar = gtk.MenuBar()
        self.main_actiongroup = gtk.ActionGroup('Tgcm')
        self.help_actiongroup = gtk.ActionGroup('Help')

        self.main_action = gtk.Action('Tgcm', self.config.get_app_name(), None, None)
        self.main_actiongroup.add_action(self.main_action)
        self.main_menuitem = self.main_action.create_menu_item()
        self.menubar.append(self.main_menuitem)

        self.help_action = gtk.Action('HelpGroup', None, None, gtk.STOCK_HELP)
        self.help_actiongroup.add_action(self.help_action)
        self.help_menuitem = self.help_action.create_menu_item()
        self.menubar.append(self.help_menuitem)

        self.main_menu = gtk.Menu()
        self.main_menuitem.set_submenu(self.main_menu)

        self.help_menu = gtk.Menu()
        self.help_menuitem.set_submenu(self.help_menu)

    def build_menus(self, accelerators):
        menu_entries = (
            ('ConnectAction', gtk.STOCK_CONNECT, None, 'app.connect()', self.main_menu),
            ('DisconnectAction', gtk.STOCK_DISCONNECT, None, 'app.disconnect()', self.main_menu),
            ('AnAction', None, _('Available networks'), 'app.networks()', self.main_menu),
            ('QuitAction', gtk.STOCK_QUIT, None, 'window.close()', self.main_menu),
            ('HelpAction', gtk.STOCK_HELP, None, 'app.help()', self.help_menu),
        )

        for entry_id, stock_id, name, oper_id, menu in menu_entries:

            action = gtk.Action(entry_id, name, None, stock_id)
            action.connect('activate', self.menu_callback, oper_id)

            accelerator = None
            if (oper_id in accelerators) and ('window.close' not in oper_id):
                accelerator = accelerators[oper_id]
            self.main_actiongroup.add_action_with_accel(action, accelerator)
            action.set_accel_group(self.accelgroup)
            action.connect_accelerator()
            menu_item = action.create_menu_item()
            menu.append(menu_item)

            if entry_id == 'ConnectAction':
                self.connect_menuitem = menu_item
            elif entry_id == 'DisconnectAction':
                self.disconnect_menuitem = menu_item

        self.device_dialer.connect('connected', self._on_connected)
        self.device_dialer.connect('disconnected', self._on_disconnected)

    def get_accelgroup(self):
        return self.accelgroup

    def get_menubar(self):
        return self.menubar

    def _on_connected(self, dialer=None):
        self.connect_menuitem.hide()
        self.disconnect_menuitem.show()

    def _on_disconnected(self, dialer=None):
        self.connect_menuitem.show()
        self.disconnect_menuitem.hide()

    def menu_callback(self, widget, func_name):
        function, params = self.parse_function(func_name)
        dock = tgcm.ui.ThemedDock()
        if params:
            dock.functions[function](params)
        else:
            dock.functions[function]()

    def parse_function(self, string):
        string = string.strip()
        regex = r"^([\w.]+)\s*\(([\w\s,]+)?\)$"
        m = re.match(regex, string)

        func_name = m.group(1)
        func_params = m.group(2)
        if func_params:
            params = [param.strip() for param in func_params.split(",")]
            return func_name, params
        else:
            return func_name, func_params
