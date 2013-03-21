#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011-2012, Telefonica Móviles España S.A.U.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import os
import gobject
import gtk

import tgcm
import tgcm.core.FreeDesktop
import tgcm.core.MainModem
import tgcm.core.MainWifi

import tgcm.ui.windows
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label
from tgcm.core.DeviceManager import DEVICE_MODEM, DEVICE_WLAN


class Devices(gtk.HBox):

    def __init__(self, settings):
        gtk.HBox.__init__(self)

        self._settings = settings
        self.conf = tgcm.core.Config.Config()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.modem_manager = tgcm.core.MainModem.MainModem()
        self.wifi_manager = tgcm.core.MainWifi.MainWifi()

        self.widget_dir = os.path.join(tgcm.widgets_dir, 'settings', self.__class__.__name__)

        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'Devices.ui'), \
                prefix='mm')

        #Device desc labels
        if tgcm.country_support == 'de':
            tech_name = '2G/3G/4G'
        else:
            tech_name = 'WWAN'
        msg = _('Choose the device you want to use with %s to connect to the %s networks. You can use a Mobile Internet Device.') % \
                (self.conf.get_app_name(), tech_name)
        self.device_wwan_label.set_markup(_('<b>%s Device</b>') % tech_name);
        self.mobile_desc_label = replace_wrap_label(self.mobile_desc_label, text=msg)

        msg = _('Choose the device you want to use with %s to connect to the Wi-Fi networks.') % self.conf.get_app_name()
        self.wifi_desc_label = replace_wrap_label(self.wifi_desc_label, text=msg)

        #Devices treview
        self.wwan_model = DeviceModel(DEVICE_MODEM)
        self.wifi_model = DeviceModel(DEVICE_WLAN)

        col = gtk.TreeViewColumn("name")
        self.mobile_devices_treeview.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'markup', 1)

        col = gtk.TreeViewColumn("name")
        self.wifi_devices_treeview.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'markup', 1)

        self.mobile_devices_treeview.set_model(self.wwan_model)
        self.mobile_devices_treeview.set_headers_visible(False)
        self.wifi_devices_treeview.set_model(self.wifi_model)
        self.wifi_devices_treeview.set_headers_visible(False)

        # Buttons signals
        self.mobile_select_button.connect("clicked", self.__mobile_select_button_clicked_cb, None)
        self.wifi_select_button.connect("clicked", self.__wifi_select_button_clicked_cb, None)
        self.mobile_unlock_button.connect("clicked", self.__mobile_unlock_button_clicked_cb, None)

        # Listen to selection changes in WWAN devices list
        selection = self.mobile_devices_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect('changed', self.__on_wwan_device_selection_changed)

        # Listen to selection changes in Wi-Fi devices list
        selection = self.wifi_devices_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect('changed', self.__on_wifi_device_selection_changed)

        self.add(self.device_conf_widget)

    def __refresh_state_wwan_buttons(self, selection):
        is_select_button_enabled = False
        is_unlock_button_enabled = False

        device = self.__get_selected_device(self.mobile_devices_treeview, selection)
        if device is not None:
            if not self.modem_manager.is_main_device(device):
                is_select_button_enabled = True
            if device.is_on() and device.is_operator_locked():
                is_unlock_button_enabled = True

        self.mobile_select_button.set_sensitive(is_select_button_enabled)
        self.mobile_unlock_button.set_sensitive(is_unlock_button_enabled)

    # UI callbacks

    def __on_wwan_device_selection_changed(self, selection):
        self.__refresh_state_wwan_buttons(selection)

    def __on_wifi_device_selection_changed(self, selection):
        is_select_button_enabled = False

        device = self.__get_selected_device(self.wifi_devices_treeview, selection)
        if (device is not None) and (not self.wifi_manager.is_main_device(device)):
            is_select_button_enabled = True

        self.wifi_select_button.set_sensitive(is_select_button_enabled)

    def __get_selected_device(self, treeview, selection=None):
        if selection is None:
            selection = treeview.get_selection()

        # Check if there is a valid selected row
        selected_device = None
        is_item_selected = selection.count_selected_rows() > 0
        if is_item_selected:
            (model, treeiter) = selection.get_selected()
            selected_device = model.get_value(treeiter, 0)

        return selected_device

    def __mobile_select_button_clicked_cb(self, button, data=None):
        device = self.__get_selected_device(self.mobile_devices_treeview)
        if device is not None:
            self.device_manager.modem_manager.set_main_device(device)

    def __wifi_select_button_clicked_cb(self, button, data=None):
        device = self.__get_selected_device(self.wifi_devices_treeview)
        if device is not None:
            self.device_manager.set_wifi_device(device)

    def __mobile_unlock_button_clicked_cb(self, button, data=None):
        device = self.__get_selected_device(self.mobile_devices_treeview)

        # Do not attempt to unlock
        if device is None:
            return

        parent = self._settings.get_dialog()
        unlock_dialog = tgcm.ui.windows.UnlockDeviceDialog(device, parent, \
                on_success_callback=self.__on_unlock_success_cb)
        unlock_dialog.run()

    def __on_unlock_success_cb(self):
        selection = self.mobile_devices_treeview.get_selection()
        self.__refresh_state_wwan_buttons(selection)


class DeviceModel(gtk.GenericTreeModel):

    def __init__(self, filter_type):
        gtk.GenericTreeModel.__init__(self)

        self.column_names = ('Object', 'DeviceName')
        self.column_types = (gobject.TYPE_PYOBJECT, str)

        self.filter_type = filter_type
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()

        if self.filter_type == DEVICE_MODEM:
            self.main_manager = tgcm.core.MainModem.MainModem()
            self.main_manager.connect('main-modem-changed', self.__main_manager_changed)
        else:
            self.main_manager = tgcm.core.MainWifi.MainWifi()
            self.main_manager.connect('main-wifi-changed', self.__main_manager_changed)

        # Load devices
        self.data = []
        devices = self.device_manager.get_available_devices()
        for device in devices:
            if device.get_type() == self.filter_type:
                self.data.append((device, device.object_path))

        # Connect signals
        self.device_manager.connect("device-added", self.__device_added_cb)
        self.device_manager.connect("device-removed", self.__device_removed_cb)

    ## Callbacks

    def __device_added_cb(self, device_manager, device):
        if device.get_type() != self.filter_type:
            return

        # Insert a new row in the model
        row = (device, device.object_path)
        self.data.append(row)
        path = (self.data.index(row),)
        treeiter = self.get_iter(path)
        self.row_inserted(path, treeiter)

    def __device_removed_cb(self, device_manager, object_path):
        # This is somewhat awkward because the parameter of the signal
        # 'device-removed' is an object path instead of a Device object.
        # It's necessary then to iterate through all the entire model to
        # find a device with that object_path
        found_row = None
        for row in self.data:
            if object_path == row[1]:
                found_row = row

        # Remove the row if the object_path belonged to a device shown
        # in that list
        if found_row is not None:
            index = self.data.index(found_row)
            self.row_deleted(index)
            self.data.remove(found_row)

    def __main_manager_changed(self, *args):
        for row in self.data:
            path = (self.data.index(row), )
            treeiter = self.get_iter(path)
            self.row_changed(path, treeiter)

    ### gtk.GenericModelTree interface ###

    def get_column_names(self):
        return self.column_names[:]

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return len(self.column_types)

    def on_get_column_type(self, n):
        self.column_types[n]
        return self.column_types[n]

    def on_get_iter(self, path):
        try:
            return self.data[path[0]]
        except IndexError:
            return None

    def on_get_path(self, rowref):
        return self.data.index(rowref)

    def on_get_value(self, rowref, column):
        if column == 0:     # Object
            return rowref[0]
        elif column == 1:   # Device name
            device = rowref[0]
            name = device.get_prettyname()
            if self.main_manager.is_main_device(device):
                name = '<b>%s</b>' % name
            return name
        return

    def on_iter_next(self, rowref):
        try:
            i = self.data.index(rowref) + 1
            return self.data[i]
        except IndexError:
            return None

    def on_iter_children(self, rowref):
        if rowref:
            return None
        return self.data[0]

    def on_iter_has_child(self, rowref):
        return False

    def on_iter_n_children(self, rowref):
        if rowref:
            return None
        return len(self.data)

    def on_iter_nth_child(self, rowref, n):
        if rowref:
            return None
        try:
            return self.data[n]
        except IndexError:
            return None

    def on_iter_parent(self, child):
        return None
