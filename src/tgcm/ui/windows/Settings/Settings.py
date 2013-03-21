#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
#
# Copyright (c) 2003-2007, Telefonica Móviles España S.A.U.
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

import gtk
import pango
import gobject

import tgcm.core.Actions
import tgcm.core.FreeDesktop
import tgcm.core.Singleton

import tgcm.ui.widgets.settings
import tgcm.ui.windows


class Settings(gobject.GObject):
    __metaclass__ = tgcm.core.Singleton.Singleton

    __gsignals__ = {
        # The intention of this callback is to notify when the 'Settings' dialog is about
        # to be closed. Any component of this dialog could use this signal for example to
        # check and save its contents before the dialog is closed.
        #
        # This callback uses the generic 'gobject.signal_accumulator_true_handled()'. That means
        # it will interrupt the notification chain if any callback returns True.
        # If a component connected to this signal could not save its data because its not valid,
        # it should then return True and notify accordingly the user.
        'is-closing' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (), \
                gobject.signal_accumulator_true_handled)
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.conf = tgcm.core.Config.Config()
        self.actions_manager = tgcm.core.Actions.ActionManager()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.theme_manager = tgcm.core.Theme.ThemeManager()

        # -- IMPORTANT: Dont change the name as this dialog is used as parent for other widgets (see below exec)
        self.dialog = tgcm.ui.windows.Dialog(buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        parent = tgcm.ui.ThemedDock().get_main_window()
        self.dialog.set_transient_for(parent)

        window_icon_path = self.theme_manager.get_icon ('icons', 'settings_taskbar.png')
        self.dialog.set_icon_from_file(window_icon_path)

        width = 750
        height = 550
        min_width = 600
        min_height = 450
        max_width = gtk.gdk.screen_width()
        max_height = gtk.gdk.screen_height()

        self.dialog.set_geometry_hints(None, \
                min_height=min_height, max_height=max_height, \
                min_width=min_width, max_width=max_width)
        self.dialog.resize(width, height)

        self.__general_notebook = gtk.Notebook()
        self.__general_notebook.set_show_tabs(False)
        self.__general_notebook.set_show_border(True)

        self.services_vbox = gtk.VBox()
        self.services_vbox.unparent()
        self.services_vbox.set_spacing(12)
        self.__general_notebook.append_page(self.services_vbox)

        self.__general_treeview = gtk.TreeView()
        self.__create_treeview()

        self.__sections = {}
        self.__sections_order = ['General', 'Dock', 'Devices', 'Connections', 'Services']
        if self.conf.is_alerts_available():
            self.__sections_order.append('Alerts')

        self.__section_titles = {
            'General' : _('Options'),
            'Dock' : _('Display'),
            'Devices' : _('Devices'),
            'Connections' : _('My Internet connections'),
            'Services' : _('Services'),
            'Alerts' : _('Alerts')
        }

        if tgcm.country_support == 'uk':
            self.__section_titles['Dock'] = _('Appearance')

        self.__load_sections()
        self.__load_treeview()

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        scrolled_window.add(self.__general_treeview)

        hpaned = gtk.HPaned()
        hpaned.pack1(scrolled_window) #, resize=False, shrink=False)
        hpaned.pack2(self.__general_notebook) #, resize=True, shrink=False)
        hpaned.set_border_width(5)
        hpaned.set_position(200)

        self.services_vbox.show()
        scrolled_window.show()
        self.__general_treeview.show()
        self.__general_notebook.show()
        hpaned.show()

        self.dialog.set_title (_("%s - Settings") % self.conf.get_caption())
        self.dialog.add(hpaned)

        self.dialog.connect('response', self.__on_dialog_response)
        self.dialog.connect('close', self.__on_dialog_close)
        self.dialog.connect('delete_event', self.__on_dialog_close)

    def get_dialog(self):
        return self.dialog

    def run (self, section=None):
        self.dialog.show()
        self.show_section(section)
        self.dialog.run()

    def show_section (self, section):
        subsection = None
        tab = None

        if section != None:
            if section.find('|') >= 0:
                section, subsection = section.split('|')
            elif section.find('>') >= 0:
                section, tab = section.split('>')
                tab = int (tab)
            else:
                subsection = None

            if section in self.__sections_order:
                model = self.__general_treeview.get_model()
                selection = self.__general_treeview.get_selection()
                iteration = model.get_iter_first()
                while iteration != None:
                    if model.get_value (iteration, 1) == section:
                        if subsection == None:
                            self.__general_treeview.set_cursor (model.get_path (iteration))
                            if section == "General" and tab != None:
                                current_page_number = self.__general_notebook.get_current_page()
                                current_page = self.__general_notebook.get_nth_page(current_page_number)
                                current_page.show_nth_tab(tab)
                            return
                        else:
                            if model.iter_has_child (iteration):
                                iteration = model.iter_children (iteration)
                                while iteration != None:
                                    if model.get_value (iteration, 1) == subsection:
                                        self.__general_treeview.expand_to_path (model.get_path (iteration))
                                        self.__general_treeview.set_cursor (model.get_path (iteration))
                                        return
                                    else:
                                        iteration = model.iter_next (iteration)
                    else:
                        iteration = model.iter_next (iteration)

    def __load_sections (self):
        for section in self.__sections_order:
            section_obj = None
            exec ('section_obj = tgcm.ui.widgets.settings.%s(self)' % section)
            section_obj.show()
            self.__sections[section] = section_obj
            self.__general_notebook.append_page(section_obj)

    def __create_treeview (self):
        base_id = 0
        for field in ["page", "section", "section_title"]:
            col = gtk.TreeViewColumn(field)
            self.__general_treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)

            if field == "section_title":
                col.set_visible (True)
                self.__general_treeview.set_tooltip_column(base_id)
            else:
                col.set_visible (False)

            base_id += 1

    def __load_treeview (self):
        model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)

        base_id = 1
        for section in self.__sections_order:
            iteration = model.append (None, ["section_%d" % base_id, section, self.__section_titles[section]])
            if section == "Services":
                self.__load_services (model, iteration)
            base_id = base_id + 1

        self.__general_treeview.set_model(model)
        self.__general_treeview.set_headers_visible(False)

        selection = self.__general_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect ('changed', self.__on_general_treeview_selection_changed)

    def __load_services (self, model, iteration):
        services = self.actions_manager.get_original_services_order ()
        for service in services:
            service_type, service_id = service.split(",")
            if service_type == "service" and  service_id != 'wifi' and service_id != 'prepay' and service_id != 'selfcare' :
                action_obj = self.actions_manager.get_action (service_id)
                model.append (iteration, ["action_%s" % service_id, service_id, action_obj.get_visible_action_name()])

    ### Some UI callbacks ###

    def __on_dialog_response(self, dialog, response, *args):
        # Emit the signal 'is-closing'. Thanks to this signal, all the elements in
        # 'Settings' dialog will attempt to validate and save the data which has not been
        # saved before. It returns a boolean which indicates if everything has gone well
        # or a problem has happened.
        is_closeable = not self.emit('is-closing')

        # The idea is to avoid closing the dialog until all the dialog fields are correct
        # and have been saved properly
        if is_closeable:
            self.dialog.hide()

    def __on_dialog_close(self, dialog, widget = None, event = None):
        # Avoid the 'Settings' dialog to be closed
        return gtk.TRUE

    def __on_general_treeview_selection_changed (self, selection):
        (model, iteration) = selection.get_selected()

        if iteration is not None:
            page_id =  model.get_value(iteration, 0)
            if page_id.startswith ("section_"):
                page = int (page_id.replace("section_", "", 1))
                self.__general_notebook.set_current_page (page)
            elif page_id.startswith ("action_"):
                children = self.services_vbox.get_children()
                if children is not None and len(children) > 0:
                    self.services_vbox.remove (children[0])
                action = page_id.replace("action_","",1)
                action_obj = self.actions_manager.get_action (action)
                self.services_vbox.add (action_obj.get_action_conf_widget())

                self.__general_notebook.set_current_page (0)

gobject.type_register(Settings)
