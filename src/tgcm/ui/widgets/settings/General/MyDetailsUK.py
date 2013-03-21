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
import gobject
import webbrowser

import tgcm.core.FreeDesktop

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, \
        format_to_maximun_unit_with_integers, get_month_day

import MobileManager

class MyDetailsUK:
    def __init__(self, conf, widget_dir):
        self.__conf = conf
        self._device_manager = tgcm.core.FreeDesktop.DeviceManager()

        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'MyDetailsUK.ui'), \
                prefix='gnrl')
        self.my_details_area.add(self.my_details_o2uk)
        self.my_details_o2uk.show_all()

        # ISMI, identifies the latest known SIM card
        self.__imsi = self.__conf.get_last_imsi_seen()

        self.alert_limit_list = self.__conf.get_alerts(is_roaming = False)
        self.alert_limit_index = {}
        self.__conf.connect("alerts-info-changed", self.__alerts_info_changed_cb)

        self.__init_o2uk_limit_combobox ()
        self.__update_o2uk_limit_combobox()
        selected_limit = self.__conf.get_imsi_based_selected_monthly_limit(self.__imsi, is_roaming=False)
        if self.alert_limit_index.keys() != [-1] :
            self.o2uk_limit_combobox.set_active (self.alert_limit_index[selected_limit])

        self.__init_o2uk_bill_date_combobox ()
        self.__update_o2uk_bill_date_combobox()

        self.manual_technology_radiobutton.set_label (_("Manual"))

        self.o2uk_postpaid_radiobutton.connect ("toggled", self.__on_o2uk_postpaid_radiobutton_toggled)

        self.o2uk_broadband_number_entry.set_text ("")
        self.o2uk_phone_entry.set_text (self.__conf.get_user_phone())

        self.o2uk_broadband_number_error_label.hide ()
        self.o2uk_phone_error_label.hide()

        o2uk_limit_tooltip = _("This is your monthly data allowance on the O2 network. You can find this by looking on your bill.")
        self.o2uk_limit_label.set_has_tooltip (True)
        self.o2uk_limit_label.set_tooltip_text (o2uk_limit_tooltip)
        self.o2uk_limit_combobox.set_has_tooltip (True)
        self.o2uk_limit_combobox.set_tooltip_text (o2uk_limit_tooltip)
        o2uk_bill_date_tooltip = _("You can find this on your bill.")
        self.o2uk_bill_date_label.set_has_tooltip (True)
        self.o2uk_bill_date_label.set_tooltip_text (o2uk_bill_date_tooltip)
        self.o2uk_bill_date_combobox.set_has_tooltip (True)
        self.o2uk_bill_date_combobox.set_tooltip_text (o2uk_bill_date_tooltip)
        o2uk_broadband_number_tooltip = _("You can find your mobile broadband number on your bill or contract.")
        self.o2uk_broadband_number_label.set_has_tooltip (True)
        self.o2uk_broadband_number_label.set_tooltip_text (o2uk_broadband_number_tooltip)
        self.o2uk_broadband_number_entry.set_has_tooltip (True)
        self.o2uk_broadband_number_entry.set_tooltip_text (o2uk_broadband_number_tooltip)
        o2uk_phone_tooltip = _("This is your personal or business mobile phone number.")
        self.o2uk_phone_label.set_has_tooltip (True)
        self.o2uk_phone_label.set_tooltip_text (o2uk_phone_tooltip)
        self.o2uk_phone_entry.set_has_tooltip (True)
        self.o2uk_phone_entry.set_tooltip_text (o2uk_phone_tooltip)

        self.__o2uk_broadband_number_entry_h = self.o2uk_broadband_number_entry.connect ('focus-out-event', self.__on_o2uk_broadband_number_entry_focus_out)
        self.__o2uk_phone_entry_h = self.o2uk_phone_entry.connect ('focus-out-event', self.__on_o2uk_phone_entry_focus_out)

        self.o2uk_privacy_button.connect ('clicked', self.__on_o2uk_privacy_button_clicked)

        # Connect some signals
        self.__connect_signals()

    def get_area(self):
        '''
        Returns a widget containing the elements of the 'My Details' tab for O2 (United Kingdom).

        @return: a GtkWidget.
        '''
        return self.my_details_o2uk

    def __connect_signals(self):
        self._device_manager.connect("active-dev-card-status-changed", self.__card_status_changed_cb)
        self.main_modem.connect("main-modem-changed", self.__main_modem_changed_cb)

    def __reload_prepay_info (self):
        dev = self._device_manager.get_main_device()
        if dev != None and dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            if dev.is_postpaid():
                self.o2uk_postpaid_radiobutton.set_active (True)
            else:
                self.o2uk_prepaid_radiobutton.set_active (True)
        else:
            self.o2uk_prepaid_radiobutton.set_active (True)

    def __on_o2uk_postpaid_radiobutton_toggled (self, widget, data=None):
        if self.o2uk_postpaid_radiobutton.get_active():
            self.o2uk_account_data_table.show()
            self.__conf.set_is_imsi_based_prepaid(self.__imsi, False)
        else:
            self.o2uk_account_data_table.hide()
            self.__conf.set_is_imsi_based_prepaid(self.__imsi, True)

    def __on_o2uk_broadband_number_entry_focus_out (self, widget, data=None):
        text = self.o2uk_broadband_number_entry.get_text ()
        if len (text) > 0 and (len (text) != 11 or not text.isdigit() or not text.startswith ('07')):
            self.o2uk_broadband_number_entry.handler_block(self.__o2uk_broadband_number_entry_h)
            self.o2uk_broadband_number_error_label.show ()
            self.o2uk_broadband_number_entry.grab_focus()
            self.o2uk_broadband_number_entry.handler_unblock(self.__o2uk_broadband_number_entry_h)
            return True
        else:
            self.o2uk_broadband_number_error_label.hide()

            device = self._device_manager.get_main_device()
            imsi = device.get_imsi ()
            self.__conf.set_user_mobile_broadband_number (imsi, self.o2uk_broadband_number_entry.get_text ())

            return False

    def __on_o2uk_phone_entry_focus_out (self, widget, data=None):
        text = self.o2uk_phone_entry.get_text ()
        if len (text) > 0 and (len (text) != 11 or not text.isdigit() or not text.startswith ('07')):
            self.o2uk_phone_entry.handler_block(self.__o2uk_phone_entry_h)
            self.o2uk_phone_error_label.show ()
            self.o2uk_phone_entry.grab_focus()
            self.o2uk_phone_entry.handler_unblock(self.__o2uk_phone_entry_h)
            return True
        else:
            self.o2uk_phone_error_label.hide()
            self.__conf.set_user_phone (self.o2uk_phone_entry.get_text ())
            return False

    def __on_o2uk_privacy_button_clicked (self, widget, data=None):
        webbrowser.open("http://o2.co.uk")

    def __alerts_info_changed_cb (self, conf):
        self.__update_o2uk_limit_combobox()

    def __init_o2uk_limit_combobox (self):
        self.alert_limit_list = self.__conf.get_alerts(is_roaming = False)

        model = gtk.ListStore (gobject.TYPE_INT, gobject.TYPE_STRING)
        base_id = 0
        for limit in self.alert_limit_list:
            if limit == -1:
                model.append ([-1, _("Custom")])
                self.alert_limit_index[-1] = base_id
            else:
                limit_str = format_to_maximun_unit_with_integers(int(limit) ,"GB","MB")
                model.append ([base_id, limit_str])
                self.alert_limit_index[base_id] = base_id
            base_id = base_id + 1

        self.o2uk_limit_combobox.set_model (model)
        cell = gtk.CellRendererText()
        self.o2uk_limit_combobox.pack_start(cell, True)
        self.o2uk_limit_combobox.add_attribute(cell, 'text', 1)

        if self.alert_limit_index.keys() == [-1] :
            self.o2uk_limit_combobox.set_active(0)

        self.o2uk_limit_combobox.connect('changed', self.__on_o2uk_limit_combobox_changed)

        self.o2uk_limit_other_spinbutton.set_value( \
                self.__conf.get_imsi_based_other_monthly_limit(self.__imsi, is_roaming = False))
        self.o2uk_limit_other_spinbutton.connect('value-changed', self.__on_o2uk_limit_other_spinbutton_changed)

    def __update_o2uk_limit_combobox(self):
        selected_limit = self.__conf.get_imsi_based_selected_monthly_limit(self.__imsi, roaming=False)
        if self.alert_limit_index.keys() != [-1] :
            self.o2uk_limit_combobox.set_active (self.alert_limit_index[selected_limit])
            self.o2uk_limit_other_spinbutton.set_value (self.__conf.get_imsi_based_other_monthly_limit(self.__imsi, False))

    def __on_o2uk_limit_combobox_changed (self, widget):
        active = widget.get_active ()

        # TODO:
        for k in self.alert_limit_index:
            if self.alert_limit_index[k] == active:
                self.__conf.set_imsi_based_selected_monthly_limit(self.__imsi, active, False)
                if k == -1:
                    self.o2uk_limit_other_hbox.show_all()
                else:
                    self.o2uk_limit_other_hbox.hide()

    def __on_o2uk_limit_other_spinbutton_changed (self, widget):
        value = widget.get_value ()
        self.__conf.set_imsi_based_other_monthly_limit(self.__imsi, value, False)

    def __init_o2uk_bill_date_combobox (self):
        model = gtk.ListStore (gobject.TYPE_INT, gobject.TYPE_STRING)
        for i in range(1, 32):
            model.append ([i, get_month_day(i)])

        self.o2uk_bill_date_combobox.set_model (model)
        cell = gtk.CellRendererText()
        self.o2uk_bill_date_combobox.pack_start(cell, True)
        self.o2uk_bill_date_combobox.add_attribute(cell, 'text', 1)

        self.o2uk_bill_date_combobox.connect('changed', self.__on_o2uk_bill_date_combobox_changed)

    def __update_o2uk_bill_date_combobox(self):
        device = self._device_manager.get_main_device()
        if device != None and device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            imsi = device.get_imsi ()

            selected_bill_date = self.__conf.get_imsi_based_billing_day (imsi) - 1
            self.o2uk_bill_date_combobox.set_active (selected_bill_date)
        else:
            self.o2uk_bill_date_combobox.set_active (0)

    def __on_o2uk_bill_date_combobox_changed (self, widget):
        device = self._device_manager.get_main_device()
        if device != None and device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            imsi = device.get_imsi ()

            active = str (int (widget.get_active () + 1))
            self.__conf.set_imsi_based_billing_day (imsi, active)
        else:
            return False

    def __card_status_changed_cb(self, mcontroller, status):
        device = self._device_manager.get_main_device()
        if device != None and device.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            if device.is_on() == True:
                imsi = device.get_imsi()
                broadband_number = self.__conf.get_user_mobile_broadband_number (imsi)

                if broadband_number == None or broadband_number == "":
                    status = device.pin_status()
                    if status == MobileManager.PIN_STATUS_READY :
                        MSDISDN = device.get_MSISDN ()
                        self.__conf.set_user_mobile_broadband_number (imsi, MSDISDN)

                self.o2uk_broadband_number_entry.set_text (self.__conf.get_user_mobile_broadband_number(imsi))

        self.__reload_prepay_info()

    def __main_modem_changed_cb(self, main_modem, mcontroller, device):
        self.__reload_prepay_info ()
        self.__update_o2uk_bill_date_combobox()
