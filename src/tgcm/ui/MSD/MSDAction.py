#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
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
import webbrowser

import tgcm
import tgcm.core.Theme
import tgcm.core.XMLTheme

import tgcm.ui.MSD
import tgcm.ui.windows
import tgcm.core.ConnectionSettingsManager

from freedesktopnet.networkmanager.networkmanager import NetworkManager
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label


class MSDAction(gobject.GObject):

    __gsignals__ = {
        'install-status-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,))
    }

    def __init__(self, config_key):
        gobject.GObject.__init__(self)

        self.conn_manager = tgcm.core.Connections.ConnectionManager()
        self.connection_settings_manager=tgcm.core.ConnectionSettingsManager.ConnectionSettingsManager()
        self.conf = tgcm.core.Config.Config()
        self._theme_manager = tgcm.core.Theme.ThemeManager()
        self._xml_theme_manager = tgcm.core.XMLTheme.XMLTheme()
        self._parent = tgcm.ui.ThemedDock().get_main_window()

        self.codename = self.__class__.__name__
        self.config_key = config_key

        action_dir = os.path.join(tgcm.actions_data_dir , self.codename)

        self._prefs_builder = gtk_builder_magic(self, \
                filename=os.path.join(action_dir, '%s_prefs.ui' % self.codename), \
                prefix='action')

        self._prefs_frame_builder = gtk_builder_magic(self, \
                filename=os.path.join(tgcm.msd_dir, 'MSDAction_frame.ui'), \
                prefix='pre')

        self.installed_service_label = replace_wrap_label(self.installed_service_label)
        self.uninstalled_service_label = replace_wrap_label(self.uninstalled_service_label)

        self.prefs_main_subcontainer.pack_end(self.connect_container)

        self.progress_dialog = tgcm.ui.MSD.MSDProgressWindow()
        self.progress_dialog.set_show_buttons(False)
        self.timer_id = 0

        self.__toggle_connections_check_button_cb_id = None
        self.__connections_combobox_cb_id = None
        self.__remove_service_button_cb_id = None
        self.__install_service_button_cb_id = None

        self.__check_preferences_interface ()
        self.set_connections_model(self.conn_manager.get_connections_model())
        self.conn_manager.connect ('pre_connections_change', self.__on_pre_connections_change)
        self.conn_manager.connect ('connections_changed', self.__on_connections_changed)
        self.connect_signals ()

    def __on_connections_changed (self, data=None):
        self.connect_signals ()

    def __on_pre_connections_change (self, data=None):
        self.disconnect_signals ()

    def disconnect_signals (self):
        if self.__toggle_connections_check_button_cb_id != None:
            self.manual_connection_check_button.disconnect (self.__toggle_connections_check_button_cb_id)
            self.__toggle_connections_check_button_cb_id = None
        if self.__connections_combobox_cb_id != None:
            self.connections_combobox.disconnect (self.__connections_combobox_cb_id)
            self.__connections_combobox_cb_id = None
        if self.__remove_service_button_cb_id != None:
            self.remove_service_button.disconnect(self.__remove_service_button_cb_id)
            self.__remove_service_button_cb_id = None
        if self.__install_service_button_cb_id != None:
            self.install_service_button.disconnect(self.__install_service_button_cb_id)
            self.__install_service_button_cb_id = None

    def connect_signals(self):
        if self.__toggle_connections_check_button_cb_id != None:
            self.manual_connection_check_button.disconnect (self.__toggle_connections_check_button_cb_id)
        if self.__connections_combobox_cb_id != None:
            self.connections_combobox.disconnect (self.__connections_combobox_cb_id)
        if self.__remove_service_button_cb_id != None:
            self.remove_service_button.disconnect(self.__remove_service_button_cb_id)
        if self.__install_service_button_cb_id != None:
            self.install_service_button.disconnect(self.__install_service_button_cb_id)

        if self._get_conf_key_value("connection") == None or self._get_conf_key_value("connection") == "":
            self.manual_connection_check_button.set_active(False)
            self.connections_combobox.set_active(0)
            self.connections_combobox.set_sensitive(False)
        else:
            self.manual_connection_check_button.set_active(True)
            self.connections_combobox.set_sensitive(True)
            connection_name = self._get_conf_key_value("connection")
            model = self.connections_combobox.get_model()
            tmp_iter = model.get_iter_first()
            self.connections_combobox.set_active(0)
            while tmp_iter != None:
                value = model.get_value(tmp_iter, 1)
                if value == connection_name :
                    self.connections_combobox.set_active_iter(tmp_iter)
                tmp_iter = model.iter_next(tmp_iter)

        self.__toggle_connections_check_button_cb_id = self.manual_connection_check_button.connect("toggled", self.__toggle_connections_check_button_cb, None)
        self.__connections_combobox_cb_id = self.connections_combobox.connect("changed", self.__connections_combobox_cb, None)

        if self.conf.check_policy ('install-services') == True:
            self.__remove_service_button_cb_id = self.remove_service_button.connect("clicked", self.__remove_service_button_cb, None)
            self.__install_service_button_cb_id = self.install_service_button.connect("clicked", self.__install_service_button_cb, None)
        else:
            self.remove_service_button.set_sensitive (False)
            self.install_service_button.set_sensitive (False)

    def __check_preferences_interface (self):
        if self._get_conf_key_value ("installed") == True:
            self.conf_container.show()
            if self._get_conf_key_value ("connection_mandatory"):
                self.connection_vbox.show()
            else:
                self.connection_vbox.hide()
            self.install_service_alignment.hide()
            self.uninstall_service_alignment.show()
            self.installed_service_label.show()
            self.uninstalled_service_label.hide()
            if self._get_conf_key_value("connection") == None or self._get_conf_key_value("connection") == "":
                self.manual_connection_check_button.set_active(False)
                self.connections_combobox.set_sensitive(False)
            else:
                self.manual_connection_check_button.set_active(True)
                self.connections_combobox.set_sensitive(True)
        else:
            self.conf_container.hide()
            self.connection_vbox.hide()
            self.install_service_alignment.show()
            self.uninstall_service_alignment.hide()
            self.installed_service_label.hide()
            self.uninstalled_service_label.show()

    def __progress_dialog_show(self, title, msg):
        settings = tgcm.ui.windows.Settings()
        self.progress_dialog.set_transient_for(settings.get_dialog())
        self.progress_dialog.show(title, msg)

    def install_service (self):
        self.__progress_dialog_show(_("Installing service"), _("Please wait while the service '%s' is being installed.") % self._get_conf_key_value("name"))
        self.timer_id = gobject.timeout_add(2000, self.__progress_timer_cb)
        self.conf_container.show()
        if self._get_conf_key_value ("connection_mandatory"):
            self.connection_vbox.show()
        else:
            self.connection_vbox.hide()
        self.install_service_alignment.hide()
        self.uninstall_service_alignment.show()
        self.conf.set_action_installed (self.config_key)

        self.__check_preferences_interface ()
        self.emit ('install-status-changed', True)

    def remove_service (self):
        mensaje = _("Do you want to uninstall the service '%s'?") % self.get_visible_action_name()
        parent  = tgcm.ui.windows.Settings().get_dialog()

        dlg = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL, message_format=mensaje)
        window_icon_path = self._theme_manager.get_icon ('icons', 'settings_taskbar.png')
        dlg.set_icon_from_file(window_icon_path)
        dlg.set_title(_("Uninstall service"))
        dlg.format_secondary_markup(_("You will be able to install it again from this configuration window."))
        ret = dlg.run()

        if ret == gtk.RESPONSE_OK :
            self.close_action()

            self.__progress_dialog_show(_("Uninstalling service"), _("Please wait while the service '%s' is being uninstalled.") % self._get_conf_key_value("name"))
            self.timer_id = gobject.timeout_add(2000, self.__progress_timer_cb)
            self.conf_container.hide()
            self.connection_vbox.hide()
            self.install_service_alignment.show()
            self.uninstall_service_alignment.hide()
            self.conf.set_action_uninstalled (self.config_key)

            self.__check_preferences_interface ()
            self.emit ('install-status-changed', False)

        dlg.destroy()

    def close_action(self, params=None):
        # Do nothing by default
        pass

    def __toggle_connections_check_button_cb (self, widget, data):
        if self.manual_connection_check_button.get_active() == False:
            self.connections_combobox.set_sensitive(False)
            self._set_conf_key_value("connection", None)
        else:
            self.connections_combobox.set_sensitive(True)
            model = self.connections_combobox.get_model()
            index = self.connections_combobox.get_active()
            try:
                tmp_iter = model.get_iter(index)
            except:
                self.connections_combobox.set_active(0)
                tmp_iter = model.get_iter(0)
            connection = model.get_value(tmp_iter, 1)
            self._set_conf_key_value("connection", connection)

    def __connections_combobox_cb (self, widget, data):
        model = self.connections_combobox.get_model()
        iter = self.connections_combobox.get_active_iter()
        if iter is not None:
            self._set_conf_key_value("connection", model.get_value(iter, 1))

    def __progress_timer_cb (self):
        self.progress_dialog.hide()

    def __remove_service_button_cb (self, widget, data):
        self.remove_service ()

    def __install_service_button_cb(self, widget, data):
        self.install_service ()

    def get_id (self):
        return self._get_conf_key_value('id')

    def is_installed (self):
        return self._get_conf_key_value('installed')

    def get_dock_button_icon(self, uninstall=False):
        pixbuf = self._xml_theme_manager.get_pixbuf(self.config_key)
        return gtk.image_new_from_pixbuf(pixbuf)

    def get_action_conf_widget(self):
        return self.prefs_main_container

    def set_connections_model(self, model):
        cell = gtk.CellRendererText()
        self.connections_combobox.pack_start(cell, True)
        self.connections_combobox.add_attribute(cell, 'text', 1)
        self.connections_combobox.set_model(model)

    def _get_conf_key_value(self, key):
        return self.conf.get_action_key_value(self.config_key, key)

    def _set_conf_key_value(self, key, value):
        self.conf.set_action_key_value(self.config_key, key, value)

    def get_visible_action_name (self):
        return _(self._get_conf_key_value("name"))

    def get_prefs_widget(self, name):
        return self._prefs_builder.get_object(name)

    def get_stats_id(self):
        return self._get_conf_key_value("id")

    def launch(self, MSDConnManager):
        if not self._get_conf_key_value("connection_mandatory") :
            self.launch_action(MSDConnManager)
            return

        conn_name = self._get_conf_key_value("connection")
        if self.manual_connection_check_button.get_active() == False :
            #FIXED : Dialer
            if self.conn_manager.ppp_manager.nmConnectionState() == NetworkManager.State.CONNECTED:
                self.launch_action()
            else:
                MSDConnManager.do_connect_with_smart_connector(action=self)
        else:
            conn_settings=self.connection_settings_manager.get_connection_info_dict(conn_name)
            if MSDConnManager.connect_to_connection(connection_settings=conn_settings, action=self) != 0:
                MSDConnManager.error_on_connection()

    def launch_action (self, MSDConnManager=None):
        webbrowser.open(self._get_conf_key_value("url"))

    def launch_help (self):
        dir_name = os.path.dirname(tgcm.help_uri)
        help_file = os.path.join(dir_name, self._get_conf_key_value("help_url"))
        webbrowser.open(help_file)
