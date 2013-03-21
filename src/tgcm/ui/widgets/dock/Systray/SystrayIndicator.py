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

import os
import gtk
import appindicator

import tgcm
from Systray import SystrayBase


class SystrayIndicator(SystrayBase):
    def __init__(self, dock, conn_manager, conn_zone):
        # Call parent constructor
        SystrayBase.__init__(self, dock, conn_manager, conn_zone)

        # Instantiate a AppIndicator
        self.__indicator = appindicator.Indicator(
                'tgcm-%s' % tgcm.country_support, '__indicator-messages',
                appindicator.CATEGORY_APPLICATION_STATUS)
        self.__indicator.set_status(appindicator.STATUS_ACTIVE)
        self.__indicator.set_property('title', self._config.get_app_name())

        # Get the location of the icons
        icon_theme_path = os.path.dirname(self._theme_manager.get_icon('icons', 'conectado.png'))
        self.__indicator.set_icon_theme_path(icon_theme_path)

        ### Glade menu modifications ###

        # Substitute the current open entry with a new with a checkbutton
        self.open.hide()
        self.open_item = gtk.CheckMenuItem(_('Show the dock'))
        self.open_item.set_active(self._config.get_ui_general_key_value('systray_showing_mw'))
        self.open_item.show()
        self.menu.insert(self.open_item, 0)

        # Add a menu separator
        item = gtk.SeparatorMenuItem()
        item.show()
        self.menu.insert(item, 1)

        # Create menu entries about connection status, statistics, etc.
        self.__labels = {}
        labels = ['connection', 'speed', 'time', 'data_usage', 'sms']
        i = 2
        for label in labels:
            item = SystrayIndicator.IndicatorLabelEntry()
            item.set_text(label)
            self.menu.insert(item.get_item(), i)
            self.__labels[label] = item
            i += 1

        # Load the gtk.Menu object into AppIndicator
        self.__indicator.set_menu(self.menu)

        # Prepare the labels
        self.__update_labels()

        # Connect various signals
        self._connect_signals()

    def _connect_signals(self):
        SystrayBase._connect_signals(self)

        # Boolean var which control the activation/desactivation of 'toggled' signal.
        # This control mechanism is necessary because otherwise we would have an infinite
        # recursive loop due to signals activations
        self.__disable_open_item_activation = None

        # signals specific to SystrayIndicator
        self.open_item.connect('toggled', self._on_systray_open_activate)
        self._config.connect('ui-general-key-value-changed', self.__on_ui_key_value_changed)

    def __update_labels(self):
        if self._is_connected():
            self.connect.hide()
            self.disconnect.show()
            nm_conn_type = self._device_dialer.nmGetConnectionType()
            connection_type = _('Unknown')
            if nm_conn_type == 'ETHERNET':
                connection_type = _('Ethernet')
                self.__labels['speed'].hide()
                self.__labels['time'].hide()
                self.__labels['data_usage'].hide()
            elif nm_conn_type == 'WIRELESS':
                connection_type = _('Wi-Fi')
                self.__labels['speed'].show()
                self.__labels['speed'].set_text(self._current_speed)
                self.__labels['time'].show()
                self.__labels['time'].set_text(self._time_elapsed)
                self.__labels['data_usage'].show()
                self.__labels['data_usage'].set_text(self._data_usage)
            elif nm_conn_type == 'GSM':
                connection_type = self._network_tech
                self.__labels['speed'].show()
                self.__labels['speed'].set_text(self._current_speed)
                self.__labels['time'].show()
                self.__labels['time'].set_text(self._time_elapsed)
                self.__labels['data_usage'].show()
                self.__labels['data_usage'].set_text(self._data_usage)

            # Update connection label with information about current connection
            conn_settings = self._device_dialer.get_current_conn_settings()
            connection_name = conn_settings.get_dock_name()
            self.__labels['connection'].set_text(_('Connected to %(name)s (%(type)s)') % { \
                    'name' : connection_name,
                    'type' : connection_type})
        else:
            self.connect.show()
            self.disconnect.hide()
            self.__labels['connection'].set_text(_('Not connected'))
            self.__labels['speed'].hide()
            self.__labels['time'].hide()
            self.__labels['data_usage'].hide()

        # Update count and update the trayicon accordingly
        self._update_sms_count()

    def _update_sms_count(self):
        SystrayBase._update_sms_count(self)

        # Update icon depending on connection status and unread SMS count
        if self._sms_count == 0:
            self.__labels['sms'].hide()
            if self._is_connected():
                self.__indicator.set_icon('conectado')
            else:
                self.__indicator.set_icon('desconectado')
        else:
            self.__labels['sms'].show()
            self.__labels['sms'].set_text(_('%d unread SMS') % self._sms_count)
            if self._is_connected():
                self.__indicator.set_icon('conectado_smspending')
            else:
                self.__indicator.set_icon('desconectado_smspending')

    ### Event callbacks ###

    def _on_connected(self, dialer = None):
        self.__update_labels()

    def _on_disconnected(self, dialer = False):
        self.__update_labels()

    def _on_speed_changed(self, sender, speed):
        SystrayBase._on_speed_changed(self, sender, speed)
        self.__labels['speed'].set_text(self._current_speed)

    def _on_session_time_changed(self, widget, hours, minutes, seconds):
        SystrayBase._on_session_time_changed(self, widget, hours, minutes, seconds)
        self.__labels['time'].set_text(self._time_elapsed)

    def _on_data_usage_changed(self, traffic_manager, num_bytes):
        SystrayBase._on_data_usage_changed(self, traffic_manager, num_bytes)
        self.__labels['data_usage'].set_text(self._data_usage)

    def _on_tech_changed(self, sender, tech):
        SystrayBase._on_tech_changed(self, sender, tech)
        self.__update_labels()

    def __on_ui_key_value_changed(self, sender, key, value):
        if key == 'systray_showing_mw':
            # First time activation: When TGCM start it will issue a spurious
            # signal'ui-general-key-value-changed'
            if self.__disable_open_item_activation == None:
                self.__disable_open_item_activation = False
                return

            # Successive activations: disable the following self.open_item activation
            # and update the checkbox button
            self.__disable_open_item_activation = True
            self.open_item.set_active(value == 'True')

    ### Widget callbacks ###

    def _on_systray_open_activate(self, widget):
        # Ignore the signal if we have triggered it when manipulating the
        # element "active" property
        if not self.__disable_open_item_activation:
            SystrayBase._on_systray_open_activate(self, widget)
        self.__disable_open_item_activation = False


    class IndicatorLabelEntry:
        def __init__(self):
            self.__label = gtk.Label('')
            self.__item = gtk.MenuItem()
            self.__item.add(self.__label)
            self.__item.set_sensitive(False)
            self.__item.show()

        def get_item(self):
            return self.__item

        def set_text(self, value):
            self.__label.set_text(value)

        def show(self):
            self.__item.show()

        def hide(self):
            self.__item.hide()
