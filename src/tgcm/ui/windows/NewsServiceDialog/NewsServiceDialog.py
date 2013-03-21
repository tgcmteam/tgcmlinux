#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2003-2013, Telefonica Móviles España S.A.U.
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
import time
import webbrowser
import webkit

import tgcm
import tgcm.core.ConnectionManager
import tgcm.core.NewsService
import tgcm.core.Singleton
import tgcm.core.Theme
import xml.sax.saxutils as saxutils
from tgcm.core.NewsService import APP_START, APP_CONNECTED

import tgcm.ui.MSD
import tgcm.ui.windows

from mobilemanager.devices.ModemGsm import  ACCESS_TECH_GSM, \
    ACCESS_TECH_GSM_COMPACT, ACCESS_TECH_GPRS, ACCESS_TECH_EDGE

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, info_dialog, \
    format_to_maximun_unit, question_dialog, error_dialog


class NewsServiceDialog:

    __metaclass__ = tgcm.core.Singleton.Singleton

    def __init__(self):
        self.conf = tgcm.core.Config.Config()
        self.theme_manager = tgcm.core.Theme.ThemeManager()
        self.news_service = tgcm.core.NewsService.NewsService()
        self.conn_manager = tgcm.core.ConnectionManager.ConnectionManager()
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()

        self.progress_dialog = None
        self.dialog = None

        ## Callbacks
        self.news_service.connect('news-updated', self.__on_news_and_updates_updated)
        self.device_dialer.connect('connected', self.__on_connection_status_changed)
        self.device_dialer.connect('disconnected', self.__on_connection_status_changed)

    def show_news_if_required(self):
        '''
        Displays News And Updates automatically (e.g. at boot up or when a
        new WWAN device appears in the system.
        '''
        if not self.conf.get_rss_on_connect():
            return

        # Check if there are unseen news or updates
        show_news_and_updates_window = False
        for data in (self.news_service.get_news(), self.news_service.get_updates()):
            for row in data:
                if row['unseen']:
                    show_news_and_updates_window = True
                    break

        # There are unseen News or Updates
        if show_news_and_updates_window:
            self.show()

    def show(self, parent=None):
        '''
        Displays News And Updates dialog
        '''
#        # Update tabs labels
#        self.__update_tabs_label_numbers()

        if self.dialog is None:
            if parent is None:
                parent = tgcm.ui.ThemedDock().get_main_window()
            self.__create_dialog()
            self.dialog.set_transient_for(parent)

            # select which tab to show and show the dialog
            self.__select_tab_to_open()
            self.dialog.run()

            # After the dialog is closed, mark all the items
            # displayed as 'seen'
            for model in (self.news_model, self.updates_model):
                model.mark_current_items_seeen()

            self.dialog.destroy()
            self.dialog = None
        else:
            # If the News And Updates dialog is already open, bring
            # it to the front as there is some action or condition
            # that required its opening
            self.dialog.present()

    def __create_dialog(self):
        self.windows_dir = os.path.join(tgcm.windows_dir , self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'NewsServiceDialog.ui'), \
                prefix='nsd')

        self.dialog = tgcm.ui.windows.Dialog( \
                buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.dialog.set_title(_("%s - News and Updates") % self.conf.get_app_name())
        self.dialog.add(self.main_widget)

        # Somewhat ugly hack to add a responseless button to the
        # action area of a gtk.Window
        self.refresh_button = gtk.Button(stock=gtk.STOCK_REFRESH)
        action_area = self.dialog.get_action_area()
        action_area.pack_start(self.refresh_button)
        action_area.reorder_child(self.refresh_button, 0)
        self.refresh_button.show()

        self.show_all_button.set_active(True)
        self.are_all_news_shown = True

        self.news_view = webkit.WebView()
        self.updates_view = webkit.WebView()

        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        viewport.add(self.news_view)
        self.news_scrolledwindow.add(viewport)
        self.news_scrolledwindow.show_all()
        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        viewport.add(self.updates_view)
        self.updates_scrolledwindow.add(viewport)
        self.updates_scrolledwindow.show_all()

        self.news_view.load_string ('', "text/html", "", "file:///")
        self.updates_view.load_string ('', "text/html", "", "file:///")

        ## News TreeView widgets

        column = gtk.TreeViewColumn(_('Title'))
        column.set_expand(True)
        self.news_treeview.append_column(column)

        cellpb = gtk.CellRendererPixbuf()
        cell = gtk.CellRendererText()

        column.pack_start(cellpb, False)
        column.pack_start(cell, True)

        column.set_attributes(cellpb, pixbuf=1)
        column.set_attributes(cell, markup=2)

        column = gtk.TreeViewColumn(_('Date'), \
                gtk.CellRendererText(), \
                markup=3)
        self.news_treeview.append_column(column)

        self.news_model = NewsTreeModel()
        model = gtk.TreeModelSort(self.news_model)
        model.set_sort_column_id(4, gtk.SORT_DESCENDING)
        self.news_model_filtered = model.filter_new()
        self.news_model_filtered.set_visible_func(self.__show_unread_filter, data=None)
        self.news_treeview.set_model(self.news_model_filtered)

        ## Update TreeView widgets

        column = gtk.TreeViewColumn(_('Title'))
        column.set_expand(True)
        self.updates_treeview.append_column(column)

        cellpb = gtk.CellRendererPixbuf()
        cell = gtk.CellRendererText()

        column.pack_start(cellpb, False)
        column.pack_start(cell, True)

        column.set_attributes(cellpb, pixbuf=1)
        column.set_attributes(cell, markup=2)

        column = gtk.TreeViewColumn(_('Date'), \
                gtk.CellRendererText(), \
                markup=3)
        self.updates_treeview.append_column(column)

        column = gtk.TreeViewColumn(_('Size'), \
                gtk.CellRendererText(), \
                markup=5)
        self.updates_treeview.append_column(column)

        self.updates_model = UpdatesTreeModel()
        model = gtk.TreeModelSort(self.updates_model)
        model.set_sort_column_id(4, gtk.SORT_DESCENDING)
        model = model.filter_new()
        model.set_visible_func(self.__show_uninstalled_filter, data=None)
        self.updates_treeview.set_model(model)

        # News and Updates selection change signals
        elements = ((self.news_treeview, self.__on_news_treeview_changed_cb), \
                (self.updates_treeview, self.__on_updates_treeview_changed_cb))
        for treeview, callback in elements:
            treeselection = treeview.get_selection()
            treeselection.connect('changed', callback, None)
            treeselection.set_mode(gtk.SELECTION_SINGLE)

        for model in (self.news_model, self.updates_model):
            model.register_datamodel_change_callback(self.__on_view_datamodel_change_cb)

        self.__update_tabs_label_numbers()

        # Refresh sensitive state of Refresh, Open and Install buttons
        self.__refresh_sensitive_state_buttons()

        self.refresh_button.connect('clicked', self.__on_refresh_button_clicked_cb, None)
        self.open_link_button.connect("clicked", self.__open_link_button_cb, None)
        self.install_button.connect("clicked", self.__install_button_cb, None)
        self.sab_handler = self.show_all_button.connect("toggled", self.__show_all_button_cb, None)
        self.sub_handler = self.show_unread_button.connect("toggled", self.__show_unread_button_cb, None)

    def __update_tabs_label_numbers(self):
        unread_news = self.news_model.get_num_unread()
        if unread_news > 0:
            label = _("News") + " (%s)" % unread_news
        else:
            label = _("News")
        self.news_tab_label.set_text(label)

        unread_updates = self.updates_model.get_num_unread()
        if unread_updates > 0:
            label = _("Updates") + " (%s)" % unread_updates
        else:
            label = _("Updates")
        self.updates_tab_label.set_text(label)

    def __select_tab_to_open(self):
        unread_news = self.news_model.get_num_unread()
        unread_updates = self.updates_model.get_num_unread()
        unseen_news = self.news_model.get_num_unseen()
        unseen_updates = self.updates_model.get_num_unseen()
        num_news = self.news_model.get_num()
        num_updates = self.updates_model.get_num()

        page_num = 0    # the dialog will open in the first tab by default
        if (unseen_news > 0) or (unseen_updates > 0):
            if unseen_news == 0:
                page_num = 1

        elif (unread_news > 0) or (unread_updates > 0):
            if unread_news == 0:
                page_num = 1

        elif (num_news > 0) or (num_updates > 0):
            if num_news == 0:
                page_num = 1

        self.notebook.set_current_page(page_num)

        return (unread_news, unread_updates)

    def __show_unread_filter(self, model, treeiter, user_data):
        # Show all entries if the flag 'show-all-news' is enabled
        if self.are_all_news_shown is True:
            return True

        # Show the entry depending on the value of its 'unread' flag
        entry = model.get_value(treeiter, 0)
        return entry['unread']

    def __show_uninstalled_filter(self, model, treeiter, user_data):
        entry = model.get_value(treeiter, 0)
        return entry['not_installed']

    def __get_selected_row(self, treeview, selection=None):
        if selection is None:
            selection = treeview.get_selection()

        # Check if there is a valid selected row
        entry = None
        is_item_selected = selection.count_selected_rows() > 0
        if is_item_selected:
            (model, tree_iter) = selection.get_selected()
            entry = model.get_value(tree_iter, 0)

        return entry

    def __refresh_sensitive_state_buttons(self):
        # Do nothing if the dialog is not instantiated
        if self.dialog is not None:
            # Only enable refresh button if there is network connection
            is_connected = self.conn_manager.is_connected()
            self.refresh_button.set_sensitive(is_connected)

            # Open button also needs to have an item selected with a link
            is_enabled = False
            entry = self.__get_selected_row(self.news_treeview)
            if entry is not None:
                is_link = (entry['link'] is not None) and (len(entry['link']) > 0)
                is_enabled = is_connected and is_link
            self.open_link_button.set_sensitive(is_enabled)

            # Install button also needs an item selected
            entry = self.__get_selected_row(self.updates_treeview)
            is_enabled = is_connected and (entry is not None)
            self.install_button.set_sensitive(is_connected and is_enabled)

    ## Callback functions

    def __on_news_and_updates_updated(self, news_service, reason):
        # Only show News and Updates window if the feature is enabled
        # and there is something to show
        if reason in (APP_START, APP_CONNECTED):
            self.show_news_if_required()

    def __on_connection_status_changed(self, device_dialer):
        self.__refresh_sensitive_state_buttons()

    def __on_view_datamodel_change_cb(self):
        self.__update_tabs_label_numbers()

    def __on_news_treeview_changed_cb(self, selection, data):
        summary = ''
        entry = self.__get_selected_row(self.news_treeview, selection)
        if entry is not None:
            summary = saxutils.escape(entry['summary'].encode("latin-1"))
            self.news_model.mark_as_read(entry)

        self.news_view.load_string(summary, 'text/html', '', 'file:///')
        self.__refresh_sensitive_state_buttons()
        self.__update_tabs_label_numbers()

    def __on_updates_treeview_changed_cb(self, selection, data):
        summary = ''
        entry = self.__get_selected_row(self.updates_treeview, selection)
        if entry is not None:
            summary = saxutils.escape(entry['summary'].encode("latin-1"))
            self.updates_model.mark_as_read(entry)

        self.updates_view.load_string(summary, 'text/html', '', 'file:///')
        self.__refresh_sensitive_state_buttons()
        self.__update_tabs_label_numbers()

    def __on_refresh_button_clicked_cb(self, widget, data=None):
        self.progress_dialog = tgcm.ui.MSD.MSDProgressWindow(parent=self.dialog)
        self.progress_dialog.set_show_buttons(False)
        self.progress_dialog.show(_("Please wait a minute..."), _("Please wait a minute..."))

        self.news_service.refresh_async(callback=self.__on_refresh_callback)
        if gtk.events_pending():
            gtk.main_iteration(False)

    def __on_refresh_callback(self):
        self.__update_tabs_label_numbers()
        if self.progress_dialog is not None:
            self.progress_dialog.hide()
            self.progress_dialog.destroy()
            self.progress_dialog = None

    def __open_link_button_cb(self, widget, data):
        entry = self.__get_selected_row(self.news_treeview)
        if entry is not None:
            webbrowser.open(entry['link'])

    def __install_button_cb(self, button, data):
        if self.conf.check_policy('warning-download-update'):
            device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
            device_manager = tgcm.core.FreeDesktop.DeviceManager()
            device = device_manager.get_main_device()
            if device_dialer.is_modem() and device.is_connected():
                tech_mm = device.get_access_technology()
                if tech_mm in (ACCESS_TECH_GSM, ACCESS_TECH_GSM_COMPACT, \
                        ACCESS_TECH_GPRS, ACCESS_TECH_EDGE):
                    markup = _("<b>Warning: slow connection</b>")
                    message = _("Your connection seems too slow and the download would take you quite a long time. Are you sure to continue?")

                    resp = question_dialog(message, markup=markup, parent=self.dialog)
                    if resp == gtk.RESPONSE_NO:
                        return

        self.progress_dialog = tgcm.ui.MSD.MSDProgressWindow(parent=self.dialog)
        self.progress_dialog.set_show_buttons(False)
        message = _("Please wait a minute...")
        self.progress_dialog.show(message, message)

        entry = self.__get_selected_row(self.updates_treeview)
        self.news_service.install_async(entry['id'], self.__on_install_callback)
        if gtk.events_pending():
            gtk.main_iteration(False)

    def __on_install_callback(self, is_success):
        if self.progress_dialog is not None:
            self.progress_dialog.hide()
            self.progress_dialog.destroy()
            self.progress_dialog = None

        if not is_success:
            markup = _("<b>The update could not be installed</b>")
            message = _("Please check your network configuration and try again")
            self.__show_error_dialog(message, markup)

    def __show_all_button_cb(self, widget, data):
        self.show_unread_button.handler_block(self.sub_handler)
        self.show_unread_button.set_active(not self.show_all_button.get_active())

        self.are_all_news_shown = self.show_all_button.get_active()
        self.news_model_filtered.refilter()

        self.show_unread_button.handler_unblock(self.sub_handler)
        self.__update_tabs_label_numbers()

    def __show_unread_button_cb(self, widget, data):
        self.show_all_button.handler_block(self.sab_handler)
        self.show_all_button.set_active(not self.show_unread_button.get_active())

        self.are_all_news_shown = self.show_all_button.get_active()
        self.news_model_filtered.refilter()

        self.show_all_button.handler_unblock(self.sab_handler)
        self.__update_tabs_label_numbers()

    def __show_error_dialog(self, message, markup):
        error_dialog(message, markup=markup, parent=self.dialog)


class BaseTreeModel(gtk.GenericTreeModel):
    def __init__(self):
        gtk.GenericTreeModel.__init__(self)

        self.column_names = ()
        self.column_types = ()

        self.news_service = tgcm.core.NewsService.NewsService()
        self.data = None
        self.data_weights = {}
        self.get_data_func = None
        self.datamodel_change_cb = None

        self.news_service.connect('news-updated', self._data_updated_cb, None)

    def get_num_unread(self):
        num = 0
        for x in self.data:
            if x['unread']:
                num += 1
        return num

    def get_num_unseen(self):
        num = 0
        for x in self.data:
            if x['unseen']:
                num += 1
        return num

    def get_num(self):
        return len(self.data)

    def mark_as_read(self, entry):
        if entry in self.data:
            # Update NewsService internal state
            entry_id = entry['id']
            self.news_service.mark_as_read(entry_id)

            # Notify treeviewer about the change
            path = (self.data.index(entry),)
            treeiter = self.get_iter(path)
            self.row_changed(path, treeiter)

    def mark_current_items_seeen(self):
        for entry in self.data:
            entry_id = entry['id']
            self.news_service.mark_as_seen(entry_id)

            # Notify treeviewer about the change
            path = (self.data.index(entry),)
            treeiter = self.get_iter(path)
            self.row_changed(path, treeiter)

    def register_datamodel_change_callback(self, callback):
        self.datamodel_change_cb = callback

    ## Callbacks

    def _data_updated_cb(self, *args):
        new_data = self.get_data_func()

        # Look for removed entries
        current_entries = list(self.data)
        for entry in current_entries:
            if entry not in new_data:
                index = self.data.index(entry)
                self.data.remove(entry)
                self.row_deleted(index)

        # Look for new entries
        for entry in new_data:
            if entry not in self.data:
                self.data.append(entry)
                path = (self.data.index(entry),)
                treeiter = self.get_iter(path)
                self.row_inserted(path, treeiter)
            else:
                path = (self.data.index(entry),)
                treeiter = self.get_iter(path)
                self.row_changed(path, treeiter)

        # Notify its change listener (if any)
        if self.datamodel_change_cb is not None:
            self.datamodel_change_cb()

    ### gtk.GenericModelTree interface ###

    def get_column_names(self):
        return self.column_names[:]

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return len(self.column_types)

    def on_get_column_type(self, n):
        self.column_types[n]
        return self.column_types[n]

    def on_get_iter(self, path):
        try:
            return self.data[path[0]]
        except IndexError:
            return None

    def on_get_path(self, rowref):
        return self.data.index(rowref)

    def on_get_value(self, rowref, column):
        return

    def on_iter_next(self, rowref):
        try:
            i = self.data.index(rowref) + 1
            return self.data[i]
        except IndexError:
            return None

    def on_iter_children(self, rowref):
        if rowref:
            return None
        return self.data[0]

    def on_iter_has_child(self, rowref):
        return False

    def on_iter_n_children(self, rowref):
        if rowref:
            return None
        return len(self.data)

    def on_iter_nth_child(self, rowref, n):
        if rowref:
            return None
        try:
            return self.data[n]
        except IndexError:
            return None

    def on_iter_parent(self, child):
        return None

    def date_to_str(self, date):
        return "%s/%s/%s" % (date.tm_mday, \
                date.tm_mon, \
                date.tm_year)


class NewsTreeModel(BaseTreeModel):
    def __init__(self):
        BaseTreeModel.__init__(self)

        self.column_names = ('Object', 'IsNew', 'Title', 'Date', 'DateNum')
        self.column_types = (gobject.TYPE_PYOBJECT, gtk.gdk.Pixbuf, str, str, float)

        self.data = self.news_service.get_news()
        self.get_data_func = self.news_service.get_news

    def on_get_value(self, rowref, column):
        if column == 0:   # Object
            return rowref
        elif column == 1:     # IsNew pixmap
            if rowref['unseen']:
                icon_theme = gtk.icon_theme_get_default()
                return icon_theme.load_icon('emblem-new', 10, gtk.ICON_LOOKUP_USE_BUILTIN)
            else:
                return None
        elif column == 2:   # Title
            title = rowref['title']
            if rowref['unread']:
                title = '<b>%s</b>' % title
            return title
        elif column == 3:   # Date
            return self.date_to_str(rowref['updated_parsed'])
        elif column == 4:   # DateNum
            entry_id = rowref['id']
            if entry_id not in self.data_weights:
                weight = time.mktime(rowref['updated_parsed'])
                if rowref['unread']:
                    weight = weight * 100
                if rowref['unseen']:
                    weight = weight * 100
                self.data_weights[entry_id] = weight
            return self.data_weights[entry_id]
        return


class UpdatesTreeModel(BaseTreeModel):
    def __init__(self):
        BaseTreeModel.__init__(self)

        self.column_names = ('Object', 'IsNew', 'Title', 'Date', 'DateNum', 'Size')
        self.column_types = (gobject.TYPE_PYOBJECT, gtk.gdk.Pixbuf, str, str, float, str)

        self.data = self.news_service.get_updates()
        self.get_data_func = self.news_service.get_updates

    def on_get_value(self, rowref, column):
        if column == 0:   # Object
            return rowref
        elif column == 1:     # IsNew pixmap
            if rowref['unseen']:
                icon_theme = gtk.icon_theme_get_default()
                return icon_theme.load_icon('emblem-new', 10, gtk.ICON_LOOKUP_USE_BUILTIN)
            else:
                return None
        elif column == 2:   # Title
            title = rowref['title']
            if rowref['unread']:
                title = '<b>%s</b>' % title
            return title
        elif column == 3:   # Date
            return self.date_to_str(rowref['updated_parsed'])
        elif column == 4:   # DateNum
            entry_id = rowref['id']
            if entry_id not in self.data_weights:
                weight = time.mktime(rowref['updated_parsed'])
                if rowref['unread']:
                    weight = weight * 100
                if rowref['unseen']:
                    weight = weight * 100
                self.data_weights[entry_id] = weight
            return self.data_weights[entry_id]
        elif column == 5:   # Size
            length = int(rowref['links'][0]['length'])
            return format_to_maximun_unit(length, "GB", "MB", "KB", "Bytes")
        return
