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

from xml.etree import ElementTree

import Config
import ConnectionSettingsManager
import Singleton
import XMLConfig

import tgcm


class Importer:
    __metaclass__ = Singleton.Singleton

    def __init__ (self):
        self.xmlconfig = XMLConfig.XMLConfig()
        self.config = Config.Config()
        self.connection_settings_manager = ConnectionSettingsManager.ConnectionSettingsManager()

    def get_connection_info_from_file(self, filepath):
        node = self.__get_node(filepath, 'wwan-connection')
        if node is not None:
            return self.xmlconfig.get_wwan_connection_info(node)

        node = self.__get_node(filepath, 'wifi-connection')
        if node is not None:
            return self.xmlconfig.get_wifi_connection_info(node)

        return None

    def import_connection_from_file(self, filepath, overwrite=False, default=False):

        xml = ElementTree.ElementTree (file=filepath)
        root = xml.getroot()
        if root is None:
            return False


        for node in root:
            if node.tag == 'wwan-connection':
                conn = self.xmlconfig.get_wwan_connection_info(node, default=default, wwan_prototype=False)
                try:
                    self.connection_settings_manager.add_wwan_connection(conn,update_if_possible=overwrite, must_write_gconf=overwrite)
                    return_value = True
                except:
                    return_value = False

            elif node.tag == 'wifi-connection':
                conn = self.xmlconfig.get_wifi_connection_info(node, default=False, prototype=False)
                try:
                    self.connection_settings_manager.add_wifi_connection(conn)
                    return_value = True
                except:
                    return_value = False


        return return_value

    def has_connection_info(self, filepath):
        node_wwan = self.__get_node(filepath, 'wwan-connection')
        node_wifi = self.__get_node(filepath, 'wifi-connection')
        if (node_wwan is not None) or (node_wifi is not None):
            return True
        else:
            return False

    def get_bookmark_info_from_file (self, filename):
        node = self.__get_node(filename, 'favorite')
        if node is not None:
            return self.xmlconfig.get_favorite_info (node)
        else:
            return None

    def import_bookmark_from_file(self, filename, overwrite=False):
        node = self.__get_node(filename, 'favorite')

        if node is not None:
            try:
                self.xmlconfig.import_favorite(node, overwrite=overwrite)
                return True
            except:
                return False

        return False

    def update_bookmarks_and_connections_from_file (self, filename):
        if not os.path.exists(filename):
            return None

        has_connection_info = self.has_connection_info (filename)
        has_bookmark_info = self.has_bookmark_info (filename)

        if not has_connection_info and not has_bookmark_info:
            return

        if has_connection_info:
            self.connection_settings_manager.del_all_readonly_connections()
        if has_bookmark_info:
            self.config.del_all_readonly_bookmarks()

        xml = ElementTree.ElementTree (file=filename)
        root = xml.getroot()

        return_value = False
        for node in root:
            if node.tag == 'favorite':
                favorite = self.xmlconfig.get_favorite_info (node)
                overwrite = self.config.exists_bookmark (favorite["name"])
                self.xmlconfig.import_favorite (node, overwrite=overwrite, force_readonly=True)
                return_value = True;
            elif node.tag == 'wwan-connection':
                self.xmlconfig.import_wwan_connection(node, force_readonly=True)
                return_value = True;

        return return_value;

    def has_bookmark_info (self, filename):
        node = self.__get_node (filename, 'favorite')
        if node != None:
            return True
        else:
            return False

    def get_destiny_country (self, filename):
        if not os.path.exists(filename):
            return False

        xml = ElementTree.ElementTree (file=filename)
        root = xml.getroot()
        if root != None and root.attrib.has_key('country'):
            return root.attrib['country'].lower()
        else:
            return False

    def __get_node (self, filename, node_name):
        if not os.path.exists(filename):
            return None

        xml = ElementTree.ElementTree (file=filename)
        root = xml.getroot()

        return_value = False
        for node in root:
            if node.tag == node_name:
                return node

        return None
