#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#
# Copyright (c) 2003-2007, Telefonica M�viles Espa�a S.A.U.
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

from xml.etree import ElementTree

import tgcm
import ConnectionSettingsManager
import Singleton

from tgcm.ui.MSD.MSDUtils import encode_password
from tgcm.core.DeviceManager import DEVICE_WIRED, DEVICE_WLAN, DEVICE_MODEM

class Exporter:
    __metaclass__ = Singleton.Singleton

    def __init__ (self):
        self.connection_settings_manager=ConnectionSettingsManager.ConnectionSettingsManager()

    def save_connection_to_file(self, conn_settings, file):
        export_root_node = ElementTree.Element("tgcm")
        export_root_node.set("country", tgcm.country_support)

        connection_node = self.__get_connection_params(conn_settings, export_root_node)
        self.__print_node_to_file(connection_node, file)


    def save_bookmark_to_file(self, bookmark, file):
        export_root_node = ElementTree.Element(u'tgcm')
        export_root_node.set(u'country', tgcm.country_support)

        bookmark_node = self.__get_bookmark_params(bookmark, export_root_node)

        conn = bookmark.get_connection()
        if conn != None and conn != "":
            bookmark_node = self.__get_connection_params(conn, bookmark_node)

        self.__print_node_to_file(bookmark_node, file)

    def __print_node_to_file(self, node, file="/tmp/prueba.tgcm", append=False):
        tree = ElementTree.ElementTree(node)

        if not append:
            file = open(file, 'w')
        else:
            file = open(file, 'a')
        file.write("<?xml version='1.0' encoding='utf-8'?>\n")
#        tree.write(file, tree.getroot(), 'utf-8', {})
        tree.write(file,encoding='utf-8')

    def __get_bookmark_params(self, bookmark, export_root_node):
        root_node = ElementTree.SubElement(export_root_node, "favorite")
        root_node.set("readonly", str(bookmark.readonly))
        root_node.set("userdata", str(bookmark.userdata))

        name_node = ElementTree.SubElement (root_node, "name")
        name_node.text = bookmark.name

        type_node = ElementTree.SubElement (root_node, "type")
        url_node = ElementTree.SubElement (root_node, "url")
        file_node = ElementTree.SubElement (root_node, "file")
        if bookmark.url.startswith("file://") == True:
            type_node.text = "1"
            file_node.text = bookmark.url
        else:
            type_node.text = "0"
            url_node.text = bookmark.url

        use_connection_node = ElementTree.SubElement (root_node, 'use-connection')
        connection_name_node = ElementTree.SubElement (root_node, 'connection-name')
        if bookmark.connection != None and  bookmark.connection != "":
            use_connection_node.text = "1"
            connection_name_node.text = bookmark.connection
        else:
            use_connection_node.text = "0"

        return export_root_node

    def __get_connection_params(self, conn_settings, export_root_node):
        conn_info = self.connection_settings_manager.get_connection_info_dict_with_profiles(conn_settings)

        if conn_info['deviceType']==DEVICE_WLAN:
            root_node = ElementTree.SubElement(export_root_node, "wifi-connection")
        else:
            root_node = ElementTree.SubElement(export_root_node, "wwan-connection")

        if conn_info['editable'] == True:
            root_node.set("readonly", "0")
        else:
            root_node.set("readonly", "1")

        node = ElementTree.SubElement (root_node, "name")
        node.text = conn_info['name']

        if ('profiles' in conn_info):
            for profile_info in conn_info['profiles']:
                self.__get_profile_params(root_node,profile_info)
        else:
            self.__get_profile_params(root_node,conn_info)


        return export_root_node


    def __get_profile_params(self,root_node,profile_info):
        def array2txt(x,y): return str(x)+';'+str(y)

        profile_node = ElementTree.SubElement (root_node, "profile")
        profile_node.set ("condition", profile_info.get('condition','default'))



        if root_node.tag=="wifi-connection":
            node = ElementTree.SubElement (profile_node, "ssid")
            node.text = profile_info['ssid']

            node = ElementTree.SubElement (profile_node, "network-password")
            node.text = encode_password(profile_info['password'])

            node = ElementTree.SubElement (profile_node, "encryption")
            node_auth = ElementTree.SubElement (profile_node, "authentication")

            if profile_info['cipher'] == 'wep-key0':
                node.text = '0';
                node_auth.text='0';
            elif profile_info['cipher'] == 'wpa-psk':
                node.text = '4';
                node_auth.text='3';
            else:
                node.text = '1';
                node_auth.text='0';
        else:
            auth_info_node = ElementTree.SubElement (profile_node, "auth-info")

            node = ElementTree.SubElement (auth_info_node, "username")
            node.text = profile_info['username']
            node = ElementTree.SubElement (auth_info_node, "password")
            node.text = encode_password(profile_info['password'])

            node = ElementTree.SubElement (auth_info_node, "ask-password")
            if profile_info['ask_password'] == True:
                node.text = '1'
            else:
                node.text = '0'
                node = ElementTree.SubElement (auth_info_node, "cypher-password")
            if profile_info['cypher_password'] == True:
                node.text = '1'
            else:
                node.text = '0'

        dns_info_node = ElementTree.SubElement (profile_node, 'dns-info')
        node = ElementTree.SubElement (dns_info_node, 'manual-dns-server')
        if profile_info['auto_dns'] == True:
            node.text = '0'
        else:
            node.text = '1'
        node = ElementTree.SubElement (dns_info_node, 'dns-server-list')
        for dns in profile_info['dns_servers']:
            dns_node = ElementTree.SubElement (node, 'dns-server')
            dns_node.text = dns
#        node = ElementTree.SubElement (dns_info_node, 'wins-server-list')
        dns_node = ElementTree.SubElement (dns_info_node, 'dns-suffixes')
        node = ElementTree.SubElement (dns_node, 'active')
        if profile_info['domains'] != None and len(profile_info['domains'])>0:
            node.text = '1'
        else:
            node.text = '0'
        node = ElementTree.SubElement (dns_node, 'suffixes')
        #node.text = profile_info['domains']
        if (profile_info['domains']!=None and len(profile_info['domains'])>0):
            node.text = reduce(array2txt,profile_info['domains'])

        proxy_info_node = ElementTree.SubElement (profile_node, 'proxy-info')
        node = ElementTree.SubElement (proxy_info_node, 'configuration')
        node.text = str(profile_info['proxy'])
        proxy_list_node = ElementTree.SubElement (proxy_info_node, 'proxy-list')
        if profile_info.has_key('proxy_ip') and profile_info['proxy_ip'] != None:
            if profile_info['proxy_same_proxy']:
                proxy_node = ElementTree.SubElement (proxy_list_node, 'proxy')
                proxy_node.set ('type', 'any')
                proxy_node.text = "%s:%s" % (profile_info['proxy_ip'], profile_info['proxy_port'])
            else:
                proxy_node = ElementTree.SubElement (proxy_list_node, 'proxy')
                proxy_node.set ('type', 'http')
                proxy_node.text = "%s:%s" % (profile_info['proxy_ip'], profile_info['proxy_port'])

                proxy_node = ElementTree.SubElement (proxy_list_node, 'proxy')
                proxy_node.set ('type', 'ftp')
                proxy_node.text = "%s:%s" % (profile_info['proxy_ftp_ip'], profile_info['proxy_ftp_port'])

                proxy_node = ElementTree.SubElement (proxy_list_node, 'proxy')
                proxy_node.set ('type', 'https')
                proxy_node.text = "%s:%s" % (profile_info['proxy_https_ip'], profile_info['proxy_https_port'])

                proxy_node = ElementTree.SubElement (proxy_list_node, 'proxy')
                proxy_node.set ('type', 'socks')
                proxy_node.text = "%s:%s" % (profile_info['proxy_socks_ip'], profile_info['proxy_socks_port'])

        if profile_info['proxy_ignore'] != None and len(profile_info['proxy_ignore'])>0:
            bypass_proxy_node = ElementTree.SubElement (proxy_info_node, 'bypass-proxy')
            bypass_addresses = ElementTree.SubElement (bypass_proxy_node, 'bypass-addresses')
            bypass_addresses.text=reduce(array2txt,profile_info['proxy_ignore'])


        apn_node = ElementTree.SubElement (profile_node, 'apn')
        apn_node.text = profile_info['apn']

        ip_info_node = ElementTree.SubElement (profile_node, 'ip-info')
        node = ElementTree.SubElement (ip_info_node, 'active')
        if profile_info['ip_info_active'] == True:
            node.text = '1'
        else:
            node.text = '0'
        node = ElementTree.SubElement (ip_info_node, 'address')
        node.text = profile_info['ip_info_address']


