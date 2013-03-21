#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
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
import tgcm.core.Importer
import tgcm.core.Singleton

from tgcm.core.DeviceManager import DEVICE_WLAN, DEVICE_MODEM
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, error_dialog


class MSDImporter (gobject.GObject):
    __metaclass__ = tgcm.core.Singleton.Singleton

    __gsignals__ = {
        'bookmark-imported' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()) ,
        'connection-imported' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()) ,
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.conf = tgcm.core.Config.Config()
        self.importer = tgcm.core.Importer.Importer()

        self.connection_treeview = None
        self.bookmarks_treeview = None
        self.import_conditions = None

        gtk_builder_magic(self, \
                os.path.join(tgcm.msd_dir, 'MSDImporter_dialog.ui'), \
                prefix='imp')

        #signals !
        self.import_connection_overwrite_checkbox.connect("toggled", self.__imp_conn_ow_checkbox_cb, None)
        self.import_bookmark_overwrite_checkbox.connect("toggled", self.__imp_book_ow_checkbox_cb, None)
        self.import_no_username_entry.connect("changed", self.__imp_no_username_entry_cb, None)

    def __imp_conn_ow_checkbox_cb(self, widget, data):
        self.__check_import_conditions()

    def __imp_book_ow_checkbox_cb(self, widget, data):
        self.__check_import_conditions()

    def __imp_no_username_entry_cb(self, editable, data):
        self.__check_import_conditions()

    def import_connection_from_file(self, filepath, parent=None):
        filepath = os.path.abspath(filepath)
        if not self.__check_destiny_country(filepath, parent):
            return False

        is_conn_info = self.importer.has_connection_info(filepath)
        if is_conn_info:
            connection = self.importer.get_connection_info_from_file(filepath)
            if connection is None:
                return False

            if self.__import_connection(connection, filepath, parent):
                self.emit("connection-imported")
                return True
            else:
#                error_dialog(_("Malformed file, the profile cannot be imported."), parent=parent)
                return False

    def import_bookmark_from_file(self, filepath, parent=None):
        filepath = os.path.abspath(filepath)
        if not self.__check_destiny_country(filepath, parent):
            return False

        is_bookmark_info = self.importer.has_bookmark_info(filepath)
        if is_bookmark_info:
            bookmark = self.importer.get_bookmark_info_from_file(filepath)
            if bookmark is None:
                return False

            self.__import_bookmark(bookmark, filepath, parent)
            self.emit("bookmark-imported")

    def __check_destiny_country(self, filepath, parent=None):
        try:
            if self.importer.get_destiny_country(filepath) != tgcm.country_support:
                destiny_country = self.importer.get_destiny_country(filepath)
                markup = _("The selected file cannot be imported in your country.")
                msg = _("The selected file must be installed in \"%s\".") % destiny_country
                error_dialog(markup=markup, msg=msg, parent=parent)
                return False
            else:
                return True
        except:
            error_dialog(_("Malformed file, the profile cannot be imported."), parent=parent)
            return False

    def __import_bookmark(self, bookmark, filepath, parent=None):
        if bookmark["url"] == None:
            markup = _("This favourite cannot be imported")
            msg = _("Error when importing the favourite. Probably the associated file does not exist in your system.")
            error_dialog(markup=markup, msg=msg)

        if not self.conf.exists_bookmark(bookmark["name"]) :
            self.import_conditions = "BOOKMARK_NOT_EXISTS"
            self.import_filename_label.set_markup("%s" % os.path.basename (filepath))
            self.import_bookmark_label.set_markup(_("<b>Favourite: '%s'</b>") % bookmark["name"])
            self.__show_parts_of_import_dialog(book_label=True)
            self.import_dialog.show()

            self.__check_import_conditions()
            self.import_dialog.set_transient_for(parent)
            ret = self.import_dialog.run()
            self.import_dialog.hide()
            if ret != gtk.RESPONSE_OK:
                return False

            self.importer.import_bookmark_from_file (filepath)
        else:
            self.import_conditions = "OW_BOOKMARK"
            self.import_filename_label.set_markup("%s" % os.path.basename (filepath))
            self.import_bookmark_label.set_markup(_("<b>Favourite: '%s'</b>") % bookmark["name"])
            self.__show_parts_of_import_dialog(book_label=True, book_ow=True)
            self.import_dialog.show()

            self.__check_import_conditions()
            self.import_dialog.set_transient_for(parent)
            ret = self.import_dialog.run()
            self.import_dialog.hide()
            if ret != gtk.RESPONSE_OK:
                return

            self.importer.import_bookmark_from_file (filepath, overwrite=True)

    def __import_connection(self, conn, filepath, parent=None):
        conn_type = conn['deviceType']
        is_wifi = conn_type == DEVICE_WLAN
        is_modem = conn_type == DEVICE_MODEM

        if is_wifi or (is_modem and conn['profiles'][0]["username"] is not None):
            self.import_conditions = "CONN_NOT_EXISTS_AND_USER_EXISTS"
            self.import_filename_label.set_markup("%s" % os.path.basename(filepath))
            self.import_connection_label.set_markup(_("<b>Connection: '%s'</b>") % conn["name"])
            self.__show_parts_of_import_dialog(conn_label=True)
            self.import_dialog.show()

            self.__check_import_conditions()
            self.import_dialog.set_transient_for(parent)
            ret = self.import_dialog.run()
            self.import_dialog.hide()
            if ret != gtk.RESPONSE_OK:
                return False

            return self.importer.import_connection_from_file(filepath)

        else:
            self.import_conditions = "CONN_EXISTS_AND_USER_NOT_EXISTS"
            self.import_filename_label.set_markup("%s" % os.path.basename(filepath))
            self.import_connection_label.set_markup(_("<b>Connection: '%s'</b>") % conn["name"])
            self.__show_parts_of_import_dialog(conn_label=True, conn_no_username=True)
            self.import_dialog.show()

            self.__check_import_conditions()
            self.import_dialog.set_trannsient_for(parent)
            ret = self.import_dialog.run()
            self.import_dialog.hide()
            if ret != gtk.RESPONSE_OK:
                return False

            conn["user"] = self.import_no_username_entry.get_text()
            return self.importer.import_connection_from_file(filepath)


    def __check_import_conditions(self):
        if self.import_conditions == None:
            return

        if self.import_conditions == "CONN_NOT_EXISTS_AND_USER_EXISTS":
            self.import_ok_button.set_sensitive(True)

        if self.import_conditions == "CONN_EXISTS_AND_USER_NOT_EXISTS":
            if len(self.import_no_username_entry.get_text()) > 0 :
                self.import_ok_button.set_sensitive(True)
            else:
                self.import_ok_button.set_sensitive(False)

        if self.import_conditions == "BOOKMARK_NOT_EXISTS":
            self.import_ok_button.set_sensitive(True)

        if self.import_conditions == "OW_BOOKMARK":
            if self.import_bookmark_overwrite_checkbox.get_active():
                self.import_ok_button.set_sensitive(True)
            else:
                self.import_ok_button.set_sensitive(False)

    def __show_parts_of_import_dialog(self, conn_label=False, \
            conn_cant_ow=False, conn_ow=False, conn_no_username=False, \
            book_label=False, book_ow=False):

        self.import_connection_vbox.hide_all()
        self.import_bookmark_vbox.hide_all()

        if conn_label == True or conn_cant_ow == True or conn_ow == True or conn_no_username ==True:
            self.import_connection_vbox.show()

        if book_label == True or book_ow == True:
            self.import_bookmark_vbox.show()

        if conn_label == True:
            self.import_connection_label.show()

        if conn_cant_ow == True:
            self.import_can_not_ow_connection_label.show()

        if conn_ow == True:
            self.import_connection_overwrite_alignment.show_all()
            self.import_connection_overwrite_checkbox.set_active(False)
            self.import_connection_overwrite_checkbox.show()

        if conn_no_username == True:
            self.import_no_username_vbox.show_all()
            self.import_no_username_entry.set_text("")

        if book_label == True:
            self.import_bookmark_label.show()

        if book_ow == True:
            self.import_bookmark_overwrite_alignment.show_all()
            self.import_bookmark_overwrite_checkbox.set_active(False)
            self.import_bookmark_overwrite_checkbox.show()
