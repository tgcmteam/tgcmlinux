#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#           Cesar Garcia <cesar.garcia@openshine.com>
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

import gtk
import os
import time
import dbus
import glib

import tgcm
import tgcm.core.FreeDesktop

import tgcm.ui

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

import MobileManager

def is_valid_pin(pin):
    try:
        int(pin)
    except:
        return False

    if len(pin) >3 and len(pin) <9:
        return True
    else:
        return False


class AskPinDialog():
    def __init__(self, parent=None):
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.theme_manager = tgcm.ui.ThemedDock()

        self.windows_dir = os.path.join(tgcm.windows_dir , 'PinDialog')
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'AskPinDialog.ui'), \
                prefix='apd')

        self.ok_button.set_sensitive(False)

        # -- Set as parent the main window
        self._parent = parent if parent is not None else self.theme_manager.get_main_window()
        self.dialog.set_transient_for(self._parent)

        self.device_manager.connect("device-removed", self.__device_removed_cb)
        self.pin_entry.connect("changed", self.pin_entry_changed_cb, None)

        self.cancelledBySystem = False
        self.__running         = False
        self.__odev            = None
        self.__error_dlg       = None

        system_bus = dbus.SystemBus()
        system_bus.add_signal_receiver(self.deviceUnlocked,"DeviceUnlocked","org.freedesktop.ModemManager.Modem.Gsm.Card")

    def pin_entry_changed_cb(self, editable, data):
        if len(self.pin_entry.get_text()) > 0:
            self.ok_button.set_sensitive(True)
        else:
            self.ok_button.set_sensitive(False)

    def running(self):
        return self.__running

    # -- This method will open the dialog only if it's already opened
    def run(self):
        if self.__running is True:
            return

        self.__running = True
        glib.idle_add(self.__run)

    def __run(self):

        self.dialog.hide()
        try:
            self.__odev = self.device_manager.get_main_device()

            status = self.__odev.pin_status()
            if status != MobileManager.PIN_STATUS_WAITING_PIN :
                self.dialog.hide()
                return

            self.pin_entry.set_text("")
            self.error_hbox.hide()
            self.dialog.show()
            self.cancelledBySystem=False;
            while status == MobileManager.PIN_STATUS_WAITING_PIN :
                response = self.dialog.run()

                if self.cancelledBySystem:
                    self.dialog.hide()
                    return

                if response != gtk.RESPONSE_OK:

                    self.__error_dlg = gtk.MessageDialog(parent=self.dialog,
                            flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                            message_format=_("You have canceled the PIN code insertion, the mobile device will be turned off"))

                    icon = self.__error_dlg.render_icon(gtk.STOCK_DIALOG_AUTHENTICATION, gtk.ICON_SIZE_MENU)
                    self.__error_dlg.set_icon(icon)
                    self.__error_dlg.set_title(_("PIN code insertion canceled"))

                    self.__error_dlg.run()

                    # -- Dont send the turn_off() if the dialog was closed due some system event (e.g. device removed)
                    if self.cancelledBySystem is False:
                        self.__odev.turn_off()
                        # -- Wait some time before freeing the dialog
                        time.sleep(1)

                    self.__error_dlg.destroy()
                    self.dialog.hide()
                    return

                pin = self.pin_entry.get_text()
                if not is_valid_pin(pin):
                    self.pin_error_label.set_markup('<b>%s</b>' % _("The PIN code requires between 4 and 8 digits"))
                    self.error_hbox.show_all()
                    continue

                res = self.__odev.send_pin(pin)
                time.sleep(2)
                status = self.__odev.pin_status()
                if status == MobileManager.PIN_STATUS_WAITING_PUK:
                    self.dialog.hide()
                    return

                if res == True and status != MobileManager.PIN_STATUS_WAITING_PIN:
                    self.dialog.hide()
                    return
                self.pin_error_label.set_markup('<b>%s.</b>' % _("The PIN code is invalid"))
                self.pin_entry.set_text("")
                self.error_hbox.show_all()

            self.dialog.hide()

        except:
            return
        finally:
            self.__odev      = None
            self.__running   = False
            self.__error_dlg = None
            return False

    def deviceUnlocked(self, object):
        ##TODO check if self.__odev.nm_dev==object
        self.cancelledBySystem=True;
        print "PIN unlocked entering device"
        self.dialog.response(gtk.RESPONSE_CANCEL)

    def __device_removed_cb (self, device_manager, objpath):

        # -- Check if the removed device belongs to our monitored object
        if (self.__odev is not None) and (self.__odev.object_path == objpath):

            self.cancelledBySystem = True

            # -- Close the error dialog if it was already opened
            if self.__error_dlg is not None:
                self.__error_dlg.response(gtk.RESPONSE_OK)
            self.dialog.response(gtk.RESPONSE_CANCEL)
