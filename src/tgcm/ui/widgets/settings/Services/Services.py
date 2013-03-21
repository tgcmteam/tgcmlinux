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

import os

import gtk

import tgcm
import tgcm.core.Config
import tgcm.core.XMLTheme

from tgcm.ui.MSD.MSDUtils import Validate, ValidationError, \
    gtk_builder_magic, error_dialog, replace_wrap_label

class Services (gtk.HBox):
    def __init__(self, settings):
        gtk.HBox.__init__(self)

        self._settings = settings
        self._parent = self._settings.get_dialog()

        self.conf = tgcm.core.Config.Config()
        self.actions_manager = tgcm.core.Actions.ActionManager()
        self.actions_manager.connect ('action-install-status-changed', self.__on_action_install_status_changed)
        self.actions_manager.connect ('url-launcher-install-status-changed', self.__on_url_launcher_install_status_changed)

        self._theme_manager = tgcm.core.Theme.ThemeManager()
        self._xml_theme_manager = tgcm.core.XMLTheme.XMLTheme()

        self.original_services_order = self.actions_manager.get_original_services_order()
        self.actions = self.actions_manager.get_actions ()
        self.actions_data = {}
        self.url_launchers_data = {}

        self.widget_dir = os.path.join(tgcm.widgets_dir , 'settings', self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'Services.ui'), \
                prefix='svc')

        # -- Replace wrapping labels
        self.auth_top_info_label  = replace_wrap_label(self.auth_top_info_label)
        self.new_users_info_label = replace_wrap_label(self.new_users_info_label)
        self.new_users_info_label2 = replace_wrap_label(self.new_users_info_label2)

        self.__init_action_panel ()

        if tgcm.country_support == "es":
            self.auth_on_radio_button.connect("toggled", self.__on_auth_on_radio_button_toggled, None)
            self.ask_password_check_button.connect("toggled", self.__on_ask_password_check_button_toggled, None)
            self._settings.connect('is-closing', self.__on_settings_closing)

            self.__load_user_data ()

            self.main_notebook.set_show_tabs (True)
        else:
            self.main_notebook.set_current_page (0)
            self.main_notebook.set_show_tabs (False)
            self.main_notebook.set_show_border(False)
            self.services_box.set_border_width(0)

        self.add (self.main_vbox)

        self.show_all()

    def __init_action_panel (self):
        children = self.services_scrolledwindow.get_children()
        for child in children:
            self.services_scrolledwindow.remove (child)
            child.destroy()

        self.main_table = gtk.Table (len(self.actions), 3, False)
        self.main_table.set_border_width (15)
        self.main_table.set_col_spacings (25)
        self.main_table.set_row_spacings (15)

        row = 0
        for service in self.original_services_order:
            service_type, service_id = service.split(",")

            if service_type == "service":
                action_obj = self.actions_manager.get_action(service_id)
                image = action_obj.get_dock_button_icon()
                label = gtk.Label (action_obj.get_visible_action_name())
                label.set_alignment(0, 0.5)
                button = gtk.Button ()
                if action_obj.is_installed ():
                    button.set_label (_("Uninstall service"))
                else:
                    button.set_label (_("Install service"))
                if self.conf.check_policy ('install-services') == True:
                    button.connect ("clicked", self.__on_install_service_button_clicked, action_obj)
                else:
                    button.set_sensitive(False)

                self.actions_data[action_obj] = (image, label, button)

                self.main_table.attach (image, 0, 1, row, row+1, xoptions=0, yoptions=0)
                self.main_table.attach (label, 1, 2, row, row+1, xoptions=gtk.FILL, yoptions=0)
                self.main_table.attach (button, 2, 3, row, row+1, xoptions=gtk.FILL, yoptions=0)

                row = row + 1
            elif service_type == "url-launcher":
                url, caption, installed = self.conf.get_url_launcher (service_id)

                pixbuf = self._xml_theme_manager.get_pixbuf(service_id)
                image = gtk.image_new_from_pixbuf(pixbuf)
                label = gtk.Label (caption)
                label.set_alignment(0, 0.5)
                button = gtk.Button ()
                if installed:
                    button.set_label (_("Uninstall service"))
                else:
                    button.set_label (_("Install service"))
                if self.conf.check_policy ('install-services') == True:
                    button.connect ("clicked", self.__on_install_url_launcher_button_clicked, service_id)
                else:
                    button.set_sensitive(False)

                self.url_launchers_data[service_id] = (image, label, button)

                self.main_table.attach (image, 0, 1, row, row+1, xoptions=0, yoptions=0)
                self.main_table.attach (label, 1, 2, row, row+1, xoptions=gtk.FILL, yoptions=0)
                self.main_table.attach (button, 2, 3, row, row+1, xoptions=gtk.FILL, yoptions=0)

                row = row + 1

        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        viewport.add(self.main_table)
        self.services_scrolledwindow.add(viewport)
        self.services_scrolledwindow.show_all()

    def __load_user_data (self):
        cell_info = self.conf.get_celular_info()
        if cell_info[0] != None:
            self.cell_number_entry.set_text(cell_info[0])
        if cell_info[1] != None:
            self.cell_password_entry.set_text(cell_info[1])

        ask_password = self.conf.get_ask_password_activate()

        self.ask_password_check_button.set_active(ask_password)
        self.cell_password_entry.set_sensitive(not ask_password)

        if self.conf.get_auth_activate() == True:
            self.auth_on_radio_button.set_active(True)
        else:
            self.auth_off_radio_button.set_active(True)
            self.cell_password_entry.set_sensitive(False)

    def __on_auth_on_radio_button_toggled (self, widget, data=None):
        if self.auth_on_radio_button.get_active() == True:
            self.cell_number_entry.set_sensitive(True)
            self.cell_password_entry.set_sensitive(True)
            self.ask_password_check_button.set_sensitive(True)
            self.conf.set_auth_activate(True)
        else:
            self.cell_number_entry.set_sensitive(False)
            self.cell_password_entry.set_sensitive(False)
            self.ask_password_check_button.set_sensitive(False)
            self.conf.set_auth_activate(False)

    def __on_ask_password_check_button_toggled (self, widget, data=None):
        if self.ask_password_check_button.get_active() == True:
            self.conf.set_ask_password_activate(True)
            self.cell_password_entry.set_sensitive(False)
        else:
            self.conf.set_ask_password_activate(False)
            self.cell_password_entry.set_sensitive(True)

    def __on_settings_closing(self, settings):
        try:
            number = self.cell_number_entry.get_text()
            if len(number) != 0:
                number = Validate.Spain.mobile_phone(number)
        except ValidationError, err:
            error_dialog(str(err), markup = _('Services - User details'), parent = self._parent)
            return True

        passwd = self.cell_password_entry.get_text()
        self.conf.set_celular_info(number, passwd)
        return False

    def __on_install_service_button_clicked (self, widget, action_obj):
        if action_obj.is_installed ():
            action_obj.remove_service ()
        else:
            action_obj.install_service ()

    def __on_install_url_launcher_button_clicked (self, widget, url_launcher):
        url, caption, installed = self.conf.get_url_launcher (url_launcher)
        if installed:
            message = _("Do you want to uninstall the service '%s'?") % caption
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK_CANCEL, message_format=message)
            window_icon_path = self._theme_manager.get_icon ('icons', 'settings_taskbar.png')
            dlg.set_transient_for(self._parent)
            dlg.set_icon_from_file(window_icon_path)
            dlg.set_title(_("Uninstall service"))
            dlg.format_secondary_markup(_("You will be able to install it again from this configuration window."))
            ret = dlg.run()

            if ret == gtk.RESPONSE_OK :
                self.actions_manager.set_url_launcher_installed (url_launcher, False)

            dlg.destroy()
        else:
            self.actions_manager.set_url_launcher_installed (url_launcher, True)

    def __on_action_install_status_changed (self, action_manager, action_obj, installed, data=None):
        self.__init_action_panel ()

    def __on_url_launcher_install_status_changed (self, action_manager, url_launcher_id, installed, data=None):
        image, label, button = self.url_launchers_data[url_launcher_id]
        if installed:
            button.set_label (_("Uninstall service"))
        else:
            button.set_label (_("Install service"))
