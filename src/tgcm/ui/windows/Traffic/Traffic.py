#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2003-2010, Telefonica Móviles España S.A.U.
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

import os
import datetime
import gtk
import gobject

import tgcm
import tgcm.core.Config
import tgcm.core.Theme

import tgcm.ui.windows
import tgcm.ui.widgets.traffic

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label, get_month_day

class Traffic:
    def __init__(self):
        self.windows_dir = os.path.join(tgcm.windows_dir , self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'Traffic.ui'), \
                prefix='trfc')

        self.message_label = replace_wrap_label(self.message_label)
        self.help_label = replace_wrap_label(self.help_label)
        self.warn_uk_label = replace_wrap_label(self.warn_uk_label)

        self.conf = tgcm.core.Config.Config()
        self.theme_manager = tgcm.core.Theme.ThemeManager()
        self.traffic_manager = tgcm.core.TrafficManager.TrafficManager()

        self.dialog = tgcm.ui.windows.ServiceWindow('banner.traffic', _('Traffic'))
        self.window_icon_path = self.theme_manager.get_icon('icons', 'traffic_taskbar.png')
        self.dialog.set_icon_from_file(self.window_icon_path)

        self.session_info = tgcm.ui.widgets.traffic.SessionInfo()
        self.billing_info = tgcm.ui.widgets.traffic.BillingInfo()
        self.dataused_info = tgcm.ui.widgets.traffic.DataUsedInfo(self.traffic_history_label)

        self.current_session_area.add(self.session_info)
        self.current_billing_day_area.add(self.billing_info)
        self.data_used_area.add(self.dataused_info)
        self.session_info.show()
        self.billing_info.show()
        self.dataused_info.show()

        self.__update_reset_history_button()

        self.reset_history_button.connect ("clicked", self.__on_reset_history_button_clicked)

        self.__update_billing_period_info_label()

        # Small hack to show smaller text in linkbuttons
        orig_label = self.change_billing_day_linkbutton.get_label()
        self.change_billing_day_linkbutton.set_label('<small>%s</small>' % orig_label)
        self.change_billing_day_linkbutton.child.set_use_markup(True)
        self.change_billing_day_linkbutton.set_tooltip_text('')

        if len(self.conf.get_selfcare_url()) > 0:
            self.help_linkbutton.set_label('<small>%s</small>' % self.conf.get_selfcare_url())
            self.help_linkbutton.child.set_use_markup(True)
            self.help_linkbutton.set_uri(self.conf.get_selfcare_url())
            self.help_linkbutton.set_tooltip_text('')
        else:
            self.help_label.hide()
            self.help_linkbutton.hide()

        self.dialog.add(self.main_widget)

        self.conf.connect('last-imsi-seen-changed', self.__on_last_imsi_changed)
        self.conf.connect('billing-day-changed', self.__on_billing_day_changed)
        self.conf.connect('fixed-billing-day-changed', self.__on_is_fixed_billing_day_changed)
        self.conf.connect('monthly-limit-changed', self.__on_monthly_limit_changed)
        self.traffic_manager.connect('billing-period-changed', self.__on_billing_period_changed)
        self.dialog.close_button.connect('clicked', self.__dialog_close_cb)
        self.dialog.connect('delete-event', self.__dialog_close_cb)

        self.__update_current_billing_period_label()

        self.dialog.resize(650, 600)


    def __update_reset_history_button(self):
        is_sensitive = self.conf.is_last_imsi_seen_valid()
        self.reset_history_button.set_sensitive(is_sensitive)

    def __update_billing_period_info_label (self):
        if tgcm.country_support != "uk" :
            if not self.conf.is_last_imsi_seen_valid():
                billing_day = self.conf.get_default_billing_day()
                is_fixed = self.conf.is_default_fixed_billing_day()
                is_imsi_valid = False
            else:
                imsi = self.conf.get_last_imsi_seen()
                billing_day = self.conf.get_imsi_based_billing_day(imsi)
                is_fixed = self.conf.is_imsi_based_fixed_billing_day(imsi)
                is_imsi_valid = True

            billing_day_start = get_month_day(billing_day)
            if billing_day <= 1:
                billing_day_end = get_month_day(31)
            else:
                billing_day_end = get_month_day(billing_day - 1)
            self.message_label.set_markup("<small>%s</small>" % \
                _("The billing period begins on the %s and ends on the %s of each month.") % \
                (billing_day_start, billing_day_end))

            self.notebook_tab_label1.set_text(_("Current period"))
            self.warn_uk_label.hide_all()
            self.warn_uk_label.set_no_show_all(True)

            if is_imsi_valid and not is_fixed:
                self.change_billing_day_linkbutton.show()
            else:
                self.change_billing_day_linkbutton.hide()
        else:
            self.message_label.hide()
            self.message_label.set_no_show_all(True)
            self.notebook_tab_label1.set_text(_("This month"))
            self.session_label.set_tooltip_text(_("This screen gives you information about your mobile broadband usage. 'This session' tells you about your current O2 data network or Wi-Fi connection. 'This month' shows your usage on the O2 data network only. For more information see the Help guide."))

            self.change_billing_day_button.hide_all()
            self.change_billing_day_button.set_no_show_all(True)

    def __on_reset_history_button_clicked (self, widget, data=None):
        message = _("You are going to delete all the history data. Are you sure?")
        dlg =gtk.MessageDialog(parent = self.dialog, type=gtk.MESSAGE_WARNING, \
                buttons=gtk.BUTTONS_OK_CANCEL, message_format=message)
        dlg.set_title(_("Restart accumulated traffic"))
        dlg.set_icon_from_file(self.window_icon_path)
        response = dlg.run()
        dlg.destroy()

        if response == gtk.RESPONSE_OK:
            imsi = self.conf.get_last_imsi_seen()
            self.conf.update_last_reset_datetime(imsi)
            self.traffic_manager.reset_history(imsi)
            self.__update_current_billing_period_label()
            self.dataused_info.reload_graph()

    def __update_current_billing_period_label(self):
        if (not self.conf.is_default_fixed_billing_day()) and self.conf.is_last_imsi_seen_valid():
            imsi = self.conf.get_last_imsi_seen()
            billing_period = self.conf.get_imsi_based_billing_period(imsi)
        else:
            imsi= ''
            billing_period = self.conf.get_default_billing_period()
        start_current_billing_period = billing_period[0]

        # A billing period may have not been completed yet the installation of TGCM. In that
        # case, the first day of that billing period is the day when TGCM was installed
        install_day = self.conf.get_install_date()
        if install_day > start_current_billing_period:
            start_current_billing_period = install_day

        # The history data may have been reseted any time in the billing period. In that case,
        # the first day of the billing period is the last day when history data was reseted
        if self.conf.is_last_imsi_seen_valid():
            last_reset_date = self.conf.get_last_reset_datetime(imsi).date()
            if last_reset_date > start_current_billing_period:
                start_current_billing_period = last_reset_date

        # Calculate the difference between today and the first day of current billing period
        today = datetime.date.today()
        delta = today - start_current_billing_period

        # Localized billing label string
        if tgcm.country_support == 'uk':
            billing_str = _('This month')
        else:
            billing_str = _('Current billing period')

        # It is necessary to increment the days difference by one
        day_str = _('day') if (delta.days + 1) == 1 else _('days')
        date_msg = _('%(delta_days)s %(day_str)s - from %(day)s/%(month)s/%(year)s until today') % { \
                'delta_days' : delta.days + 1, 'day_str' : day_str, 'day' : start_current_billing_period.day, \
                'month' : start_current_billing_period.month, 'year' : start_current_billing_period.year}
        self.billing_label.set_markup('<b>%s (%s)</b>' % (billing_str, date_msg))

        # Update title label from History tab
        storage = self.traffic_manager.get_storage()
        expenses_interval = storage.get_history_date_interval(imsi)
        sumary_str = _('<b>Summary from %s</b>') % expenses_interval[0].strftime('%b\'%y')
        self.traffic_history_label.set_markup(sumary_str)

    def __dialog_close_cb(self, *args):
        self.dialog.hide()
        return True

    def run(self):
        self.dialog.show()

    def destroy(self):
        self.dialog.destroy()

    def hide(self):
        self.dialog.hide()

    def show_change_billing_day_dialog(self):
        bd_dialog = BillingDayChangeDialog(_("Change your billing period"), self.dialog,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_OK, gtk.RESPONSE_OK))

        if not self.conf.is_last_imsi_seen_valid():
            billing_day = self.conf.get_default_billing_day()
        else:
            imsi = self.conf.get_last_imsi_seen()
            billing_day = self.conf.get_imsi_based_billing_day(imsi)
        bd_dialog.set_billing_day(billing_day)
        ret = bd_dialog.run()

        if ret == gtk.RESPONSE_OK :
            if self.conf.is_last_imsi_seen_valid():
                imsi = self.conf.get_last_imsi_seen()
                billing_day = bd_dialog.get_billing_day()
                self.conf.set_imsi_based_billing_day(imsi, billing_day)

        bd_dialog.destroy()
        self.__update_current_billing_period_label()

    ### Configuration changes callbacks ###

    def __on_last_imsi_changed(self, sender, new_imsi):
        self.__update_current_billing_period_label()
        self.__update_billing_period_info_label()
        self.dataused_info.reload_graph()
        self.__update_reset_history_button()

    def __on_billing_day_changed (self, conf, data=None):
        self.__update_current_billing_period_label()
        self.__update_billing_period_info_label()
        self.dataused_info.reload_graph()

    def __on_is_fixed_billing_day_changed(self, sender, is_fixed):
        self.__update_current_billing_period_label()
        self.__update_billing_period_info_label()
        self.dataused_info.reload_graph()

    def __on_billing_period_changed(self, sender, data=None):
        self.__update_current_billing_period_label()

    def __on_monthly_limit_changed(self, sender, data=None):
        self.dataused_info.reload_graph()


class BillingDayChangeDialog (gtk.Dialog) :
    def __init__(self, title=None, parent=None, flags=0, buttons=None, show_preferences_button=True, show_help_button=True):
        gtk.Dialog.__init__(self, title, parent, flags, buttons)
        self.set_has_separator(False)

        self.windows_dir = os.path.join(tgcm.windows_dir , "Traffic")
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'BillingDayChangeDialog.ui'), \
                prefix='bd')

        self.get_children()[0].add(self.main_widget)

        self._days = range(1, 32)
        if tgcm.country_support == 'es':
            self._days = (1, 10, 18, 24)

        model = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        for i in self._days:
            model.append([i, get_month_day(i)])
        self.billing_day_combobox.set_model(model)

    def get_billing_day(self):
        return self._days[self.billing_day_combobox.get_active()]

    def set_billing_day(self, billing_day):
        try:
            index = self._days.index(billing_day)
        except IndexError:
            index = 0
        self.billing_day_combobox.set_active(index)
        cell = gtk.CellRendererText()
        self.billing_day_combobox.pack_start(cell, True)
        self.billing_day_combobox.add_attribute(cell, 'text', 1)

if __name__ == '__main__':
    tgcm.country_support = "es"
    traffic = Traffic()
    traffic.dialog.run()
    gtk.main()
