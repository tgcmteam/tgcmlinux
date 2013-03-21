#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2003-2013, Telefonica Móviles España S.A.U.
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
import webbrowser

import tgcm.core.Actions
import tgcm.core.FreeDesktop
import tgcm.ui.windows
import tgcm.ui.widgets.themedwidgets
from freedesktopnet.networkmanager.networkmanager import NetworkManager

BUTTON_VISIBLE = 1
BUTTON_VISIBLE_IN_MORE = 2
BUTTON_NOT_VISIBLE = 3


class ServicesToolbar (gtk.HBox):
    def __init__(self, dock, act_manager, conn_manager, services, paddingX=5):
        gtk.HBox.__init__(self)
        self.set_homogeneous (False)
        self.set_spacing (paddingX)

        self.__dock = dock
        self.__act_manager = act_manager
        self.__conn_manager = conn_manager

        self.__services_theme_definition = services

        self.__config = tgcm.core.Config.Config()

        self.__mcontroller = tgcm.core.FreeDesktop.DeviceManager()
        self.__main_modem  = self.__mcontroller.main_modem
        self.__device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.__action_manager = tgcm.core.Actions.ActionManager()

        self.__config.connect('launcher-items-order-changed', self.__on_launcher_items_order_changed)
        self.__config.connect('user-prepay-changed', self.__on_user_prepay_changed)
        self.__config.connect('last-imsi-seen-changed', self.__on_last_imsi_seen_changed)
        self.__action_manager.connect('action-install-status-changed', self.__on_action_install_status_changed)
        self.__action_manager.connect('url-launcher-install-status-changed', self.__on_action_install_status_changed)
        self.__mcontroller.connect("active-dev-card-status-changed", self.__refresh_services)
        self.__mcontroller.connect('active-dev-sms-spool-changed', self.__refresh_services)
        self.__main_modem.connect("main-modem-changed", self.__main_modem_changed_cb)

        self.services = self.__action_manager.get_action_list()

        self.show_all ()

        self.__create_buttons ()
        self.__check_buttons_visibility()

        self.connect("size_allocate", self.__on_size_allocate)

    def get_service_buttons_status(self):
        return self.__element_status

    def resize(self):
        self.__check_buttons_visibility()

    def __create_buttons (self):
        self.buttons = {}
        actions = self.__action_manager.get_actions ()
        dockables = self.__config.get_dockables_list ()
        url_launchers = self.__config.get_url_launchers (only_installed=True)

        for service_definition in self.__services_theme_definition['buttons']:
            if service_definition['id'] in dockables:
                widget = tgcm.ui.widgets.themedwidgets.ThemedServiceButton (service_definition)
                widget.set_title (tgcm.dockables_info [service_definition['id']])
                widget.connect ('clicked', self.__on_service_button_clicked)

                self.buttons[service_definition['id']] = widget

                self.pack_start (widget)

            elif service_definition['id'] in actions:
                service = actions[service_definition['id']]

                widget = tgcm.ui.widgets.themedwidgets.ThemedServiceButton (service_definition)
                widget.set_title (_(service.get_visible_action_name ()))
                widget.connect ('clicked', self.__on_service_button_clicked)

                self.buttons[service_definition['id']] = widget

                self.pack_start (widget)

            elif service_definition['id'] in url_launchers:
                url, caption, installed = self.__config.get_url_launcher (service_definition['id'])

                widget = tgcm.ui.widgets.themedwidgets.ThemedServiceButton (service_definition)
                widget.set_title (caption)
                widget.connect ('clicked', self.__on_url_launcher_button_clicked, url)

                self.buttons[service_definition['id']] = widget

                self.pack_start (widget)

            elif service_definition['id'] == 'btn.moreservices':
                widget = tgcm.ui.widgets.themedwidgets.ThemedServiceButton (service_definition)
                widget.set_title (_("More"))
                widget.set_visible (True)
                widget.connect('event', self.__on_more_button_clicked)

                self.buttons["more"] = widget

                self.pack_start (widget)

        # Reload buttons so they decorations like SMS count is shown
        self.__reload_all()

    def __main_modem_changed_cb(self, main_modem, device_manager, device):
        self.__reload_all()

    def __refresh_services (self, mcontroller, index):
        self.__reload_all ()

    def __reload_all (self):
        self.__check_buttons_visibility()
        self.__reload_sms_button_image()

    def __check_buttons_visibility(self):
        # Calculate available space for services in ServicesToolbar
        dock_width = self.__dock.get_size()[0]
        left_margin = self.__services_theme_definition['left']
        space_available = dock_width - left_margin

        # Reset 'more' button state
        self.__show_more_button = False

        # Hide current buttons
        for button in self.buttons.values():
            button.hide()

        # Determine elements to be shown in ServicesToolbar
        dock_items = self.__config.get_launcher_items_order()

        self.__element_status = {}
        elements_shown = []
        self.__elements_shown_in_more = []

        # Iterate through the elements calculating its size
        for i in range(len(dock_items)):
            elem_key = dock_items[i]

            # Must the item be shown?
            if not self.__must_service_be_visible(elem_key):
                self.__element_status[elem_key] = BUTTON_NOT_VISIBLE
                continue

            # Calculate the width of current element
            elem = self.buttons[elem_key]
            elem_width = elem.width

            # Calculate the width of next element (if possible)
            try:
                button_key = dock_items[i+1]
                button = self.buttons[button_key]
                next_width = button.width
            except IndexError:
                next_width = None

            # Calculate space requested for current element and the next one. If both of them
            # does not fit in ServiceToolbar, the current element wouldn't be shown because
            # its space is necessary for the 'more' button
            if next_width is not None:
                space_requested = elem_width + self.get_spacing() + next_width
            else:
                space_requested = elem_width

            # Do the space requested fit in current available space?
            if space_requested <= space_available:
                elements_shown.append(elem)
                self.__element_status[elem_key] = BUTTON_VISIBLE
            else:
                self.__elements_shown_in_more.append(elem_key)
                self.__element_status[elem_key] = BUTTON_VISIBLE_IN_MORE

            # Update available space in ServicesToolbar
            space_available -= elem_width + self.get_spacing()

        # Display all available items
        for button in elements_shown:
            button.show_all()

        # Do not display all the remaining items
        if len(self.__elements_shown_in_more) > 0:
            self.__show_more_button = True

            self.buttons['more'].show_all()

            for key in self.__elements_shown_in_more:
                button = self.buttons[key]
                button.hide()

        # Schedule the widget to have its size renegotiated
        self.queue_resize()

    def __must_service_be_visible(self, key):
        # Prepay service (DE)
        if key == "prepay" and tgcm.country_support == "de":
            is_shown = False
            try:
                device = self.__mcontroller.get_main_device()
                if (device is not None) and \
                        (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM) and \
                        (not device.is_postpaid()):
                    is_shown = True
            except:
                pass
            return is_shown

        # Prepay service (ES)
        elif key == 'recargasaldo':
            return tgcm.ui.windows.RecargaSaldo.is_visible()

        # Other services are visible by default
        else:
            return True

    def __reload_sms_button_image (self):
        for key, button in self.buttons.items ():
            if key == 'sms':
                action = self.__action_manager.get_action ('sms')
                button.set_alt_text (action.alt_text())
                return

    def __on_service_button_clicked (self, widget, data=None):
        for key, button in self.buttons.items ():
            if button == widget:
                if key in tgcm.dockables_info:
                    self.__launch_dockable (key)
                else:
                    self.__act_manager.launch_action (key)
                return

    def __on_url_launcher_button_clicked (self, widget, url=None):
        if url != None:
            if self.__device_dialer.nmConnectionState() == NetworkManager.State.CONNECTED:
                webbrowser.open(url)
            else:
                #We should pass a bookmark or a MSDaction object to do_connect_with_smart_connector instead of connecting to device_dialer
                self.__url_launcher_connected_id = self.__device_dialer.connect ('connected', self.__on_url_launcher_connected, url)
                self.__conn_manager.do_connect_with_smart_connector()

    def __on_url_launcher_connected (self, dialer, url):
        self.__device_dialer.disconnect (self.__url_launcher_connected_id)
        webbrowser.open(url)

    def __launch_dockable (self, dock_item):
        if dock_item == "help":
            help_dialog = tgcm.ui.windows.HelpDialog ()
            help_dialog.show()
        elif dock_item == "settings":
            settings_dialog = tgcm.ui.windows.Settings()
            settings_dialog.run()
        elif dock_item == "addressbook":
            addressbook_dialog = tgcm.ui.windows.AddressBook ()
            addressbook_dialog.run()
        elif dock_item == 'recargasaldo':
            recargasaldo_dialog = tgcm.ui.windows.RecargaSaldo()
            recargasaldo_dialog.run()

    def __on_more_button_clicked (self, widget, event=None):
        if event.type == gtk.gdk.BUTTON_PRESS:
            actions = self.__action_manager.get_actions ()
            dockables = self.__config.get_dockables_list ()
            url_launchers = self.__config.get_url_launchers (only_installed=True)

            self.actions_menu = gtk.Menu()
            for key in self.__elements_shown_in_more:
                if key in actions:
                    action = actions[key]
                    button = self.buttons[key]

                    menu_item = gtk.ImageMenuItem (button.text)
                    menu_item.connect("activate", self.__on_service_item_activated, action)
                    menu_item.set_image(gtk.image_new_from_pixbuf (button.more_menu_image))
                    self.actions_menu.append (menu_item)
                elif key in dockables:
                    button = self.buttons[key]

                    menu_item = gtk.ImageMenuItem (button.text)
                    menu_item.connect("activate", self.__on_dockable_item_activated, key)
                    menu_item.set_image(gtk.image_new_from_pixbuf (button.more_menu_image))
                    self.actions_menu.append (menu_item)
                elif key in url_launchers:
                    url, caption, installed = self.__config.get_url_launcher (key)
                    button = self.buttons[key]

                    menu_item = gtk.ImageMenuItem (caption)
                    menu_item.connect("activate", self.__on_url_launcher_item_activated, url)
                    menu_item.set_image(gtk.image_new_from_pixbuf (button.more_menu_image))
                    self.actions_menu.append (menu_item)

            self.actions_menu.show_all()
            self.actions_menu.popup(None, None, None, event.button, event.time)

            return True
        else:
            return False

    def __on_service_item_activated (self, widget, action):
        self.__act_manager.launch_action (action.config_key)

    def __on_dockable_item_activated (self, widget, action):
        self.__launch_dockable (action)

    def __on_url_launcher_item_activated (self, widget, url):
        self.__on_url_launcher_button_clicked (widget, url)

    def __on_launcher_items_order_changed (self, data=None):
        self.__reload_all ()

    def __on_user_prepay_changed(self, sender, is_prepay):
        self.__reload_all()

    def __on_last_imsi_seen_changed(self, sender, imsi):
        self.__reload_all()

    def __on_action_install_status_changed (self, action_manager, action_obj, installed, data=None):
        self.__reload_all ()

    def __on_size_allocate (self, widget, allocation, params=None):
        services_left = allocation.x
        services_top = allocation.y
        paddingX = self.get_spacing ()
        i = 0

        for service in self.__config.get_launcher_items_order ():
            if service not in self.buttons:
                continue

            service_button = self.buttons [service]
            if service_button.get_property ("visible"):
                service_button.size_allocate (gtk.gdk.Rectangle (services_left + i, services_top, service_button.width, service_button.height))
                i += paddingX + service_button.width

        if self.__show_more_button:
            service_button = self.buttons ["more"]
            service_button.size_allocate (gtk.gdk.Rectangle (services_left + i, services_top, service_button.width, service_button.height))
