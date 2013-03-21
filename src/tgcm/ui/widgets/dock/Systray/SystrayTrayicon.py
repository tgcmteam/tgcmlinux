#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2003-2007, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
import gobject

from Systray import SystrayBase

class SystrayTrayicon(SystrayBase):
    def __init__(self, dock, conn_manager, conn_zone):
        # Call parent constructor
        SystrayBase.__init__(self, dock, conn_manager, conn_zone)

        ### Instantiate a gtk.StatusIcon ###
        # gnome-shell checks XClassHint.res_class with ShellTrayIcon.
        # gtk_status_icon_set_name() can set XClassHint.res_class .
        # However gtk_status_icon_new() also calls gtk_window_realize() so
        # gtk_status_icon_set_visible() needs to be called to set WM_CLASS
        # so that gtk_window_realize() is called later again.
        # set_title is for gnome-shell notificationDaemon in bottom right.
        self.__sicon = gtk.StatusIcon()
        self.__sicon.set_visible(False)
        self.__sicon.set_title(self._config.get_app_name())
        self.__sicon.set_visible(True)
        self.__set_status_trayicon(is_connected = False, is_sms_pending = False)
        self.open.set_label(_('Open %s') % self._config.get_app_name())

        # Prepare the tooltip
        self.__update_tooltip()

        # Connect various signals
        self._connect_signals()

        self.__timeout = None
        if self._is_connected():
            self._on_connected()
        else:
            self._on_disconnected()

    def _connect_signals(self):
        SystrayBase._connect_signals(self)
        self.__sicon.connect('activate', self._on_systray_open_activate, None)
        self.__sicon.connect('popup-menu', self._popup_menu, None)

    ### Event callbacks ###

    def _on_connected(self, dialer = None):
        SystrayBase._on_connected(self, dialer)
        self.__update_tooltip()
        self.__timeout = gobject.timeout_add(1000, self.__update_tooltip)

    def _on_disconnected(self, dialer = False):
        SystrayBase._on_disconnected(self, dialer)
        if self.__timeout is not None:
            gobject.source_remove(self.__timeout)
        self.__update_tooltip()

    def _popup_menu(self, status_icon, button, activate_time, data):
        mw_shown = self._config.get_ui_general_key_value('systray_showing_mw')
        if mw_shown:
            self.open.set_sensitive(False)
        else:
            self.open.set_sensitive(True)
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, status_icon)

    def __update_tooltip(self):
        tooltip = []
        if self._is_connected():
            nm_conn_type = self._device_dialer.nmGetConnectionType()
            stats = []
            connection_type = _('Unknown')
            if nm_conn_type == 'ETHERNET':
                connection_type = _('Ethernet')
            elif nm_conn_type == 'WIRELESS':
                connection_type = _('Wi-Fi')
                stats.append(self._current_speed)
                stats.append(self._time_elapsed)
                stats.append(self._data_usage)
            elif nm_conn_type == 'GSM':
                connection_type = self._network_tech
                stats.append(self._current_speed)
                stats.append(self._time_elapsed)
                stats.append(self._data_usage)

            # Update connection label with information about current connection
            conn_settings = self._device_dialer.get_current_conn_settings()
            connection_name = conn_settings.get_dock_name()
            tooltip.append(self._config.get_app_name())
            tooltip.append(_('Connected to %s (%s)') % (connection_name, connection_type))
            tooltip.extend(stats)
        else:
            tooltip.append('%s - %s' % (self._config.get_app_name(), _('Disconnected')))

        # Update count and update the trayicon accordingly
        self._update_sms_count()
        if self._sms_count > 0:
            tooltip.append(_('%d unread SMS') % self._sms_count)
        self.__sicon.set_tooltip('\n'.join(tooltip))

        return True

    def _update_sms_count(self):
        SystrayBase._update_sms_count(self)

        # Update icon depending on connection status and unread SMS count
        is_connected = self._is_connected()
        is_sms_pending = self._sms_count != 0
        self.__set_status_trayicon(is_connected, is_sms_pending)

    def __set_status_trayicon(self, is_connected, is_sms_pending):
        if is_sms_pending == 0:
            if is_connected:
                icon_name = 'conectado.png'
            else:
                icon_name = 'desconectado.png'
        else:
            if is_connected:
                icon_name = 'conectado_smspending.png'
            else:
                icon_name = 'desconectado_smspending.png'

        size = self.__sicon.get_size()
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self._theme_manager.get_icon('icons', icon_name), size, size)
        self.__sicon.set_from_pixbuf(pixbuf)
