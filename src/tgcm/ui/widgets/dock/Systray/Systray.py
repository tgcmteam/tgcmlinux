#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011-2012, Telefonica Móviles España S.A.U.
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
import dbus

import tgcm.core.Actions
import tgcm.core.Config
import tgcm.core.FreeDesktop as _fd
import tgcm.core.TrafficManager
import tgcm.core.Theme

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, format_to_maximun_unit
import freedesktopnet.networkmanager.networkmanager as _nm

UNITY_URI = 'com.canonical.Unity'
UNITY_LAUNCHER_PATH = '/com/canonical/Unity/Launcher'

class SystrayManager:
    def __init__(self, dock, conn_manager, conn_zone):
        if self.is_unity() and self.is_appindicator_available():
            import SystrayIndicator
            self.systray = SystrayIndicator.SystrayIndicator(dock, conn_manager, conn_zone)
        else:
            import SystrayTrayicon
            self.systray = SystrayTrayicon.SystrayTrayicon(dock, conn_manager, conn_zone)

    def get_systray(self):
        return self.systray

    def is_unity(self):
        is_unity = False
        try:
            bus = dbus.SessionBus()
            bus.get_object(UNITY_URI, UNITY_LAUNCHER_PATH)
            is_unity = True
        except dbus.exceptions.DBusException:
            pass
        return is_unity

    def is_appindicator_available(self):
        is_appindicator_available = False
        try:
            import appindicator
            is_appindicator_available = True
        except ImportError:
            pass
        return is_appindicator_available

class SystrayBase:

    TRAFFIC_UPDATER_INTERVAL = 1.0

    def __init__(self, dock, conn_manager, conn_zone):
        self.__dock = dock
        self.__conn_manager = conn_manager
        self.__conn_zone = conn_zone
        self.__sms_action = tgcm.core.Actions.ActionManager().get_action('sms')
        self.__traffic_manager = tgcm.core.TrafficManager.TrafficManager()
        self._config = tgcm.core.Config.Config()
        self._theme_manager = tgcm.core.Theme.ThemeManager()
        self._device_dialer = _fd.DeviceDialer()
        self.__device_manager = _fd.DeviceManager()
        self.__traffic_updater = tgcm.core.TrafficUpdater.TrafficUpdater(interval = self.TRAFFIC_UPDATER_INTERVAL)

        # Automatically load widgets from a Glade file
        theme_path = os.path.join('dock', 'Systray')
        widget_dir = os.path.join(tgcm.widgets_dir, theme_path)
        gtk_builder_magic(self, \
                filename=os.path.join(widget_dir, 'Systray.ui'), \
                prefix='systray')

        # Initialize variables and prepare the labels
        self.__initialize_vars()

    def __initialize_vars(self):
        self._network_tech = _fd.DeviceManager.get_technology_string()
        self._current_speed = _('Calculating...')
        self._time_elapsed = _('Calculating...')
        self._data_usage = _('Calculating...')
        self._sms_count = int(self.__sms_action.alt_text())

    def _is_connected(self):
        return self._device_dialer.nmConnectionState() == _nm.NetworkManager.State.CONNECTED

    def _connect_signals(self):
        # Various signals: connection, disconnection, statistics, SMS, etc.
        self._device_dialer.connect('connected', self._on_connected)
        self._device_dialer.connect('disconnected', self._on_disconnected)

        self.__conn_zone.connect('connection_speed_changed', self._on_speed_changed)
        self.__traffic_manager.connect('update-session-time', self._on_session_time_changed)
        self.__traffic_manager.connect('update-session-data-transfered', self._on_data_usage_changed)
        self.__device_manager.connect('active-dev-sms-spool-changed', self._on_sms_count_changed)
        self.__device_manager.connect('active-dev-tech-status-changed', self._on_tech_changed)

        # Some UI signals
        self.open.connect('activate', self._on_systray_open_activate)
        self.connect.connect('activate', self._on_systray_connect_activate)
        self.disconnect.connect('activate', self._on_systray_disconnect_activate)
        self.show_available_networks.connect('activate', self._on_systray_show_available_networks_activate)
        self.exit.connect('activate', self._on_systray_exit_activate)

    def _update_sms_count(self):
        self._sms_count = int(self.__sms_action.alt_text())

    ### Event callbacks ###

    def _on_connected(self, dialer = None):
        self.connect.hide()
        self.disconnect.show()

    def _on_disconnected(self, dialer = False):
        self.connect.show()
        self.disconnect.hide()

    def _on_speed_changed(self, sender, speed):
        self._current_speed = _('Current speed: %s') % speed

    def _on_session_time_changed(self, widget, hours, minutes, seconds):
        self._time_elapsed = _('Time elapsed: %02d:%02d:%02d') % (hours, minutes, seconds)

    def _on_data_usage_changed(self, traffic_manager, nbytes):
        if nbytes <= 0:
            nbytes = 0
        self._data_usage = _('Data usage: %s') % \
                format_to_maximun_unit(nbytes,"GBits","MBits","KBits","Bits")

    def _on_sms_count_changed(self, sender, count):
        self._update_sms_count()

    def _on_tech_changed(self, sender, tech):
        self._network_tech = _fd.DeviceManager.get_technology_string(tech)

    ### Widget signals ###
    def _on_systray_open_activate(self, widget, event=None):
        mw_shown = self._config.get_ui_general_key_value('systray_showing_mw')
        if mw_shown:
            self.__dock.hide_main_window()
        else:
            self.__dock.show_main_window()

    def _on_systray_connect_activate(self, widget):
        self.__conn_zone.do_connect()

    def _on_systray_disconnect_activate(self, widget):
        self.__conn_manager.disconnect()

    def _on_systray_show_available_networks_activate (self, widget):
        self.__dock.connection_zone.show_available_networks()

    def _on_systray_exit_activate(self, widget):
        self.__dock.close_app()
