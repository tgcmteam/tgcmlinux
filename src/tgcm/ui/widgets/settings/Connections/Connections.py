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
import subprocess
import webbrowser

import tgcm
import tgcm.core.ConnectionSettingsManager
import tgcm.core.Config
import tgcm.core.Theme

import tgcm.ui.MSD
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label
from tgcm.ui.MSD.MSDMessages import MSG_DELETE_CONNECTION_TITLE, MSG_DELETE_CONNECTION

class Connections(gtk.HBox):
    def __init__(self, settings):
        gtk.HBox.__init__(self)

        self._settings = settings
        self._parent = self._settings.get_dialog()
        self.conf = tgcm.core.Config.Config()
        self.connection_settings_manager = tgcm.core.ConnectionSettingsManager.ConnectionSettingsManager()

        self.conn_manager = tgcm.core.Connections.ConnectionManager()
        self.theme_manager = tgcm.core.Theme.ThemeManager()

        self.widget_dir = os.path.join(tgcm.widgets_dir, 'settings', self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'Connections.ui'), \
                prefix='cnnt')
        self.add(self.main_vbox)

        # -- Replace for having wrapping labels
        msg = _("Here, you can manage the connections saved in %s and order them according to your connection preferences.") % self.conf.get_app_name()
        self.top_info_label = replace_wrap_label(self.top_info_label, text=msg)
        msg = _("You can add new connections to %s by pressing the following buttons:") % self.conf.get_app_name()
        self.second_info_label = replace_wrap_label(self.second_info_label, text=msg)

        if tgcm.country_support == 'de':
            self.add_wwan_connection_button.set_label(_("New 2G/3G/4G connection"))

        is_log_enabled = self.conf.is_connection_log_enabled()
        self.activate_connection_log_checkbutton.set_active(is_log_enabled)
        self.connection_file_label.set_text(self.conf.get_connection_log_filepath())

        self.importer = tgcm.ui.MSD.MSDImporter()
        self.importer.connections_treeview = self.connections_treeview
        self.importer.connect("connection-imported", self.__connection_imported_cb)

        self.__create_connections_treeview()
        self.__load_connections_treeview()
        self.__connect_signals()

    def __create_connections_treeview (self):
        column = gtk.TreeViewColumn('Connections_order', \
                gtk.CellRendererText(), text=0)
        self.connections_treeview.append_column(column)

        column = gtk.TreeViewColumn('Connections_name', \
                gtk.CellRendererText(), text=1)
        self.connections_treeview.append_column(column)

        column = gtk.TreeViewColumn('Connections_type', \
                gtk.CellRendererText(), text=2)
        self.connections_treeview.append_column(column)

        treeselection = self.connections_treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_SINGLE)
        treeselection.select_path(0)

    def __load_connections_treeview (self, *args):
        TARGETS = [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0)]
        self.conn_manager.load_connections_model()
        liststore = self.conn_manager.get_connections_model()
        self.connections_treeview.enable_model_drag_dest(TARGETS,gtk.gdk.ACTION_MOVE)
        self.connections_treeview.set_model(liststore)
        self.connections_treeview.set_reorderable(True)
        self.connections_treeview.connect("drag-end", self.drag_data_end)

    def __connect_signals(self):
        self.connection_settings_manager.connect('connection-added', self.__load_connections_treeview)
        self.connection_settings_manager.connect('connection-removed', self.__load_connections_treeview)
        self.connection_settings_manager.connect('connection-changed', self.__load_connections_treeview)

        if self.conf.check_policy('create-connection') == True:
            self.add_wwan_connection_button.connect("clicked", self.__add_wwan_connection_button_cb, None)
            self.add_wifi_connection_button.connect("clicked", self.__add_wifi_connection_button_cb, None)
        else:
            self.add_wwan_connection_button.set_sensitive(False)

        self.edit_connection_button.connect("clicked", self.__edit_connection_button_cb, None)
        self.del_connection_button.connect("clicked", self.__del_connection_button_cb, None)
        self.arrow_up_button.connect("clicked",self.__arrow_up_button_cb, None)
        self.arrow_down_button.connect("clicked",self.__arrow_down_button_cb, None)

        self.export_connection_button.connect("clicked", self.__export_connection_button_cb, None)
        if self.conf.check_policy('import-connection') == True:
            self.import_connection_button.connect("clicked", self.__import_connection_button_cb, None)
        else:
            self.import_connection_button.set_sensitive(False)

        self.activate_connection_log_checkbutton.connect("toggled", self.__activate_connection_log_checkbutton_cb, None)
        self.open_log_button.connect("clicked", self.__open_log_button_cb, None)

        treeselection = self.connections_treeview.get_selection()
        treeselection.connect("changed" , self.__connections_treview_row_changed_cb, None)

        self.__connections_treview_row_changed_cb(treeselection, None)

    def __open_log_button_cb(self, widget, data):
        os.system("touch %s" % os.path.expanduser("~/.tgcm/connection.log"))
        webbrowser.open(os.path.expanduser("~/.tgcm/connection.log"))

    def __activate_connection_log_checkbutton_cb(self, widget, data):
        self.conf.set_connection_log_enabled(widget.get_active())

    def __connection_imported_cb (self, data):
        self.__load_connections_treeview()

    def __add_wwan_connection_button_cb(self, widget, data):
        cd = tgcm.ui.windows.ConnectionDialog(parent=self._parent)
        cd.run()

    def __add_wifi_connection_button_cb(self, widget, data):
        command = ['nm-connection-editor']
        command.append('--type=802-11-wireless')
        command.append('--create')
        subprocess.Popen(command, shell=False, stdin=None, stdout=None, \
                stderr=None, close_fds=True)

    def __edit_connection_button_cb(self, widget, data):
        treeselection = self.connections_treeview.get_selection()
        (model, pathlist) = treeselection.get_selected_rows()

        iterator =  model.get_iter(pathlist[0])
        conn_settings = model.get_value(iterator, 4)
        conn_type = model.get_value(iterator, 2)

        if conn_type == 'LAN':
            command = ['nm-connection-editor']
            command.append('--type=802-3-ethernet')
            command.append('--edit=%s' % conn_settings.get_uuid())
            subprocess.Popen(command, shell=False, stdin=None, stdout=None, \
                    stderr=None, close_fds=True)
        elif conn_type == 'Wi-Fi':
            command = ['nm-connection-editor']
            command.append('--type=802-11-wireless')
            command.append('--edit=%s' % conn_settings.get_uuid())
            subprocess.Popen(command, shell=False, stdin=None, stdout=None, \
                    stderr=None, close_fds=True)
        else:
            dialog = tgcm.ui.windows.ConnectionDialog(self._parent)
            dialog.open_conn_settings(conn_settings)
            dialog.run()


    def __del_connection_button_cb(self, widget, data):
        treeselection = self.connections_treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        conn_settings =  model.get_value(iter, 4)

        dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK_CANCEL, parent = self._parent)
        window_icon_path = self.theme_manager.get_icon ('icons', 'settings_taskbar.png')
        dlg.set_icon_from_file(window_icon_path)
        dlg.set_markup(MSG_DELETE_CONNECTION_TITLE)
        dlg.format_secondary_markup(MSG_DELETE_CONNECTION % gobject.markup_escape_text (conn_settings['name']))
        ret = dlg.run()
        dlg.destroy()

        if ret != gtk.RESPONSE_OK:
            return

        conn_settings.delete()

    def __export_connection_button_cb(self, widget, data):
        treeselection = self.connections_treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        p = False
        while p == False:
            dlg = gtk.FileChooserDialog(title=_("Export connection"),
                    action=gtk.FILE_CHOOSER_ACTION_SAVE, parent = self._parent,
                    buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
            window_icon_path = self.theme_manager.get_icon ('icons', 'settings_taskbar.png')
            dlg.set_icon_from_file(window_icon_path)
            dlg.set_current_folder(os.environ["HOME"])
            dlg.set_current_name(model.get_value(iter, 1).replace("/","_") + ".tgcm")

            dlg_filter = gtk.FileFilter()
            dlg_filter.set_name(_("TGCM files"))
            dlg_filter.add_pattern("*.tgcm")
            dlg.add_filter(dlg_filter)

            dlg.set_do_overwrite_confirmation(True)

            ret = dlg.run()
            if ret == gtk.RESPONSE_OK:
                if not dlg.get_filename().endswith(".tgcm") :
                    msg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_CLOSE, parent = self._parent)
                    window_icon_path = self.theme_manager.get_icon ('icons', 'settings_taskbar.png')
                    msg.set_icon_from_file(window_icon_path)
                    msg.set_markup(_("<b>The file must have an extension</b>"))
                    msg.format_secondary_markup(_("The files that you save must have extension .tgcm"))
                    msg.run()
                    msg.destroy()
                    dlg.destroy()
                else:
                    p = True
            else:
                dlg.destroy()
                return

        conn_settings =  model.get_value(iter, 4)
        self.conn_manager.export_connection (conn_settings, dlg.get_filename())
        dlg.destroy()

    def __import_connection_button_cb(self, widget, data):
        dlg = gtk.FileChooserDialog(title=_("Import connection"),
                action=gtk.FILE_CHOOSER_ACTION_OPEN, parent=self._parent,
                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        window_icon_path = self.theme_manager.get_icon ('icons', 'settings_taskbar.png')
        dlg.set_icon_from_file(window_icon_path)
        dlg.set_current_folder(os.environ["HOME"])

        dlg_filter = gtk.FileFilter()
        dlg_filter.set_name(_("TGCM files"))
        dlg_filter.add_pattern("*.tgcm")
        dlg.add_filter(dlg_filter)

        ret = dlg.run()
        result_file = dlg.get_filename()
        dlg.destroy()

        if ret == gtk.RESPONSE_OK:
            self.importer.import_connection_from_file(result_file, self._parent)

    def __connections_treview_row_changed_cb(self, selection, data):
        selection = self.connections_treeview.get_selection()
        (model, iterator) = selection.get_selected()

        if iterator == None:
            self.edit_connection_button.set_sensitive(False)
            self.del_connection_button.set_sensitive(False)
            self.export_connection_button.set_sensitive(False)
        elif (model.get_value(iterator, 2) == 'Wi-Fi'):
            is_editable = model.get_value(iterator, 3)
            self.edit_connection_button.set_sensitive(is_editable)
            self.del_connection_button.set_sensitive(is_editable)
            self.export_connection_button.set_sensitive(True)
        elif (model.get_value(iterator, 2) == 'LAN'):
            is_editable = model.get_value(iterator, 3)
            self.edit_connection_button.set_sensitive(is_editable)
            self.del_connection_button.set_sensitive(is_editable)
            self.export_connection_button.set_sensitive(False)
        else:
            self.edit_connection_button.set_sensitive(bool(self.conf.check_policy('edit-connection')))
            self.export_connection_button.set_sensitive(bool(self.conf.check_policy('export-connection')))
            if model.get_value(iterator, 3) == False:
                self.del_connection_button.set_sensitive(False)
            else:
                self.del_connection_button.set_sensitive(bool(self.conf.check_policy('delete-connection')))

    def __arrow_down_button_cb(self, widget, data):
        treeselection = self.connections_treeview.get_selection()
        (model, pathlist) = treeselection.get_selected_rows()

        iter =  model.get_iter(pathlist[0])
        iterNext =  model.iter_next(iter)

        if (iterNext!=None):
            model.move_after(iter,iterNext)

            self.update_and_save_order(model)


    def __arrow_up_button_cb(self, widget, data):
        treeselection = self.connections_treeview.get_selection()
        (model, pathlist) = treeselection.get_selected_rows()
        if (pathlist[0][0]>0):

            iter =  model.get_iter(pathlist[0])
            iterPrev =  model.get_iter(pathlist[0][0]-1)
            model.move_before(iter,iterPrev)

            self.update_and_save_order(model)


    def drag_data_end(self,  treeview, dragConext):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        self.update_and_save_order(model)

    def update_and_save_order(self, model):
        connections_list=[];
        iter =  model.get_iter_first()
        i=0
        while iter!=None:
            i=i+1;
            connection_settings=model.get_value(iter, 4)
            model.set_value(iter,0,str(i))
            connections_list.append(connection_settings)
            iter =  model.iter_next(iter)

        self.connection_settings_manager.set_connection_list(connections_list)
