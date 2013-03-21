#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
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
import socket

import tgcm
import tgcm.core.Theme
import tgcm.core.ConnectionSettingsManager

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, error_dialog
from tgcm.ui.MSD.MSDMessages import MSG_NO_CONNECTION_NAME_TITLE, MSG_NO_CONNECTION_NAME,\
    MSG_NO_CONNECTION_USER, MSG_NO_CONNECTION_USER_TITLE, MSG_NO_CONNECTION_APN_TITLE,\
    MSG_NO_CONNECTION_APN, MSG_NO_CONNECTION_PROXY_IP_TITLE, MSG_NO_CONNECTION_PROXY_IP,\
    MSG_NO_CONNECTION_PROXY_PORT_TITLE, MSG_NO_CONNECTION_PROXY_PORT, MSG_NO_CONNECTION_DNS_TITLE,\
    MSG_NO_CONNECTION_DNS


class ConnectionDialog(gtk.Dialog):
    def __init__(self, parent=None):
        if tgcm.country_support == 'de':
            title = _("New 2G/3G/4G connection")
        else:
            title = _("New WWAN connection")

        self._conn_settings_manager = tgcm.core.ConnectionSettingsManager.ConnectionSettingsManager()

        gtk.Dialog.__init__(self, title, parent, \
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, \
                 gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

        self.set_border_width(6)

        self.windows_dir = os.path.join(tgcm.windows_dir, 'ConnectionDialog')
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'ConnectionDialog_editor.ui'), \
                prefix='conn')

        theme_manager = tgcm.core.Theme.ThemeManager()
        self.window_icon_path = theme_manager.get_icon('icons', 'settings_taskbar.png')
        self.set_icon_from_file(self.window_icon_path)
        self.vbox.pack_start(self.main_vbox)

        # Initial dialog configuration
        self._create_data_model()
        self._enable_password_area()
        self._enable_dns_area()
        self._enable_proxy_area()

        ### Signals

        # Avoid dialog to close events
        self.connect('response', self._on_dialog_response)
        self.connect('close', self._on_dialog_close)
        self.connect('delete_event', self._on_dialog_close)

        # 'More' proxy button
        self.proxy_more_button.connect('clicked', self._on_proxy_more_activated)

        # Widget events
        self.ask_password_checkbutton.connect('toggled', self._on_ask_password_toggled)
        self.use_proxy_radiobutton.connect('toggled', self._on_use_proxy_radiobutton_toggled)
        self.dns_user_radiobutton.connect('toggled', self._on_dns_user_radiobutton_toggled)

    def open_conn_settings(self, conn_settings):
        self.current_conn_settings = conn_settings

        title = _('Edit connection - %s') % conn_settings['name']
        self.set_title(title)

        is_editable = conn_settings['editable']

        # Current ConnectionSetting object is not editable
        if not is_editable:
            button = self.get_widget_for_response(gtk.RESPONSE_CANCEL)
            button.set_label(gtk.STOCK_CLOSE)
            button = self.get_widget_for_response(gtk.RESPONSE_ACCEPT)
            button.set_visible(False)

            self.connection_details_vbox.set_sensitive(False)
            self.network_configuration_vbox.set_sensitive(False)

        ## Load dialog fields

        # Connection details
        self.connection_name_entry.set_text(conn_settings['name'])

        self.username_entry.set_text(conn_settings['username'])

        if ('password' in conn_settings) and (conn_settings['password'] is not None):
            self.password_entry.set_text(conn_settings['password'])
        self.ask_password_checkbutton.set_active(conn_settings['ask_password'])
        if ('apn' in conn_settings) and (conn_settings['apn'] is not None):
            self.apn_entry.set_text(conn_settings['apn'])

        # Network configuration
        if 'proxy' in conn_settings:
            is_proxy = conn_settings['proxy']
            self.use_proxy_radiobutton.set_active(is_proxy)
        self._enable_proxy_area()

        if ('proxy_ip' in conn_settings) and (conn_settings['proxy_ip'] is not None):
            self.proxy_address_entry.set_text(conn_settings['proxy_ip'])
        if ('proxy_port' in conn_settings) and (conn_settings['proxy_port'] is not None):
            self.proxy_port_entry.set_value(conn_settings['proxy_port'])

        proxy_fields = ('proxy_ip', 'proxy_https_ip', \
                    'proxy_ftp_ip', 'proxy_socks_ip', \
                    'proxy_port', 'proxy_https_port', \
                    'proxy_ftp_port', 'proxy_socks_port', \
                    'proxy_ignore', 'proxy_same_proxy')
        for field in proxy_fields:
            if (field in conn_settings) and (conn_settings[field] is not None):
                self._more_proxy_data[field] = conn_settings[field]

        if 'auto_dns' in conn_settings:
            is_auto_dns = conn_settings['auto_dns']
            if is_auto_dns:
                self.dns_network_radiobutton.set_active(True)
            else:
                self.dns_user_radiobutton.set_active(True)
        self._enable_dns_area()

        if len(conn_settings['dns_servers']) >= 1:
            self.primary_dns_entry.set_text(conn_settings['dns_servers'][0])
        if len(conn_settings['dns_servers']) >= 2:
            self.secondary_dns_entry.set_text(conn_settings['dns_servers'][1])

        if 'domains' in conn_settings and conn_settings['domains'] is not None and len(conn_settings['domains'])>0:
            def f(x,y): return str(x)+','+str(y)
            self.dns_suffix_entry.set_text(reduce(f,conn_settings['domains']))

        # Enable or disable dialog areas if necessary
        self._enable_password_area()
        self._enable_dns_area()
        self._enable_proxy_area()

    def _check_values(self):
        is_error = False
        title = None
        message = None

        # Name check
        name = self.connection_name_entry.get_text()
        if (not is_error) and (len(name) == 0):
            is_error = True
            title = MSG_NO_CONNECTION_NAME_TITLE
            message = MSG_NO_CONNECTION_NAME

        # Username check
        username = self.username_entry.get_text()
        if (not is_error) and (len(username) == 0):
            is_error = True
            title = MSG_NO_CONNECTION_USER_TITLE
            message = MSG_NO_CONNECTION_USER

        # APN check
        apn_name = self.apn_entry.get_text()
        if (not is_error) and (len(apn_name) == 0):
            is_error = True
            title = MSG_NO_CONNECTION_APN_TITLE
            message = MSG_NO_CONNECTION_APN

        # Only perform proxy checks if proxy support is enabled
        is_proxy_server = self.use_proxy_radiobutton.get_active()
        if is_proxy_server:
            # Proxy address check
            proxy_address = self.proxy_address_entry.get_text()
            if (not is_error) and (len(proxy_address) == 0):
                is_error = True
                title = MSG_NO_CONNECTION_PROXY_IP_TITLE
                message = MSG_NO_CONNECTION_PROXY_IP

            # Proxy port check
            proxy_port = self.proxy_port_entry.get_value()
            if (not is_error) and (proxy_port < 0):
                is_error = True
                title = MSG_NO_CONNECTION_PROXY_PORT_TITLE
                message = MSG_NO_CONNECTION_PROXY_PORT

        # Only perform DNS checks if custom DNS support is enabled
        is_custom_dns = self.dns_user_radiobutton.get_active()
        if (not is_error) and is_custom_dns:
            # Check primary DNS is not empty and correctly formatted
            primary_dns = self.primary_dns_entry.get_text()
            try:
                socket.inet_aton(primary_dns)
            except:
                is_error = True
                title = MSG_NO_CONNECTION_DNS_TITLE
                message = MSG_NO_CONNECTION_DNS

            # Check secondary DNS is correctly formatted
            secondary_dns = self.secondary_dns_entry.get_text()
            if len(secondary_dns) > 0:
                try:
                    socket.inet_aton(secondary_dns)
                except:
                    is_error = True
                    title = MSG_NO_CONNECTION_DNS_TITLE
                    message = MSG_NO_CONNECTION_DNS

        # Show an error message if an error has been detected
        if is_error:
            error_dialog(parent=self, markup=title, msg=message)

        return not is_error

    def _save_current_connection_settings(self):
        # If there is no current connection create an empty one
        # from a template
        if self.current_conn_settings is None:
            self.current_conn_settings = self._conn_settings_manager.get_connection_profile()

        name = self.connection_name_entry.get_text()
        self.current_conn_settings['name'] = name

        username = self.username_entry.get_text()
        self.current_conn_settings['username'] = username

        password = self.password_entry.get_text()
        self.current_conn_settings['password'] = password

        is_ask_password = self.ask_password_checkbutton.get_active()
        self.current_conn_settings['ask_password'] = is_ask_password

        apn_name = self.apn_entry.get_text()
        self.current_conn_settings['apn'] = apn_name

        is_proxy_server = self.use_proxy_radiobutton.get_active()
        self.current_conn_settings['proxy'] = is_proxy_server

        proxy_address = self.proxy_address_entry.get_text()
        self.current_conn_settings['proxy_ip'] = proxy_address

        proxy_port = self.proxy_port_entry.get_value()
        self.current_conn_settings['proxy_port'] = int(proxy_port)

        more_proxy_fields = ('proxy_https_ip', 'proxy_ftp_ip', \
                     'proxy_socks_ip', 'proxy_https_port', \
                     'proxy_ftp_port', 'proxy_socks_port', \
                     'proxy_ignore', 'proxy_same_proxy')
        for field in more_proxy_fields:
            self.current_conn_settings[field] = self._more_proxy_data[field]

        is_auto_dns =  self.dns_network_radiobutton.get_active()
        self.current_conn_settings['auto_dns'] = is_auto_dns

        self.current_conn_settings['dns_servers'] = []
        if not is_auto_dns:
            primary_dns = self.primary_dns_entry.get_text()
            if len(primary_dns) > 0:
                self.current_conn_settings['dns_servers'].append(primary_dns)

            secondary_dns = self.secondary_dns_entry.get_text()
            if len(secondary_dns) > 0:
                self.current_conn_settings['dns_servers'].append(secondary_dns)

        self.current_conn_settings['domains'] = self.dns_suffix_entry.get_text().rsplit(',')

        # Only write changes to GConf if necessary
        if self.current_conn_settings['origin'] == 'networkmanager':
            need_write_gconf = False
        else:
            need_write_gconf = True
        self._conn_settings_manager.add_wwan_connection(self.current_conn_settings, must_write_gconf=need_write_gconf)

    def _create_data_model(self):
        # If editing an existing connection profile, a referente to its
        # ConnectionSettings is necessary
        self.current_conn_settings = None

        # Some scaffolding for 'More' proxy options
        self._more_proxy_data = {}
        self._more_proxy_data['proxy_same_proxy'] = True
        self._more_proxy_data['proxy_ip'] = ''
        self._more_proxy_data['proxy_https_ip'] = ''
        self._more_proxy_data['proxy_ftp_ip'] = ''
        self._more_proxy_data['proxy_socks_ip'] = ''
        self._more_proxy_data['proxy_port'] = 80
        self._more_proxy_data['proxy_https_port'] = 443
        self._more_proxy_data['proxy_ftp_port'] = 21
        self._more_proxy_data['proxy_socks_port'] = 1
        self._more_proxy_data['proxy_ignore'] = []

    def _enable_password_area(self):
        is_enabled = not self.ask_password_checkbutton.get_active()
        self.password_entry.set_sensitive(is_enabled)

    def _enable_proxy_area(self):
        is_use_proxy = self.use_proxy_radiobutton.get_active()
        self.proxy_alignment.set_sensitive(is_use_proxy)

    def _enable_dns_area(self):
        is_user_dns = self.dns_user_radiobutton.get_active()
        self.dns_info_area.set_sensitive(is_user_dns)

    ### UI Callbacks ###

    def _on_dialog_response(self, dialog, response, *args):
        # Only check values if response is gtk.RESPONSE_ACCEPT
        if response == gtk.RESPONSE_ACCEPT:
            is_closeable = self._check_values()

            # The idea is to avoid closing the dialog until all the dialog fields
            # are correct and have been saved properly
            if is_closeable:
                self._save_current_connection_settings()
                self.hide()
        else:
            self.hide()

    def _on_dialog_close(self, dialog, widget=None, event=None):
        # Avoid the dialog to be closed except explicitly requested
        return gtk.TRUE

    def _on_proxy_more_activated(self, widget, data=None):
        proxy_name = self.proxy_address_entry.get_text()
        proxy_port = self.proxy_port_entry.get_value()
        self._more_proxy_data['proxy_ip'] = proxy_name
        self._more_proxy_data['proxy_port'] = proxy_port

        proxy_dialog = ProxyOptionsDialog(self, self._more_proxy_data)
        response = proxy_dialog.run()
        if response == gtk.RESPONSE_ACCEPT:
            proxy_name = self._more_proxy_data['proxy_ip']
            proxy_port = self._more_proxy_data['proxy_port']
            self.proxy_address_entry.set_text(proxy_name)
            self.proxy_port_entry.set_value(proxy_port)
        proxy_dialog.destroy()

    def _on_ask_password_toggled(self, widget, data=None):
        self._enable_password_area()

    def _on_use_proxy_radiobutton_toggled(self, widget, data=None):
        self._enable_proxy_area()

    def _on_dns_user_radiobutton_toggled(self, widget, data=None):
        self._enable_dns_area()


class ProxyOptionsDialog(gtk.Dialog):
    def __init__(self, parent, proxy_data):

        gtk.Dialog.__init__(self, _('Proxy settings'), parent, \
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, \
                 gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

        self.set_border_width(6)

        self.windows_dir = os.path.join(tgcm.windows_dir, 'ConnectionDialog')
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'ConnectionDialog_proxy.ui'), \
                prefix='conn')

        self.proxy_editor_vbox.show()
        self.vbox.pack_start(self.proxy_editor_vbox)

        # Load proxy values
        self._load_proxy_data(proxy_data)
        self._enable_proxy_widgets()

        ### Signals

        # Avoid dialog to close events
        self.connect('response', self._on_dialog_response)
        self.connect('close', self._on_dialog_close)
        self.connect('delete_event', self._on_dialog_close)

        # Widget events
        self.proxy_same_proxy_checkbutton.connect('toggled', self._on_same_proxy_toggled)

    def _load_proxy_data(self, proxy_data):
        self._proxy_data = proxy_data

        is_same_proxy = proxy_data['proxy_same_proxy']
        self.proxy_same_proxy_checkbutton.set_active(is_same_proxy)

        self.proxy_http_entry.set_text(proxy_data['proxy_ip'])
        self.proxy_https_entry.set_text(proxy_data['proxy_https_ip'])
        self.proxy_ftp_entry.set_text(proxy_data['proxy_ftp_ip'])
        self.proxy_socks_entry.set_text(proxy_data['proxy_socks_ip'])

        self.proxy_http_spinbutton.set_value(proxy_data['proxy_port'])
        self.proxy_https_spinbutton.set_value(proxy_data['proxy_https_port'])
        self.proxy_ftp_spinbutton.set_value(proxy_data['proxy_ftp_port'])
        self.proxy_socks_spinbutton.set_value(proxy_data['proxy_socks_port'])

        ignored_hosts = ','.join(proxy_data['proxy_ignore'])
        self.proxy_ignore_entry.set_text(ignored_hosts)

    def _save_proxy_data(self):
        is_same_proxy = self.proxy_same_proxy_checkbutton.get_active()
        self._proxy_data['proxy_same_proxy'] = is_same_proxy

        self._proxy_data['proxy_ip'] = self.proxy_http_entry.get_text()
        self._proxy_data['proxy_https_ip'] = self.proxy_https_entry.get_text()
        self._proxy_data['proxy_ftp_ip'] = self.proxy_ftp_entry.get_text()
        self._proxy_data['proxy_socks_ip'] = self.proxy_socks_entry.get_text()

        self._proxy_data['proxy_port'] = int(self.proxy_http_spinbutton.get_value())
        self._proxy_data['proxy_https_port'] = int(self.proxy_https_spinbutton.get_value())
        self._proxy_data['proxy_ftp_port'] = int(self.proxy_ftp_spinbutton.get_value())
        self._proxy_data['proxy_socks_port'] = int(self.proxy_socks_spinbutton.get_value())

        self._proxy_data['proxy_ignore'] = []
        ignored_hosts = self.proxy_ignore_entry.get_text()
        for host in ignored_hosts.split(','):
            host = host.strip()
            if len(host) > 0:
                self._proxy_data['proxy_ignore'].append(host)

        return self._proxy_data

    def _enable_proxy_widgets(self):
        widgets = (self.proxy_http_entry, self.proxy_https_entry, \
                self.proxy_ftp_entry, self.proxy_socks_entry, \
                self.proxy_http_spinbutton, self.proxy_https_spinbutton, \
                self.proxy_ftp_spinbutton, self.proxy_socks_spinbutton)

        is_same_proxy = self.proxy_same_proxy_checkbutton.get_active()
        for widget in widgets:
            widget.set_sensitive(not is_same_proxy)

        if is_same_proxy:
            proxy_name = self.proxy_http_entry.get_text()
            proxy_port = self.proxy_http_spinbutton.get_value()
            self._set_same_proxy(proxy_name, proxy_port)

    def _set_same_proxy(self, proxy_name, proxy_port):
        widgets = (self.proxy_http_entry, self.proxy_https_entry, \
                self.proxy_ftp_entry, self.proxy_socks_entry)
        for widget in widgets:
            widget.set_text(proxy_name)

        widgets = (self.proxy_http_spinbutton, self.proxy_https_spinbutton, \
                self.proxy_ftp_spinbutton, self.proxy_socks_spinbutton)
        for widget in widgets:
            widget.set_value(proxy_port)

    ### UI Callbacks ###

    def _on_dialog_response(self, dialog, response, *args):
        # Only save dialog values if response is gtk.RESPONSE_ACCEPT
        if response == gtk.RESPONSE_ACCEPT:
            # That is a good place to verify dialog values
            self._save_proxy_data()
            self.hide()
        else:
            self.hide()

    def _on_dialog_close(self, dialog, widget=None, event=None):
        # Avoid the dialog to be closed except explicitly requested
        return gtk.TRUE

    def _on_same_proxy_toggled(self, widget, data=None):
        self._enable_proxy_widgets()


if __name__ == '__main__':
    conn_dialog = ConnectionDialog()
    conn_dialog.run()
    conn_dialog.destroy()
