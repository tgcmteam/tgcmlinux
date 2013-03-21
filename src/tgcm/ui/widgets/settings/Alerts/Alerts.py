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
import gobject

import tgcm.core.Config

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, \
        format_to_maximun_unit_one_decimal, replace_wrap_label

class Alerts(gtk.HBox):
    def __init__(self, settings):
        gtk.HBox.__init__(self)

        self._conf = tgcm.core.Config.Config()
        self._settings = settings

        self.widget_dir = os.path.join(tgcm.widgets_dir, 'settings', self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'Alerts.ui'), \
                prefix='alrt')

        self._alert_text = _('Alert me when I reach %(percent)s%% of the reference data volume (%(data)s)')

        self._alert_widgets = [
            self.limit1_checkbutton,
            self.limit2_checkbutton,
            self.limit3_checkbutton,
            self.limit4_checkbutton,
        ]

        self._alert_roaming_widgets = [
            self.ro_limit1_checkbutton,
            self.ro_limit2_checkbutton,
            self.ro_limit3_checkbutton,
            self.ro_limit4_checkbutton,
        ]

        self._alert_labels = [
            self.limit1_label,
            self.limit2_label,
            self.limit3_label,
            self.limit4_label,
        ]

        self._alert_roaming_labels = [
            self.ro_limit1_label,
            self.ro_limit2_label,
            self.ro_limit3_label,
            self.ro_limit4_label,
        ]

        self.__init_dialog()

        # IMSI, identifies the latest known SIM card
        self.__imsi = self._conf.get_last_imsi_seen()
        if not self._conf.is_last_imsi_seen_valid():
            self.main_vbox.set_sensitive(False)
        else:
            self.__load_data(is_roaming = False)
            self.__load_data(is_roaming = True)

        # Connect signals
        self.__connect_signals()

        self.ref_label_connected = replace_wrap_label(self.ref_label_connected)
        self.ref_label_roaming = replace_wrap_label(self.ref_label_roaming)
        self.ref_label_connected.set_markup(_("<b>When connected via %s network...</b>") % \
                self._conf.get_network_mnemonic())
        self.add(self.main_vbox)

    def __init_dialog(self):
        self.__init_reference_volume(is_roaming = False)
        self.__init_reference_volume(is_roaming = True)

        self.__init_alerts(is_roaming = False)
        self.__init_alerts(is_roaming = True)

    def __connect_signals(self):
        # UI signals
        self._widget_signals = []
        signal_id = self.ref_data_combobox.connect('changed', self.__on_monthly_data_limits_changed, False)
        self._widget_signals.append((self.ref_data_combobox, signal_id))
        signal_id = self.ref_ro_data_combobox.connect('changed', self.__on_monthly_data_limits_changed, True)
        self._widget_signals.append((self.ref_ro_data_combobox, signal_id))
        signal_id = self.ref_data_other_spinbutton.connect('value-changed', self.__on_custom_monthly_data_limit_changed, False)
        self._widget_signals.append((self.ref_data_other_spinbutton, signal_id))
        signal_id = self.ref_ro_data_other_spinbutton.connect('value-changed', self.__on_custom_monthly_data_limit_changed, True)
        self._widget_signals.append((self.ref_ro_data_other_spinbutton, signal_id))

        for alert in self._alert_widgets:
            alert.connect('toggled', self.__on_alert_checkbutton_toggled, False)
        for alert in self._alert_roaming_widgets:
            alert.connect('toggled', self.__on_alert_checkbutton_toggled, True)

        self._conf.connect("alerts-info-changed", self.__alerts_info_changed_cb)
        self._conf.connect('monthly-limit-changed', self.__on_monthly_limit_changed)
        self._conf.connect('last-imsi-seen-changed', self.__on_imsi_changed)

    def __init_reference_volume(self, is_roaming):
        if not is_roaming:
            self._monthly_limits = self._conf.get_monthly_limits(is_roaming)
            monthly_limits = self._monthly_limits
            combobox = self.ref_data_combobox
            hbox = self.ref_data_other_hbox
        else:
            self._monthly_ro_limits = self._conf.get_monthly_limits(is_roaming)
            monthly_limits = self._monthly_ro_limits
            combobox = self.ref_ro_data_combobox
            hbox = self.ref_ro_data_other_hbox

        model = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        for limit in monthly_limits:
            if limit == -1:
                model.append([-1, _("Other")])
            else:
                limit_str = format_to_maximun_unit_one_decimal(int(limit) * 1024, "GB", "MB", "KB")
                model.append([limit, limit_str])

        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)

        default_limit = self._conf.get_default_selected_monthly_limit(is_roaming)
        index = monthly_limits.index(default_limit)
        combobox.set_active(index)

        if default_limit == -1:
            hbox.show_all()
        else:
            hbox.hide()

    def __init_alerts(self, is_roaming = False):
        self._alerts = self._conf.get_alerts(is_roaming)
        enabled_alerts = self._conf.get_default_enabled_alerts(is_roaming)
        if not is_roaming:
            alert_widgets = self._alert_widgets
        else:
            alert_widgets = self._alert_roaming_widgets

        for i in range(0, 4):
            alert = self._alerts[i]
            is_enabled = alert in enabled_alerts
            checkbutton = alert_widgets[i]
            checkbutton.set_active(is_enabled)

        monthly_limit = self._conf.get_default_selected_monthly_limit(is_roaming)
        self.__update_labels(monthly_limit, is_roaming)


    def __load_data(self, is_roaming):
        self.main_vbox.set_sensitive(True)

        if not is_roaming:
            monthly_limits = self._monthly_limits
            combobox = self.ref_data_combobox
            hbox = self.ref_data_other_hbox
            spinbutton = self.ref_data_other_spinbutton
            alert_widgets = self._alert_widgets
        else:
            monthly_limits = self._monthly_ro_limits
            combobox = self.ref_ro_data_combobox
            hbox = self.ref_ro_data_other_hbox
            spinbutton = self.ref_ro_data_other_spinbutton
            alert_widgets = self._alert_roaming_widgets

        # Monthly limits
        monthly_limit = self._conf.get_imsi_based_selected_monthly_limit(self.__imsi, is_roaming)
        index = monthly_limits.index(monthly_limit)
        combobox.set_active(index)

        # Other monthly limits
        other_monthly_limit = self._conf.get_imsi_based_other_monthly_limit(self.__imsi, is_roaming)
        spinbutton.set_value(other_monthly_limit)
        if monthly_limit == -1:
            hbox.show_all()
            monthly_limit = other_monthly_limit
        else:
            hbox.hide()

        # Alerts
        enabled_alerts = self._conf.get_imsi_based_enabled_alerts(self.__imsi, is_roaming)
        for i in range(0, 4):
            checkbutton = alert_widgets[i]
            alert = self._alerts[i]
            is_enabled = alert in enabled_alerts
            checkbutton.set_active(is_enabled)

        self.__update_labels(monthly_limit, is_roaming)


    def __update_labels(self, monthly_limit, is_roaming):
        if not is_roaming:
            alert_widgets = self._alert_labels
        else:
            alert_widgets = self._alert_roaming_labels

        for i in range(0, 4):
            checkbutton = alert_widgets[i]
            alert = self._alerts[i]
            avail_data = monthly_limit * alert * 1024 / 100.0
            percent = str(alert)
            data = format_to_maximun_unit_one_decimal(avail_data, "GB", "MB", "KB")
            checkbutton.set_label(self._alert_text % {'percent' : percent, 'data' : data})


    ### UI callbacks ###

    def __on_alert_checkbutton_toggled(self, widget, is_roaming):
        if not is_roaming:
            alert_widgets = self._alert_widgets
        else:
            alert_widgets = self._alert_roaming_widgets

        for i in range(0, 4):
            alert = self._alerts[i]
            checkbutton = alert_widgets[i]
            is_enabled = checkbutton.get_active()
            self._conf.enable_imsi_based_alert(self.__imsi, alert, is_enabled, is_roaming)

    def __on_monthly_data_limits_changed(self, widget, is_roaming = False):
        active = widget.get_active()

        if not is_roaming:
            new_monthly_limit = self._monthly_limits[active]
            hbox = self.ref_data_other_hbox
        else:
            new_monthly_limit = self._monthly_ro_limits[active]
            hbox = self.ref_ro_data_other_hbox
        self._conf.set_imsi_based_selected_monthly_limit(self.__imsi, new_monthly_limit, is_roaming)
        if new_monthly_limit == -1:
            other_monthly_limit = self._conf.get_imsi_based_other_monthly_limit(self.__imsi, is_roaming)
            new_monthly_limit = other_monthly_limit
            hbox.show_all()
        else:
            hbox.hide()

        self.__update_labels(new_monthly_limit, is_roaming)

    def __on_custom_monthly_data_limit_changed (self, widget, is_roaming = False):
        if not is_roaming:
            spinbutton = self.ref_data_other_spinbutton
        else:
            spinbutton = self.ref_ro_data_other_spinbutton
        new_monthly_limit = spinbutton.get_value_as_int()
        if new_monthly_limit >= 1:
            self._conf.set_imsi_based_other_monthly_limit(self.__imsi, new_monthly_limit, is_roaming)
            self.__update_labels(new_monthly_limit, is_roaming)


    ### Configuration changes callbacks ###

    def __alerts_info_changed_cb (self, conf):
        self.__load_data(False)
        self.__load_data(True)

    def __on_monthly_limit_changed(self, sender):
        self.__load_data(False)
        self.__load_data(True)

    def __on_imsi_changed(self, sender, imsi):
        self.__imsi = imsi
        self.main_vbox.set_sensitive(True)

        for widget, signal_id in self._widget_signals:
            widget.handler_block(signal_id)

        self.__load_data(False)
        self.__load_data(True)

        for widget, signal_id in self._widget_signals:
            widget.handler_unblock(signal_id)
