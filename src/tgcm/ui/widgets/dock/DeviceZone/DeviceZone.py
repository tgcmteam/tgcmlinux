#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2003-2012, Telefónica Móviles España S.A.U.
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

import gobject

import tgcm.core.ConnectionLogger
import tgcm.core.FreeDesktop
import tgcm.ui.widgets.dock

from tgcm.core.DeviceManager import DEVICE_MODEM
from tgcm.ui.MSD.MSDUtils import normalize_strength, error_dialog

from MobileManager.MobileStatus import CARD_STATUS_READY, \
    CARD_STATUS_ATTACHING, CARD_STATUS_NO_SIM, CARD_STATUS_PH_NET_PIN_REQUIRED


class DeviceZone (gobject.GObject):

    __gsignals__ = {
        'active_device_changed':        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN, gobject.TYPE_STRING,)),
        'active_device_info_changed':   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'active_device_signal_changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'active_device_tech_changed':   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'roaming_state_changed':        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
        'carrier_changed':              (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'supported_device_added':       (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'supported_device_removed':     (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'supported_device_detected':    (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'supported_device_ready':       (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.at_options_button = tgcm.ui.widgets.dock.DeviceMenuPopup()

        #Internal tooltip info
        self.__t_signal_strength = None
        self.__t_network_tech = None
        self.__t_carrier = None
        self.__t_pin_act = False
        self.__t_roaming = False

        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.connection_logger = tgcm.core.ConnectionLogger.ConnectionLogger()
        self.main_modem = self.device_manager.main_modem

        self.device_manager.connect("active-dev-signal-status-changed", self.__active_dev_signal_status_changed_cb)
        self.device_manager.connect("active-dev-card-status-changed", self.__active_device_card_status_changed_cb)
        self.device_manager.connect("active-dev-carrier-changed", self.__active_dev_carrier_changed_cb)
        self.device_manager.connect("active-dev-tech-status-changed", self.__active_dev_tech_status_changed_cb)
        self.device_manager.connect("active-dev-roaming-status-changed", self.__active_dev_roaming_status_changed_cb)
        self.device_manager.connect("active-dev-pin-act-status-changed", self.__active_dev_pin_act_status_changed_cb)
        self.device_manager.connect("device-added", self.__device_added_cb)
        #self.device_manager.connect ("device-removed", self.__device_removed_cb)
        self.device_manager.connect("main-device-fatal-error", self.__main_modem_fatal_error)

        self.main_modem.connect("main-modem-changed", self.__main_device_changed_cb)
        self.main_modem.connect("main-modem-removed", self.__main_modem_removed_cb)

        self.__strength_strings = [
            _('Very low'),
            _('Low'),
            _('Good'),
            _('Very good'),
            _('Excellent'),
        ]

        self.__init_device()

        self.__update_selected_device()
        self.__update_device_info()
        pass

    def __init_device(self):
        device = self.main_modem.current_device()

        if device is not None:
            device.turn_on()
            self.device_manager.set_main_device(device)

    def __update_selected_device(self):
        device = self.main_modem.current_device()

        if device == None:
            self.emit('active_device_changed', False, _('No device'))
        else:
            self.emit('active_device_changed', True, device.get_prettyname())

    def __active_dev_signal_status_changed_cb(self, mcontroller, signal):
        self.__t_signal_strength = normalize_strength(signal, use_nm_levels=True)
        self.__update_device_info()

        self.connection_logger.register_wwan_signal_change(signal)
        self.emit('active_device_signal_changed', signal)

    def __main_device_changed_cb(self, main_modem, device_manager, dev):
        self.__update_selected_device()
        #self.__reset_tooltip_info()
        self.__update_device_info()
        self.__check_roaming()

    def __active_device_card_status_changed_cb(self, mcontroller, status):
        if status == CARD_STATUS_READY:
            self.emit('supported_device_ready')
            self.__main_device_changed_cb(mcontroller.main_modem, mcontroller, None)
        elif status == CARD_STATUS_ATTACHING:
            device = self.main_modem.current_device()
            self.emit('active_device_changed', True, device.get_prettyname())
            self.emit('supported_device_detected')
        elif status == CARD_STATUS_NO_SIM:
            self.emit('active_device_changed', False, _('No valid SIM'))
        elif status == CARD_STATUS_PH_NET_PIN_REQUIRED:
            device = self.main_modem.current_device()
            self.emit('active_device_changed', True, device.get_prettyname())
        else:
            device = self.main_modem.current_device()
            self.emit('active_device_changed', False, device.get_prettyname())
            self.__update_device_info()

    def __active_dev_tech_status_changed_cb(self, mcontroller, tech):
        self.__t_network_tech = tgcm.core.FreeDesktop.DeviceManager.get_technology_string(tech)
        self.__update_device_info()

        self.connection_logger.register_wwan_technology_change(self.__t_network_tech)
        self.emit('active_device_tech_changed', self.__t_network_tech)

    def __active_dev_roaming_status_changed_cb(self, mcontroller, roaming):
        self.__check_roaming()

    def __active_dev_pin_act_status_changed_cb(self, mcontroller, status):
        self.__t_pin_act = status
        self.__update_selected_device()
        self.__update_device_info()
        self.__check_roaming()

    def __device_added_cb(self, mcontroller, dev):
        self.emit('supported_device_added', dev)

    def __main_modem_removed_cb(self, main_modem, opath):
        self.connection_logger.register_remove_device(main_modem)
        self.emit('active_device_changed', False, _('No device'))
        self.emit('supported_device_removed', opath)
        self.__update_device_info()

    def __main_modem_fatal_error(self, device_manager):
        title = _("Mobile Internet Device connection failed")
        markup = _("Please remove the Mobile Internet Device and connect again")
        msg = _("The connection with the Mobile Internet Device has failed. It is not possible to establish a new connection until the device is removed and inserted again.")
        error_dialog(msg, markup='<b>%s</b>' % markup, title=title)

    def __active_dev_carrier_changed_cb(self, mcontroller, carrier_name):
        self.__t_carrier = carrier_name
        self.__update_device_info()
        self.__check_roaming()

        self.connection_logger.register_wwan_carrier_change(carrier_name)
        self.emit('carrier_changed', carrier_name)

    def __check_roaming(self):
        odev = self.main_modem.current_device()
        if odev != None and odev.get_type() == DEVICE_MODEM:
                roaming = odev.is_roaming()
        else:
            roaming = False

        if roaming != self.__t_roaming:
            self.__t_roaming = roaming
            self.emit('roaming_state_changed', roaming)

    def show_device_menu(self, event=None):
        device = self.main_modem.current_device()
        if device is None:
            return

        self.at_options_button.popup(event=event)

    def __show_network_info(self, value):
        if value == False:
            self.carrier_label.hide()
            self.tech_label.hide()
            self.image.hide()
        else:
            self.carrier_label.show()
            self.tech_label.show()
            self.image.show()

    def __reset_tooltip_info(self):
        self.__t_signal_strength = None
        self.__t_network_tech = None
        self.__t_carrier = None

    def __update_device_info(self):
        device = self.main_modem.current_device()
        if device == None:
            info_str = _("Device: No device")
            self.__t_carrier = _("Device: No device")
        elif device.get_type() == DEVICE_MODEM:
            if not device.is_on():
                model = device.get_prettyname()
                info_str = _("Device: %s\nDevice turned off") % model
            else:
                ss = "--"
                nt = "--"
                op = "--"
                pin = "--"

                if self.__t_signal_strength != None:
                    ss = self.__strength_strings[self.__t_signal_strength]

                if self.__t_network_tech != None:
                    nt = self.__t_network_tech

                if self.__t_carrier != None:
                    op = self.__t_carrier

                if self.__t_pin_act == True:
                    pin = _("Activate")
                else:
                    pin = _("Deactivate")

                info_str = _("Device: %s\nSignal Strength: %s\nNetwork technology: %s\nOperator: %s\nPIN: %s") % \
                    (device.get_prettyname(), ss, nt, op, pin)
        else:
            info_str = _("Device: %s" % device.get_prettyname())

        self.emit('active_device_info_changed', info_str)

gobject.type_register(DeviceZone)
