#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
#
# Copyright (c) 2003-2012, Telefonica Móviles España S.A.U.
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
import glib
import gobject
import time

import tgcm
import tgcm.core.Config
import tgcm.core.Connections
import tgcm.core.ConnectionLogger
import tgcm.core.FreeDesktop
from tgcm.core.DeviceExceptions import DeviceHasNotCapability

from freedesktopnet.networkmanager.networkmanager import NetworkManager

import tgcm.ui.MSD
import tgcm.ui.windows
from tgcm.ui.MSD.MSDUtils import error_dialog

from MobileManager import CARD_STATUS_ERROR, \
    CARD_STATUS_NO_DETECTED, CARD_STATUS_DETECTED, CARD_STATUS_CONFIGURED, \
    CARD_STATUS_NO_SIM, CARD_STATUS_PIN_REQUIRED, CARD_STATUS_PUK_REQUIRED, \
    CARD_STATUS_OFF, CARD_STATUS_ATTACHING, CARD_STATUS_READY, \
    CARD_STATUS_PH_NET_PIN_REQUIRED, CARD_STATUS_PH_NET_PUK_REQUIRED, \
    PIN_STATUS_WAITING_PIN, PIN_STATUS_WAITING_PUK

STARTUP_SECS = 20


class DevicePolicy:

    def __init__(self):
        self._config = tgcm.core.Config.Config(tgcm.country_support)
        self._device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self._connection_manager = tgcm.core.Connections.ConnectionManager()
        self._connection_logger = tgcm.core.ConnectionLogger.ConnectionLogger()

        self.__devtable = None
        self.__popup = None
        self.__candidate_modem = None
        self.is_showing_no_sim_dialog = False
        self._is_on_startup = False
        self.startup_time = time.time()

        # -- This is the data for detecting a new modem on the system
        self._main_modem = self._device_manager.main_modem
        self._main_modem.connect("main-modem-candidate-added", self.__main_modem_candidate_added_cb)
        self._main_modem.connect("main-modem-candidate-removed", self.__main_modem_candidate_removed_cb)

        # Listen for card status changes
        self.hander_status = self._device_manager.connect( \
            "active-dev-card-status-changed", self.__active_device_card_status_changed)
        self._device_manager.connect( \
            "active-dev-card-status-changed", self.__save_imsi_preferred_cb)

        if self._main_modem.candidate() is not None:
            self.__main_modem_candidate_added_cb(self._main_modem, self._main_modem.candidate())
        else:
            gobject.timeout_add(500, self._connect_on_startup)

    def _connect_on_startup(self):
        if self._config.get_connect_on_startup():
            if self.device_dialer.nmConnectionState() == NetworkManager.State.DISCONNECTED:
                tgcm.info("Trying to connect on startup...")
                MSDConnManager = tgcm.ui.MSD.MSDConnectionsManager()
                MSDConnManager.do_connect_with_smart_connector()

    def __active_device_card_status_changed(self, mcontroller, status):
        device = self._device_manager.get_main_device()

        if status == CARD_STATUS_DETECTED:
            pass

        elif status == CARD_STATUS_CONFIGURED:
            pass

        elif (status == CARD_STATUS_NO_SIM) or (status == CARD_STATUS_ERROR):
            self._connection_logger.register_invalid_imsi()

            self._is_on_startup = False
            self.startup_time = 0
            if self.is_showing_no_sim_dialog == True:
                return

            self.is_showing_no_sim_dialog = True

            # -- Turn the device off before opening the error dialog otherwise the device checker remains triggering
            # -- AT commands to the Mobile Manager
            if device is not None:
                device.turn_off()

            msg = _("The Internet Mobile Device does not have a valid SIM card. Please, check that the SIM card is correctly inserted in the Internet Mobile Device.")
            markup = _("<b>SIM not found</b>")
            error_dialog(msg, markup)

            self.is_showing_no_sim_dialog = False

        elif status == CARD_STATUS_PIN_REQUIRED:
            if  (time.time() - self.startup_time) < STARTUP_SECS:
                self._is_on_startup = True

            rstatus = device.pin_status()
            device.stop_checker()
            self._device_manager.emit("active-dev-pin-act-status-changed",True)

            if rstatus != PIN_STATUS_WAITING_PIN:
                tgcm.info("PIN REQUIRED ... not")
                return

            pin_dialog = tgcm.ui.windows.AskPinDialog()
            pin_dialog.run()

        elif status == CARD_STATUS_PUK_REQUIRED:
            if (time.time() - self.startup_time) < STARTUP_SECS:
                self._is_on_startup = True

            tgcm.info("PUK REQUIRED")
            if device.is_on() == False:
                return

            rstatus = device.pin_status()
            device.stop_checker()
            if rstatus != PIN_STATUS_WAITING_PUK:
                tgcm.info("PUK REQUIRED ... not")
                return

            self._device_manager.emit("active-dev-pin-act-status-changed", True)

            ask_puk = tgcm.ui.windows.PukDialog()
            ask_puk.request()

        elif status == CARD_STATUS_OFF:
            self._is_on_startup = False
            self.startup_time = 0

        elif status == CARD_STATUS_ATTACHING:
            # Check if device is not network locked for this card
            if device.is_operator_locked():
                # Prompt the user to remove the network lock
                self.__ask_network_pin_code(device)

        elif status == CARD_STATUS_READY:
            # Register the device in the connection log
            self._connection_logger.register_new_device(device)

            try:
                self._device_manager.emit("active-dev-roaming-status-changed", device.is_roaming())
                self._device_manager.emit("active-dev-pin-act-status-changed", device.is_pin_active())

                # Check if the IMSI has been blacklisted
                is_imsi_allowed = self.__is_imsi_allowed(device)

                # NOTE:
                # Originally the following code was used to ensure that the device was registered
                # in the network with the values established by the operator in the file
                # 'regional-info.xml':
                #
                # if dev.has_domain_preferred:
                #    gobject.timeout_add(3000, self.__set_current_mode_domain)
                #
                # Unfortunately we don't know the reason why the function '__set_current_mode_domain'
                # was being called with a delay of 3 seconds. Calling it directly seems to work
                # well.
                if is_imsi_allowed:

                    # Attempt to establish the correct device mode and domain
                    self.__set_current_mode_domain(device)

                    # Unknown connection procedure
                    if ((time.time() - self.startup_time) < STARTUP_SECS) \
                            or self._is_on_startup:
                        self._is_on_startup = False
                        self.startup_time = 0
                        self._connect_on_startup()
            except DeviceHasNotCapability:
                pass

        elif status == CARD_STATUS_PH_NET_PIN_REQUIRED:
            self.__ask_network_pin_code(device)

        elif status == CARD_STATUS_PH_NET_PUK_REQUIRED:
            pass

    def __ask_network_pin_code(self, device):
        unlock_dialog = tgcm.ui.windows.UnlockDeviceDialog(device, turn_off_if_cancel=True)
        unlock_dialog.run()

    def __set_current_mode_domain(self, device, status=None):
        ''' Configures the technology (mode) and domain of the WWAN device to the last
        values established by the user or the operator '''

        if status is None:
            status = device.get_card_status()

        if status == CARD_STATUS_READY:
            mode = self._config.get_last_device_mode()
            domain = self._config.get_last_domain()

            device.set_technology(mode)
            device.set_domain(domain)
            tgcm.info("Set regional info domain preferred")

        return False

    def __save_imsi_preferred_cb(self, mcontroller=None, status=None, device=None):
        if device is None:
            device = self._device_manager.get_main_device()

        self.__register_imsi(device, status)

    def __is_imsi_allowed(self, device, status=None):
        # By default every IMSI is allowed to use TGCM
        is_allowed = True

        # sim-locks is a whitelist of IMSI numbers allowed to connect to
        # a WWAN network using TGCM
        sim_whitelist = self._config.get_sim_locks()

        if status is None:
            status = device.get_card_status()

        if status == CARD_STATUS_READY:
            try:
                imsi = device.get_imsi()

                # Some countries have a whitelist of allowed IMSI numbers
                # to connect to a WWAN network using TGCM. If a IMSI is not listed
                # TGCM won't allow the user to connect to the network
                if (len(sim_whitelist) > 0) and (imsi is not None) and (len(imsi) > 0):
                    is_allowed = False
                    for sim in sim_whitelist:
                        if imsi.startswith(sim):
                            is_allowed = True
                            break
            except DeviceHasNotCapability:
                pass

        if not is_allowed:
            msg = _("The Mobile Internet Device does not have a valid SIM card.\nPlease check to see that the device contains a SIM of your network operator.")
            markup = _('<b>Invalid SIM</b>')
            error_dialog(msg, markup)
            device.turn_off()

        return is_allowed

    def __register_imsi(self, device, status=None):
        if status is None:
            status = device.get_card_status()

        if status == CARD_STATUS_READY:
            try:
                imsi = device.get_imsi()
                if (imsi is not None) and (len(imsi) > 0):
                    self._config.set_last_imsi_seen(imsi)
                    tgcm.debug("Set imsi preferred : %s" % imsi)
            except DeviceHasNotCapability:
                pass

    # -- Schedule the task for dont blocking the other gobject signals like the modem removed event
    def __main_modem_candidate_added_cb(self, main_modem, candidate):
        glib.idle_add(self.__main_modem_candidate_handler, main_modem,
                candidate.mm_obj(), candidate.vendor(), candidate.vid(), candidate.pid())

    def __main_modem_candidate_handler(self, main_modem, modem, vendor, vid, pid):
        show_popup = False
        pdp_active = False
        select_new = False
        self.__candidate_modem = modem

        # -- If a PDP context is active we are not allowed to change the main modem nor to show
        # -- a popup, so return at this point
        current_modem = self._main_modem.current_modem()
        if current_modem is not None:
            if self.device_dialer.is_modem():
                print "--> Returning as PPP context active"
                return

        # -- Check if the device is new on the system
        if self.__devtable is None:
            self.__devtable = _DeviceTable()
        is_new = self.__devtable.is_new(vid, pid)

        # -- If a main modem is already selected, show the popup if the new attached device is new on the system
        if current_modem is not None:
            if is_new is True:
                show_popup = True
        else:
            # -- If there is no main modem selected and the modem already exists in the table, select it without
            # -- requesting an user confirmation. If the modem is new, show the popup and ask for confirmation.
            if is_new is False:
                select_new = True
            else:
                show_popup = True

        if show_popup is True:
            self.__popup = _PlugAndPlayPopup(gtk.MESSAGE_QUESTION)
            resp = self.__popup.show_new(vendor)
            self.__popup = None
            if resp == gtk.RESPONSE_YES:
                select_new = True
            else:
                return

        # -- If the new modem is selected as new main device, request to emit the signal from the main modem and
        # -- add this new device to the devices table
        if select_new is True:
            main_modem.emit_main_modem_changed(self.__candidate_modem)
            self.__devtable.add(vid, pid)

        # It is possible that a modem with a SIM card with PIN number disabled changes its card
        # status before it is registered as a main_modem. In that case it is necessary to
        # explicitly register its IMSI in order to initialize various TGCM subsystems
        device = main_modem.current_device()

        # Check if the IMSI has been blacklisted
        is_imsi_allowed = self.__is_imsi_allowed(device)
        if is_imsi_allowed:
            self.__register_imsi(device)

            # Configure the mode and domain of the device with the last known values
            self.__set_current_mode_domain(device)

            # The card might be already ready if a device was already present
            # in the system when TGCM was started, or has its PIN disabled
            status = device.get_card_status()
            if status == CARD_STATUS_READY:
                # If the card status is already READY, register it as a new
                # device in the log
                self._connection_logger.register_new_device(device)

                # Unknown connection procedure
                if  (time.time() - self.startup_time) < STARTUP_SECS:
                    self._is_on_startup = False
                    self.startup_time = 0
                    self._connect_on_startup()

    def __main_modem_candidate_removed_cb(self, main_modem, candidate):
        if (candidate.mm_obj() == self.__candidate_modem) and (self.__popup is not None):
            self.__popup.response(gtk.RESPONSE_CANCEL)


class _PlugAndPlayPopup(gtk.MessageDialog):

    def __init__(self, type, title=None, msg=None):

        if title is None:
            title = _("Plug &amp; play device detected")

        main_window = tgcm.ui.ThemedDock().get_main_window()

        gtk.MessageDialog.__init__(self, parent=main_window, type=type, \
                flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_YES_NO)

        self.set_icon_name("tgcm")
        self.set_markup("<b>%s</b>" % title)

        if msg is not None:
            self.format_secondary_markup(msg)

    def show_new(self, name):
        if tgcm.country_support == 'de':
            msg = _("Device '%s' has been detected.\nWould you like to select it as a 2G/3G/4G device?") % name
        else:
            msg = _("Device '%s' has been detected.\nWould you like to select it as a WWAN device?") % name

        if msg is not None:
            self.format_secondary_markup(msg)

        resp = self.run()
        self.destroy()
        return resp


class _DeviceTable():

    def __init__(self):
        self.__config = tgcm.core.Config.Config(tgcm.country_support)

    # -- Check if the device doesnt exist in the table
    def is_new(self, vid, pid):
        current = self.__config.get_device_main_modem_selected()
        return (False if vid in current else True)

    # -- Save the new device in the remanent config
    def add(self, vid, pid):
        self.__config.add_device_main_modem_selected(vid, pid)
