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
import gobject

import tgcm
import tgcm.core.DeviceManager
import tgcm.core.FreeDesktop

import tgcm.ui
import tgcm.ui.MSD
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

class CZRecharge(tgcm.ui.MSD.MSDAction):
    def __init__(self):
        tgcm.info ("Init CZRecharge")

        tgcm.ui.MSD.MSDAction.__init__(self, "prepay")

        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.taskbar_icon_name = 'prepay_taskbar.png'
        self.security_manager = tgcm.ui.MSD.MSDSecurityManager()
        self.action_dir = os.path.join(tgcm.actions_data_dir , self.codename)
        self.theme_manager = tgcm.core.Theme.ThemeManager()
        self.window_icon_path = self.theme_manager.get_icon('icons', self.taskbar_icon_name)

        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir, 'CZRecharge_main.ui'), \
                prefix='czr')

        parent = tgcm.ui.ThemedDock().get_main_window()
        self.recharge_dialog = tgcm.ui.windows.Dialog( \
                title="%s - %s" % (self.conf.get_app_name(), "Dobíjení Kreditu"), \
                parent = parent, buttons=(gtk.STOCK_CLOSE,  gtk.RESPONSE_CLOSE))

        # FIXME: We are always loading unnecessary services independently of the
        # country support. Sometimes that situation causes many problems, for example
        # when a theme-related resource is required and it is only available in the
        # theme package of a specific country.
        if self.window_icon_path is not None:
            self.recharge_dialog.set_icon_from_file(self.window_icon_path)

        self.recharge_dialog.add(self.main_widget)

        self.number_entry.connect("changed", self.__number_entry_changed_cb, None)
        self.recharge_button.connect("clicked", self.__request_recharge_cb, None)
        self.check_button.connect("clicked", self.__request_check_cb, None)

        self.recharge_button.set_sensitive(False)

    def launch_action(self, params=None):
        self.number_entry.set_text("")
        self.recharge_dialog.run()
        self.recharge_dialog.hide()
        return True

    def __number_entry_changed_cb(self, widget, data):
        if len(widget.get_text()) > 0 :
            self.recharge_button.set_sensitive(True)
        else:
            self.recharge_button.set_sensitive(False)

    def __request_recharge_cb(self, widget, data):
        self.recharge_dialog.hide()
        self.progress = tgcm.ui.MSD.MSDProgressWindow()
        self.progress.set_show_buttons(False)
        self.progress.show(_("Please wait a minute..."), _("Please wait a minute..."))

        mainloop =  gobject.MainLoop(is_running=True)
        context = mainloop.get_context()

        while context.pending() :
            context.iteration()

        ussd_request = self._get_conf_key_value("ussd_recharge").replace("%1%",self.number_entry.get_text())

        dev = self.device_manager.get_main_device()
        if dev == None:
            self.__ussd_call_error_func(None)
        elif dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            tgcm.debug("Sending ussd code : %s" % ussd_request)
            ussd_request = dev.get_cover_key(ussd_request,
                                              self.__ussd_call_func,
                                              self.__ussd_call_error_func)
        else:
            self.__ussd_call_error_func(None)


    def __request_check_cb(self, widget, data):
        self.recharge_dialog.hide()
        self.progress = tgcm.ui.MSD.MSDProgressWindow()
        self.progress.set_show_buttons(False)
        self.progress.show(_("Please wait a minute..."), _("Please wait a minute..."))

        mainloop =  gobject.MainLoop(is_running=True)
        context = mainloop.get_context()

        while context.pending() :
            context.iteration()

        ussd_request = self._get_conf_key_value("ussd_check")

        dev = self.device_manager.get_main_device()
        if dev == None:
            self.__ussd_call_error_func(None)
        elif dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            tgcm.debug("Sending ussd code : %s" % ussd_request)
            ussd_request = dev.get_cover_key(ussd_request,
                                              self.__ussd_call_func,
                                              self.__ussd_call_error_func)
        else:
            self.__ussd_call_error_func(None)

    def __ussd_call_func(self, response):
        self.progress.hide()
        self.progress.progress_dialog.destroy()

        dlg = gtk.MessageDialog(parent = self.recharge_dialog, \
                type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK)
        dlg.set_title (_(u'Sending message'))
        dlg.set_markup(_("<b>Answer received:</b>"))
        dlg.format_secondary_markup("'%s'" % response)
        if self.window_icon_path is not None:
            dlg.set_icon_from_file(self.window_icon_path)

        dlg.run()
        dlg.destroy()

    def __ussd_call_error_func(self, e):
        self.progress.hide()
        self.progress.progress_dialog.destroy()

        dlg = gtk.MessageDialog(parent = self.recharge_dialog, \
                type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK)
        dlg.set_title (_(u'Sending message'))
        dlg.set_markup("<b>Answer received:</b>")
        dlg.format_secondary_markup("'%s'" % _("Service not available"))
        if self.window_icon_path is not None:
            dlg.set_icon_from_file(self.window_icon_path)

        dlg.run()
        dlg.destroy()
