#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
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

import tgcm.core.FreeDesktop
import tgcm.core.TrafficManager
import tgcm.core.Theme

import tgcm.ui.windows
from tgcm.ui.MSD.MSDUtils import format_to_maximun_unit, gtk_builder_magic


class BillingInfo (gtk.HBox) :
    def __init__(self):
        gtk.HBox.__init__(self)

        self._theme_path = 'dock/TrafficZone'

        self.widget_dir = os.path.join(tgcm.widgets_dir , 'traffic', self.__class__.__name__)
        self.traffic_manager = tgcm.core.TrafficManager.TrafficManager()
        self.conf = tgcm.core.Config.Config(tgcm.country_support)
        self._mcontroller = tgcm.core.FreeDesktop.DeviceManager()
        self._theme_manager = tgcm.core.Theme.ThemeManager()

        if tgcm.country_support == "uk":
            gtk_builder_magic(self, \
                    filename=os.path.join(self.widget_dir, 'BillingInfoUK.ui'), \
                    prefix='bi')
            self.my_details_button.connect("clicked", self.__on_my_details_button_clicked, None)
        elif tgcm.country_support == "es":
            gtk_builder_magic(self, \
                    filename=os.path.join(self.widget_dir, 'BillingInfoES.ui'), \
                    prefix='bi')
        else:
            gtk_builder_magic(self, \
                    filename=os.path.join(self.widget_dir, 'BillingInfo.ui'), \
                    prefix='bi')

        self.add(self.main_widget)

        self.datatransfered_image = gtk.image_new_from_file(self._theme_manager.get_icon(self._theme_path, 'loads_0.png'))

        if tgcm.country_support == "uk" :
            self.eventbox1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
            self.eventbox2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
            self.eventbox3.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

            self.datatransfered_alignment.hide ()

        elif tgcm.country_support == "es" :
            self.sms_total_title_label.set_markup('<small>%s</small>' % self.conf.get_company_name())
            self.main_widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

        else:
            self.sms_total_title_label.set_markup('<small>%s</small>' % self.conf.get_company_name())
            self.main_widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
            self.datatransferedprogressbar_alignment.add (self.datatransfered_image)
            self.datatransferedprogressbar_alignment.show_all()
            self.tl_vbox.set_tooltip_text(_("Data limit at maximun speed"))
            self.ad_vbox.set_tooltip_text(_("Available data at maximun speed"))



        # Load initial form values
        imsi = self.conf.get_last_imsi_seen()
        data = self.traffic_manager.get_current_traffic_data()
        self.__load_data(data['data_used'], data['data_used_roaming'], data['data_limit'], data['billing_period'])
        self.__load_sms_info(self.conf, imsi)

        # Connect signals
        self.traffic_manager.connect('traffic-data-changed', self.__on_traffic_data_changed)
        self.conf.connect('last-imsi-seen-changed', self.__on_last_imsi_changed)
        self.conf.connect("sms-counter-changed", self.__on_sms_counter_changed)
        self.conf.connect("sms-counter-reset", self.__on_sms_counter_reset)

    def __load_data(self, data_used, data_used_roaming, data_limit, billing_period):
        data_used_string = format_to_maximun_unit(data_used ,"GB","MB","KB","Bytes")
        self.data_used_label.set_markup("<b>%s</b>" % data_used_string)

        data_used_roaming_string = format_to_maximun_unit(data_used_roaming, "GB", "MB", "KB", "Bytes")
        self.roaming_data_used_label.set_markup("<b>%s</b>" % data_used_roaming_string)

        if tgcm.country_support!='es':
            data_limit_string = format_to_maximun_unit(data_limit ,"GB","MB","KB","Bytes")
            self.transference_limit_label.set_markup("<b>%s</b>" % data_limit_string)

            data_available = 0 if (data_used > data_limit) else (data_limit - data_used)
            data_available_string = format_to_maximun_unit(data_available, "GB", "MB", "KB", "Bytes")
            self.available_data_label.set_markup("<b>%s</b>" % data_available_string)

            progressbar_fraction = float(data_used) / data_limit
            if progressbar_fraction > 1:
                progressbar_fraction = 1.0
            progressbar_fraction = round(progressbar_fraction * 100)
            self.__load_progressbar_image(progressbar_fraction)

        if tgcm.country_support == "uk" :
            if progressbar_fraction >= 100:
                self.warning_exceeded_label.show()
            else:
                self.warning_exceeded_label.hide()

    def __load_progressbar_image (self, fraction):
        if fraction >= 0 and fraction < 1:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_0.png')
        elif fraction >= 1 and fraction < 10:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_1.png')
        elif fraction >= 10 and fraction < 20:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_1.png')
        elif fraction >= 20 and fraction < 30:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_2.png')
        elif fraction >= 30 and fraction < 40:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_3.png')
        elif fraction >= 40 and fraction < 50:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_4.png')
        elif fraction >= 50 and fraction < 60:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_5.png')
        elif fraction >= 60 and fraction < 70:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_6.png')
        elif fraction >= 70 and fraction < 80:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_7.png')
        elif fraction >= 80 and fraction < 90:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_8.png')
        elif fraction >= 90 and fraction < 100:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_9.png')
        else:
            image = self._theme_manager.get_icon (self._theme_path, 'loads_10.png')

        self.datatransfered_image.set_from_file (image)

    def __load_sms_info(self, conf, imsi):
        sms_normal  = conf.get_sms_sent(False, imsi)
        sms_roaming = conf.get_sms_sent(True, imsi)
        sms_total   = sms_normal + sms_roaming

        self.sms_total_label.set_markup("<b>%s</b>" % sms_total)
        self.sms_roaming_label.set_markup("<b>%s</b>" % sms_roaming)

    ## Callbacks

    def __on_traffic_data_changed(self, traffic_manager, data_used, data_used_roaming, data_limit, billing_period):
        self.__load_data(data_used, data_used_roaming, data_limit, billing_period)

    def __on_last_imsi_changed(self, conf, imsi):
        self.__load_sms_info(conf, imsi)

    def __on_sms_counter_changed(self, conf, imsi):
        self.__load_sms_info(conf, imsi)

    def __on_sms_counter_reset(self, conf):
        self.sms_total_label.set_markup("<b>0</b>")
        self.sms_roaming_label.set_markup("<b>0</b>")

    def __on_my_details_button_clicked (self, widget, data):
        preferences_dialog = tgcm.ui.windows.Settings()
        preferences_dialog.run("General>1")

if __name__ == '__main__':
    w = gtk.Window()
    b = BillingInfo()
    w.add(b)
    w.show_all()
    gtk.main()
