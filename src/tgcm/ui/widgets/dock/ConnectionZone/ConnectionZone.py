#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
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

import gtk
import gobject
import webbrowser

import tgcm.core.Connections
import tgcm.core.ConnectionLogger
import tgcm.core.ConnectionSettingsManager
import tgcm.core.FreeDesktop
import tgcm.core.TrafficManager
from tgcm.core.DeviceExceptions import *

import tgcm.ui
import tgcm.ui.windows
import tgcm.ui.widgets.dock

from tgcm.ui.MSD.MSDUtils import format_to_maximun_unit

import MobileManager

import freedesktopnet
import freedesktopnet.networkmanager.accesspoint
from freedesktopnet.networkmanager.networkmanager import NetworkManager

#CONNECTED = 0
#CONNECTING = 1
#DISCONNECTING = 2
#DISCONNECTED = 3

ASLEEP = NetworkManager.State.ASLEEP
CONNECTED = NetworkManager.State.CONNECTED
CONNECTING = NetworkManager.State.CONNECTING
UNKNOWN = NetworkManager.State.UNKNOWN
DISCONNECTED = NetworkManager.State.DISCONNECTED
DISCONNECTING = 10


class ConnectionZone (gobject.GObject):

    __gsignals__ = {
        'connection_speed_changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'connected':                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'disconnected':             (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'connecting':               (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    }

    def __init__(self, conn_manager):
        gobject.GObject.__init__(self)

        self.MSDConnManager = conn_manager
        self.MSDConnManager.connection_zone = self

        #Internal tooltip info
        self.__t_connection_name = "--"
        self.__t_speed = "--"
        self._waiting_wifi_connection_uuid = None

        self.conf = tgcm.core.Config.Config()
        self.connection_settings_manager = tgcm.core.ConnectionSettingsManager.ConnectionSettingsManager()

        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.connection_manager = tgcm.core.Connections.ConnectionManager()
        self.traffic_manager = tgcm.core.TrafficManager.TrafficManager()
        self.connection_logger = tgcm.core.ConnectionLogger.ConnectionLogger()

        self._main_window = tgcm.ui.ThemedDock().get_main_window()

        self.device_dialer.connect("connected", self.__connected_cb)
        self.device_dialer.connect("disconnected", self.__disconnected_cb)
        self.device_dialer.connect("connecting", self.__connecting_cb)
        self.device_dialer.connect("disconnecting", self.__disconnecting_cb)

        self.connection_manager.connect("connections_changed", self.__connections_changed_cb)
        self.traffic_manager.connect("update-instant-velocity", self.__updated_traffic_info_cb)
        self.connection_settings_manager.connect('connection-added', self.__on_new_connection_cb)
#        if self.device_dialer.status() == MobileManager.PPP_STATUS_CONNECTED:
#            self.connection_manager.disconnect ()
        self.connection_state = DISCONNECTED

        #self.connection_state =self.device_dialer.nmConnectionState();
        #self.connection_state = CONNECTED

    def do_connect(self):
        self.connection_index = -1
#        self.do_connect_with_smart_connector()
        self.MSDConnManager.do_connect_with_smart_connector()

    def do_disconnect(self):
        try:
            #if self.device_dialer.status() == MobileManager.PPP_STATUS_CONNECTED :
            if self.device_dialer.nmConnectionState() == CONNECTED:
                self.connection_manager.disconnect()
            else:
                pass
        except DeviceHasNotCapability:
            self.MSDConnManager.show_no_available_device_error()
        except DeviceNotReady:
            pass

    def do_cancel_connect(self):
        try:
            #if self.device_dialer.status() == MobileManager.PPP_STATUS_CONNECTING:
            if self.device_dialer.nmConnectionState() == CONNECTING:
                self.MSDConnManager.abort_connection_now()
            else:
                pass
        except DeviceHasNotCapability:
            self.MSDConnManager.show_no_available_device_error()
        except DeviceNotReady:
            pass

    def __connected_cb(self, dialer):
        self.connection_state = CONNECTED

        conn_settings = self.device_dialer.get_current_conn_settings()
        self.__t_connection_name = conn_settings.get_dock_name()

        self.connection_logger.register_connected_event(conn_settings)
        self.emit('connected', self.__t_connection_name)

        if tgcm.country_support == "mx":
            webbrowser.open("http://www.movistar.com.mx/internetmovistar")
        elif tgcm.country_support == "uk":
            dev = self.device_manager.get_main_device()
            if dev != None and dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM:
                if not dev.is_postpaid():
                    imsi = dev.get_imsi()
                    broadband_number = self.conf.get_user_mobile_broadband_number(imsi)
                    if broadband_number != "":
                        webbrowser.open("https://mobilebroadbandaccess.o2.co.uk/?DMPN=%s" % broadband_number)
                    else:
                        webbrowser.open("https://mobilebroadbandaccess.o2.co.uk")

    def __disconnected_cb(self, dialer):
        old_connection = self.__t_connection_name
        if self.__t_connection_name == "--":
            old_connection = self.connection_manager.get_default_connection_name()

        self.connection_state = DISCONNECTED
        self.__t_connection_name = "--"

        conn_settings = self.device_dialer.get_current_conn_settings()
        self.connection_logger.register_disconnection_event(conn_settings)

        self.emit("disconnected", old_connection)

    def __connecting_cb(self, dialer):
        self.connection_state = CONNECTING

        conn_settings = self.device_dialer.get_current_conn_settings()
        self.connection_logger.register_connecting_event(conn_settings)
        self.__t_connection_name = conn_settings.get_dock_name()

        self.emit("connecting", self.__t_connection_name)

    def __disconnecting_cb(self, dialer):
        self.connection_state = DISCONNECTING

    def __connections_changed_cb(self, cm):
        if self.device_dialer.status() == MobileManager.PPP_STATUS_DISCONNECTED:
            self.__t_connection_name = ''

    def __on_new_connection_cb(self, csetting_manager, conn_settings):
        if self._waiting_wifi_connection_uuid != None:
            if self._waiting_wifi_connection_uuid == conn_settings["uuid"]:
                self._waiting_wifi_connection_uuid = None
                self.connection_settings_manager.insert_after_first_ethernet(conn_settings["name"]);
                #We launch in this way to allow the NetworkManager signals to arrive
                gobject.idle_add(self.MSDConnManager.connect_to_connection, conn_settings, True)

    def __updated_traffic_info_cb(self, widget, in_data, out_data):
        if tgcm.country_support == "uk":
            return

        self.__t_speed = '%s/s' % format_to_maximun_unit(in_data * 8, "GBits","MBits","KBits","Bits")
        self.emit('connection_speed_changed', self.__t_speed)

    def show_available_networks(self):
        self._waiting_wifi_connection_uuid=None
        dialog = tgcm.ui.widgets.dock.AvailableNetworksDialog( \
                self.connection_settings_manager, self._main_window)
        ret = dialog.run()
        if ret == gtk.RESPONSE_ACCEPT:
            selected_connection = dialog.get_selected_connection()
            is_connect_operation = dialog.is_button_operation_connect()
            dialog.destroy()

            # The user wants to connect to a network
            if is_connect_operation:
                if selected_connection.__class__ is tgcm.core.ConnectionSettingsManager.ConnectionSettings:
                    # Selected item is a ConnectionSettings, it could be used directly to establish
                    # a connection with a suitable device
                    conn_settings = selected_connection
                    self.MSDConnManager.connect_to_connection(conn_settings, force_connection=True)
                else:
                    nm_access_point = selected_connection

                    # Check if it is an unsafe network, and if that is the case ask the user
                    # for confirmation
                    if nm_access_point['flags'] != freedesktopnet.networkmanager.accesspoint.AccessPoint.Flags.PRIVACY:
                        question_str = _('This network is not encrypted and can be unsafe. Are you sure you want to proceed connecting?')
                        dialog = tgcm.ui.windows.CheckboxDialog('unsafe-network-confirmation', \
                                default_response=gtk.RESPONSE_YES, title=_('Warning: Unsafe network'), \
                                parent=self._main_window, type=gtk.MESSAGE_WARNING, \
                                buttons=gtk.BUTTONS_YES_NO, message_format=question_str)
                        response = dialog.run()
                        dialog.destroy()

                        # Seems the user did not really want to connect to that access point, in
                        # that case just do nothing
                        if response != gtk.RESPONSE_YES:
                            return

                    # Selected item is an Access Point, it is necessary to create a ConnectionSettings
                    # first, and then a connection could be established
                    conDict = self.connection_settings_manager.add_wifi_connection_to_nm(nm_access_point)
                    self._waiting_wifi_connection_uuid = str(conDict['connection']['uuid'])

            # The user wants to disconnect to a network
            else:
                conn_settings = selected_connection
                self.MSDConnManager.disconnect_from_connection(conn_settings)
        else:
            dialog.destroy()
            self.__t_connection_name = '--'
