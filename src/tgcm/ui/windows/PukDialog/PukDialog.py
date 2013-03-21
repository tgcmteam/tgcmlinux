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
import glib

import tgcm
import tgcm.core.FreeDesktop
import tgcm.ui

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, gtk_sleep

import MobileManager

PIN_LENGTH_RANGE = range(4, 9)
PUK_LENGTH_RANGE = range(8, 9)

def is_valid_pin(pin):
    if type(pin) != type(""):
        pin = str(pin)
    return True if (pin.isdigit() and (len(pin) in PIN_LENGTH_RANGE)) else False

def is_valid_puk(puk):
    if type(puk) != type(""):
        puk = str(puk)
    return True if (puk.isdigit() and (len(puk) in PUK_LENGTH_RANGE)) else False


class PukDialog:

    STATE_IDLE          = 0
    STATE_RUNNING       = 1
    STATE_MODEM_CHANGED = 2

    ENTRY_VALID          = 1
    ENTRY_INVALID_DIGITS = 2
    ENTRY_INVALID_LENGTH = 3

    def __init__(self):
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.__main_modem = tgcm.core.MainModem.MainModem()
        self.__state = self.STATE_IDLE
        self.__error_dlg = None

        self.windows_dir = os.path.join(tgcm.windows_dir, "PukDialog")

        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'PukDialog.ui'), \
                prefix='pd')

        # -- Set the main window as parent of this dialog
        main_window = tgcm.ui.ThemedDock().get_main_window()
        self.dialog.set_transient_for(main_window)

        self.ok_button.set_sensitive(False)

        # -- Set the tooltips for the entries
        self.puk_entry.set_tooltip_text(_("PUK number has length of 8 digits"))
        self.new_pin_entry.set_tooltip_text(_("PIN number has length between 4 and 8 digits"))
        self.new_pin_confirm_entry.set_tooltip_text(_("PIN number has length between 4 and 8 digits"))

        # -- Connect to the gobject signals
        self.new_pin_entry.connect("changed", self.entries_changed_cb, None)
        self.new_pin_confirm_entry.connect("changed", self.entries_changed_cb, None)
        self.puk_entry.connect("changed", self.entries_changed_cb, None)
        self.__main_modem.connect('main-modem-removed' , self.__main_modem_changed_cb)
        self.__main_modem.connect('main-modem-changed' , self.__main_modem_changed_cb)

    def __check_entry_valid(self, widget, is_puk = False):

        value = widget.get_text()

        # -- Check for only digits
        if not value.isdigit():
            return self.ENTRY_INVALID_DIGITS

        # -- Now check the length
        if is_puk and not (len(value) in PUK_LENGTH_RANGE):
            ret = self.ENTRY_INVALID_LENGTH
        elif not (len(value) in PIN_LENGTH_RANGE):
            ret = self.ENTRY_INVALID_LENGTH
        else:
            ret = self.ENTRY_VALID

        return ret

    def entries_changed_cb(self, editable, data):
        puk  = self.__check_entry_valid(self.puk_entry, is_puk = True)
        pin1 = self.__check_entry_valid(self.new_pin_entry)
        pin2 = self.__check_entry_valid(self.new_pin_confirm_entry)

        errmsg = None

        if puk == self.ENTRY_INVALID_DIGITS:
            errmsg = _("Only digits allowed for PUK number")
        elif puk == self.ENTRY_INVALID_LENGTH:
            errmsg = _("PUK length is 8 digits")

        elif pin1 == self.ENTRY_INVALID_DIGITS:
            errmsg = _("Only digits allowed for PIN numbers")
        elif pin1 == self.ENTRY_INVALID_LENGTH:
            errmsg = _("PIN length is between 4 and 8 digits")

        elif self.new_pin_entry.get_text() != self.new_pin_confirm_entry.get_text():
            errmsg = _("Both PIN numbers must be equal")

        if errmsg is not None:
            self.ok_button.set_sensitive(False)
            self.__error_hbox_show(errmsg)
        else:
            self.ok_button.set_sensitive(True)
            self.__error_hbox_clear()

    def __clean_dialog_fields(self):
        self.puk_entry.set_text("")
        self.new_pin_entry.set_text("")
        self.new_pin_confirm_entry.set_text("")

    def __error_hbox_show(self, msg):
        self.error_label.set_markup('<b>%s</b>' % msg)
        self.error_hbox.show_all()

    def __error_hbox_clear(self):
        self.error_hbox.hide_all()
        self.error_label.set_text("")
        self.error_label.hide()

    def __error_dialog(self, markup, msg, title=None):
        # Cancel action : Show message and turn off the device if necesary
        self.__error_dlg = gtk.MessageDialog(parent  = self.dialog, \
                flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
                type = gtk.MESSAGE_ERROR, \
                buttons = gtk.BUTTONS_OK)
        if title is not None:
            self.__error_dlg.set_title(title)
        self.__error_dlg.set_markup("<b>%s</b>" % markup)
        self.__error_dlg.format_secondary_markup(msg)
        self.__error_dlg.run()
        self.__error_dlg.destroy()
        self.__error_dlg = None

    # -- Open the dialog for requesting to enter the PUK
    def request(self):
        if self.__state == self.STATE_IDLE:
            self.__state = self.STATE_RUNNING
            glib.idle_add(self.__run)

    def __run(self):

        # -- First remove the old error message and grab the focus to the PUK field entry
        self.puk_entry.grab_focus()
        self.__error_hbox_clear()

        try:
            odev = self.device_manager.get_main_device()
            if odev == None:
                print "ERROR: There is no Main device"
                return

            status = odev.pin_status()

            # -- We must stop the device checker as the modem normally doesn't respond when the PUK is requested
            if status == MobileManager.PIN_STATUS_WAITING_PUK:
                odev.stop_checker()

            self.__clean_dialog_fields()

            while status == MobileManager.PIN_STATUS_WAITING_PUK:
                response = self.dialog.run()

                # -- This response is received when the modem was removed
                if response == gtk.RESPONSE_REJECT:
                    break

                elif response != gtk.RESPONSE_OK:
                    self.__error_dialog(_("PUK authentication cancel"),
                                        _("You have canceled the PUK authentication process, the card will be turn off"))

                    # -- Turn the modem off only if it has not changed before
                    if self.__state != self.STATE_MODEM_CHANGED:
                        odev.turn_off()
                    break

                # -- We dont need to check for the entries as they are validated when a entry change is detected
                puk = self.puk_entry.get_text()
                new_pin = self.new_pin_entry.get_text()
                new_pin_confirm = self.new_pin_confirm_entry.get_text()

                # -- While the PUK is sent, the modem could be removed so we need to check for the state flag
                send_puk_result = odev.send_puk(puk, new_pin)

                # -- First check if the modem was probably removed during the PUK was sent to the device. In that
                # -- case no error message is required as the Dock shows that no device is available
                if self.__state == self.STATE_MODEM_CHANGED:
                    break

                if send_puk_result is False:
                    self.__error_hbox_show(_("PUK authentication failed, please verify the number."))
                    continue

                # -- Now we need to wait until the card is ready. Using an arbitrary timeout for avoding a deadlock
                loop_time = 0.25
                timeout   = int(4 / loop_time)
                while timeout > 0:
                    timeout -= 1
                    gtk_sleep(loop_time)
                    status = odev.pin_status()
                    if status == MobileManager.PIN_STATUS_READY:
                        odev.start_checker()
                        return

                self.__error_dialog(_("PUK authentication failure"),
                                    _("Timeout waiting for PIN ready status. Please try reconnecting the modem."))
                break

        except Exception, err:
            print "@FIXME: PukDialog error, %s" % err
        finally:
            self.dialog.hide()
            self.__state = self.STATE_IDLE

    def __main_modem_changed_cb(self, *args):
        if self.__state == self.STATE_RUNNING:
            self.__state = self.STATE_MODEM_CHANGED
            if self.__error_dlg is not None:
                self.__error_dlg.response(gtk.RESPONSE_OK)
            self.dialog.response(gtk.RESPONSE_REJECT)
