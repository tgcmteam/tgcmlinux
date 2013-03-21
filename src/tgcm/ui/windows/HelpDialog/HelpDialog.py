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
import glib
import webbrowser

import tgcm
import tgcm.core.Config
import tgcm.core.Constants
import tgcm.core.DocManager
import tgcm.core.FreeDesktop
import tgcm.core.Theme

import tgcm.ui

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label


class HelpDialog :

    ENTRY_NO_DEVICE = _("No device in use")
    ENTRY_UNKNOWN   = _("Unknown")

    def __init__(self):
        self.conf = tgcm.core.Config.Config()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.doc_manager = tgcm.core.DocManager.DocManager()
        self.theme_manager = tgcm.core.Theme.ThemeManager()
        self.__main_modem = tgcm.core.MainModem.MainModem()
        self.__main_wifi  = tgcm.core.MainWifi.MainWifi()

        self.windows_dir = os.path.join(tgcm.windows_dir , self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'HelpDialog.ui'), \
                prefix='hd')

        window_icon_path = self.theme_manager.get_icon ('icons', 'help_taskbar.png')
        self.help_dialog.set_icon_from_file(window_icon_path)

        self.help_dialog.set_title (_("%s - Help") % self.conf.get_caption())

        self.help_liststore = gtk.ListStore(str, str, str)
        column = gtk.TreeViewColumn('Option_key', gtk.CellRendererText(), markup=0)
        self.help_info_treeview.append_column(column)
        column = gtk.TreeViewColumn('Option_value', gtk.CellRendererText(), markup=1)
        self.help_info_treeview.append_column(column)
        # -- This column will store the tooltip
        column = gtk.TreeViewColumn('Option_tooltip', gtk.CellRendererText(), markup=2)
        column.set_visible(False)
        self.help_info_treeview.append_column(column)
        self.help_info_treeview.set_tooltip_column(2)

        # -- Set the model for this treeview
        self.help_info_treeview.set_model(self.help_liststore)

        self.help_tgcm_version_label.set_markup("<b>%s Linux %s (%s)</b>" % \
                (self.conf.get_app_name(), self.conf.get_version(), tgcm.core.Constants.TGCM_DEVELOPMENT_REVISION()))

        help_phone = self.conf.get_help_phone()
        url = self.conf.get_support_url().replace ("&", "&amp;")
        show_url = len(url) > 0
        show_phone = len(help_phone) > 0

        if tgcm.country_support == 'es':
            url_text = _('Online help')
        else:
            url_text = url

        if not (url.startswith('http://') or url.startswith('https://')):
            url = "http://%s" % url

        self.help_online_linkbutton.set_label(url_text)
        self.help_online_linkbutton.set_uri(url)
        self.help_online_linkbutton.set_tooltip_text('')

        hide_phone_label=False;
        if show_url and show_phone:
            self.help_phone_label.set_text (_("For more information, you can either call %s or post your enquiry at the following address:") % help_phone)
        elif show_url and not show_phone:
            self.help_phone_label.set_text (_("For more information, you can send your query to the following address:"))
        elif not show_url and show_phone:
            self.help_phone_label.set_text (_("For more information, you can phone %s.") % help_phone)
            self.help_online_linkbutton.hide()
        else:
            hide_phone_label=True
            self.help_phone_label.hide()
            self.help_online_linkbutton.hide()

        #signals
        self.help_button.connect("clicked", self.__open_help_button_cb, None)
        self.help_close_button.connect("clicked", self.__close_help_dialog_cb, None)
        self.help_dialog.connect("delete_event", self.__close_help_dialog_cb)
        self.device_manager.connect ("active-dev-card-status-changed", self.__active_device_status_changed_cb)

        self.__main_modem.connect('main-modem-changed' , self.__refresh_info_treeview)
        self.__main_modem.connect('main-modem-removed' , self.__refresh_info_treeview)
        self.__main_wifi.connect('main-wifi-changed' , self.__refresh_info_treeview)
        self.__main_wifi.connect('main-wifi-removed' , self.__refresh_info_treeview)

        self.help_close_button.grab_focus()

        parent = tgcm.ui.ThemedDock().get_main_window()
        self.help_dialog.set_transient_for(parent)

        # -- Replace the Labels for happing a correct wrapping
        self.help_description_label = replace_wrap_label(self.help_description_label)
        if not hide_phone_label:
            self.help_phone_label = replace_wrap_label(self.help_phone_label)

        glib.idle_add(self.__refresh_info_treeview)

    def show(self):
        self.help_dialog.show()

    def __open_help_button_cb(self, widget, data):
        doc_filename = "index.htm"
        url = self.doc_manager.get_doc_path (doc_filename)
        webbrowser.open(url)

    def __close_help_dialog_cb(self, widget, event):
        self.help_dialog.hide()
        return True

    def __active_device_status_changed_cb(self, device_manager, status):
        self.__refresh_info_treeview()

    def __refresh_info_treeview(self, *args):
        main_modem = self.__main_modem.current_device()
        main_wifi  = self.__main_wifi.current_device()

        # -- First clear all the treeview
        self.help_liststore.clear()

        # -- Add the header for the modem
        if tgcm.country_support == 'de':
            tech_str = '2G/3G/4G'
        else:
            tech_str = 'WWAN'
        self.help_liststore.append(["<b>%s</b>" % tech_str, "" , None])

        if main_modem is not None:
            manu, model, fw = self.__get_modem_info(main_modem)
            imei = self.__get_imei(main_modem)
            self.help_liststore.append([ _("Model:")        , model , model ])
            self.help_liststore.append([ _("Manufacturer:") , manu  , manu  ])
            self.help_liststore.append([ _("Firmware:")     , fw    , fw    ])
            self.help_liststore.append([ _("IMEI:")         , imei  , imei  ])
        else:
            self.help_liststore.append([ self.ENTRY_NO_DEVICE , "" , self.ENTRY_NO_DEVICE ])

        # -- Add a row between modem and wi-fi (requested by QA)
        self.help_liststore.append([ None , None , None ])

        # -- Add the header for the wifi
        self.help_liststore.append([ "<b>Wi-Fi</b>" , "" , None ])

        if main_wifi is not None:
            mac = self.__get_hw_addr(main_wifi)
            self.help_liststore.append([ _("Physical address:") , mac, mac ])
        else:
            self.help_liststore.append([ self.ENTRY_NO_DEVICE , "" , self.ENTRY_NO_DEVICE ])

    def __get_hw_addr(self, dev):
        try:
            return dev.mac()
        except Exception, err:
            print "@FIXME: HelpDialog: error getting MAC, %s" % err
            return self.ENTRY_UNKNOWN

    def __get_imei(self, dev):
        try:
            retval = self.ENTRY_UNKNOWN
            val = dev.get_IMEI()
            if type(val) == type("") and len(val) > 0:
                retval = val
        except Exception, err:
            print "@FIXME: HelpDialog: error reading IMEI, %s" % err
        finally:
            return retval

    def __get_modem_info(self, dev):
        info = dev.device_info()
        try:
            manu  = info['manufacturer']
            model = info['model']
            fw    = info['firmware'] if (len(info['firmware']) > 0) else (self.ENTRY_UNKNOWN)
            return [ manu, model, fw ]
        except Exception, err:
            print "@FIXME: HelpDialog: error reading device info, %s" % err
            return [ self.ENTRY_UNKNOWN ] * 3
