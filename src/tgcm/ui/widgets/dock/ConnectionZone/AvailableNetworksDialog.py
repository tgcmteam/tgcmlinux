#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos Serrano <dcastellanos@indra.es>
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

import tgcm.core.ConnectionManager
import tgcm.core.DeviceManager
import tgcm.core.FreeDesktop
import tgcm.core.Theme

from tgcm.ui.MSD.MSDUtils import normalize_strength

import freedesktopnet.networkmanager.accesspoint

from MobileManager import CARD_STATUS_READY


class AvailableNetworksDialog(gtk.Dialog):
    def __init__(self, connection_settings_manager, parent=None):
        conf = tgcm.core.Config.Config()
        gtk.Dialog.__init__(self,
                title = ('%s - %s') % (conf.get_app_name(), _('Available networks')),
                parent = parent,
                flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
                buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_CONNECT, gtk.RESPONSE_ACCEPT))
        self.set_border_width(5)
        self.vbox.set_spacing(1)

        self.__connection_settings_manager = connection_settings_manager
        self.__device_manager = tgcm.core.FreeDesktop.DeviceManager()

        contents_vbox = gtk.VBox()
        contents_vbox.set_border_width(5)
        contents_vbox.set_spacing(6)
        self.vbox.pack_start(contents_vbox, True, True, 0)

        label = gtk.Label(_('Select the connection that you want to use and press the Connect button.'))
        label.set_alignment(0, 0.5)
        contents_vbox.pack_start(label, False, True, 0)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        contents_vbox.pack_start(scrolled_window, True, True, 0)

        self.treeview = gtk.TreeView()
        self.treeview.set_headers_visible(False)
        scrolled_window.add(self.treeview)

        # Signal strength column
        column = gtk.TreeViewColumn('signal-strength',
                gtk.CellRendererPixbuf(), pixbuf = 2)
        self.treeview.append_column(column)

        # AP name
        column = gtk.TreeViewColumn('SSID',
                gtk.CellRendererText(), text = 3)
        column.set_expand(True)
        self.treeview.append_column(column)

        # Connected
        column = gtk.TreeViewColumn('connected',
                gtk.CellRendererText(), text = 4)
        self.treeview.append_column(column)

        # AP Security
        column = gtk.TreeViewColumn('ap-security',
                gtk.CellRendererPixbuf(), pixbuf = 5)
        self.treeview.append_column(column)

        # Tooltip
        self.treeview.set_tooltip_column(7)

        # TreeView model
        self.model = AvailableNetworksModel(self.__connection_settings_manager)
        model = gtk.TreeModelSort(self.model)
        model.set_sort_column_id(1, gtk.SORT_DESCENDING)
        model = model.filter_new()
        model.set_visible_func(self.model._filter_func, data=None)
        self.treeview.set_model(model)

        # Disable the "connect" button by default, because when
        # AN dialog is shown there is no selection by default
        button = self.get_widget_for_response(gtk.RESPONSE_ACCEPT)
        button.set_sensitive(False)

        # Listen to selection changes
        selection = self.treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect('changed', self.__on_selection_changed)
        selection.select_path(0)

        # Listen to double-click event in a row
        self.treeview.connect('row-activated', self.__on_row_activated)

        self.show_all()
        self.resize(450, 350)

    def get_selected_connection(self):
        selected_row = self.__get_selected_row()
        value = selected_row.get_value() if selected_row is not None else None
        return value

    def is_button_operation_connect(self):
        button = self.get_widget_for_response(gtk.RESPONSE_ACCEPT)
        return button.get_label() == gtk.STOCK_CONNECT

    def destroy(self):
        # Make sure that all the things are disconnected and properly disposed
        self.model.disconnect_signals()
        self.model = None

        # Attempt to destroy this widget
        gtk.Widget.destroy(self)

    def __on_selection_changed(self, selection):
        button = self.get_widget_for_response(gtk.RESPONSE_ACCEPT)

        selected_row = self.__get_selected_row(selection)

        # There is at least one selected network, I'll enable the connect
        # button and show the corresponding label
        if selected_row is not None:
            button.set_sensitive(True)
            if selected_row.is_connected():
                button.set_label(gtk.STOCK_DISCONNECT)
            else:
                button.set_label(gtk.STOCK_CONNECT)

        # There is no selected network, I'll disable the connect button
        else:
            button.set_sensitive(False)
            button.set_label(gtk.STOCK_CONNECT)

    def __on_row_activated(self, treeview, path, column):
        selected_row = self.__get_selected_row()
        if selected_row is not None:
            self.response(gtk.RESPONSE_ACCEPT)

    def __get_selected_row(self, selection=None):
        if selection is None:
            selection = self.treeview.get_selection()

        # Check if there is a valid selected row
        selected_row = None
        is_item_selected = selection.count_selected_rows() > 0
        if is_item_selected:
            (model, tree_iter) = selection.get_selected()
            connection = model.get_value(tree_iter, 6)
            if not isinstance(connection, ConnectionSettingsEmptyEntry):
                selected_row = connection

        return selected_row


class AvailableNetworksModel(gtk.GenericTreeModel):
    column_types = (bool, int, gtk.gdk.Pixbuf, str, str, gtk.gdk.Pixbuf, gobject.TYPE_PYOBJECT, str)
    column_names = ('IsVisible', 'Priority', 'Strength', 'Name', 'Status', 'Security', 'Object', 'Tooltip')

    def __init__(self, connection_settings_manager):
        gtk.GenericTreeModel.__init__(self)

        self.__conn_settings_manager = connection_settings_manager
        self.__conn_manager = tgcm.core.ConnectionManager.ConnectionManager()
        self.__theme_manager = tgcm.core.Theme.ThemeManager()
        self.__device_manager = tgcm.core.FreeDesktop.DeviceManager()

        # Ethernet pixbuf
        icon_file = self.__theme_manager.get_icon('dock', 'lan.png')
        pixbuf = gtk.gdk.pixbuf_new_from_file(icon_file)
        pixbuf = pixbuf.add_alpha(True, 255, 0, 255)
        self.__eth_pixbuf = pixbuf.subpixbuf(0, 23, 23, 23)

        # Wi-Fi signal pixbufs
        icon_file = self.__theme_manager.get_icon('dock', 'wifisignal.png')
        pixbuf = gtk.gdk.pixbuf_new_from_file(icon_file)
        self.__wifi_pixbufs = {}
        for i in range(0, 6):
            self.__wifi_pixbufs[i] = pixbuf.subpixbuf(0, i * 23, 23, 23)

        # GSM signal pixbufs
        icon_file = self.__theme_manager.get_icon('dock', 'signal.png')
        pixbuf = gtk.gdk.pixbuf_new_from_file(icon_file)
        self.__modem_pixbufs = {}
        for i in range(0, 6):
            self.__modem_pixbufs[i] = pixbuf.subpixbuf(0, i * 23, 23, 23)

        # Privacy pixbufs
        self.__security_pixbufs = {}
        icon_file = self.__theme_manager.get_icon('dock', 'lock.png')
        self.__security_pixbufs[True] = gtk.gdk.pixbuf_new_from_file(icon_file)
        icon_file = self.__theme_manager.get_icon('dock', 'unlock.png')
        self.__security_pixbufs[False] = gtk.gdk.pixbuf_new_from_file(icon_file)

        # Load available connections
        self.__available_connections = []
        self.__load_networks()
        self.__create_listeners()

    def disconnect_signals(self):
        for connection in self.__available_connections:
            connection.disconnect_signals()

        for signal in self._dbus_signals:
            signal.remove()

        for signal in self._gobject_signals:
            self.__conn_settings_manager.disconnect(signal)

    def _filter_func(self, model, treeiter, user_data=None):
        is_visible = model.get_value(treeiter, 0)
        return is_visible

    def __load_networks(self):
        # Create a fake empty entry in the AN connection lists
        self.__empty_entry = ConnectionSettingsEmptyEntry( \
                self.__device_manager, self.__conn_manager, \
                self.__conn_settings_manager, self.__available_connections, \
                self.__refresh_connection)
        self.__available_connections.append(self.__empty_entry)

        # Load profiles stored by Network Manager
        conn_settings_list = self.__conn_settings_manager.get_connections_list(True, True, True)
        len_conn_settings = len(conn_settings_list)
        for conn_settings in conn_settings_list:
            conn_settings_index = conn_settings_list.index(conn_settings)
            base_priority = (len_conn_settings - conn_settings_index) * 1000
            entry = self.__create_entry(conn_settings, base_priority)
            self.__available_connections.append(entry)

        # Get a list of accessible Access Points if possible
        self._wifi_device = self.__device_manager.get_wifi_device()
        if self._wifi_device is not None:
            self._find_access_points()

    def __create_entry(self, conn_settings, base_priority):
        if conn_settings['deviceType'] == tgcm.core.DeviceManager.DEVICE_WIRED:
            return ConnectionSettingsWiredEntry( \
                    self.__device_manager, self.__conn_manager, self.__conn_settings_manager, \
                    conn_settings, self.__refresh_connection)
        elif conn_settings['deviceType'] == tgcm.core.DeviceManager.DEVICE_WLAN:
            return ConnectionSettingsWifiEntry( \
                    self.__device_manager, self.__conn_manager, self.__conn_settings_manager, \
                    conn_settings, self.__refresh_connection)
        elif conn_settings['deviceType'] == tgcm.core.DeviceManager.DEVICE_MODEM:
            return ConnectionSettingsModemEntry( \
                    self.__device_manager, self.__conn_manager, self.__conn_settings_manager, \
                    conn_settings, self.__refresh_connection)

    def __remove_entry(self, conn_settings_entry):
        if conn_settings_entry in self.__available_connections:
            conn_settings_entry.disconnect_signals()
            index = self.__available_connections.index(conn_settings_entry)
            self.row_deleted(index)
            self.__available_connections.remove(conn_settings_entry)

    def __create_listeners(self):
        # Device listeners
        self._dbus_signals = []
        if self._wifi_device is not None:
            nm_device = self._wifi_device.get_nm_device()
            self._dbus_signals.append(nm_device.connect_to_signal( \
                    'AccessPointAdded', self.__on_access_point_added))
            self._dbus_signals.append(nm_device.connect_to_signal( \
                    'AccessPointRemoved', self.__on_access_point_removed))

        # Connection Settings listeners
        self._gobject_signals = []
        signal_id = self.__conn_settings_manager.connect('connection-added', self.__on_conn_settings_added)
        self._gobject_signals.append(signal_id)
        signal_id = self.__conn_settings_manager.connect('connection-removed', self.__on_conn_settings_removed)
        self._gobject_signals.append(signal_id)

    def __refresh_connection(self, connection):
        # Refresh connection
        if connection in self.__available_connections:
            path = (self.__available_connections.index(connection), )
            treeiter = self.get_iter(path)
            self.row_changed(path, treeiter)

        # Refresh the empty connection too
        path = (self.__available_connections.index(self.__empty_entry), )
        treeiter = self.get_iter(path)
        self.row_changed(path, treeiter)

    ### Access Point list management methods ###

    def _find_access_points(self):
        if self._wifi_device.is_ready():
            for access_point in self._wifi_device.get_access_points():
                self._add_access_point(access_point)

    def _add_access_point(self, access_point):
        # Ignore Access Points without a SSID because we have no way to determine which
        # NM connection settings belongs to, nor connect to them without a SSID.
        if len(access_point['ssid']) == 0:
            return None

        # Iterate through all entries in available connections list, and ask for every entry
        # if it can handle the access point.
        #
        # It a new entry was created, this method returns a pointer to this object. Otherwise, it
        # will return None.
        for connection in self.__available_connections:
            if connection.add_access_point(access_point):
                return None

        # Seems that no entry can handle the access point, so it is necessary to create a new
        # one for it
        new_entry = AccessPointEntry(access_point, self.__refresh_connection)
        self.__available_connections.append(new_entry)
        return new_entry

    ### UI signal callbacks ###

    def __on_access_point_added(self, object_path):
        access_point = freedesktopnet.networkmanager.accesspoint.AccessPoint(object_path)
        new_entry = self._add_access_point(access_point)

        # Update the tree
        if new_entry is not None:
            path = (self.__available_connections.index(new_entry),)
            treeiter = self.get_iter(path)
            self.row_inserted(path, treeiter)

    def __on_access_point_removed(self, object_path):
        parent_connection = None
        for connection in self.__available_connections:
            if connection.remove_access_point(object_path):
                parent_connection = connection
                break

        if (parent_connection is not None) and \
                isinstance(parent_connection, AccessPointEntry) and \
                (len(parent_connection.get_access_points()) == 0):
            self.__remove_entry(parent_connection)

    def __on_conn_settings_added(self, sender, conn_settings):
        # Create a new entry for the new ConnectionSettings object
        new_entry = self.__create_entry(conn_settings, 0)
        self.__available_connections.append(new_entry)

        # Remove current AccessPoint entries for the SSID of the
        # newly created ConnectionSettings
        if isinstance(new_entry, ConnectionSettingsWifiEntry):
            for known_entry in self.__available_connections:
                if isinstance(known_entry, AccessPointEntry):
                    if known_entry.get_ssid() == new_entry.get_ssid():
                        self.__remove_entry(known_entry)

        # Update the tree if necessary
        if new_entry is not None:
            path = (self.__available_connections.index(new_entry),)
            treeiter = self.get_iter(path)
            self.row_inserted(path, treeiter)

    def __on_conn_settings_removed(self, sender, conn_settings):
        # Look for the entry related to the ConnectionSettings to be removed
        conn_sett_entry = None
        for entry in self.__available_connections:
            if entry.get_value() == conn_settings:
                conn_sett_entry = entry
                break

        # If the entry corresponds to a ConnectionSettingsWifiEntry, it must be removed
        # and replaced with a new AccessPointEntry
        if (conn_sett_entry is not None) and isinstance(conn_sett_entry, ConnectionSettingsWifiEntry):
            # Search for a working access point (if any)
            access_point = None
            for foo in conn_sett_entry.get_access_points():
                if foo is not None:
                    access_point = foo
                    break

            # Remove the entry for the deleted Connection Setting
            self.__remove_entry(conn_sett_entry)

            # Create a new AccessPointEntry and update the tree if necessary
            if access_point is not None:
                new_entry = self._add_access_point(access_point)
                path = (self.__available_connections.index(new_entry),)
                treeiter = self.get_iter(path)
                self.row_inserted(path, treeiter)

    ### gtk.GenericModelTree interface ###

    def get_column_names(self):
        return self.column_names[:]

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return len(self.column_types)

    def on_get_column_type(self, n):
        return self.column_types[n]

    def on_get_iter(self, path):
        return self.__available_connections[path[0]]

    def on_get_path(self, rowref):
        return self.__available_connections.index(rowref)

    def on_get_value(self, rowref, column):
        if column == 0:     # Is Visible
            return rowref.is_visible()
        elif column == 1:     # Priority
            return rowref.get_priority()
        elif column == 2:   # Signal strength
            if isinstance(rowref, ConnectionSettingsEmptyEntry):
                return None
            elif isinstance(rowref, ConnectionSettingsWiredEntry):
                return self.__eth_pixbuf
            elif isinstance(rowref, AccessPointEntryBase):
                return self.__wifi_pixbufs[rowref.get_strength()]
            elif isinstance(rowref, ConnectionSettingsModemEntry):
                return self.__modem_pixbufs[rowref.get_strength()]
        elif column == 3:   # Connection name
            return rowref.get_name()
        elif column == 4:   # Connection status
            if rowref.is_connected():
                return _('Connected')
            else:
                return ''
        elif column == 5:   # Connection security
            security = rowref.get_security()
            if security is not None:
                return self.__security_pixbufs[security]
            else:
                return None
        elif column == 6:   # Python object
            return rowref
        elif column == 7:   # Tooltip
            return rowref.get_tooltip()
        return

    def on_iter_next(self, rowref):
        try:
            i = self.__available_connections.index(rowref) + 1
            return self.__available_connections[i]
        except IndexError:
            return None

    def on_iter_children(self, rowref):
        if rowref:
            return 0
        return self.__available_connections[0]

    def on_iter_has_child(self, rowref):
        return False

    def on_iter_n_children(self, rowref):
        if rowref:
            return None
        return len(self.__available_connections)

    def on_iter_nth_child(self, rowref, n):
        if rowref:
            return None
        try:
            return self.__available_connections[n]
        except IndexError:
            return None

    def on_iter_parent(self, child):
        return None


class AccessPointEntryBase():
    def __init__(self):
        self._ssid = None
        self._access_points = {}
        self._best_strength = 0

    def disconnect_signals(self):
        for object_path in self._access_points.keys():
            signal = self._access_points.pop(object_path)[1]
            signal.remove()

    def get_name(self):
        return self._ssid

    def get_ssid(self):
        return self._ssid

    def get_security(self):
        security = None
        if len(self._access_points) > 0:
            security = self._access_points[self._access_points.keys()[0]][0]['flags'] == \
                    freedesktopnet.networkmanager.accesspoint.AccessPoint.Flags.PRIVACY
        return security

    def get_strength(self):
        return normalize_strength(self._best_strength)

    def get_tooltip(self):
        conn_type = _('Wi-Fi Network')
        conn_ssid = 'SSID: %s' % self.get_ssid()
        conn_status = _('Connected') if self.is_connected() else _('Disconnected')
        conn_status = _('Status: %s') % conn_status
        conn_security = _('Secured network') if self.get_security() else _('Unsecured network')

        label_entries = []
        label_entries.append(conn_type)
        label_entries.append(conn_ssid)
        label_entries.append(conn_status)
        label_entries.append(conn_security)

        return '\n'.join(label_entries)

    def add_access_point(self, access_point):
        if self._ssid == access_point['Ssid']:
            self._add_access_point(access_point)
            self._refresh_entry()
            return True
        else:
            return False

    def remove_access_point(self, object_path):
        if object_path in self._access_points.keys():
            self._remove_access_point(object_path)
            self._refresh_entry()
            return True
        else:
            return False

    def get_access_points(self):
        access_points = []
        for access_point, signal_id in self._access_points.values():
            access_points.append(access_point)
        return access_points

    ### Helper methods ###

    def _find_access_points(self):
        # Find all matching APs for this profile
        if self._device.is_ready():
            for access_point in self._device.get_access_points():
                self._add_access_point(access_point)

    def _calculate_best_strength(self):
        # Choose the AP with the strongest signal
        for access_point in self._access_points.values():
            try:
                signal_strength = access_point[0]['Strength']
                if signal_strength > self._best_strength:
                    self._best_strength = signal_strength
            except TypeError:
                # Seems that sometimes D-Bus throws some exceptions. There is very little
                # to do here, except to capture the exception and pray there is not anything
                # more broken.
                pass

    def _add_access_point(self, access_point):
        if self._ssid == access_point['Ssid']:
            signal_id = access_point.connect_to_signal( \
                    'PropertiesChanged', self.__on_access_point_properties_changed)
            self._access_points[access_point.object_path] = (access_point, signal_id)

    def _remove_access_point(self, object_path):
        if object_path in self._access_points.keys():
            signal = self._access_points.pop(object_path)[1]
            signal.remove()

    ### Signal callbacks ###

    def __on_access_point_properties_changed(self, properties):
        self._calculate_best_strength()
        self._refresh_entry()


class ConnectionSettingsEntry():
    def __init__(self, dev_manager, conn_manager, conn_sett_manager, conn_settings, notify_cb):
        self._device_manager = dev_manager
        self._device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self._conn_manager = conn_manager
        self._conn_settings_manager = conn_sett_manager
        self._conn_settings = conn_settings
        self._notify_callback = notify_cb
        self._device = None

        self.__calculate_priority()
        self.__create_listeners()

    def __calculate_priority(self):
        conn_settings_list = self._conn_settings_manager.get_connections_list(True, True, True)
        self._base_priority = 0
        if self._conn_settings in conn_settings_list:
            len_conn_settings = len(conn_settings_list)
            index = conn_settings_list.index(self._conn_settings)
            self._base_priority = (len_conn_settings - index) * 1000

    def __create_listeners(self):
        self.__gobject_signals = []
        sid = self._device_dialer.connect('connected', self.__on_device_connected)
        self.__gobject_signals.append((self._device_dialer, sid))
        sid = self._device_dialer.connect('disconnected', self.__on_device_disconnected)
        self.__gobject_signals.append((self._device_dialer, sid))
        sid = self._conn_settings_manager.connect('connection-added', self.__on_conn_settings_added)
        self.__gobject_signals.append((self._conn_settings_manager, sid))
        sid = self._conn_settings_manager.connect('connection-removed', self.__on_conn_settings_removed)
        self.__gobject_signals.append((self._conn_settings_manager, sid))
        sid = self._conn_settings_manager.connect('priorities-changed', self.__on_conn_priority_changed)
        self.__gobject_signals.append((self._conn_settings_manager, sid))
        if self._conn_settings is not None:
            sid = self._conn_settings.connect('properties-changed', self.__on_conn_properties_changed)
            self.__gobject_signals.append((self._conn_settings, sid))

    ### Signal callbacks ###

    def __on_device_connected(self, sender):
        self._refresh_entry()

    def __on_device_disconnected(self, sender):
        self._refresh_entry()

    def __on_conn_settings_added(self, sender, conn_settings):
        self.__calculate_priority()
        self._refresh_entry()

    def __on_conn_settings_removed(self, sender, conn_settings):
        self.__calculate_priority()
        self._refresh_entry()

    def __on_conn_priority_changed(self, sender):
        self.__calculate_priority()
        self._refresh_entry()

    def __on_conn_properties_changed(self, sender):
        self._refresh_entry()

    ### Entry interface methods ###

    def get_value(self):
        return self._conn_settings

    def disconnect_signals(self):
        for sender, signal_id in self.__gobject_signals:
            sender.disconnect(signal_id)

    def get_name(self):
        return self._conn_settings.get_name()

    def get_priority(self):
        return self._base_priority

    def get_security(self):
        return None

    def get_strength(self):
        return None

    def is_connected(self):
        active_connection = self._conn_manager.get_related_active_connection(self._conn_settings)
        return self._conn_manager.is_active_connection_connected(active_connection)

    def is_visible(self):
        is_visible = False
        if self._device is not None:
            is_visible = self._device.is_ready()
        return is_visible

    def _refresh_entry(self):
        self._notify_callback(self)

    ### Access Point interface methods ###

    def add_access_point(self, access_point):
        return False

    def remove_access_point(self, object_path):
        return False

    def get_access_points(self):
        return []


class ConnectionSettingsEmptyEntry(ConnectionSettingsEntry):
    def __init__(self, dev_manager, conn_manager, conn_sett_manager, available_connections, notify_cb):
        ConnectionSettingsEntry.__init__(self, dev_manager, conn_manager, \
                conn_sett_manager, None, notify_cb)
        self._available_connections = available_connections

    def get_name(self):
        return _('No connections available')

    def get_tooltip(self):
        return _('No connections available')

    def is_connected(self):
        return False

    def is_visible(self):
        is_any_entry_shown = False
        for entry in self._available_connections:
            is_not_empty_entry = not isinstance(entry, ConnectionSettingsEmptyEntry)
            if is_not_empty_entry and entry.is_visible():
                is_any_entry_shown = True
                break

        return not is_any_entry_shown


class ConnectionSettingsWiredEntry(ConnectionSettingsEntry):
    def __init__(self, dev_manager, conn_manager, conn_sett_manager, conn_settings, notify_cb):
        ConnectionSettingsEntry.__init__(self, dev_manager, conn_manager, \
                conn_sett_manager, conn_settings, notify_cb)
        self._device = self._device_manager.get_wired_device()

        if self._device is not None:
            self.__create_listeners()

    def __create_listeners(self):
        nm_device = self._device.get_nm_device()
        self._dbus_signals = []
        self._dbus_signals.append(nm_device.connect_to_signal( \
                'PropertiesChanged', self.__on_device_properties_changed))

    def disconnect_signals(self):
        ConnectionSettingsEntry.disconnect_signals(self)

        for signal in self._dbus_signals:
            signal.remove()

    def get_tooltip(self):
        conn_type = _('Ethernet Network')
        conn_status = _('Connected') if self.is_connected() else _('Disconnected')

        label_entries = []
        label_entries.append(conn_type)
        label_entries.append(conn_status)

        return '\n'.join(label_entries)

    ### Signal callbacks ###

    def __on_device_properties_changed(self, properties):
        self._refresh_entry()


class ConnectionSettingsWifiEntry(AccessPointEntryBase, ConnectionSettingsEntry):
    def __init__(self, dev_manager, conn_manager, conn_sett_manager, conn_settings, notify_cb):
        AccessPointEntryBase.__init__(self)
        ConnectionSettingsEntry.__init__(self, dev_manager, conn_manager, \
                conn_sett_manager, conn_settings, notify_cb)

        self._ssid = conn_settings['ssid']

        self._device = self._device_manager.get_wifi_device()
        self._dbus_signals = []
        if self._device is not None:
            self._find_access_points()
            self._calculate_best_strength()
            self.__create_nm_wifi_listeners()

    ### Entry interface methods ###

    def disconnect_signals(self):
        AccessPointEntryBase.disconnect_signals(self)
        ConnectionSettingsEntry.disconnect_signals(self)

        for signal in self._dbus_signals:
            signal.remove()

    def get_name(self):
        ssid = self.get_ssid()
        conn_name = self._conn_settings.get_name()
        if ssid == conn_name:
            name = ssid
        else:
            name = '%s (%s)' % (ssid, conn_name)
        return name

    def is_visible(self):
        is_visible = False
        if self._device is not None:
            is_visible = self._device.is_ready() and (len(self._access_points) > 0)
        return is_visible

    ### Helper methods ###

    def _find_access_points(self):
        # Find all matching APs for this profile
        if self._device.is_ready():
            for access_point in self._device.get_access_points():
                self._add_access_point(access_point)

    def __create_nm_wifi_listeners(self):
        nm_device = self._device.get_nm_device()
        self._dbus_signals.append(nm_device.connect_to_signal( \
                'PropertiesChanged', self.__on_device_properties_changed))

    ### Signal callbacks ###

    def __on_device_properties_changed(self, properties):
        if self._device.is_ready():
            self._find_access_points()
            self._calculate_best_strength()
        else:
            self._access_points.clear()
        self._refresh_entry()


class ConnectionSettingsModemEntry(ConnectionSettingsEntry):
    def __init__(self, dev_manager, conn_manager, conn_sett_manager, conn_settings, notify_cb):
        ConnectionSettingsEntry.__init__(self, dev_manager, conn_manager, \
                conn_sett_manager, conn_settings, notify_cb)
        self._device = self._device_manager.get_main_device()

        self._cached_signal_strength = 0
        self._cached_card_ready = False
        if self._device is not None:
            self.__update_card_status()
            self.__update_signal_strength()
        self.__create_listeners()

    def get_strength(self):
        return self._cached_signal_strength

    def get_tooltip(self):
        conn_type = _('3G Network')
        conn_status = _('Connected') if self.is_connected() else _('Disconnected')

        label_entries = []
        label_entries.append(conn_type)
        label_entries.append(conn_status)

        return '\n'.join(label_entries)

    def is_visible(self):
        is_visible = ConnectionSettingsEntry.is_visible(self)
        return is_visible and self._cached_card_ready

    def __create_listeners(self):
        self.__gobject_signals = []
        signal_id = self._device_manager.connect('device-added', self.__on_device_added)
        self.__gobject_signals.append(signal_id)
        signal_id = self._device_manager.connect('device-removed', self.__on_device_removed)
        self.__gobject_signals.append(signal_id)
        signal_id = self._device_manager.connect( \
                'active-dev-card-status-changed', self.__on_card_status_changed)
        self.__gobject_signals.append(signal_id)
        signal_id = self._device_manager.connect( \
                'active-dev-signal-status-changed', self.__on_signal_changed)
        self.__gobject_signals.append(signal_id)

    def disconnect_signals(self):
        ConnectionSettingsEntry.disconnect_signals(self)

        for signal in self.__gobject_signals:
            self._device_manager.disconnect(signal)

    def __update_card_status(self, status = None):
        entry_refresh_needed = False
        if status is None:
            status = self._device.get_card_status()
        card_ready = (status == CARD_STATUS_READY)
        if card_ready != self._cached_card_ready:
            self._cached_card_ready = card_ready
            entry_refresh_needed = True
        return entry_refresh_needed

    def __update_signal_strength(self, signal_quality = None):
        entry_refresh_need = False
        if signal_quality is None:
            signal_quality = self._device.get_SignalQuality()
        signal_strength = normalize_strength(signal_quality)
        if signal_strength != self._cached_signal_strength:
            self._cached_signal_strength = signal_strength
            entry_refresh_need = True
        return entry_refresh_need

    ### Callbacks ###

    def __on_device_added(self, sender, device):
        # Only recognize events from Modem devices
        if isinstance(device, tgcm.core.FreeDesktop.DeviceModem):
            self._device = device
            self.__update_card_status()
            self.__update_signal_strength()
            self._refresh_entry()

    def __on_device_removed(self, sender, object_path):
        if self._device.object_path == object_path:
            self._device = None
            self._refresh_entry()

    def __on_card_status_changed(self, sender = None, status = None):
        if (self._device is not None) and self.__update_card_status(status):
            self._refresh_entry()

    def __on_signal_changed(self, sender = None, signal_quality = None):
        if (self._device is not None) and self.__update_signal_strength(signal_quality):
            self._refresh_entry()


class AccessPointEntry(AccessPointEntryBase):
    def __init__(self, access_point, notify_callback):
        AccessPointEntryBase.__init__(self)
        self._notify_callback = notify_callback

        self._ssid = access_point['Ssid']
        self._add_access_point(access_point)
        self._calculate_best_strength()

    ### Entry interface methods ###

    def get_priority(self):
        return self._best_strength

    def get_value(self):
        if len(self.get_access_points()) > 0:
            return self.get_access_points()[0]

    def is_connected(self):
        return False

    def is_visible(self):
        if self._best_strength < 20:
            return False
        else:
            return True

    ### Helper methods ###

    def _refresh_entry(self):
        self._notify_callback(self)
