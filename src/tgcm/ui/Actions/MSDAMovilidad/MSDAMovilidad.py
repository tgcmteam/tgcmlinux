#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#           Cesar Garcia <tapia@openshine.com>
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

import tgcm
import tgcm.core.DeviceManager
import tgcm.core.FreeDesktop
import tgcm.core.HotSpotsService
import tgcm.core.Signals
import tgcm.ui.MSD
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, gtk_sleep

from MobileManager.MobileManagerDbus import MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI
from MobileManager import CARD_STATUS_READY


class MSDAMovilidad(tgcm.ui.MSD.MSDAction):

    # -- Enable/Disable the search button after the function execution
    class SearchButtonSensitive():

        def __init__(self, activate):
            self.__activate = activate

        def __call__(self, func):
            activate_search_button = self.__activate
            def newf(self, *args, **kwargs):
                retval = func(self, *args, **kwargs)
                self.search_button.set_sensitive(activate_search_button)
                return retval
            return newf

    def __init__(self):
        tgcm.ui.MSD.MSDAction.__init__(self, "wifi")

        self.mcontroller = tgcm.core.FreeDesktop.DeviceManager()
        self.main_modem  = self.mcontroller.main_modem
        self.hs_service = tgcm.core.HotSpotsService.HotSpotsService()
        self.taskbar_icon_name = 'wifi_taskbar.png'
        self.security_manager = tgcm.ui.MSD.MSDSecurityManager()
        self._theme_manager = tgcm.core.Theme.ThemeManager()
        self.action_dir = os.path.join(tgcm.actions_data_dir , self.codename)
        self.XMLTheme = tgcm.core.XMLTheme.XMLTheme ()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()

        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir, 'MSDAMovilidad_main.ui'), \
                prefix='wa')

        if tgcm.country_support != 'es':
            self.request_password_vbox.hide()

        if tgcm.country_support == 'uk':
            self.state_combobox.hide()
            self.state_label.hide()

        service_name = self._get_conf_key_value("name")
        self.wifiareas_dialog = tgcm.ui.windows.ServiceWindow('banner.wifi', service_name)
        self.wifiareas_dialog.add(self.main_widget)
        self.window_icon_path = self._theme_manager.get_icon ('icons', self.taskbar_icon_name)
        self.wifiareas_dialog.set_icon_from_file(self.window_icon_path)

        column = gtk.TreeViewColumn("Name",
                                    gtk.CellRendererText(),
                                    markup=0)
        self.search_treeview.append_column(column)
        self.search_treeview.set_model(gtk.ListStore(str))

        self.__init_comboboxes()

        self.wifiareas_dialog.connect('delete-event', self.__close_button_clicked_cb)
        self.wifiareas_dialog.close_button.connect('clicked', self.__close_button_clicked_cb)
        self.search_button.connect("clicked", self.__search_button_cb, None)
        self.request_button.connect("clicked", self.__request_button_cb, None)

        url = self.conf.get_wifi_url()
        if len(url) > 0:
            self.check_online_link.set_uri(url)
            self.check_online_link.set_tooltip_text('')
        else:
            self.check_online_link.hide()

        self.main_modem.connect("main-modem-removed", self.__main_modem_removed_cb)
        self.main_modem.connect("main-modem-changed", self.__main_modem_changed_cb)
        self.mcontroller.connect("active-dev-card-status-changed", self.__active_device_card_status_changed)
        self.hs_service.connect("hotspots-updated", self.__hotspots_updated)

        _signals = [
            ['state', self.state_combobox, 'changed', self.__province_combobox_changed_cb],
            ['city', self.city_combobox, 'changed', self.__city_combobox_changed_cb],
            ['zipcode', self.zipcode_combobox, 'changed', self.__zipcode_combobox_changed_cb],
            ['type', self.type_combobox, 'changed', self.__type_combobox_changed_cb],
            ['location', self.location_entry, 'changed', self.__location_entry_activate_cb],
        ]
        self.__signals = tgcm.core.Signals.GobjectSignals(_signals)

        self.location_entry.set_tooltip_text (_("Enter a letter of the location you want to find and click search."))
        self.location_label.set_tooltip_text (_("Enter a letter of the location you want to find and click search."))
        self.zipcode_combobox.set_tooltip_text (_("Enter a letter or a number of the postcode you want to find and click search."))
        self.zipcode_label.set_tooltip_text (_("Enter a letter or a number of the postcode you want to find and click search."))

        self.__refresh_update_date_label()
        self.request_button.set_sensitive(False)

    def __refresh_update_date_label(self):
        updated = self.hs_service.get_update_date()
        if updated is not None:
            self.update_date_label.set_visible(True)
            self.update_date_label.set_text(_("Updated on %s") % updated)
        else:
            self.update_date_label.set_visible(False)

    def launch_action(self, params=None):
        self.wifiareas_dialog.show()
        return True

    def close_action(self, params=None):
        self.wifiareas_dialog.hide()

    def __close_button_clicked_cb(self, *args):
        self.wifiareas_dialog.hide()
        return True

    def __hotspots_updated(self, hs_service):
        tgcm.debug("Hotspots updated !!")
        self.__refresh_update_date_label()

        # Remove old comboboxes and create new ones. That is far less
        # resource expensive than attempting to clear the models
        for vbox, combobox in ((self.state_vbox, self.state_combobox),
            (self.city_vbox, self.city_combobox),
            (self.type_vbox, self.type_combobox),
            (self.zipcode_vbox, self.zipcode_combobox)):
            vbox.remove(combobox)

        self.__init_comboboxes()

    def __init_comboboxes(self):
        tgcm.debug("init comboboxes")

        self.state_combobox = gtk.combo_box_entry_new_text()
        self.city_combobox = gtk.combo_box_entry_new_text()
        self.type_combobox = gtk.combo_box_entry_new_text()
        self.zipcode_combobox = gtk.combo_box_entry_new_text()

        foo = ((self.state_vbox, self.state_combobox, self.hs_service.get_states_list),
            (self.city_vbox, self.city_combobox, self.hs_service.get_cities_list),
            (self.type_vbox, self.type_combobox, self.hs_service.get_types_list),
            (self.zipcode_vbox, self.zipcode_combobox, self.hs_service.get_zipcodes_list))

        for vbox, combobox, function in foo:
            vbox.add(combobox)
            combobox.show()
            for row in function():
                combobox.append_text(row)
            combobox.set_active(0)

        tgcm.debug("end comboboxes")

    def __init_search_treeview(self):
        model = self.search_treeview.get_model()
        for row in self.wifiareas_info["hotspots"] :
            name = "<b>%s</b>\n<small>%s</small>\n<small>%s - %s - %s</small>" % (row[1], row[2], row[4], row[3], row[5])
            model.append([name, row[4], row[3],row[6]])

    @SearchButtonSensitive(False)
    def __search_button_cb(self, widget, data):
        model = self.search_treeview.get_model()
        model.clear()

        state_re=None
        city_re=None
        type_re=None
        zipcode_re=None
        location_re=None

        if self.state_combobox.get_active_text() != _("All") :
            if len(self.state_combobox.get_active_text()) != 0 :
                state_re = self.state_combobox.get_active_text()

        if self.city_combobox.get_active_text() != _("All") :
            if len(self.city_combobox.get_active_text()) != 0 :
                city_re = self.city_combobox.get_active_text()

        if self.type_combobox.get_active_text() != _("All") :
            if len(self.type_combobox.get_active_text()) != 0 :
                type_re = self.type_combobox.get_active_text()

        if self.zipcode_combobox.get_active_text() != _("All") :
            if len(self.zipcode_combobox.get_active_text()) != 0 :
                zipcode_re = self.zipcode_combobox.get_active_text()

        if len(self.location_entry.get_text()) != 0 :
            location_re = self.location_entry.get_text()

        widget.set_sensitive(False)
        progress = tgcm.ui.MSD.MSDProgressWindow()
        progress.set_show_buttons(False)
        progress.show(_("Please wait a minute..."), _("Please wait a minute..."))
        mainloop =  gobject.MainLoop(is_running=True)
        context = mainloop.get_context()

        aps = self.hs_service.search_hotspots(state_re, city_re, type_re, zipcode_re, location_re)
        if len(aps) == 0:
            model.append([ _("There are no Wi-Fi\naccess points with the selected criteria.") ])
        else:
            for row in aps:
                model.append([row])

        progress.hide()
        progress.progress_dialog.destroy()

    def __request_button_cb(self, widget, data):
        self.progress = tgcm.ui.MSD.MSDProgressWindow()
        self.progress.set_show_buttons(False)
        self.progress.show(_("Please wait a minute..."), _("Please wait a minute..."))

        self.progress.progressbar.hide()
        gtk_sleep(0.5)


        mainloop =  gobject.MainLoop(is_running=True)
        context = mainloop.get_context()

        while context.pending() :
            context.iteration()

        dev = self.mcontroller.get_main_device()
        cover_key = ""

        if dev != None and dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM  and dev.get_card_status() == CARD_STATUS_READY:
            if dev.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) :
                tgcm.debug("Sending ussd code : %s" % self._get_conf_key_value("ussd"))
                cover_key = dev.get_cover_key(self._get_conf_key_value("ussd"),
                                               self.__cover_key_func,
                                               self.__cover_key_error_func)
                return

        self.progress.hide()


    def __cover_key_func(self, response):
        self.progress.hide()
        self.progress.progress_dialog.destroy()

        action_dir = os.path.join(tgcm.actions_data_dir , self.codename)
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK, parent = self.wifiareas_dialog)
        dlg.set_icon_from_file(self.window_icon_path)
        dlg.set_title (_(u'Sending message'))
        dlg.set_markup(_("<b>Answer received:</b>"))
        if response=='':
            response=_('Service not available. Please try again later.')
        dlg.format_secondary_markup("'%s'" % response)

        dlg.run()
        dlg.destroy()

    def __cover_key_error_func(self, e):
        self.progress.hide()
        self.progress.progress_dialog.destroy()

        action_dir = os.path.join(tgcm.actions_data_dir , self.codename)
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK, parent = self.wifiareas_dialog)
        dlg.set_icon_from_file (self.window_icon_path)
        dlg.set_title (_(u'Sending message'))
        dlg.set_markup("<b>Answer received:</b>")
        dlg.format_secondary_markup("'%s'" % _("Service not available"))

        dlg.run()
        dlg.destroy()

    def __main_modem_removed_cb (self, main_modem, opath):
        self.request_button.set_sensitive(False)

    def __main_modem_changed_cb (self, main_modem, opath, device):

        if device is not None and device.get_card_status() == CARD_STATUS_READY :
            self.request_button.set_sensitive(True)
        else:
            self.request_button.set_sensitive(False)


    def __active_device_card_status_changed (self, mcontroller, status):
        dev = self.mcontroller.get_main_device()
        cover_key = ""

        if dev == None :
            self.request_button.set_sensitive(False)
            return

        if dev != None and dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            if dev.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) and status == CARD_STATUS_READY:
                self.request_button.set_sensitive(True)
                return

        self.request_button.set_sensitive(False)

    def show_all(self):
        tgcm.ui.MSD.MSDAction.show_all(self)
        self.connection_vbox.hide()

    def __show_error_msg(self, title, msg):
        dlg = gtk.MessageDialog(parent         = self.wifiareas_dialog,
                                flags          = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                type           = gtk.MESSAGE_ERROR,
                                buttons        = gtk.BUTTONS_OK,
                                message_format = msg)
        dlg.set_title(title)
        dlg.run()
        dlg.hide()

    @SearchButtonSensitive(True)
    def __province_combobox_changed_cb(self, widget):
        self.__combobox_change_handler(province = widget.get_active_text())

    @SearchButtonSensitive(True)
    def __city_combobox_changed_cb(self, widget):
        self.__combobox_change_handler(city = widget.get_active_text())

    @SearchButtonSensitive(True)
    def __zipcode_combobox_changed_cb(self, widget):
        self.__combobox_change_handler(zipcode = widget.get_active_text())

    @SearchButtonSensitive(True)
    def __type_combobox_changed_cb(self, widget):
        pass

    @SearchButtonSensitive(True)
    def __location_entry_activate_cb(self, *args):
        pass

    def __combobox_change_handler(self, province=None, city=None, zipcode=None):
        provinces = None
        cities    = None
        zipcodes  = None

        # -- If the province changes, the other boxes will be reset to ALL with the  new
        # -- entries of this province
        if province is not None:
            if province != self.hs_service.VALUE_ALL:
                cities   = self.hs_service.get_cities_of_province(province)
                zipcodes = self.hs_service.get_zipcodes_of_province(province)
            else:
                cities   = self.hs_service.get_cities_list()
                zipcodes = self.hs_service.get_zipcodes_list()

        elif city is not None:
            # -- When the City combo changes to ALL need to select all the zipcodes of the province
            # -- otherwise select the zipcodes  of the selected city
            province = self.state_combobox.get_active_text()
            if city != self.hs_service.VALUE_ALL:
                zipcodes = self.hs_service.get_zipcodes(province, city)
            else:
                # -- When the city changes to ALL provide all the available zipcodes for the city
                zipcodes = self.hs_service.get_zipcodes_of_province(province)

        elif zipcode is not None:
            pass

        # -- Now update all the comboboxes
        if provinces is not None:
            self.__update_combobox_blocking(self.state_combobox, provinces, 'province')
        if cities is not None:
            self.__update_combobox_blocking(self.city_combobox, cities, 'city')
        if zipcodes is not None:
            self.__update_combobox_blocking(self.zipcode_combobox, zipcodes, 'zipcode')

    # -- We must block the signals when changing the comboboxes otherwise the callbacks are called!
    def __update_combobox_blocking(self, box, values, signal_key):
        self.__signals.block_by_key(signal_key)
        self.__update_combobox(box, values)
        self.__signals.unblock_by_key(signal_key)

    def __update_combobox(self, box, values):
        liststore = gtk.ListStore(str)
        liststoresort = gtk.TreeModelSort(liststore)

        box.set_property("text-column", 0)
        box.set_model(liststoresort)

        if type(values) != type([ ]):
            values = [values]
        for value in values:
            liststore.append([ value ])
        box.set_active(0)
