#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
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
import gobject
import gtk
import time

import tgcm
import tgcm.core.FreeDesktop
import tgcm.ui

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

import MobileManager


class CarrierDialog():

    def __init__(self, parent=None):
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.main_modem = self.device_manager.main_modem
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()

        self.windows_dir = os.path.join(tgcm.windows_dir , self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'CarrierDialog.ui'), \
                prefix='cd')

        # -- Block the passed parent otherwise the Dock
        if parent is None:
            parent = tgcm.ui.ThemedDock().get_main_window()
        self.carrier_selection_dialog.set_transient_for(parent)

        odev = self.device_manager.get_main_device()
        if odev != None and odev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            status = odev.pin_status()
            if not status == MobileManager.PIN_STATUS_READY :
                return
        else:
            tgcm.error("Exception")
            return

        self.carrier_combobox_changed_id = self.carrier_combobox.connect("changed", self.__carrier_combobox_cb, None)

        cell = gtk.CellRendererPixbuf()
        self.carrier_combobox.pack_start(cell, False)
        self.carrier_combobox.add_attribute(cell, "stock_id",0)

        cell = gtk.CellRendererText()
        self.carrier_combobox.pack_start(cell, False)
        self.carrier_combobox.add_attribute(cell, 'text', 1)

        self.carrier_selection_dialog.connect("delete-event", self.__carrier_dialog_delete_event_cb, None)
        self.main_modem.connect("main-modem-removed", self.__main_modem_removed_cb)

        self.refresh_button.connect("clicked",self.__refresh_button_cb, None)
        self.ok_button.connect("clicked",self.__ok_button_cb, None)
        self.cancel_button.connect("clicked",self.__cancel_button_cb, None)

        self.timer = gobject.timeout_add (100, self.__progress_timeout_cb, None)

        self.carrier_combobox_hbox.show()
        self.carrier_scan_progressbar.hide()

        self.reg_attempts = 0
        self.__scanning = False

    def __main_modem_removed_cb(self, main_modem, objpath):
        # -- If we are not scanning send the signal for closing the carrier dialog. Otherwise the DBus callback will
        # -- return with a failure and the corresponding callback will close the dialog
        if self.__scanning is False:
            self.__close_carrier_dialog = True
            self.carrier_selection_dialog.response(gtk.RESPONSE_CLOSE)

    def __progress_timeout_cb(self, data):
        self.carrier_scan_progressbar.pulse()
        return True

    # -- This callback is executed before 'run()' returns a value. So here we decide if the
    # -- carrier dialog should be hiden or now
    def __carrier_dialog_delete_event_cb(self, widget, event, data):
        if self.__scanning is True:
            self.__show_message_dialog(gtk.MESSAGE_INFO,
                                       _("Operator selection"),
                                       _("Sorry, but need to wait until the Mobile Internet Device is done with the scan request."))
            self.__close_carrier_dialog = False
            return True
        else:
            # -- Afaik, by returning False the deleve event will be passed to other listeners
            self.__close_carrier_dialog = True
            return False

    CARRIER_FAILURE = 1
    CARRIER_SUCCESS = 2

    def run(self, refresh=True):
        refresh_at_start = refresh

        odev = self.device_manager.get_main_device()
        if odev == None or odev.get_type() != tgcm.core.DeviceManager.DEVICE_MODEM :
            return self.CARRIER_FAILURE

        self.carrier_selection_dialog.show()

        while True :
            if refresh_at_start == True :
                self.refresh_button.emit("clicked")
                refresh_at_start = False

            self.__dialog_active = True
            res = self.carrier_selection_dialog.run()
            self.__dialog_active = False

            print "Mobile Carrier Dialog res --> %s" % res

            # -- @XXX: Why the fucking hell is run() returning ZERO! This is not defined as return value of Dialog.run()
            if res == 0:
                continue
            elif res == gtk.RESPONSE_OK:
                res = self.__select_carrier()
                if res == True :
                    self.carrier_combobox_hbox.hide()
                    self.carrier_scan_progressbar.set_text(_("Attaching to network"))
                    self.carrier_scan_progressbar.show()
                    self.ok_button.set_sensitive(False)
                    self.cancel_button.set_sensitive(False)
                    self.refresh_button.set_sensitive(False)

                    self.reg_attempts = 10
                    gobject.timeout_add (1500, self.__registering_timeout_cb, None)

                else:
                    self.__show_message_dialog(gtk.MESSAGE_ERROR,
                                               _("Operator selection failure"),
                                               _("Operator selection has failed. Try again or select another network."))
                    continue

                return self.CARRIER_SUCCESS

            elif res == gtk.RESPONSE_DELETE_EVENT:
                # -- We can NOT return to the main window if we are still waiting for a modem response as the modem is
                # -- probably not ready
                if self.__close_carrier_dialog is True:
                    self.carrier_selection_dialog.hide()
                    return self.CARRIER_SUCCESS

            elif res == gtk.RESPONSE_REJECT:
                # -- The DBus callback informed about an error
                self.carrier_combobox_hbox.show()
                self.carrier_scan_progressbar.hide()
                self.ok_button.set_sensitive(False)
                self.cancel_button.set_sensitive(True)
                self.refresh_button.set_sensitive(True)
                self.__show_message_dialog(gtk.MESSAGE_ERROR,
                                           _("Operator selection failure"),
                                           _("The operation failed. Please try it again or check for the Mobile Internet Device and SIM card."))

                # -- Hide the dialog as probably the modem was removed (or something similar)
                self.carrier_selection_dialog.hide()
                return self.CARRIER_FAILURE

            elif res == gtk.RESPONSE_CANCEL:
                # -- Cancel means for us nothing has changed, so return a success at this point otherwise our caller will
                # -- not update the status of the menu dialog and this is deathly!
                self.carrier_selection_dialog.hide()
                return self.CARRIER_SUCCESS

            elif res == gtk.RESPONSE_CLOSE:
                # -- Close the window and return a failure
                self.carrier_selection_dialog.hide()
                return self.CARRIER_FAILURE

            else:
                print "@FIXME: Unknown response %i from carrier dialog" % res
                self.carrier_selection_dialog.hide()
                return self.CARRIER_FAILURE

    def __show_message_dialog(self, type, title, msg):
        dlg = gtk.MessageDialog(parent  = self.carrier_selection_dialog,
                                type    = type,
                                flags   = (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT),
                                buttons = gtk.BUTTONS_OK)
        dlg.set_icon_name("phone")
        dlg.set_markup("<b>%s</b>" % title)
        dlg.format_secondary_markup(msg)
        dlg.run()
        dlg.destroy()

    def __registering_timeout_cb(self, data):
        try:
            odev = self.device_manager.get_main_device()

            if odev.is_attached() == True:
                self.carrier_selection_dialog.hide()
                return False
            else:
                if self.reg_attempts == 0:
                    self.carrier_combobox_hbox.show()
                    self.carrier_scan_progressbar.hide()
                    self.cancel_button.set_sensitive(True)
                    self.refresh_button.set_sensitive(True)
                    model =  self.carrier_combobox.get_model()
                    if len(model) > 0 :
                        self.ok_button.set_sensitive(True)
                    else:
                        self.ok_button.set_sensitive(False)

                    self.run(refresh=False)
                    return False
                else:
                    self.reg_attempts = self.reg_attempts - 1
                    return True
        except :
            tgcm.error("Exception")
            return False

    def __select_carrier(self):
        odev = self.device_manager.get_main_device()

        model = self.carrier_combobox.get_model()
        act_iter = self.carrier_combobox.get_active_iter()
        if act_iter != None :
            res = odev.set_carrier(model.get_value(act_iter, 3),
                                   int(model.get_value(act_iter, 4)))
            if res == True :
                return True
            else:
                return False
        return False

    def __refresh_button_cb (self, widget, data):
        try:
            odev = self.device_manager.get_main_device()

            self.carrier_combobox_hbox.hide()
            self.carrier_scan_progressbar.set_text(_("Scanning carriers"))
            self.carrier_scan_progressbar.show()
            self.ok_button.set_sensitive(False)
            self.cancel_button.set_sensitive(False)
            self.refresh_button.set_sensitive(False)

            self.__scanning = True

            mainloop =  gobject.MainLoop(is_running=True)
            context = mainloop.get_context()
            t1 = time.time()
            while time.time() - t1 < 2 :
                context.iteration()

            odev.get_carrier_list(reply_handler=self.__update_carrier_list,
                                  error_handler=self.__network_scan_error)

        except Exception, err:
            print "@FIXME: Unexpected failure starting Network Scan, %s" % err
            self.__network_scan_error("Unexpected failure, %s" % err)

    def __network_scan_error(self, err):
        self.__scanning = False
        self.carrier_selection_dialog.response(gtk.RESPONSE_REJECT)

    def __update_carrier_list(self, carrierlist):
        self.__scanning = False
        carrier_list = carrierlist

        model = gtk.ListStore(str,str,str,str,str)
        for x in carrier_list:
            record = [int(x["status"]),
                      str(x["operator-long"]),
                      str(x["operator-short"]),
                      str(x["operator-num"]),
                      int(x["access-tech"])]

            if record[0] == 1 or record[0] == 2:
                record.pop(0)
                record.insert(0,gtk.STOCK_YES)
            else:
                record.pop(0)
                record.insert(0,gtk.STOCK_NO)

            if record[4] == 2:
                record[1] = record [1] + " (3G)"
            else:
                record[1] = record [1] + " (2G)"

            model.append(record)

        self.carrier_combobox.set_model(model)
        self.cancel_button.set_sensitive(True)
        self.refresh_button.set_sensitive(True)
        self.carrier_combobox_hbox.show()
        self.carrier_scan_progressbar.hide()
        if len(model) > 0 :
            self.carrier_combobox.set_active(0)
            self.ok_button.set_sensitive(True)
        else:
            self.ok_button.set_sensitive(False)


    def __carrier_combobox_cb(self, widget, data):
        carrier_num = widget.get_active()
        if carrier_num <0 :
            self.ok_button.set_sensitive(False)
            return

        iter = widget.get_active_iter()
        if widget.get_model().get_value (iter, 0)  == gtk.STOCK_NO :
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)


    def __cancel_button_cb(self, widget, data):
        gobject.source_remove(self.timer)
        self.timer = 0
        self.carrier_selection_dialog.hide()


    def __ok_button_cb(self, widget, data):
        pass
