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

import tgcm
import tgcm.core.Actions
import tgcm.core.Config

import tgcm.ui.ThemedDock
from tgcm.ui.widgets.dock.ServicesToolbar import BUTTON_VISIBLE, \
        BUTTON_NOT_VISIBLE, BUTTON_VISIBLE_IN_MORE
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label


class Dock (gtk.HBox):
    def __init__(self, parent=None):
        gtk.HBox.__init__(self)

        self.conf = tgcm.core.Config.Config()
        self.conf.connect('user-prepay-changed', self.__load_services_treeview)
        self.conf.connect('launcher-items-order-changed', self.__load_services_treeview)
        self.conf.connect('last-imsi-seen-changed', self.__load_services_treeview)

        self.action_manager = tgcm.core.Actions.ActionManager()
        self.action_manager.connect('action-install-status-changed', \
                self.__load_services_treeview)
        self.action_manager.connect('url-launcher-install-status-changed', \
                self.__load_services_treeview)

        self.widget_dir = os.path.join(tgcm.widgets_dir, 'settings', \
                self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'Dock.ui'), \
                prefix='dock')

        if tgcm.country_support == 'uk':
            self.title_label.set_text('<big><b>%s</b></big>' %_('Appearance'))

        # -- Replace the label for wrapping
        self.top_info_label = replace_wrap_label(self.top_info_label)

        self.add(self.main_container)

        self.selected = []

        self.__create_services_treeview ()
        self.__load_services_treeview ()

        self.up_button.connect ('clicked', self.__on_up_button_clicked)
        self.down_button.connect ('clicked', self.__on_down_button_clicked)
        self.up_button.set_sensitive (False)
        self.down_button.set_sensitive (False)


    def __on_up_button_clicked (self, widget, data=None):
        self.items = self.conf.get_launcher_items_order ()
        liststore = self.services_treeview.get_model()
        iter = liststore.get_iter_first()
        count = 0
        while True:
            selected = liststore[iter][1]
            if selected and count > 0:
                tmp = self.items[count]
                self.items[count] = self.items[count-1]
                self.items[count-1] = tmp

            iter = liststore.iter_next (iter)
            if iter is None:
                break

            count = count + 1

        self.conf.set_launcher_items_order (self.items)
        liststore.foreach (self.__liststore_foreach_cb)

    def __on_down_button_clicked (self, widget, data=None):
        self.items = self.conf.get_launcher_items_order ()
        liststore = self.services_treeview.get_model()
        length = len(self.items)-1
        count = length
        while True:
            if count < 0:
                break

            iter = liststore.get_iter(count)
            selected = liststore[iter][1]
            if selected and count < length:
                tmp = self.items[count]
                self.items[count] = self.items[count+1]
                self.items[count+1] = tmp

            count = count - 1

        self.conf.set_launcher_items_order (self.items)
        liststore.foreach (self.__liststore_foreach_cb)

    def __create_services_treeview (self):
        liststore = gtk.ListStore(str, 'gboolean', str, str)
        toggle_renderer = gtk.CellRendererToggle ()
        column = gtk.TreeViewColumn('services_selected',
                                    toggle_renderer,
                                    active=1)
        self.services_treeview.append_column(column)
        column = gtk.TreeViewColumn('services_name',
                                    gtk.CellRendererText(),
                                    text=2, foreground=3)
        self.services_treeview.append_column(column)

        self.services_treeview.set_model(liststore)

        treeselection = self.services_treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_SINGLE)
        treeselection.connect('changed', self.__on_services_treeview_selection_changed)

    def __on_services_treeview_selection_changed (self, selection):
        if selection.count_selected_rows() > 0:
            model, paths = selection.get_selected_rows()
            self.__on_toggle_renderer_toggled (path=paths[0])
            selection.unselect_all()

    def __load_services_treeview(self, *args, **kwargs):
        liststore = self.services_treeview.get_model()
        liststore.clear()

        service_status = tgcm.ui.ThemedDock().get_service_buttons_status()
        for item in self.conf.get_launcher_items_order():
            is_selected = item in self.selected

            status = service_status[item]
            if status == BUTTON_VISIBLE:
                foreground = 'blue'
            elif status == BUTTON_VISIBLE_IN_MORE:
                foreground = 'black'
            else:
                foreground = 'grey'

            if item in tgcm.dockables_info:
                name = tgcm.dockables_info[item]
            elif item in self.conf.get_url_launchers():
                name = self.conf.get_url_launcher(item)[1]
            else:
                service = self.action_manager.get_action(item)
                name = service.get_visible_action_name()

            liststore.append([item, is_selected, name, foreground])

    def __on_toggle_renderer_toggled (self, cell=None, path=None, data=None):
        liststore = self.services_treeview.get_model()
        liststore[path][1] = not liststore[path][1]

        if liststore[path][1]:
            self.selected.append (liststore[path][0])
        else:
            self.selected.remove (liststore[path][0])

        self.up_button.set_sensitive (False)
        self.down_button.set_sensitive (False)
        liststore.foreach (self.__liststore_foreach_cb)

    def __liststore_foreach_cb (self, liststore, path, iter, data=None):
        selected = liststore[path][1]
        if selected:
            first_item_iter = liststore.get_iter_first()
            first_item_path = liststore.get_path(first_item_iter)

            last_item_iter = first_item_iter
            while True:
                item_aux = liststore.iter_next(last_item_iter)
                if item_aux is None:
                    break
                else:
                    last_item_iter = item_aux
            last_item_path = liststore.get_path (last_item_iter)

            if first_item_path != path:
                self.up_button.set_sensitive (True)
            if last_item_path != path:
                self.down_button.set_sensitive (True)
