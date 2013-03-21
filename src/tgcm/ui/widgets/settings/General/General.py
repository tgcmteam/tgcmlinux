#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
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
import tgcm.core.Autostart
import tgcm.core.Config
import tgcm.core.FreeDesktop

import tgcm.ui.widgets.dock
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic
from tgcm.ui.widgets.settings.General import MyDetailsCommon, MyDetailsUK

import MobileManager

class General(gtk.HBox):

    def __init__(self, settings):
        gtk.HBox.__init__(self)

        self._settings = settings
        self.conf = tgcm.core.Config.Config()
        self.autostart = tgcm.core.Autostart.Autostart()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.main_modem = self.device_manager.main_modem
        self.news_dialog = None
        self.menu_device = tgcm.ui.widgets.dock.Menu()

        self.widget_dir = os.path.join(tgcm.widgets_dir , 'settings', self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'General.ui'), \
                prefix='gnrl')

        ### General tab page ###

        self.general_tab_label.set_text(self.conf.get_app_name())

        is_autostart = self.autostart.is_enabled()
        self.launch_tgcm_at_startup_checkbutton.set_active(is_autostart)

        if self.conf.get_connect_on_startup():
            self.connect_automatically_checkbutton.set_active(True)
        else:
            self.connect_automatically_checkbutton.set_active(False)

        if self.conf.get_reconnect_on_disconnect():
            self.reconnect_automatically_checkbutton.set_active(True)
        else :
            self.reconnect_automatically_checkbutton.set_active(False)

        if self.conf.get_rss_on_connect():
            self.look_for_updates_checkbutton.set_active(True)
        else:
            self.look_for_updates_checkbutton.set_active(False)

        # Connect the signals related to the widgets of "General" tab
        self.__connect_general_tab_related_signals()

        if not self.conf.is_news_available():
            self.news_frame.hide()

        ### "My details" tab page ###

        if tgcm.country_support == 'es':
            # Load 'es' specific screen into 'My Details' tab
            self.common_area = MyDetailsCommon.MyDetailsCommonArea(self.conf, self.widget_dir, settings)
            self.my_details_area.add(self.common_area.get_area())
#        elif tgcm.country_support == 'uk':
#            # Load 'uk' specific screen into 'My Details' tab
#            self.common_area = MyDetailsUK.MyDetailsUK(self.conf, self.widget_dir)
#            self.my_details_area.add(self.common_area.get_area())
        else:
            self.main_notebook.get_nth_page (1).hide()

        ### SIM tab page ###

        self.__tech_list = (MobileManager.CARD_TECH_SELECTION_UMTS, \
                MobileManager.CARD_TECH_SELECTION_UMTS_PREFERED, \
                MobileManager.CARD_TECH_SELECTION_GPRS, \
                MobileManager.CARD_TECH_SELECTION_GRPS_PREFERED)

        # Enable or disable the entire area depending on the availability of a device and the
        # connection status
        self.__update_sim_tab_visibility()

        # PIN
        self.__update_sim_area()

        # Network technology
        self.__update_network_technology_area()

        # Network operator
        self.__update_operator_area()

        # Connect the signals related to the widget of "Networks and SIM card" tab
        self.__connect_sim_tab_related_signals()

        # Connect some device and configuration related signals
        self.__connect_core_signals()

        self.add(self.main_vbox)

    def show_nth_tab(self, tab_number):
        self.main_notebook.set_current_page(tab_number)

    def __connect_general_tab_related_signals(self):
        '''
        Connect UI signals related to the "General" tab of the form
        '''
        self.launch_tgcm_at_startup_checkbutton.connect("toggled", self.__on_launch_tgcm_at_startup_checkbutton_toggled)
        self.connect_automatically_checkbutton.connect("toggled", self.__on_connect_automatically_checkbutton_toggled)
        self.reconnect_automatically_checkbutton.connect("toggled", self.__on_reconnect_automatically_checkbutton_toggled)
        self.look_for_updates_checkbutton.connect("toggled", self.__on_look_for_updates_checkbutton_toggled)
        self.check_updates_button.connect("clicked", self.__on_check_updates_button_clicked)

    def __connect_sim_tab_related_signals(self):
        '''
        Connect UI signals related to the "Networks and SIM card" tab of the form
        '''
        self._sim_area_handlers = []
        signal_id = self.deactivate_pin_checkbutton.connect("toggled", self.__on_deactivate_pin_checkbutton_toggled)
        self._sim_area_handlers.append((self.deactivate_pin_checkbutton, signal_id))
        signal_id = self.change_pin_button.connect("clicked", self.__on_change_pin_button_clicked)
        self._sim_area_handlers.append((self.change_pin_button, signal_id))
        signal_id = self.automatic_technology_radiobutton.connect("toggled", self.__on_automatic_technology_radiobutton_toggled)
        self._sim_area_handlers.append((self.automatic_technology_radiobutton, signal_id))
        signal_id = self.network_technology_combobox.connect("changed", self.__on_network_technology_combobox_changed)
        self._sim_area_handlers.append((self.network_technology_combobox, signal_id))
        signal_id = self.automatic_operator_radiobutton.connect("toggled", self.__on_automatic_operator_radiobutton_changed)
        self._sim_area_handlers.append((self.automatic_operator_radiobutton, signal_id))
        signal_id = self.select_operators_button.connect("clicked", self.__on_select_operators_button_clicked)
        self._sim_area_handlers.append((self.select_operators_button, signal_id))

    def __connect_core_signals(self):
        '''
        Connect core signals related to data model and configuration changes
        '''
        self.device_manager.connect("active-dev-pin-act-status-changed", self.__pin_activate_status_changed_cb)
        self.device_manager.connect("active-dev-card-status-changed", self.__card_status_changed_cb)
        self.device_manager.connect("active-dev-mode-status-changed", self.__device_mode_status_changed_cb)
        self.device_manager.connect("active-dev-carrier-changed", self.__carrier_changed_cb)

        self.main_modem.connect("main-modem-changed", self.__main_modem_changed_cb)
        self.main_modem.connect("main-modem-connecting", self.__main_modem_connecting_cb)
        self.main_modem.connect("main-modem-connected", self.__main_modem_connected_cb)
        self.main_modem.connect("main-modem-disconnected", self.__main_modem_disconnected_cb)
        self.main_modem.connect("main-modem-removed", self.__main_modem_removed_cb)

        self.autostart.connect("changed", self.__on_autostart_changed_cb)

    def __update_sim_tab_visibility(self):
        device = self.device_manager.get_main_device()
        is_enabled = (device is not None) and (device.is_on()) and \
                (device.get_card_status() == MobileManager.CARD_STATUS_READY) and \
                device.is_disconnected()
        self.sim_area.set_sensitive(is_enabled)

        if device is not None:
            vendor_str = device.vendor()
        else:
            vendor_str = _('No device found')

        self.sim_device_label.set_markup(_("Settings for device: %s") % vendor_str)

    def __update_sim_area(self):
        # The default behavior is to have the PIN enabled
        is_pin_enabled = True

        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_card_status() == MobileManager.CARD_STATUS_READY):
            is_pin_enabled = device.is_pin_active()

        self.deactivate_pin_checkbutton.set_active(not is_pin_enabled)
        self.change_pin_button.set_sensitive(is_pin_enabled)

    def __update_network_technology_area(self):
        # The default behavior is to select the network technology as auto
        is_auto_tech_active = True
        is_manual_tech_sensitive = False
        index_network_tech = 0

        device = self.device_manager.get_main_device()
        if (device is not None) and \
                (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM) and \
                (device.get_card_status() == MobileManager.CARD_STATUS_READY):
            # Calculate widget status depending on current network technology
            mode = device.get_technology()
            if mode == MobileManager.CARD_TECH_SELECTION_AUTO:
                # Considered in the default behavior, it is expressed here explicitly just
                # for clarification
                pass
            elif mode == MobileManager.CARD_TECH_SELECTION_UMTS:
                is_auto_tech_active = False
                is_manual_tech_sensitive = True
                index_network_tech = 0
            elif mode == MobileManager.CARD_TECH_SELECTION_UMTS_PREFERED:
                is_auto_tech_active = False
                is_manual_tech_sensitive = True
                index_network_tech = 1
            elif mode == MobileManager.CARD_TECH_SELECTION_GPRS:
                is_auto_tech_active = False
                is_manual_tech_sensitive = True
                index_network_tech = 2
            elif mode == MobileManager.CARD_TECH_SELECTION_GRPS_PREFERED:
                is_auto_tech_active = False
                is_manual_tech_sensitive = True
                index_network_tech = 3

        self.automatic_technology_radiobutton.set_active(is_auto_tech_active)
        self.manual_technology_radiobutton.set_active(not is_auto_tech_active)
        self.network_technology_combobox.set_sensitive(is_manual_tech_sensitive)
        self.network_technology_combobox.set_active(index_network_tech)

    def __update_operator_area(self):
        # The default  behavior is to select the default operator
        is_auto_operator_active = True

        device = self.device_manager.get_main_device()
        if (device is not None) and \
                (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM) and \
                (device.get_card_status() == MobileManager.CARD_STATUS_READY):
            if device.is_carrier_auto() == False:
                is_auto_operator_active = False

        self.automatic_operator_radiobutton.set_active(is_auto_operator_active)
        self.manual_operator_radiobutton.set_active(not is_auto_operator_active)
        self.select_operators_button.set_sensitive(not is_auto_operator_active)

    def __block_sim_area_handlers(self):
        for widget, handler_id in self._sim_area_handlers :
            widget.handler_block(handler_id)

    def __unblock_sim_area_handlers(self):
        for widget, handler_id in self._sim_area_handlers :
            widget.handler_unblock(handler_id)


    ### UI callbacks ###

    ## Callbacks related to the "General" tab of the form

    def __on_launch_tgcm_at_startup_checkbutton_toggled (self, widget):
        self.autostart.set_enabled(widget.get_active())

    def __on_connect_automatically_checkbutton_toggled (self, widget):
        self.conf.set_connect_on_startup(widget.get_active())

    def __on_reconnect_automatically_checkbutton_toggled(self, widget):
        self.conf.set_reconnect_on_disconnect(widget.get_active())

    def __on_look_for_updates_checkbutton_toggled (self, widget):
        self.conf.set_rss_on_connect(widget.get_active())

    def __on_check_updates_button_clicked (self, widget):
        if self.news_dialog == None :
            self.news_dialog = tgcm.ui.windows.NewsServiceDialog()
        parent = self._settings.get_dialog()
        self.news_dialog.show(parent)


    ## Callbacks related to the "Networks and SIM card" tab of the form

    def __on_deactivate_pin_checkbutton_toggled(self, widget):
        is_new_pin_disabled = self.deactivate_pin_checkbutton.get_active()

        dialog = tgcm.ui.windows.ManagePinDialog(self._settings.get_dialog())
        if is_new_pin_disabled:
            dialog.run_deactivate()
        else:
            dialog.run_activate()

        self.__block_sim_area_handlers()
        self.__update_sim_area()
        self.__unblock_sim_area_handlers()

    def __on_change_pin_button_clicked(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            pin_active = device.is_pin_active()
            if pin_active == None :
                return
            elif pin_active == True:
                dialog = tgcm.ui.windows.ChangePinDialog(self._settings.get_dialog())
                dialog.run()
        else:
            tgcm.error("This device or not exist or not has the capability")

    def __on_automatic_technology_radiobutton_toggled(self, widget):
        is_automatic_tech_enabled = self.automatic_technology_radiobutton.get_active()

        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            if is_automatic_tech_enabled:
                mode = MobileManager.CARD_TECH_SELECTION_AUTO
                is_tech_combobox_enabled = False
            else:
                index = self.network_technology_combobox.get_active()
                mode = self.__tech_list[index]
                is_tech_combobox_enabled = True

            device.set_technology(mode)
            self.network_technology_combobox.set_sensitive(is_tech_combobox_enabled)

    def __on_network_technology_combobox_changed(self, widget):
        is_automatic_tech_enabled = self.automatic_technology_radiobutton.get_active()
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            if not is_automatic_tech_enabled:
                index = self.network_technology_combobox.get_active()
                mode = self.__tech_list[index]
                device.set_technology(mode)

    def __on_automatic_operator_radiobutton_changed(self, widget):
        is_automatic_operator_enabled = self.automatic_operator_radiobutton.get_active()
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            if is_automatic_operator_enabled:
                self.select_operators_button.set_sensitive(False)
                device.set_carrier_auto_selection()
            else:
                self.select_operators_button.set_sensitive(True)

    def __on_select_operators_button_clicked(self, widget):
        dialog = tgcm.ui.windows.CarrierDialog(parent = self._settings.get_dialog())
        res = dialog.run()
        if res == dialog.CARRIER_FAILURE:
            return

        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            if not device.is_attached():
                device.set_carrier_auto_selection()
                self.automatic_operator_radiobutton.set_active(True)
                self.select_operators_button.set_sensitive(False)
            else:
                self.automatic_operator_radiobutton.set_active(False)
                self.select_operators_button.set_sensitive(True)


    ### Configuration change callbacks ###

    def __pin_activate_status_changed_cb(self, mcontroller, status):
        self.__block_sim_area_handlers()
        self.__update_sim_area()
        self.__unblock_sim_area_handlers()

    def __card_status_changed_cb(self, sender, status):
        self.__block_sim_area_handlers()
        self.__update_sim_tab_visibility()
        self.__unblock_sim_area_handlers()

    def __device_mode_status_changed_cb(self, device_manager, status):
        self.__block_sim_area_handlers()
        self.__update_operator_area()
        self.__update_network_technology_area()
        self.__unblock_sim_area_handlers()

    def __carrier_changed_cb(self, device_manager, op_name):
        self.__block_sim_area_handlers()
        self.__update_operator_area()
        self.__unblock_sim_area_handlers()

    def __main_modem_changed_cb(self, main_modem, mcontroller, device):
        self.__block_sim_area_handlers()
        self.__update_sim_tab_visibility()
        self.__update_sim_area()
        self.__update_network_technology_area()
        self.__update_operator_area()
        self.__unblock_sim_area_handlers()

    def __main_modem_connecting_cb(self, main_modem, dialer):
        self.__update_sim_tab_visibility()

    def __main_modem_connected_cb(self, main_modem, dialer, objpath):
        self.__update_sim_tab_visibility()

    def __main_modem_disconnected_cb(self, main_modem, dialer, objpath):
        self.__update_sim_tab_visibility()

    def __main_modem_removed_cb(self, main_modem, objpath):
        self.__update_sim_tab_visibility()

    def __on_autostart_changed_cb(self, autostart, is_enabled):
        self.launch_tgcm_at_startup_checkbutton.set_active(is_enabled)
