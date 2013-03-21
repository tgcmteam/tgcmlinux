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


class ChangePinDialog:

    def __init__(self, parent=None):
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.theme_manager = tgcm.ui.ThemedDock()

        self.windows_dir = os.path.join(tgcm.windows_dir , 'PinDialog')
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'ChangePinDialog.ui'), \
                prefix='cpd')

        self._parent = parent if parent is not None else self.theme_manager.get_main_window()
        self.dialog.set_transient_for(self._parent)

        self.ok_button.set_sensitive(False)

        self.new_pin_entry.connect("changed", self.entries_changed_cb, None)
        self.new_pin_confirm_entry.connect("changed", self.entries_changed_cb, None)
        self.current_pin_entry.connect("changed", self.entries_changed_cb, None)

    def entries_changed_cb(self, editable, data):
        if len(self.current_pin_entry.get_text()) > 0 and \
                len(self.new_pin_entry.get_text()) > 0 and \
                len(self.new_pin_confirm_entry.get_text()) > 0:
            self.ok_button.set_sensitive(True)
        else:
            self.ok_button.set_sensitive(False)

    def run(self):
        try:
            odev = self.device_manager.get_main_device()
            status = odev.pin_status()

            if status == MobileManager.PIN_STATUS_WAITING_PUK :
                return

            stop = False

            self.current_pin_entry.set_text("")
            self.new_pin_entry.set_text("")
            self.new_pin_confirm_entry.set_text("")
            self.error_label.show()
            self.error_hbox.hide()
            self.dialog.show()

            while not stop :
                response = self.dialog.run()

                if response != gtk.RESPONSE_OK:
                    self.dialog.hide()
                    return

                new_pin = self.new_pin_entry.get_text()
                new_pin_confirm = self.new_pin_confirm_entry.get_text()
                current_pin = self.current_pin_entry.get_text()

                if not is_valid_pin(new_pin) or not is_valid_pin(current_pin):
                    self.error_label.set_markup('<b>%s</b>' % _("The PIN code requires between 4 and 8 digits"))
                    self.error_hbox.show_all()
                    continue

                if new_pin != new_pin_confirm:
                    self.error_label.set_markup('<b>%s</b>' % _("The two PIN codes are not equal"))
                    self.error_hbox.show_all()
                    continue

                res = odev.set_pin(current_pin,new_pin)
                time.sleep(2)
                status = odev.pin_status()
                if status == MobileManager.PIN_STATUS_WAITING_PUK:
                    odev.turn_off()
                    self.dialog.hide()
                    dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
                    dlg.set_markup(_("<b>Error changing PIN code</b>"))
                    dlg.format_secondary_markup(_("The PIN code change of your SIM card has failed. Now , your card will be turn off. The next turn on of your card, the PUK code will be required"))
                    dlg.run()
                    dlg.destroy()
                    return

                if res == True :
                    self.dialog.hide()
                    return

                self.error_label.set_markup('<b>%s.</b>' % _("The PIN code is invalid"))
                self.current_pin_entry.set_text("")
                self.error_hbox.show_all()

        except :
            return
