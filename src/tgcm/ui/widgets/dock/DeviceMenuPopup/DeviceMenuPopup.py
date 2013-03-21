#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2003-2012, Telefonica Móviles España S.A.U.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import os
import gtk
import gobject

import tgcm
import tgcm.core.DeviceManager
import tgcm.core.FreeDesktop
import tgcm.core.Singleton
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

import MobileManager
from MobileManager.MobileManagerDbus import MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI, \
        MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI, MOBILE_MANAGER_DEVICE_NO_OPTIONS_MENU

class Menu(gobject.GObject):
    __metaclass__ = tgcm.core.Singleton.Singleton

    class _RadioButtonActive():
        def __call__(self, func):
            def newf(self, widget):
                if widget.get_active() is True:
                    func(self, widget)
            return newf

    def __init__(self) :
        gobject.GObject.__init__(self)

        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.main_modem = self.device_manager.main_modem

        self.widget_dir = os.path.join(tgcm.widgets_dir, 'dock', 'DeviceMenuPopup')
        self.dmp_dir = os.path.join(tgcm.widgets_dir, 'dock', 'DeviceMenuPopup')

        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'DeviceMenuPopup.ui'), \
                prefix='dmp')

        self.conf = tgcm.core.Config.Config()

        # Enable or disable the entire menu depending on the availability of a device and the
        # connection status
        self.__update_menu_options_visibility()

        self.__update_device_submenu()
        self.__update_pin_submenu()
        self.__update_technology_submenu()
        self.__update_operator_submenu()

        # Connect the signals related to the widgets
        self.__connect_widget_signals()

        # Connect some device and configuration related signals
        self.__connect_core_signals()

    def popup(self, widget=None, event=None):
        # Only show the menu popup when it is a WWAN device present in the system
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            if not device.has_capability(MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI):
                return False

            if device.has_capability(MOBILE_MANAGER_DEVICE_NO_OPTIONS_MENU):
                return False

            data = widget if widget is not None else self
            evt_button = event.button if event is not None else 0
            evt_time = event.time if event is not None else 0

            self.menu.show()
            self.menu.popup(None, None, None, evt_button, evt_time, data=data)
            return True
        else:
            return False

    def __connect_widget_signals(self):
        self.activate_pin.connect('activate', self.__on_pin_activate)
        self.deactivate_pin.connect('activate', self.__on_pin_deactivate)
        self.change_pin.connect('activate', self.__on_change_pin_activate)
        self.activate_card.connect('activate', self.__on_card_activate)
        self.deactivate_card.connect('activate', self.__on_card_deactivate)

        self._widget_handlers = []
        # -- The manual operator selection must be always available even it's already selected
        signal_id = self.manual_oper.connect("activate", self.__on_oper_activate)
        self._widget_handlers.append((self.manual_oper, signal_id))
        signal_id = self.auto_tech.connect("toggled", self.__on_auto_tech_activate)
        self._widget_handlers.append((self.auto_tech, signal_id))
        signal_id = self.only_utms.connect("toggled", self.__on_only_utms_activate)
        self._widget_handlers.append((self.only_utms, signal_id))
        signal_id = self.only_gprs.connect("toggled", self.__on_only_gprs_activate)
        self._widget_handlers.append((self.only_gprs, signal_id))
        signal_id = self.preferred_utms.connect("toggled", self.__on_preferred_utms_activate)
        self._widget_handlers.append((self.preferred_utms, signal_id))
        signal_id = self.preferred_gprs.connect("toggled", self.__on_preferred_gprs_activate)
        self._widget_handlers.append((self.preferred_gprs, signal_id))

    def __connect_core_signals(self):
        '''
        Connect core signals related to data model and configuration changes
        '''
        self.device_manager.connect("active-dev-pin-act-status-changed", self.__pin_activate_status_changed_cb)
        self.device_manager.connect("active-dev-card-status-changed", self.__card_status_changed_cb)
        self.device_manager.connect("active-dev-mode-status-changed", self.__device_mode_status_changed_cb)
        self.device_manager.connect("active-dev-carrier-changed", self.__carrier_changed_cb)

        self.main_modem.connect('main-modem-changed', self.__main_modem_changed_cb)
        self.main_modem.connect("main-modem-connecting", self.__main_modem_connecting_cb)
        self.main_modem.connect('main-modem-connected', self.__main_modem_connected_cb)
        self.main_modem.connect("main-modem-disconnected", self.__main_modem_disconnected_cb)
        self.main_modem.connect("main-modem-removed", self.__main_modem_removed_cb)

    def __update_menu_options_visibility(self):
        device = self.device_manager.get_main_device()
        is_enabled = (device is not None) and (device.is_on()) and (not device.is_connected()) and \
                ((device.get_card_status() == MobileManager.CARD_STATUS_READY) or \
                 (device.get_card_status() == MobileManager.CARD_STATUS_ATTACHING))

        # Tech options
        self.auto_tech.set_sensitive(is_enabled)
        self.only_utms.set_sensitive(is_enabled)
        self.preferred_utms.set_sensitive(is_enabled)
        self.only_gprs.set_sensitive(is_enabled)
        self.preferred_gprs.set_sensitive(is_enabled)

        # PIN options
        self.activate_pin.set_sensitive(is_enabled)
        self.deactivate_pin.set_sensitive(is_enabled)
        self.change_pin.set_sensitive(is_enabled)

        # Operator options
        self.auto_oper.set_sensitive(is_enabled)
        self.manual_oper.set_sensitive(is_enabled)

    def __update_device_submenu(self):
        device = self.device_manager.get_main_device()
        is_device_enabled = (device is not None) and \
                (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM) and \
                device.is_on()
        if is_device_enabled:
            self.activate_card.hide()
            self.deactivate_card.show()
        else:
            self.activate_card.show()
            self.deactivate_card.hide()

    def __update_pin_submenu(self):
        # The default behavior is to have the PIN active
        is_pin_enabled = True

        device = self.device_manager.get_main_device()
        if (device is not None) and \
                (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM) and \
                (device.get_card_status() == MobileManager.CARD_STATUS_READY):
            is_pin_enabled = device.is_pin_active()

        if is_pin_enabled:
            self.activate_pin.hide()
            self.deactivate_pin.show()
            self.change_pin.show()
        else:
            self.activate_pin.show()
            self.deactivate_pin.hide()
            self.change_pin.hide()

    def __update_operator_submenu(self):
        # The default  behavior is to select the default operator
        is_auto_operator_active = True

        device = self.device_manager.get_main_device()
        if (device is not None) and \
                (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM) and \
                (device.get_card_status() == MobileManager.CARD_STATUS_READY):
            is_auto_operator_active = device.is_carrier_auto()

        self.auto_oper.set_active(is_auto_operator_active)
        self.manual_oper.set_active(not is_auto_operator_active)

    def __update_technology_submenu(self):
        # The default behavior is to select the network technology as auto
        mode = MobileManager.CARD_TECH_SELECTION_AUTO

        device = self.device_manager.get_main_device()
        if (device is not None) and \
                (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM) and \
                (device.get_card_status() == MobileManager.CARD_STATUS_READY):
            mode = device.get_technology()

        # Calculate widget status depending on current network technology
        if mode == MobileManager.CARD_TECH_SELECTION_AUTO:
            self.auto_tech.set_active(True)
        elif mode == MobileManager.CARD_TECH_SELECTION_UMTS:
            self.only_utms.set_active(True)
        elif mode == MobileManager.CARD_TECH_SELECTION_UMTS_PREFERED:
            self.preferred_utms.set_active(True)
        elif mode == MobileManager.CARD_TECH_SELECTION_GPRS:
            self.only_gprs.set_active(True)
        elif mode == MobileManager.CARD_TECH_SELECTION_GRPS_PREFERED:
            self.preferred_gprs.set_active(True)

    def __block_widgets_signals(self):
        for widget, handler_id in self._widget_handlers:
            widget.handler_block(handler_id)

    def __unblock_widgets_signals(self):
        for widget, handler_id in self._widget_handlers:
            widget.handler_unblock(handler_id)

    ### UI callbacks ###

    def __on_pin_activate(self, widget):
        dialog = tgcm.ui.windows.ManagePinDialog()
        dialog.run_activate()

    def __on_pin_deactivate(self, widget):
        dialog = tgcm.ui.windows.ManagePinDialog()
        dialog.run_deactivate()

    def __on_card_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.turn_on()

    def __on_card_deactivate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.turn_off()

    def __on_change_pin_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            pin_status = device.is_pin_active()
            if pin_status == True:
                dialog = tgcm.ui.windows.ChangePinDialog()
                dialog.run()

    def __on_oper_activate(self, widget):
        if self.manual_oper.get_active() is True:
            # -- Always open the carrier selection dialog even it's already selected
            self.__on_manual_oper_activate(self.manual_oper)
        else:
            self.__on_auto_oper_activate(self.auto_oper)

    def __on_manual_oper_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            dialog = tgcm.ui.windows.CarrierDialog()
            res = dialog.run()
            if res == dialog.CARRIER_FAILURE:
                return

            self.__block_widgets_signals()

            if not device.is_attached():
                device.set_carrier_auto_selection()
                self.auto_oper.set_active(True)
                self.manual_oper.set_active(False)

            self.__unblock_widgets_signals()

    def __on_auto_oper_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.set_carrier_auto_selection()

    @_RadioButtonActive()
    def __on_auto_tech_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.set_technology(MobileManager.CARD_TECH_SELECTION_AUTO)

    @_RadioButtonActive()
    def __on_only_utms_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.set_technology(MobileManager.CARD_TECH_SELECTION_UMTS)

    @_RadioButtonActive()
    def __on_preferred_utms_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.set_technology(MobileManager.CARD_TECH_SELECTION_UMTS_PREFERED)

    @_RadioButtonActive()
    def __on_only_gprs_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.set_technology(MobileManager.CARD_TECH_SELECTION_GPRS)

    @_RadioButtonActive()
    def __on_preferred_gprs_activate(self, widget):
        device = self.device_manager.get_main_device()
        if (device is not None) and (device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM):
            device.set_technology(MobileManager.CARD_TECH_SELECTION_GRPS_PREFERED)


    ### Configuration change callbacks ###

    def __pin_activate_status_changed_cb(self, device_manager, status):
        self.__block_widgets_signals()
        self.__update_pin_submenu()
        self.__update_technology_submenu()
        self.__unblock_widgets_signals()

    def __card_status_changed_cb(self, device_manager, status):
        self.__block_widgets_signals()
        self.__update_menu_options_visibility()
        self.__update_device_submenu()
        self.__update_pin_submenu()
        self.__update_technology_submenu()
        self.__update_operator_submenu()
        self.__unblock_widgets_signals()

    def __device_mode_status_changed_cb(self, device_manager, status):
        self.__block_widgets_signals()
        self.__update_menu_options_visibility()
        self.__update_device_submenu()
        self.__update_operator_submenu()
        self.__update_technology_submenu()
        self.__unblock_widgets_signals()

    def __carrier_changed_cb(self, device_manager, op_name):
        self.__block_widgets_signals()
        self.__update_operator_submenu()
        self.__unblock_widgets_signals()


    ### Configuration change callbacks ###

    def __main_modem_changed_cb(self, main_modem, mcontroller, device):
        self.__update_menu_options_visibility()
        self.__update_pin_submenu()
        self.__update_device_submenu()

    def __main_modem_connecting_cb(self, main_modem, dialer):
        self.__update_menu_options_visibility()

    def __main_modem_connected_cb(self, main_modem, mcontroller, device):
        self.__update_menu_options_visibility()

    def __main_modem_disconnected_cb(self, main_modem, dev, objpath):
        self.__update_menu_options_visibility()
        self.__update_device_submenu()

    def __main_modem_removed_cb(self, main_modem, objpath):
        self.__update_menu_options_visibility()
        self.__update_device_submenu()


class DeviceMenuPopup(gtk.Button):
    def __init__(self):
        gtk.Button.__init__(self)

        self.menu = Menu()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.main_modem = self.device_manager.main_modem

        self.connect("event", self.__show_menu_cb)
        self.device_manager.connect("active-dev-card-status-changed", self.__card_status_changed_cb)
        self.main_modem.connect("main-modem-changed", self.__main_device_changed_cb)
        self.main_modem.connect("main-modem-removed", self.__main_modem_removed_cb)

        odev = self.device_manager.get_main_device()

        if odev != None and odev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            if not odev.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) :
                self.set_sensitive(False)
                return
            else:
                if odev.has_capability(MOBILE_MANAGER_DEVICE_NO_OPTIONS_MENU) :
                    self.set_sensitive(False)
                    return

                self.set_sensitive(True)
                state = odev.get_card_status()
                self.__card_status_changed_cb(self.device_manager, state)

    def popup(self, widget=None, event=None):
        self.menu.popup(self, event=event)

    def __show_menu_cb(self, widget, event=None):
        self.menu.popup(self, event=event)

    def __card_status_changed_cb(self, device_mananger, status):
        odev = self.device_manager.get_main_device()
        if odev != None and odev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            if not odev.has_capability(MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI):
                self.set_sensitive(False)
                return

            if odev.has_capability(MOBILE_MANAGER_DEVICE_NO_OPTIONS_MENU) :
                self.set_sensitive(False)
                return False

            self.set_sensitive(True)

        else:
            self.set_sensitive(False)
            return

    def __main_device_changed_cb(self, main_modem, device_manager, device):
        if not device.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) :
            self.set_sensitive(False)
            return
        else:
            if device.has_capability(MOBILE_MANAGER_DEVICE_NO_OPTIONS_MENU) :
                self.set_sensitive(False)
                return

            self.set_sensitive(True)
            state = device.get_card_status()
            self.__card_status_changed_cb(self.device_manager, state)

    def __main_modem_removed_cb(self, main_modem, opath):
        self.set_sensitive(False)

gobject.type_register(Menu)
gobject.type_register(DeviceMenuPopup)
