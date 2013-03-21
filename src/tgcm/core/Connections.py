#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
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

import tgcm
import Config
import FreeDesktop
import DeviceManager
import ConnectionSettingsManager
import Exporter
import Singleton

class ConnectionManager (gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'connections_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'pre_connections_change': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    def __init__ (self):
        gobject.GObject.__init__(self)

        self.conf = Config.Config ()
        self.connection_settings_manager=ConnectionSettingsManager.ConnectionSettingsManager()

        self.mcontroller = FreeDesktop.DeviceManager()
        self.device_dialer = FreeDesktop.DeviceDialer()

        self.ppp_manager = None

        self.connections_model = None
        self.load_connections_model ()

        self.conf.connect ("connection-added", self.__on_connection_added)
        self.conf.connect ("connection-deleted", self.__on_connection_deleted)


    def __on_connection_added (self, conf, conn_name):
        self.load_connections_model ()

    def __on_connection_deleted (self, conf, conn_name):
        self.load_connections_model ()

    def add_wwan_connection (self, conn):
        self.connection_settings_manager.add_wwan_connection(conn)

    def edit_connection (self, conn, conn_name):
        self.connection_settings_manager.add_wwan_connection(conn)

    def get_default_connection_name (self):
        return self.conf.get_default_connection_name()

    def get_connection_name_from_index (self,connection_index):
        return self.conf.get_connection_name_from_index(connection_index)

#    def get_connection_info (self, conn_name):
#        return self.get_default_connection_name.get_connection_info_dict (conn_name)

    def get_connections_model (self):
        return self.connections_model

    def export_connection (self, conn_settings, file):
        exporter = Exporter.Exporter()
        exporter.save_connection_to_file (conn_settings, file)

    def is_device_selected (self):
        dev = self.mcontroller.get_main_device()
        if dev != None:
            return True
        else:
            return False

    def get_ask_before_connect (self):
        return self.conf.get_ask_before_connect_to_action()

    def set_ask_before_connect (self, value):
        self.conf.set_ask_before_connect(value)

    def get_ask_before_change_connection (self):
        return self.conf.get_ask_before_change_connection()

    def set_ask_before_change_connection (self, value):
        self.conf.set_ask_before_change_connection(value)

    def get_ask_before_connect_to_action(self):
        return self.conf.get_ask_before_connect_to_action()

    def set_ask_before_connect_to_action(self, value):
        self.conf.set_ask_before_connect_to_action(value)

    def connect_to_bus (self, connection_ui):
        if self.ppp_manager != None:
            return True

        if self.device_dialer != None :
            self.ppp_manager = self.device_dialer
            self.ppp_manager.connect("connected", connection_ui._connected_cb)
            self.ppp_manager.connect("disconnected", connection_ui._disconnected_cb)
            self.ppp_manager.connect("connecting", connection_ui._connecting_cb)
            self.ppp_manager.connect("disconnecting", connection_ui._disconnecting_cb)

            return True
        else:
            self.ppp_manager = None
            return False

    def disconnect (self):
        tgcm.debug("disconnect")
        self.ppp_manager.stop()

    def disconnect_from_connection(self, conn_settings):
        tgcm.debug("disconnect")
        self.ppp_manager.stop_connection(conn_settings)

    def load_connections_model (self):
        self.emit ('pre_connections_change')

        if self.connections_model == None:
#            self.connections_model = gtk.ListStore(gtk.gdk.Pixbuf, str, 'gboolean', 'gboolean', gtk.gdk.Pixbuf)
            self.connections_model = gtk.ListStore(str, str, str, 'gboolean',object)
        else:
            self.connections_model.clear ()

        i=0
        conn_list=self.connection_settings_manager.get_connections_list()
        for cs in conn_list:
            i=i+1
            connectionType=cs["deviceType"]
            if connectionType == DeviceManager.DEVICE_MODEM:
                if tgcm.country_support == 'de':
                    connectionTypeStr='2G/3G/4G'
                else:        
                    connectionTypeStr='WWAN'
                    
            elif connectionType == DeviceManager.DEVICE_WLAN:
                connectionTypeStr='Wi-Fi'
            elif connectionType == DeviceManager.DEVICE_WIRED:
                connectionTypeStr='LAN'
            else:
                connectionTypeStr='Other'

            self.connections_model.append([str(i), cs['name'], connectionTypeStr ,cs["editable"],cs])
            self.emit ('connections_changed')
