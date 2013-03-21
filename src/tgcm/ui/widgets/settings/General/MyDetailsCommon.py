#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011-2012, Telefonica Móviles España S.A.U.
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

import tgcm.core.FreeDesktop
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label, \
        format_to_maximun_unit_with_integers, get_month_day, error_dialog

class MyDetailsCommonArea:
    def __init__(self, conf, widget_dir, settings):
        self.__settings = settings
        self.__conf = conf
        self.__device_manager = tgcm.core.FreeDesktop.DeviceManager()

        gtk_builder_magic(self, \
                filename=os.path.join(widget_dir, 'MyDetailsCommon.ui'), \
                prefix='gnrl')

        text = self.common_cancel_label.get_text() % {'app_name' : self.__conf.get_app_name()}
        self.common_cancel_label.set_text(text)

        # -- Replease these two labels for wrapping
        self.top_info_label = replace_wrap_label(self.top_info_label)
        self.bam_info_label = replace_wrap_label(self.bam_info_label)

        self.my_details_common.show_all()

        # FIXME: It seems that Movistar ES has disabled monthly limits
        self.is_monthly_limit_enabled = tgcm.country_support != 'es'

        # Init comboboxes
        self.__init_dialog()

        # Load the BAM phone query area for Movistar (Spain)
        parent = self.__settings.get_dialog()

        self.__phonequery_area = tgcm.ui.windows.RecargaSaldoPhoneQuery(parent)
        self.phonenumber_parent.add(self.__phonequery_area.get_area())

        bam_textc = _('Mobile broadband number')
        self.__phonequery_area.set_description_label('%s:' % bam_textc)

        # Don't show the tooltip for the BAM help button
        self.phonenumber_bam_help.set_tooltip_text('')

        # IMSI, identifies the latest known SIM card
        self.__imsi = self.__conf.get_last_imsi_seen()
        if not self.__conf.is_last_imsi_seen_valid():
            self.my_details_common.set_sensitive(False)
        else:
            self.__load_dialog_values()

        # Connect some signals
        self.__connect_signals()

    def get_area(self):
        '''
        Returns a widget containing the elements of the 'My Details' tab for Movistar (Spain).
        @return: a GtkWidget.
        '''
        return self.my_details_common

    ### Helper methods ###

    def __init_dialog(self):
        # Prepay/postpay user radiobutton
        is_default_prepaid = self.__conf.is_default_prepaid()
        self.common_prepaid_radiobutton.set_active(is_default_prepaid)
        self.common_postpaid_radiobutton.set_active(not is_default_prepaid)

        # Monthly limits combobox
        self._monthly_limits = self.__conf.get_monthly_limits(is_roaming = False)

        model = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        for limit in self._monthly_limits:
            if limit == -1:
                model.append([-1, _('Other')])
            else:
                limit_str = format_to_maximun_unit_with_integers(limit, 'GB', 'MB')
                model.append([limit, limit_str])

        if self.is_monthly_limit_enabled:
            self.common_data_allowance_combobox.set_model(model)
            cell = gtk.CellRendererText()
            self.common_data_allowance_combobox.pack_start(cell, True)
            self.common_data_allowance_combobox.add_attribute(cell, 'text', 1)

            default_limit = self.__conf.get_default_selected_monthly_limit(False)
            index = self._monthly_limits.index(default_limit)
            self.common_data_allowance_combobox.set_active(index)

            if default_limit == -1:
                self.common_limit_other_hbox.show_all()
            else:
                self.common_limit_other_hbox.hide()
        else:
            self.common_data_allowance_combobox.set_visible(False)
            self.common_data_allowance_label.set_visible(False)
            self.common_limit_other_hbox.hide()

        # Billing period combobox
        self._days = range(1, 32)
        if tgcm.country_support == 'es':
            self._days = (1, 10, 18, 24)

        model = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        for i in self._days:
            model.append([i, get_month_day(i)])
        self.common_billing_period_combobox.set_model(model)

        cell = gtk.CellRendererText()
        self.common_billing_period_combobox.pack_start(cell, True)
        self.common_billing_period_combobox.add_attribute(cell, 'text', 1)

        default_day = self.__conf.get_default_billing_day()
        index = self._days.index(default_day)
        self.common_billing_period_combobox.set_active(index)

        is_fixed = self.__conf.is_default_fixed_billing_day()
        self.__enable_billing_day(not is_fixed)

    def __load_dialog_values(self):
        # Enable screen contents
        self.my_details_common.set_sensitive(True)

        # Prepaid radio buttons
        is_prepaid = self.__conf.is_imsi_based_prepaid(self.__imsi)
        self.common_prepaid_radiobutton.set_active(is_prepaid)
        self.common_postpaid_radiobutton.set_active(not is_prepaid)

        # Monthly data allowance combobox
        if self.is_monthly_limit_enabled:
            self.__update_monthly_limit_combobox()

        # Billing day period combobox
        self.__update_billing_day_combobox()

    def __update_monthly_limit_combobox(self):
        monthly_limit = self.__conf.get_imsi_based_selected_monthly_limit(self.__imsi, is_roaming = False)
        index = self._monthly_limits.index(monthly_limit)
        self.common_data_allowance_combobox.set_active(index)

        other_monthly_limit = self.__conf.get_imsi_based_other_monthly_limit(self.__imsi, is_roaming = False)
        self.common_limit_other_spinbutton.set_value(other_monthly_limit)
        if monthly_limit == -1:
            self.common_limit_other_hbox.show_all()
        else:
            self.common_limit_other_hbox.hide()

    def __update_billing_day_combobox(self):
        billing_day = self.__conf.get_imsi_based_billing_day(self.__imsi)
        try:
            index = self._days.index(billing_day)
        except IndexError:
            index = 0
        self.common_billing_period_combobox.set_active(index)

        is_fixed = self.__conf.is_imsi_based_fixed_billing_day(self.__imsi)
        self.__enable_billing_day(not is_fixed)

    def __connect_signals(self):
        # UI signals
        self._widget_signals = []
        signal_id = self.common_prepaid_radiobutton.connect('toggled', self.__on_prepaid_toggled)
        self._widget_signals.append((self.common_prepaid_radiobutton, signal_id))
        signal_id = self.common_data_allowance_combobox.connect('changed', self.__on_monthly_data_limits_changed)
        self._widget_signals.append((self.common_data_allowance_combobox, signal_id))
        signal_id = self.common_limit_other_spinbutton.connect('value-changed', self.__on_custom_monthly_data_limit_changed)
        self._widget_signals.append((self.common_limit_other_spinbutton, signal_id))
        signal_id = self.common_billing_period_combobox.connect('changed', self.__on_billing_period_changed)
        self._widget_signals.append((self.common_billing_period_combobox, signal_id))

        # Settings window signals
        self.__settings.connect('is-closing', self.__on_settings_is_closing)

        # Configuration changes signals
        self.__conf.connect('last-imsi-seen-changed', self.__on_last_imsi_seen_changed)
        self.__conf.connect('billing-day-changed', self.__on_config_billing_day_changed)
        self.__conf.connect('monthly-limit-changed', self.__on_monthly_limit_changed)
        self.__conf.connect('fixed-billing-day-changed', self.__on_is_fixed_billing_day_changed)

    def __enable_billing_day(self, is_enabled):
        self.common_billing_period_label.set_sensitive(is_enabled)
        self.common_billing_period_combobox.set_sensitive(is_enabled)

    ### UI callbacks ###

    def __on_prepaid_toggled(self, widget):
        is_prepaid = widget.get_active()
        self.__conf.set_is_imsi_based_prepaid(self.__imsi, is_prepaid)

        self.__on_prepaid_toggled_custom_spain(is_prepaid)

    def __on_monthly_data_limits_changed(self, widget=None):
        active = self.common_data_allowance_combobox.get_active()

        new_monthly_limit = self._monthly_limits[active]
        self.__conf.set_imsi_based_selected_monthly_limit(self.__imsi, new_monthly_limit, is_roaming = False)
        if new_monthly_limit == -1:
            self.common_limit_other_hbox.show_all()
        else:
            self.common_limit_other_hbox.hide()

    def __on_custom_monthly_data_limit_changed(self, widget):
        value = widget.get_value_as_int()
        if value >= 1:
            self.__conf.set_imsi_based_other_monthly_limit(self.__imsi, value, is_roaming = False)

    def __on_billing_period_changed(self, widget):
        billing_day = self._days[widget.get_active()]
        self.__conf.set_imsi_based_billing_day(self.__imsi, billing_day)


    ### Settings window event callbacks ###

    def __on_settings_is_closing(self, settings):
        is_ok = False

        # Request the phone query area to validate its contents and save them
        try:
            self.__phonequery_area.do_save()
            is_ok = True    # Everything went all right

        # Seems there was a problem saving the BAM phone query area, change
        # the displayed tab in settings to 'My Details' and warn the user
        # about the problem
        except tgcm.ui.windows.RecargaSaldoSaveError, err:
            self.__settings.show_section('General>1')
            self.__phonequery_area.grab_focus()
            error_dialog(err.details, markup = err.msg, parent = self.__settings.get_dialog())

        # The signal 'is-closing' expects the return value True if there have been
        # any problem and it should not close the 'Settings' dialog.
        return not is_ok


    ### Configuration changes callbacks ###

    def __on_last_imsi_seen_changed(self, sender, imsi):
        self.__imsi = imsi

        for widget, signal_id in self._widget_signals:
            widget.handler_block(signal_id)

        self.__load_dialog_values()

        for widget, signal_id in self._widget_signals:
            widget.handler_unblock(signal_id)

    def __on_config_billing_day_changed(self, sender):
        self.__update_billing_day_combobox()

    def __on_monthly_limit_changed(self, sender):
        self.__update_monthly_limit_combobox()

    def __on_is_fixed_billing_day_changed(self, sender, is_fixed):
        self.__enable_billing_day(not is_fixed)


    ### Prepay custom actions for specific countries ###

    # Some countries have some special behaviors which have not been completely fully described in
    # regional-info. The function below is intended to address that situation.

    ## Spain ##

    def __on_prepaid_toggled_custom_spain(self, is_prepaid):
        if is_prepaid:
            fixed_billing_day = True
            billing_day = 1
        else:
            fixed_billing_day = False
            billing_day = self.__conf.get_default_billing_day()

        self.__conf.set_is_imsi_based_fixed_billing_day(self.__imsi, fixed_billing_day)

        try:
            index = self._days.index(billing_day)
        except IndexError:
            index = 0
        self.common_billing_period_combobox.set_active(index)
