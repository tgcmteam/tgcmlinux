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

import gobject

import Config
import Exporter


class BookmarksManager(gobject.GObject):
    def __init__ (self):
        gobject.GObject.__init__(self)
        self.conf = Config.Config()

        self._bookmark_list = []

    def get_bookmarks (self):
        self._bookmark_list = []
        for bookmark_dict in self.conf.get_bookmarks_list():
            bookmark = Bookmark()
            bookmark._name = bookmark_dict['name']
            bookmark._url = bookmark_dict['url']
            bookmark._connection = bookmark_dict['connection']
            bookmark._timestamp = bookmark_dict['timestamp']
            bookmark._readonly = bookmark_dict['readonly']
            bookmark._userdata = bookmark_dict['userdata']
            self._bookmark_list.append(bookmark)
        return self._bookmark_list

    def get_bookmark (self, bookmark_name):
        bookmark_dict = self.conf.get_bookmark(bookmark_name)
        bookmark = None
        if bookmark_dict is not None:
            bookmark = Bookmark()
            bookmark._name = bookmark_dict['name']
            bookmark._url = bookmark_dict['url']
            bookmark._connection = bookmark_dict['connection']
            bookmark._timestamp = bookmark_dict['timestamp']
            bookmark._readonly = bookmark_dict['readonly']
            bookmark._userdata = bookmark_dict['userdata']
        return bookmark

    def new_bookmark(self, name, url, connection):
        self.conf.add_bookmark(name, url, connection)
        return self.get_bookmark(name)

    def exists_bookmark (self, bookmark_name):
        return self.conf.exists_bookmark(bookmark_name)

    def can_create_bookmarks (self):
        return bool(self.conf.check_policy('create-favorite'))

    def can_edit_bookmarks (self):
        return bool(self.conf.check_policy('edit-favorite'))

    def can_delete_bookmarks (self):
        return bool(self.conf.check_policy('delete-favorite'))

    def can_import_bookmarks (self):
        return bool(self.conf.check_policy('import-favorite'))

    def can_export_bookmarks (self):
        return bool(self.conf.check_policy('export-favorite'))


class Bookmark(gobject.GObject):
    def __init__ (self):
        gobject.GObject.__init__(self)
        self.conf = Config.Config ()
        self._name = ""
        self._timestamp = 0
        self._readonly = False
        self._userdata = ""
        self._url = ""
        self._connection = ""

    def get_name (self):
        return self._name
    name = property (get_name)

    def get_timestamp (self):
        return self._timestamp
    timestamp = property (get_timestamp)

    def get_readonly (self):
        return self._readonly
    readonly = property (get_readonly)

    def get_userdata (self):
        return self._userdata
    userdata = property (get_userdata)

    def get_url (self):
        return self._url
    url = property (get_url)

    def get_connection (self):
        return self._connection
    connection = property (get_connection)

    def delete (self):
        self.conf.del_bookmark (self.name)

    def save(self, name, url, connection, readonly=False, userdata=None):
        self.conf.modify_bookmark(self._name, name, url, connection, userdata, readonly)
        self._name = name
        self._url = url
        self._connection = connection
        if readonly != None:
            self._readonly = readonly
        if userdata != None:
            self._userdata = userdata

    def export_to_file (self, filename):
        exporter = Exporter.Exporter()
        exporter.save_bookmark_to_file (self, filename)

gobject.type_register(Bookmark)
