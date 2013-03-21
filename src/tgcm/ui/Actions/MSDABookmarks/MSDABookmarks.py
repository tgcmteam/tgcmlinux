#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
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
import gio
import glib
import subprocess
import urlparse
import urllib
import webbrowser

import tgcm
import tgcm.core.Bookmarks
import tgcm.core.ConnectionSettingsManager

import tgcm.ui.MSD
import tgcm.ui.ThemedDock
import tgcm.ui.windows

from tgcm.ui.MSD.MSDMessages import *
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

from freedesktopnet.networkmanager.networkmanager import NetworkManager


class MSDABookmarks(tgcm.ui.MSD.MSDAction):
    def __init__(self, dock_launcher = False, bookmarks_list_store = None):
        tgcm.info("Init MSDABookmarks")
        tgcm.ui.MSD.MSDAction.__init__(self, "favorites")

        self.dock_launcher = dock_launcher
        self.connection_settings_manager = tgcm.core.ConnectionSettingsManager.ConnectionSettingsManager()

        self.action_dir = os.path.join(tgcm.actions_data_dir , self.codename)
        self.taskbar_icon_name = 'favorites_taskbar.png'

        self.connection_manager = tgcm.core.Connections.ConnectionManager()
        self.bookmarks_manager = tgcm.core.Bookmarks.BookmarksManager()
        self.security_manager = tgcm.ui.MSD.MSDSecurityManager()
        self.conf = tgcm.core.Config.Config()
        self.theme_manager = tgcm.core.Theme.ThemeManager()
        self.xml_theme_manager = tgcm.core.XMLTheme.XMLTheme()

        self.conf.connect("bookmark-added", self.__reload_bookmarks)
        self.conf.connect("bookmark-deleted", self.__reload_bookmarks)
        self.conf.connect("bookmark-changed", self.__reload_bookmarks)

        self.connection_manager.connect("connections_changed", self.__connection_manager_changed)

        self.add_bookmark_button = self.get_prefs_widget("add_bookmark_button")
        self.edit_bookmark_button = self.get_prefs_widget("edit_bookmark_button")
        self.del_bookmark_button = self.get_prefs_widget("del_bookmark_button")
        self.open_bookmark_button = self.get_prefs_widget("open_bookmark_button")
        self.bookmarks_treeview = self.get_prefs_widget("bookmarks_treeview")

        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir, 'MSDABookmarks_dialog.ui'), \
                prefix='bmk')

        self.window_icon_path = self.theme_manager.get_icon('icons', self.taskbar_icon_name)
        self.bookmark_dialog.set_icon_from_file(self.window_icon_path)

        self.bd_is_add_dialog = None
        self.bd_show_confirmation = False

        # -- Favorites service dialog, it is shown when 'launch_action()' is executed
        self.dialog = tgcm.ui.windows.ServiceWindow('banner.favorites', _("Favourites"))
        self.dialog.set_icon_from_file(self.window_icon_path)
        self.dialog.resize (750, 500)
        self.dialog_bookmark_container = None

        if tgcm.country_support == "uk":
            self.bd_connection_help_label.set_text (_("(*) If you do not select this option, the connection used will be the one that is currently active or the preferred O2 connection."))

        # Bookmarks confirmation dialog
        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir, 'MSDABookmarks_confirm.ui'), \
                prefix='bmk')

        self.bookmark_confirmation_dialog.set_icon_from_file(self.window_icon_path)
        self.bookmark_confirmation_icon.set_from_file(self.window_icon_path)

        self.importer = tgcm.ui.MSD.MSDImporter ()
        self.importer.bookmarks_treeview = self.bookmarks_treeview
        self.importer.connect("bookmark-imported", self.__bookmark_imported_cb)

        self.dialog.connect('delete-event', self.__dialog_close_event_cb)
        self.dialog.close_button.connect('clicked', self.__dialog_close_event_cb)

        self.bookmark_dialog.connect("delete_event", self.__delete_event_bookmarks_cb)
        if self.bookmarks_manager.can_create_bookmarks ():
            self.add_bookmark_button.connect("clicked", self.__add_bookmark_button_cb, None)
        else:
            self.add_bookmark_button.set_sensitive(False)
        self.edit_bookmark_button.connect("clicked", self.__edit_bookmark_button_cb, None)
        self.del_bookmark_button.connect("clicked", self.__del_bookmark_button_cb, None)
        self.open_bookmark_button.connect('clicked', self.__open_bookmark_button_cb, None)

        self.bookmark_confirmation_dialog.connect("delete_event", self.__delete_event_bookmark_confirmation_cb)
        self.bookmark_confirmation_ok_button.connect("clicked", self.__ok_bookmark_confirmation_button_cb, None)
        self.bookmark_confirmation_dont_show.connect("toggled", self.__dont_show_bookmark_confirmation_cb, None)

        self.bd_url_radio_button.connect("toggled", self.__bd_url_radio_button_cb, None)
        self.bd_check_connection.connect("toggled", self.__bd_check_connection_cb, None)
        self.bd_cancel_button.connect("clicked", self.__bd_cancel_button_cb, None)
        self.bd_ok_button.connect("clicked", self.__bd_ok_button_cb, None)

        treeselection = self.bookmarks_treeview.get_selection()
        treeselection.connect("changed" , self.__bookmarks_treview_row_changed_cb, None)
        self.__bookmarks_treview_row_changed_cb(treeselection, None)

        #Populate bd_connection_combobox
        liststore = self.conn_manager.get_connections_model()
        self.bd_connection_combobox.set_model(liststore)
        cell = gtk.CellRendererText()
        self.bd_connection_combobox.pack_start(cell, True)
        self.bd_connection_combobox.add_attribute(cell, 'text', 1)
        self.bd_connection_combobox.set_active(0)

        #Populate bookmarks in the bookmarks tab treeview
        liststore = gtk.ListStore(tgcm.core.Bookmarks.Bookmark, gtk.gdk.Pixbuf, str, long, str)

        name_column = gtk.TreeViewColumn('bookmark_name')
        self.bookmarks_treeview.append_column(name_column)

        icon_cell = gtk.CellRendererPixbuf()
        name_cell = gtk.CellRendererText()

        name_column.pack_start(icon_cell, False)
        name_column.pack_start(name_cell, True)

        name_column.set_attributes(icon_cell, pixbuf=1)
        name_column.set_attributes(name_cell, text=2)

        if self.dock_launcher == True:
            url_column = gtk.TreeViewColumn('bookmark_url')
            self.bookmarks_treeview.append_column(url_column)

            url_cell = gtk.CellRendererText()
            url_column.pack_start(url_cell, True)

            url_column.set_attributes(url_cell, text=4)

        self.bookmarks_treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.bookmarks_treeview.set_headers_visible(False)

        self.bookmark_icon_pixbuf = self.xml_theme_manager.get_pixbuf('favorite-item')

        if bookmarks_list_store == None :
            self.bookmarks_treeview.set_model(liststore)
            self.load_bookmarks()
            self.bookmarks_treeview.connect("row-activated", self.__on_bookmarks_edit_row_activated)
        else:
            self.bookmarks_treeview.set_model(bookmarks_list_store)
            self.bookmarks_treeview.connect("row-activated", self.__on_bookmarks_row_activated)

    def __connection_manager_changed (self, conn_manager):
        self.load_bookmarks()

    def load_bookmarks(self):
        liststore = self.bookmarks_treeview.get_model()
        if liststore != None:
            liststore.clear()
            icon_theme = gtk.icon_theme_get_default()

            bookmarks = self.bookmarks_manager.get_bookmarks()
            for bookmark in bookmarks:
                parse_result = urlparse.urlparse(bookmark.url)

                # If the bookmark is read-only I assume it is an operator one, and the
                # favorite icon from the theme must be displayed
                if bookmark.readonly:
                    pixbuf = self.bookmark_icon_pixbuf

                # It is a file-based bookmark, so I'll display the mimetype icon
                elif parse_result.scheme == 'file':
                    filepath = urlparse.urlparse(bookmark.url).path
                    filepath = urllib.url2pathname(filepath)
                    try:
                        mimetype = self.__get_mimetype(filepath)
                        type_names = gio.content_type_get_icon(mimetype).get_names()
                    except:
                        type_names = ['text-x-generic']

                    pixbuf = None
                    for stock_id in type_names:
                        try:
                            pixbuf = icon_theme.load_icon(stock_id, 16, gtk.ICON_LOOKUP_USE_BUILTIN)
                            break
                        except glib.GError:
                            pass

                # Finally, it seems that it is an user bookmark
                else:
                    pixbuf = icon_theme.load_icon('text-html', 16, gtk.ICON_LOOKUP_USE_BUILTIN)

                # If something goes wrong and no pixbuf has been selected, just show a boring
                # default icon
                if pixbuf is None:
                    pixbuf = icon_theme.load_icon('text-x-generic', 16, gtk.ICON_LOOKUP_USE_BUILTIN)

                # GConf returns encoded URLs, it doesn't look so good
                url = urllib.url2pathname(bookmark.url)

                liststore.append([bookmark, pixbuf , bookmark.name, long(bookmark.timestamp), url])

    def __dialog_close_event_cb(self, *args):
        self.dialog.hide()
        return True

    def launch_action(self, MSDConnManager):
        # This method is invoked when the "Favorites" service is invoked from the
        # dock
        list_store = self.bookmarks_treeview.get_model()
        bookmarks = MSDABookmarks(dock_launcher=True, bookmarks_list_store=list_store)

        # Although "Favorites" screen is almost the same in the service configuration
        # area and the service itself, it is necessary to show or hide some elements
        bookmarks.prefs_main_container.set_border_width(0)
        bookmarks.title_label.hide()
        bookmarks.installed_service_label.hide()
        bookmarks.uninstalled_service_label.hide()
        bookmarks.install_service_alignment.hide()
        bookmarks.uninstall_service_alignment.hide()
        bookmarks.connect_container.hide()
        bookmarks.open_bookmark_button.show();

        # I have no idea what is being done here, probably each time the service is
        # invoked a new instance of MSDABookmarks is created, and current controls of the
        # service screen is replaced with the controls of the new instance
        if self.dialog_bookmark_container is not None:
            self.dialog.remove(self.dialog_bookmark_container)

        self.dialog.add(bookmarks.prefs_main_container)
        self.dialog_bookmark_container = bookmarks.prefs_main_container

        # Adjust the transient relation of the service dialog with the dock
        dock = tgcm.ui.ThemedDock()
        parent = dock.get_main_window()
        self.dialog.set_transient_for(parent)

        # Show the service dialog
        self.dialog.show()

    def close_action(self, params=None):
        self.dialog.hide()

    def __open_bookmark_button_cb(self, widget, data):
        self.__launch_bookmark()

    def __on_bookmarks_row_activated(self, treeview, path, column) :
        self.__launch_bookmark()

    def __on_bookmarks_edit_row_activated(self, treeview, path, column) :
        self.__edit_bookmark()

    def __get_mimetype(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                header = f.read(256)
                size = len(header)
        except IOError:
            header = None
            size = 0

        mimetype = gio.content_type_guess(filepath, header, size)[0]
        return mimetype

    def __launch_bookmark(self) :
        treeselection = self.bookmarks_treeview.get_selection()
        (model, list_iter) = treeselection.get_selected()
        bookmark = model.get_value(list_iter, 0)
        url = bookmark.get_url()

        # Determine the current window parent
        parent = self.__get_current_window_parent()

        parse_result = urlparse.urlparse(url)

        # It seems to be a file-based bookmark
        if parse_result.scheme == 'file':
            # Test if it is an executable
            filepath = urllib.url2pathname(parse_result.path)
            mimetype = self.__get_mimetype(filepath)
            is_executable = gio.content_type_can_be_executable(mimetype) and \
                    os.access(filepath, os.X_OK)

            # If it is an executable attempt to open it
            if is_executable:
                subprocess.Popen([filepath])

            # Just attempt to open the file with the default handler described
            # in the system
            else:
                subprocess.Popen(['xdg-open', filepath])

        else:
            connection = bookmark.get_connection()
            if connection == "":
                connection = None

            msdcm = tgcm.ui.MSD.MSDConnectionsManager()

            if connection == None :
                if self.connection_manager.ppp_manager.nmConnectionState() == NetworkManager.State.CONNECTED:
                    if url.startswith ("http:"):
                        if bookmark.userdata == 1:
                            self.security_manager.launch_url(url, parent=parent)
                        else:
                            webbrowser.open(url)
                    else:
                        webbrowser.open("http://%s" % url)
                else:
                    msdcm.do_connect_with_smart_connector(bookmark_info=bookmark)

            else:
                conn_settings=self.connection_settings_manager.get_connection_info_dict(name=connection)
                if msdcm.connect_to_connection(connection_settings=conn_settings, bookmark_info=bookmark) != 0:
                    msdcm.error_on_connection()

    def create_bookmark(self, parent, name='', url='', filename=''):
        self.__create_bookmark(parent, name, url, filename)

    def __add_bookmark_button_cb(self, widget, data=None):
        parent = self.__get_current_window_parent()
        self.__create_bookmark(parent)

    def __create_bookmark(self, parent, name='', url='', filename=''):
        self.bd_is_add_dialog = True
        self.bookmark_dialog.set_title(MSG_ADD_BOOKMARK_TITLE)

        # Establish the current parent for this dialog
        self.bookmark_dialog.set_transient_for(parent)

        #Clean the bookmark dialog
        self.bd_name_entry.set_text(name)
        self.bd_name_entry.set_sensitive(True)
        self.bd_filechooser.set_filename(filename)
        self.bd_url_entry.set_text(url)
        self.bd_url_radio_button.set_active(True)
        self.bd_check_connection.set_active(False)

        self.__bd_url_radio_button_cb(self.bd_url_radio_button, None)
        self.__bd_check_connection_cb(self.bd_check_connection, None)

        self.bd_main_vbox.set_sensitive(True)

        self.bookmark_dialog.show_all()
        self.bd_cancel_button.grab_focus()

    def __edit_bookmark_button_cb(self, widget, data):
        self.__edit_bookmark()

    def __edit_bookmark(self):
        self.bd_is_add_dialog = False
        self.bookmark_dialog.set_title(MSG_EDIT_BOOKMARK_TITLE)

        # Establish the current parent for this dialog
        parent = self.__get_current_window_parent()
        self.bookmark_dialog.set_transient_for(parent)

        #Complete form fields
        treeselection = self.bookmarks_treeview.get_selection()
        (model, list_iter) = treeselection.get_selected()

        bookmark = model.get_value (list_iter, 0)

        self.editing_bookmark = bookmark
        self.bd_name_entry.set_text(bookmark.name)

        resource = bookmark.url
        if resource.startswith("file://") == True:
            self.bd_filechooser.set_uri(resource)
            self.bd_file_radio_button.set_active(True)
            self.bd_url_entry.set_text("")
        else:
            self.bd_filechooser.set_uri("")
            self.bd_url_entry.set_text(resource)
            self.bd_url_radio_button.set_active(True)

        connection_name = bookmark.connection
        if connection_name == None or connection_name == '':
            self.bd_check_connection.set_active(False)
        else:
            self.bd_check_connection.set_active(True)
            liststore = self.bd_connection_combobox.get_model()
            iter_tmp = liststore.get_iter(0)

            while iter_tmp != None:
                if connection_name == liststore.get_value(iter_tmp, 1):
                    self.bd_connection_combobox.set_active_iter(iter_tmp)
                iter_tmp = liststore.iter_next(iter_tmp)

        self.__bd_url_radio_button_cb(self.bd_url_radio_button, None)
        self.__bd_check_connection_cb(self.bd_check_connection, None)

        if bookmark.readonly == True:
            self.bd_main_vbox.set_sensitive (False)
        else:
            self.bd_main_vbox.set_sensitive (True)

        self.bookmark_dialog.show_all()
        self.bd_ok_button.grab_focus()

    def __delete_event_bookmarks_cb(self, widget, data):
        self.bookmark_dialog.hide_all()
        return True

    def __del_bookmark_button_cb(self, widget, data):
        treeselection = self.bookmarks_treeview.get_selection()
        (model, list_iter) = treeselection.get_selected()
        bookmark = model.get_value(list_iter, 0)

        # Determine the current parent for this dialog
        parent = self.__get_current_window_parent()

        dlg = gtk.MessageDialog(parent = parent, \
                type = gtk.MESSAGE_WARNING, buttons = gtk.BUTTONS_OK_CANCEL)
        dlg.set_icon_from_file(self.window_icon_path)
        dlg.set_markup(MSG_DELETE_BOOKMARK_TITLE)
        dlg.format_secondary_markup(MSG_DELETE_BOOKMARK % gobject.markup_escape_text (bookmark.name))
        ret = dlg.run()
        dlg.destroy()

        if ret != gtk.RESPONSE_OK:
            return

        iter_tmp = model.get_iter(0)

        while iter_tmp != None:
            if model.get_value(iter_tmp, 0) == bookmark:
                model.remove(iter_tmp)
                break
            iter_tmp = model.iter_next(iter_tmp)

        bookmark.delete()

    def __bookmarks_treview_row_changed_cb(self, selection, data):
        selection = self.bookmarks_treeview.get_selection()
        (model, list_iter) = selection.get_selected()

        if list_iter == None:
            self.edit_bookmark_button.set_sensitive(False)
            self.del_bookmark_button.set_sensitive(False)
            self.open_bookmark_button.set_sensitive(False)
        else:
            bookmark =  model.get_value(list_iter, 0)

            if bookmark.readonly == True:
                self.del_bookmark_button.set_sensitive(False)
            else:
                self.del_bookmark_button.set_sensitive(self.bookmarks_manager.can_delete_bookmarks())
            self.edit_bookmark_button.set_sensitive(self.bookmarks_manager.can_edit_bookmarks())
            self.open_bookmark_button.set_sensitive(self.bookmarks_manager.can_export_bookmarks())

    def __reload_bookmarks (self, conf, data):
        self.load_bookmarks()

    def __bookmark_imported_cb (self, data):
        self.load_bookmarks()

    def __bd_url_radio_button_cb (self, widget, data):
        if widget.get_active() == True:
            self.bd_url_entry.set_sensitive(True)
            self.bd_filechooser.set_sensitive(False)
        else:
            self.bd_url_entry.set_sensitive(False)
            self.bd_filechooser.set_sensitive(True)

    def __bd_check_connection_cb (self, widget, data):
        if widget.get_active() == True:
            self.bd_connection_combobox.set_sensitive(True)
        else:
            self.bd_connection_combobox.set_sensitive(False)

    def __bd_cancel_button_cb(self, widget, data):
        self.bookmark_dialog.hide_all()

    def __bd_ok_button_cb(self, widget, data):
        if '/' in self.bd_name_entry.get_text():
            mesg = gtk.MessageDialog(self.bookmark_dialog, gtk.DIALOG_MODAL, \
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
            mesg.set_icon_from_file(self.window_icon_path)
            mesg.set_markup(MSG_INVALID_BOOKMARK_NAME_TITLE)
            mesg.format_secondary_markup(MSG_INVALID_BOOKMARK_NAME)
            if (mesg.run() != None):
                mesg.destroy()
        elif self.__add_bookmark() == True:
            self.bookmark_dialog.hide_all()
            # Show confirmation
            if self.bd_is_add_dialog == False or self.bd_show_confirmation == False:
                return
            if (self.conf.get_ui_general_key_value("show_new_bookmark_confirmation") == True):
                self.bookmark_confirmation_dialog.show_all()
                self.bd_show_confirmation = False

    def __add_bookmark(self):
        name = self.bd_name_entry.get_text()
        if name == "" :
            mesg = gtk.MessageDialog(self.bookmark_dialog, gtk.DIALOG_MODAL, \
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
            mesg.set_icon_from_file(self.window_icon_path)
            mesg.set_markup(MSG_NO_BOOKMARK_NAME_TITLE)
            mesg.format_secondary_markup(MSG_NO_BOOKMARK_NAME)
            if (mesg.run() != None):
                mesg.destroy()
                return False

        if (self.bd_is_add_dialog == True and self.bookmarks_manager.exists_bookmark(name)) or \
           (self.bd_is_add_dialog == False and self.bookmarks_manager.exists_bookmark(name) and name != self.editing_bookmark.name):
            mesg = gtk.MessageDialog(self.bookmark_dialog, gtk.DIALOG_MODAL, \
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
            mesg.set_icon_from_file(self.window_icon_path)
            mesg.set_markup(MSG_BOOKMARK_NAME_EXISTS_TITLE % name)
            mesg.format_secondary_markup(MSG_BOOKMARK_NAME_EXISTS)
            if (mesg.run() != None):
                mesg.destroy()
                return False

        if self.bd_file_radio_button.get_active():
            resource = self.bd_filechooser.get_uri()
            if resource == None :
                mesg = gtk.MessageDialog(self.bookmark_dialog, gtk.DIALOG_MODAL, \
                        gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
                mesg.set_icon_from_file(self.window_icon_path)
                mesg.set_markup(MSG_BOOKMARK_NO_FILE_SELECTED_TITLE)
                mesg.format_secondary_markup(MSG_BOOKMARK_NO_FILE_SELECTED)
                if (mesg.run() != None):
                    mesg.destroy()
                    return False
        else:
            resource = self.bd_url_entry.get_text()
            if resource == "" :
                mesg = gtk.MessageDialog(self.bookmark_dialog, gtk.DIALOG_MODAL, \
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
                mesg.set_icon_from_file(self.window_icon_path)
                mesg.set_markup(MSG_BOOKMARK_NO_URL_SELECTED_TITLE)
                mesg.format_secondary_markup(MSG_BOOKMARK_NO_URL_SELECTED)
                if (mesg.run() != None):
                    mesg.destroy()
                    return False

        if self.bd_check_connection.get_active() == False:
            connection = None
        else:
            model = self.bd_connection_combobox.get_model()
            list_iter = self.bd_connection_combobox.get_active_iter()
            connection = model.get_value(list_iter, 1)
            if connection == self.conf.get_default_connection_name():
                connection = None

        if self.bd_is_add_dialog == False:
            self.editing_bookmark.save(name, resource, connection)
            new_bookmark = self.editing_bookmark
        else:
            new_bookmark = self.bookmarks_manager.new_bookmark(name, resource, connection)

        return True

    def __delete_event_bookmark_confirmation_cb(self, widget, data):
        self.bookmark_confirmation_dialog.hide_all()
        return True

    def __ok_bookmark_confirmation_button_cb(self, widget, data):
        self.bookmark_confirmation_dialog.hide_all()
        return True

    def __dont_show_bookmark_confirmation_cb(self, widget, data):
        self.conf.set_ui_general_key_value("show_new_bookmark_confirmation", not widget.get_active())

    def __get_current_window_parent(self):
        toplevel = self.bookmarks_treeview.get_toplevel()
        parent = toplevel if toplevel.is_toplevel() else None
        return parent
