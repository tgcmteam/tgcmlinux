#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : José María Gonzalez Calabozo <jmgonzalezc@indra.es>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011-2012, Telefónica Móviles España S.A.U.
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

import dbus
import gobject
import gconf
import time
import re
import gtk
import os
import pwd
import uuid

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import gettext
import __builtin__
__builtin__._ = gettext.gettext

import tgcm
import FreeDesktop
import Singleton

from tgcm.core.DeviceManager import DEVICE_WIRED, DEVICE_WLAN, DEVICE_MODEM
from MobileManager.MobileManagerDbus import MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI
from NetworkManagerDbus import NM_URI, NM_SETTINGS_PATH, NM_SETTINGS_IFACE, NM_CONN_SETTINGS_IFACE


class ConnectionSettingsManager(gobject.GObject):
    __metaclass__ = Singleton.Singleton
    __gsignals__ = {
        'connection-added' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'connection-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'connection-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'priorities-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.gconf_path = "%s/%s" % (tgcm.gconf_path, tgcm.country_support)
        self.client = gconf.client_get_default()
        #self.client.add_dir(self.gconf_path, gconf.CLIENT_PRELOAD_RECURSIVE)
        self.device_manager = FreeDesktop.DeviceManager()

        self.bus = dbus.SystemBus()
        proxy = self.bus.get_object(NM_URI, NM_SETTINGS_PATH)
        self.nm_settings = dbus.Interface(proxy, dbus_interface=NM_SETTINGS_IFACE)

        self.known_conn_settings = {}

        self.__load_connections_from_gconf()
        self.__load_connections()
        self.__connect_signals()
        self.get_connections_list()
        #self.__print_known_conns_sett()


    def __load_connections_from_gconf(self):
        """
        Load connection info from gconf and stores it into Network Manager
        """
        for conn_path in self.client.all_dirs("%s/connections/wwan" % self.gconf_path):
            name = self.client.get_string("%s/name" % conn_path)
            if len(name) > 0:
                conn_data = self.get_connection_info_dict_from_gconf(conn_path)
                try:
                    self.add_wwan_connection(conn_data, write_gconf_if_required=False, update_if_possible=True) #Update NM with gconf content
                    self.__add_list_connection(conn_data)
                except Exception, err:
                    tgcm.info("ERROR in add_wwan_connection %s-%s: %s"  % (conn_data['name'], conn_data['uuid'], err))

        for conn_path in self.client.all_dirs('%s/connections/wifi' % self.gconf_path):
            name = self.client.get_string('%s/name' % conn_path)
            if len(name) > 0:
                conn_data = self.get_connection_info_dict_from_gconf(conn_path)
                self.add_wifi_connection(conn_data, write_gconf_if_required=False, update_if_possible=True)
                self.__add_list_connection(conn_data)

    def get_connection_profile(self):
        """
        Gets the default profile for a new connection defined by the user
        """
        conn = ConnectionSettings(self)
        conn['name'] = ''
        conn['default'] = False
        conn['editable'] = True
        conn['ask_password']= False
        self.__read_wwan_connection_params (conn, "%s/connections/wwan/connection/profile0" % self.gconf_path)
        return conn


    def get_connection_info_dict (self, name=''):
        """
        @deprecated:
        It gets the network settings for a network named 'name'
        @param name: Network name.
        @type name: string
        @return: A dictionary with all the information refered to that network
        """
        if (name=='') or name==None:
            return self.get_connection_by_index(0)

        for connection_setting in self.known_conn_settings.values():
            if connection_setting['name']==name:
                return connection_setting

        return None
    def get_connection_by_uuid (self, uuid):
        """
        @deprecated:
        It gets the network settings for a network with an specified uuid
        @param name: uuid.
        @type name: string
        @return: A dictionary with all the information refered to that network
        """

        for connection_setting in self.known_conn_settings.values():
            if connection_setting['uuid']==uuid:
                return connection_setting

        return None

    def get_connection_by_index(self,index=0):
        """
        It gets the network settings for the given index
        @param index: Network index as defined by the user preferences
        @type index: integer
        @requires: ConnectionSettings object
        """
        conn_list=self.get_connections_list()
        try:
            return conn_list[index]
        except:
            return None

    def get_connection_info_dict_from_gconf(self,connection=''):
        uuid =  self.client.get_string ("%s/uuid" % connection)
        conn = ConnectionSettings(self, uuid=uuid)
        conn['name'] = self.client.get_string("%s/name" % connection)
        conn['default'] = self.client.get_bool("%s/default" % connection)
        conn['editable'] = self.client.get_bool("%s/editable" % connection)
        conn['origin'] = 'gconf'
        conn['gconf_path'] = connection
        conn['deviceType'] = self.client.get_int("%s/deviceType" % connection)

        is_profile_set = False
        for profile_path in self.client.all_dirs ("%s" % connection):
            if conn['deviceType'] == DEVICE_WIRED:
                pass
            elif conn['deviceType'] == DEVICE_WLAN:
                self.__read_wifi_connection_params(conn, profile_path)
                break
            elif conn['deviceType'] == DEVICE_MODEM:
                condition = self.client.get_string("%s/condition" % profile_path)
                if self.__check_connection_condition (condition):
                    is_profile_set = True
                    self.__read_wwan_connection_params(conn, profile_path)
                    break

                if not is_profile_set:
                    if tgcm.country_support == "uk":
                        for profile_path in self.client.all_dirs ("%s" % connection):
                            condition = self.client.get_string("%s/condition" % profile_path)
                            if condition == "is-postpaid":
                                self.__read_wwan_connection_params (conn, profile_path)
                                break
                    else:
                        for profile_path in self.client.all_dirs ("%s" % connection):
                            self.__read_wwan_connection_params (conn, profile_path)
                            break

        return conn

    def get_connection_info_dict_with_profiles (self, conn_settings):
        """
        Exports the connection settings with all the available profiles
        """
        if conn_settings['origin']=='gconf':
            profiles = []
            for profile_path in self.client.all_dirs ("%s" % conn_settings['gconf_path']):
                profile = {}
                if conn_settings['deviceType']==DEVICE_WLAN:
                    self.__read_wifi_connection_params (profile, profile_path)
                else:
                    self.__read_wwan_connection_params (profile, profile_path)

                profiles.append(profile)
                conn_settings['profiles'] = profiles


        return conn_settings

    def __read_wwan_connection_params (self, conn, profile_path):
        """
        Reads the selected profile for the given connection.
        @param conn: Connection dictionary
        @type conn: Dictionary
        @param profile_path: Path to the desired connection profile
        @type profile_path: String
        """
        conn['deviceType'] = DEVICE_MODEM
        conn['type'] = "gsm"

        conn['apn'] = self.client.get_string("%s/apn" % profile_path)
        conn['condition'] = self.client.get_string("%s/condition" % profile_path)

        conn['username'] = self.client.get_string("%s/auth/user" % profile_path)
        conn['password'] = self.client.get_string("%s/auth/pass" % profile_path)
        conn['ask_password'] = self.client.get_bool("%s/auth/ask_password" % profile_path)
        conn['cypher_password'] = self.client.get_bool("%s/auth/cypher_password" % profile_path)

        conn['auto_dns'] = self.client.get_bool("%s/dns_info/auto_dns" % profile_path)
        conn['dns_servers'] = self.client.get_list ("%s/dns_info/dns_servers" % profile_path, gconf.VALUE_STRING)

        conn['domain_active'] = self.client.get_bool("%s/dns_info/dns_suffixes_active" % profile_path)
        conn['domains'] = self.client.get_list ("%s/dns_info/dns_suffixes" % profile_path, gconf.VALUE_STRING)

        conn['proxy'] = self.client.get_bool("%s/proxy_info/proxy" % profile_path)
        if conn['proxy'] != 1:
            conn['proxy_ip'] = None
            conn['proxy_port'] = None

            conn['proxy_same_proxy'] = True

            conn['proxy_ip'] = None
            conn['proxy_port'] = None

            conn['proxy_ftp_ip'] = None
            conn['proxy_ftp_port'] = None

            conn['proxy_https_ip'] = None
            conn['proxy_https_port'] = None

            conn['proxy_socks_ip'] = None
            conn['proxy_socks_port'] = None

            conn['proxy_ignore'] = None
        else:
            conn['proxy_same_proxy'] = self.client.get_bool("%s/proxy_info/proxy_same_proxy" % profile_path)

            conn['proxy_ip'] = self.client.get_string("%s/proxy_info/proxy_ip" % profile_path)
            conn['proxy_port'] = self.client.get_int("%s/proxy_info/proxy_port" % profile_path)

            conn['proxy_ftp_ip'] = self.client.get_string("%s/proxy_info/proxy_ftp_ip" % profile_path)
            conn['proxy_ftp_port'] = self.client.get_int("%s/proxy_info/proxy_ftp_port" % profile_path)

            conn['proxy_https_ip'] = self.client.get_string("%s/proxy_info/proxy_https_ip" % profile_path)
            conn['proxy_https_port'] = self.client.get_int("%s/proxy_info/proxy_https_port" % profile_path)

            conn['proxy_socks_ip'] = self.client.get_string("%s/proxy_info/proxy_socks_ip" % profile_path)
            conn['proxy_socks_port'] = self.client.get_int("%s/proxy_info/proxy_socks_port" % profile_path)

            conn['proxy_ignore'] = self.client.get_list("%s/proxy_info/proxy_ignore" % profile_path,gconf.VALUE_STRING )


        conn['ip_info_active'] = self.client.get_bool("%s/ip_info/active" % profile_path)
        conn['ip_info_address'] = self.client.get_string("%s/ip_info/address" % profile_path)

    def __read_wifi_connection_params(self, conn, profile_path):
        conn['deviceType'] = DEVICE_WLAN
        conn['type'] = '802-11-wireless'

        profile = {}
        profile['ssid'] = self.client.get_string('%s/ssid' % profile_path)
        profile['mac'] = self.client.get_string('%s/mac' % profile_path)
        profile['encryption'] = self.client.get_int('%s/encryption' % profile_path)
        profile['authentication'] = self.client.get_int('%s/authentication' % profile_path)
        profile['network-password'] = self.client.get_string('%s/network-password' % profile_path)
        profile['hidden'] = self.client.get_bool('%s/hidden' % profile_path)
        profile['type'] = self.client.get_string('%s/type' % profile_path)
        profile['user'] = self.client.get_string('%s/user' % profile_path)
        profile['password'] = self.client.get_string('%s/password' % profile_path)

        conn['profiles'] = []
        conn['profiles'].append(profile)

    def __check_connection_condition (self, condition):
        """
        Checks if a condition is valid for the selected mail GPRS device
        @param condition: Condition to be evaluated, obtained from gconf: connections/wwwan/connectionX/profileX/condition
        @type condition: string
        @return: True if the condition is satisfied, false otherwise
        """
        if condition == 'default':
            return True
        else:
            dev = self.device_manager.get_main_device()
            if dev == None :
                return False
            elif dev.get_type() == DEVICE_MODEM :
                if condition.startswith('match-imsi:'):
                    if dev.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) == False:
                        return False

                    match = condition[11:]
                    p = re.compile(match)

                    try:
                        imsi = dev.get_imsi()
                        if p.match (imsi):
                            tgcm.debug("IMSI MATCH VERIFIED")
                            return True
                        else:
                            return False
                    except:
                        return False
                elif condition == 'is-postpaid':
                    if dev.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) == False:
                        return False

                    if dev.is_postpaid():
                        tgcm.debug("POSTPAID VERIFIED")
                        return True
                    else:
                        return False
                elif condition == 'is-prepaid':
                    if dev.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) == False:
                        return False

                    if dev.is_postpaid():
                        tgcm.debug("PREPAID VERIFIED")
                        return False
                    else:
                        return True

            return False

    def add_regional_info_wwan_connection (self, conn, wwan_prototype=False):
        """
        Add regional info settings to the gconf.
        It is called by XMLConfig on first startup (via add_wwan_connection),
        when a new GSM connection with proxy is added or when it is imported from a file

        @param conn: Connection information
        @type conn: Dictionary
        @param wwan_prototype: Used to create a prototype which will be used as default new connection
        @type wwan_prototype: Boolean
        @return: GConf name path
        """
        conn_name=''

        if  wwan_prototype == False:

            for tmp_con_name in self.client.all_dirs ("%s/connections/wwan" % self.gconf_path):
                uuid=self.client.get_string ("%s/uuid" % tmp_con_name)
                if uuid== conn['uuid']:
                    conn_name=tmp_con_name

            if conn_name=='':
                counter = -1
                while True:
                    counter += 1
                    if not self.client.dir_exists ("%s/connections/wwan/connection%d" % (self.gconf_path, counter)):
                        conn_name = "%s/connections/wwan/connection%d" % (self.gconf_path, counter)
                        break
        else:
            conn_name = "%s/connections/wwan/connection" % (self.gconf_path)

        self.client.set_string ("%s/name" % conn_name, conn['name'])
        conn['origin']='gconf'
        conn['deviceType'] = DEVICE_MODEM
        self.client.set_int ("%s/deviceType" % conn_name, conn['deviceType'])

        if ('uuid' in conn):
            self.client.set_string ("%s/uuid" % conn_name, conn['uuid'])


        self.client.set_bool ("%s/editable" % conn_name, conn['editable'])
        counter = 0
        for profile in conn['profiles']:
            self.client.set_string ("%s/profile%d/condition" % (conn_name, counter), profile['condition'])
            self.client.set_string ("%s/profile%d/auth/user" % (conn_name, counter), profile['username'])
            if ('password' not in profile or profile['password'] is None):
                self.client.set_string ("%s/profile%d/auth/pass" % (conn_name, counter), '')
            else:
                self.client.set_string ("%s/profile%d/auth/pass" % (conn_name, counter), profile['password'])

            self.client.set_bool ("%s/profile%d/auth/ask_password" % (conn_name, counter), profile['ask_password'])
            self.client.set_bool ("%s/profile%d/auth/cypher_password" % (conn_name, counter), profile['cypher_password'])
            self.client.set_bool ("%s/profile%d/dns_info/auto_dns" % (conn_name, counter), profile['auto_dns'])
            if profile.has_key('dns_servers') and len(profile['dns_servers']) > 0:
                self.client.set_list ("%s/profile%d/dns_info/dns_servers" % (conn_name, counter), gconf.VALUE_STRING, profile['dns_servers'])
            else:
                self.client.set_list ("%s/profile%d/dns_info/dns_servers" % (conn_name, counter), gconf.VALUE_STRING, [])

            if profile.has_key('domain_active') and profile['domain_active']!=None:
                self.client.set_bool ("%s/profile%d/dns_info/dns_suffixes_active" % (conn_name, counter), profile['domain_active'])
            else:
                self.client.set_bool ("%s/profile%d/dns_info/dns_suffixes_active" % (conn_name, counter), False)

            if profile.has_key('domains') and len(profile['domains']) > 0:
                self.client.set_list ("%s/profile%d/dns_info/dns_suffixes" % (conn_name, counter), gconf.VALUE_STRING, profile['domains'])
            else:
                self.client.set_list ("%s/profile%d/dns_info/dns_suffixes" % (conn_name, counter), gconf.VALUE_STRING, [])

            if  ('proxy' in profile and profile['proxy'] == True ):
                self.client.set_bool("%s/profile%d/proxy_info/proxy" % (conn_name, counter), True)
            else:
                self.client.set_bool("%s/profile%d/proxy_info/proxy" % (conn_name, counter), False)

            if  ('proxy_same_proxy' in profile and profile['proxy_same_proxy'] == True ):
                self.client.set_bool("%s/profile%d/proxy_info/proxy_same_proxy" % (conn_name, counter),True)
            else:
                self.client.set_bool("%s/profile%d/proxy_info/proxy_same_proxy" % (conn_name, counter),False)

            if ('proxy_ip' in profile and profile['proxy_ip'] is not None):
                self.client.set_string ("%s/profile%d/proxy_info/proxy_ip" % (conn_name, counter), profile['proxy_ip'])
            else:
                self.client.set_string ("%s/profile%d/proxy_info/proxy_ip" % (conn_name, counter), '')

            if ('proxy_port' in profile and profile['proxy_port'] is not None):
                self.client.set_int ("%s/profile%d/proxy_info/proxy_port" % (conn_name, counter), profile['proxy_port'])
            else:
                self.client.set_int ("%s/profile%d/proxy_info/proxy_port" % (conn_name, counter), 80)

            if ('proxy_ftp_ip' in profile and profile['proxy_ftp_ip'] != None):
                self.client.set_string ("%s/profile%d/proxy_info/proxy_ftp_ip" % (conn_name, counter), profile['proxy_ftp_ip'])
                self.client.set_int ("%s/profile%d/proxy_info/proxy_ftp_port" % (conn_name, counter), profile['proxy_ftp_port'])

            if ('proxy_https_ip' in profile and  profile['proxy_https_ip'] != None):
                self.client.set_string ("%s/profile%d/proxy_info/proxy_https_ip" % (conn_name, counter), profile['proxy_https_ip'])
                self.client.set_int ("%s/profile%d/proxy_info/proxy_https_port" % (conn_name, counter), profile['proxy_https_port'])

            if ('proxy_socks_ip'in profile and profile['proxy_socks_ip'] != None):
                self.client.set_string ("%s/profile%d/proxy_info/proxy_socks_ip" % (conn_name, counter), profile['proxy_socks_ip'])
                self.client.set_int ("%s/profile%d/proxy_info/proxy_socks_port" % (conn_name, counter), profile['proxy_socks_port'])

            if ('proxy_ignore' in profile) and (profile['proxy_ignore'] != None):
                self.client.set_list ("%s/profile%d/proxy_info/proxy_ignore" % (conn_name, counter), gconf.VALUE_STRING, profile['proxy_ignore'])

            self.client.set_string ("%s/profile%d/apn" % (conn_name, counter), profile['apn'])
            self.client.set_bool ("%s/profile%d/ip_info/active" % (conn_name, counter), profile['ip_info_active'])

            if ('ip_info_address' in profile) and (profile['ip_info_address'] != None):
                self.client.set_string ("%s/profile%d/ip_info/address" % (conn_name, counter), profile['ip_info_address'])

            counter += 1

        return conn_name

    def add_regional_info_wifi_connection(self, conn, wifi_prototype=False):
        """
        Add regional info settings to the gconf.
        It is called by XMLConfig on first startup (via add_wwan_connection),
        when a new WiFi connection with proxy is added or when it is imported from a file

        @param conn: Connection information
        @type conn: Dictionary
        @param wwan_prototype: Used to create a prototype which will be used as default new connection
        @type wwan_prototype: Boolean
        @return: GConf name path
        """
        conn_path = None
        if wifi_prototype == False:
            for tmp_conn_path in self.client.all_dirs('%s/connections/wifi' % self.gconf_path):
                uuid = self.client.get_string('%s/uuid' % tmp_conn_path)
                if uuid == conn['uuid']:
                    conn_path = tmp_conn_path

            if conn_path is None:
                counter = -1
                while True:
                    counter += 1
                    if not self.client.dir_exists('%s/connections/wifi/connection%d' % (self.gconf_path, counter)):
                        conn_path = '%s/connections/wifi/connection%d' % (self.gconf_path, counter)
                        break
        else:
            conn_path = '%s/connections/wifi/connection' % self.gconf_path

        self.client.set_string('%s/name' % conn_path, conn['name'])
        self.client.set_bool('%s/editable' % conn_path, conn['editable'])
        conn['origin'] = 'gconf'
        conn['deviceType'] = DEVICE_WLAN
        self.client.set_int('%s/deviceType' % conn_path, conn['deviceType'])
        if 'uuid' in conn:
            self.client.set_string('%s/uuid' % conn_path, conn['uuid'])

        profile_path = '%s/profile' % conn_path
        profile_data = conn['profiles'][0]
        self.client.set_int('%s/authentication' % profile_path, int(profile_data['authentication']))
        self.client.set_int('%s/encryption' % profile_path, int(profile_data['encryption']))
        self.client.set_bool('%s/hidden' % profile_path, profile_data['hidden'])
        self.client.set_string('%s/mac' % profile_path, profile_data['mac'])
        self.client.set_string('%s/network-password' % profile_path, profile_data['network-password'])
        self.client.set_string('%s/ssid' % profile_path, profile_data['ssid'])
        self.client.set_string('%s/type' % profile_path, profile_data['type'])
        self.client.set_string('%s/user' % profile_path, profile_data['user'])
        self.client.set_string('%s/password' % profile_path, profile_data['password'])

        return conn_path

    def add_wwan_connection (self, conn_data, write_gconf_if_required=True, must_write_gconf=False,update_if_possible=False,password=None):
        """
        Adds a GSM connection to the Network Manager
        @param conn_data: Network parameters
        @type conn_data: Dictionary with network information
        @param write_gconf_if_required: If true it will write proxy info to gconf if available.
                                   If false it will not write any value to gconf even if there is a proxy defined.
        @type write_gconf_if_required: boolean
        @param must_write_gconf: If true it will write all the connection setting to gconf, even if it has not a proxy
        @type must_write_gconf: boolean
        @param update_if_possible:  If true it will try to update any connection which have the same name.
                                    If false it will create a new connection even if there is another one with the same name
        @type update_if_possible: boolean
        @param password:  String with a password for the connection. If None the password used is the given by conn_data
        @type password: string
        """
        def ip2int(s_ip):
            if len(s_ip)==0:
                return 0L

            s_ip=s_ip.rstrip().split('.')
            i_ip=0L
            while s_ip:
                i_ip=(i_ip<<8)+int(s_ip.pop())

            #if (i_ip>(2L**31-1)):
            #    i_ip=int(i_ip-2L**32)

            return i_ip

        if 'profiles' in conn_data:
            profile = conn_data['profiles'][0]
        else:
            profile = conn_data

        new_conn=False
        if ('uuid' not in conn_data) or (conn_data["uuid"] is None):
            conn_data["uuid"] = str(uuid.uuid1())
            new_conn = True

        password_flags = 4L

        username = pwd.getpwuid(os.getuid())[0]
        s_con = dbus.Dictionary({
            'autoconnect':0,
            'id': conn_data["name"],
            'timestamp': time.time(),
            'type':'gsm',
            'permissions': ['user:%s' % username,],
            'uuid':conn_data["uuid"]})

        s_gsm = dbus.Dictionary({
            'apn':profile["apn"],
            'home_only':1,
            'number':'*99***1#',
            # -- Disable the Secret Agent for the movistar connections for avoiding the password dialog
            # -- when the connection fails.
            # -- The flag values are described in the documentation 'ref-settings.html' of 'network-manager-dev'
            #'password-flags': password_flags,
            'cypher_password': False,
            'editable': False})

        if not (profile['username']=='' or profile['username']==None):
            s_gsm['username']=profile["username"]

        if password is not None:
            s_gsm['password']=password
        elif not (profile['password']=='' or profile['password']==None):
            s_gsm['password']=profile["password"]

        s_serial=dbus.Dictionary({u'baud': 115200L})

        if 'dns_servers' in profile and len(profile['dns_servers']) > 0:
            dns_servers=map(ip2int,profile['dns_servers'])
            while 0 in dns_servers:
                dns_servers.remove(0)
        else:
            dns_servers=[];

        if 'domains' in profile and len(profile['domains']) > 0:
            dns_domains=profile['domains']
        else:
            dns_domains=['']


        if len(dns_servers)>0:
            s_ipv4=dbus.Dictionary({dbus.String(u'routes'): dbus.Array([], signature=dbus.Signature('au'), variant_level=1), dbus.String(u'method'): dbus.String(u'auto', variant_level=1), dbus.String(u'addresses'): dbus.Array([], signature=dbus.Signature('au'), variant_level=1), dbus.String(u'dns'): dbus.Array(dns_servers, signature=dbus.Signature('u'), variant_level=1), dbus.String(u'ignore-auto-dns'): dbus.Boolean(True, variant_level=1),dbus.String(u'dns-search'): dbus.Array(dns_domains)}, signature=dbus.Signature('sv'))
        else:
            s_ipv4=dbus.Dictionary({'addresses': [0], 'dns': [0], 'dns-search':dns_domains, 'method': 'auto', 'routes': [0]})

        s_ipv6=dbus.Dictionary({'method': 'ignore'})


        conDict = dbus.Dictionary({
            'connection': s_con,
            'gsm': s_gsm,
            'ipv4':s_ipv4,
            'ipv6':s_ipv6,
            'ppp':{},
            'serial':s_serial})

        if new_conn==True :
            if self.__add_or_update_nm(conDict,update_if_possible):
                #This means it has been upddated an the uuid is different
                conn_data['uuid']=str(conDict['connection']['uuid'])
                self.__update_uuid(conn_data)
            if conn_data.__class__.__name__ == 'ConnectionSettings':
                conn_data.reload_dbus()
        else:
            try:
                object_path=self.nm_settings.GetConnectionByUuid(conn_data['uuid'])
                proxy = self.bus.get_object(NM_URI, object_path)
                connection = dbus.Interface(proxy, NM_CONN_SETTINGS_IFACE)
                connection.Update(conDict)
                tgcm.info("Updated Connection - %s - %s "%(conn_data['name'],conn_data['uuid']))
            except:
                if self.__add_or_update_nm(conDict,update_if_possible):
                    #This means it has been upddated an the uuid is different
                    conn_data['uuid']=str(conDict['connection']['uuid'])
                    self.__update_uuid(conn_data)

                if conn_data.__class__.__name__ == 'ConnectionSettings':
                    conn_data.reload_dbus()

        #We need to do this because NetworkManager0.9 does not manage proxy configuration.
        #This will change in future version of NM.
        if ((conn_data['editable'] == True) and \
                ((profile['proxy'] == True) or (profile['ask_password'] == True)) and \
                (write_gconf_if_required == True)) or (must_write_gconf == True):
            if ('profiles' not in conn_data):
                conn_data['profiles']=[]
                conn_data['profiles'].append(profile)
            conn_name=self.add_regional_info_wwan_connection(conn_data)
            conn_settings=self.get_connection_info_dict_from_gconf(conn_name)
            self.__add_list_connection(conn_settings)

        return conn_data
        #end def add_wwan_connection

    def add_wifi_connection(self, conn_data, write_gconf_if_required=True, \
            must_write_gconf=False, update_if_possible=False, password=None):

        ap = {}
        ap['name'] = conn_data['name']
        ap['Ssid'] = conn_data['profiles'][0]['ssid']
        ap['password'] = conn_data['profiles'][0]['password']
        ap['hidden'] = conn_data['profiles'][0]['hidden']

        # http://projects.gnome.org/NetworkManager/developers/api/09/spec.html#type-NM_802_11_AP_SEC
        encryption = int (conn_data['profiles'][0]['encryption'])
        authentication = int(conn_data['profiles'][0]['authentication'])

        if encryption==1:
            # No encryption
            ap['flags'] = 0
        else:
            # Wi-Fi network is encrypted, set some flags
            ap['flags'] = 1
            ap['rsnFlags'] = 0
            ap['wpaFlags'] = 0

        # Some additional flags in case network is encrypted
        if encryption == 0 :
            # WEP encryption
            ap['wpaFlags'] = 0
        elif authentication == 3:
            # WPA encryption
            ap['wpaFlags'] = 0x8 or 0x200
        elif authentication==4:
            # WPA_PSK encryption
            ap['wpaFlags'] = 0x8 or 0x200
        elif authentication==6:
            # WPA2 encryption
            ap['wpaFlags'] = 0x8 or 0x200
        elif authentication==7:
            # WPA2_PSK encryption
            ap['wpaFlags'] = 0x8 or 0x200


        conDict = self.add_wifi_connection_to_nm(ap, ap['name'], ap['password'])
        uuid = str(conDict['connection']['uuid'])
        conn_data['uuid'] = uuid

        is_editable = conn_data['editable'] == True
        if (not is_editable) and (write_gconf_if_required or must_write_gconf):
            conn_name = self.add_regional_info_wifi_connection(conn_data)
            #conn_settings = self.get_connection_info_dict_from_gconf(conn_name)
            #self.__add_list_connection(conn_settings)

        return conn_data

    def add_wifi_connection_to_nm(self, ap, conn_name=None, password=None, mode=None):
        """
        Adds a WiFi connection to the Network Manager
        @param ap: Wifi Access Point
        @type ap: Dictionary with Access Point information
        @param name: Network name profile
        @type name: String
        @param password: Wifi password
        @type password: String
        @param mode: Wifi mode 'infraestructure' or 'ad-hoc'
        @type mode: String
        @return: new connection UUID if succeed, None otherwise
        """

        if ap is None:
            return

        if conn_name is None:
            conn_name = str(ap["Ssid"])

        username = pwd.getpwuid(os.getuid())[0]
        tmp_uuid=str(uuid.uuid1())
        s_con = dbus.Dictionary({'autoconnect': 0,
            'id': conn_name,
            'type': '802-11-wireless',
            'permissions': ['user:%s' % username,],
            'uuid': tmp_uuid})

        if mode is None:
            mode = 'infrastructure'

        s_wireless = dbus.Dictionary({'ssid':dbus.ByteArray(ap["Ssid"]),'mode': mode }) #str(ap["Ssid"]),
        #    'mac-address':dbus.ByteArray(ap["HwAddress"]), #[str(ap["HwAddress"])],
        #   'mode': 'infrastructure'})
        #  http://cgit.freedesktop.org/NetworkManager/NetworkManager/tree/examples/python
        #  http://cgit.freedesktop.org/NetworkManager/NetworkManager/tree/examples/python/update-secrets.py

        s_ipv4 = dbus.Dictionary({'method': 'auto'})

        #if (ap["flags"]==freedesktopnet.networkmanager.accesspoint.AccessPoint.Flags.PRIVACY):
        if ap["flags"] != 0x0:
            s_wireless['security'] = '802-11-wireless-security';
            if (ap["wpaFlags"] == 0) and (ap["rsnFlags"] == 0):
                s_wireless_security = {'key-mgmt': 'none'}
                s_wireless_security["wep-tx-keyidx"] = 0
                if password is not None:
                    #s_wireless_security["wep-key-type"] = 2 Use with hasked hey
                    s_wireless_security["wep-key-type"] = 1 #Use with plain text key
                    s_wireless_security['wep-key0'] = password
            else: #e1Wtka7rRR3EOHAyRoQR
                # WPA(TKIP) - WpaFlags - PAIR_TKIP,GROUP_TKIP,KEY_MGMT_PSK
                # WPA(AES)--- RsnFlags - PAIR_TKIP,GROUP_TKIP,KEY_MGMT_PSK
                # WPA2(TKIP) -WpaFlags - PAIR_CCMP,GROUP_CCMP,KEY_MGMT_PSK
                # WPA2(AES) - RsnFlags - PAIR_TKIP,GROUP_TKIP,KEY_MGMT_PSK
                s_wireless_security = {'key-mgmt': 'wpa-psk', 'proto': ['wpa', 'rsn']}
                if password is not None:
                    s_wireless_security['psk'] = password

            conDict = dbus.Dictionary({'connection': s_con,
                '802-11-wireless': s_wireless,
                'ipv4': s_ipv4,
                '802-11-wireless-security': s_wireless_security})

        else:
            conDict = dbus.Dictionary({'connection': s_con,
                '802-11-wireless': s_wireless,
                'ipv4': s_ipv4})

        try:
            self.__add_or_update_nm(conDict, update_if_possible=True)
            return conDict
        except:
            return None

    def del_connection (self, conn_settings):
        conn_settings.delete()

    def del_all_readonly_connections(self):
        connections=self.get_connections_list()
        for conn_settings in connections:
            if conn_settings['origin']!='networkmanager' and conn_settings['editable']==False:
                conn_settings['editable']=True
                conn_settings.delete()

    def set_connection_list(self,conn_settings_list):
        """
        Sets the list of network names in priority order
        @param conn_settings_list:
        """
        self._set_connection_list(conn_settings_list)
        self.emit('priorities-changed')

    def _set_connection_list(self, conn_settings_list):
        """
        Sets the list of network names in priority order
        @param conn_settings_list:
        """
        uuid_list = []
        for conn_settings in conn_settings_list:
            uuid_list.append(conn_settings.get_uuid())

        self._set_connection_list_by_uuid(uuid_list)

    def _set_connection_list_by_uuid(self,uuid_list):
        self.client.set_list("%s/connections/sorted_connections" % self.gconf_path, gconf.VALUE_STRING, uuid_list)

    def get_connections_list(self, show_ethernet=True, show_wifi=True, show_3G=True):
        """
        Gets the list of network names in priority order
        @param show_ethernet: If true, shows ethernet connections. Default value True
        @type show_ethernet: boolean
        @param show_wifi: If true, shows wifi connections. Default value True
        @type show_wifi: boolean
        @param show_3G: If true, shows 3G connections. Default value True
        @type show_3G: boolean
        @return: A ConnectionSettings array with all the network connections in priority order
        """

        conn_settings_list = []
        conn_settings_ether_list = []
        conn_settings_wifi_list = []
        conn_settings_3G_list = []

        #uuid_list is a string array of UUIDs
        orig_uuid_list = self.client.get_list ("%s/connections/sorted_connections" % self.gconf_path, gconf.VALUE_STRING)

        uuid_list=list(orig_uuid_list)
        for uuid in orig_uuid_list:
            if self.known_conn_settings.has_key(uuid):
                conn_settings=self.known_conn_settings[uuid];
                if conn_settings['deviceType'] == DEVICE_MODEM and show_3G == True:
                    conn_settings_list.append(conn_settings)
                elif conn_settings['deviceType'] == DEVICE_WLAN and show_wifi == True:
                    conn_settings_list.append(conn_settings)
                elif conn_settings['deviceType'] == DEVICE_WIRED and show_ethernet == True:
                    conn_settings_list.append(conn_settings)
            else:
                uuid_list.remove(uuid)

        for conn_settings in self.known_conn_settings.values():
            uuid=conn_settings.get_uuid()
            if uuid not in uuid_list:
                if conn_settings['deviceType'] == DEVICE_MODEM and show_3G == True:
                    conn_settings_list.append(conn_settings)
                    conn_settings_ether_list.append(conn_settings)
                elif conn_settings['deviceType'] == DEVICE_WLAN and show_wifi == True:
                    conn_settings_list.append(conn_settings)
                    conn_settings_wifi_list.append(conn_settings)
                elif conn_settings['deviceType'] == DEVICE_WIRED and show_ethernet == True:
                    conn_settings_list.append(conn_settings)
                    conn_settings_3G_list.append(conn_settings)

        if (orig_uuid_list==[]):
            conn_settings_list=[]
            conn_settings_list.extend(conn_settings_3G_list)
            conn_settings_list.extend(conn_settings_wifi_list)
            conn_settings_list.extend(conn_settings_ether_list)

        if show_ethernet==True and show_wifi==True and show_3G==True:
            self._set_connection_list(conn_settings_list)

        return conn_settings_list

    def set_first_in_list_device_type(self,my_conn_uuid,my_conn_type):
        conn_settings_list=self.get_connections_list()
        conn_settings_list_uuid=[]
        for conn_settings in conn_settings_list:
            conn_settings_list_uuid.append(str(conn_settings.get_uuid()))

        i=0
        if my_conn_type == DEVICE_WIRED:
            try:
                conn_settings_list_uuid.remove(my_conn_uuid)
            except:
                pass
            conn_settings_list_uuid.insert(0, my_conn_uuid)
        elif my_conn_type == DEVICE_WLAN:
            for conn_settings in conn_settings_list:
                if (conn_settings['deviceType'] != DEVICE_WIRED):
                    try:
                        conn_settings_list_uuid.remove(my_conn_uuid)
                    except:
                        pass

                    conn_settings_list_uuid.insert(i, my_conn_uuid)
                    break
                i=i+1
        elif my_conn_type == DEVICE_MODEM:
            for conn_settings in conn_settings_list:
                if (conn_settings['deviceType'] != DEVICE_WIRED and conn_settings['deviceType'] != DEVICE_WLAN):
                    try:
                        conn_settings_list_uuid.remove(my_conn_uuid)
                    except:
                        pass

                    conn_settings_list_uuid.insert(i, my_conn_uuid)
                    break
                i=i+1

        self._set_connection_list_by_uuid(conn_settings_list_uuid)


    def insert_after_first_ethernet(self,conn_name):
        conn_settings_list=self.get_connections_list()
        my_conn_settings=None
        for conn_settings in conn_settings_list:
            if (conn_settings['name']==conn_name):
                my_conn_settings=conn_settings;
                break
        if my_conn_settings==None:
            return

        if (conn_settings_list[0]['deviceType'] == DEVICE_WIRED):
            conn_settings_list.remove(my_conn_settings)
            conn_settings_list.insert(1, my_conn_settings)
        else:
            conn_settings_list.remove(my_conn_settings)
            conn_settings_list.insert(0, my_conn_settings)

        self.set_connection_list(conn_settings_list)


    def __update_uuid(self,conn_settings):
        if (conn_settings['uuid']!=None and conn_settings['origin']=='gconf'):
            self.client.set_string ("%s/uuid" % conn_settings['gconf_path'], conn_settings['uuid'])

        try:
            if conn_settings.object_path is None:
                conn_settings.object_path =self.nm_settings.GetConnectionByUuid(conn_settings['uuid'])
        except:
            pass

    def __add_or_update_nm(self, conDict, update_if_possible=False):
        if '802-11-wireless' in conDict:
            compareWith = 'ssid'
            txt_to_compare = conDict['802-11-wireless']['ssid']
        else:
            compareWith = 'id'
            txt_to_compare = conDict['connection']['id']

        cons = self.nm_settings.ListConnections()
        updated = False
        if update_if_possible == True:
            for object_path in cons:
                proxy = self.bus.get_object(NM_URI, object_path)
                connection = dbus.Interface(proxy, NM_CONN_SETTINGS_IFACE)

                try:
                    connection_nm_settings = connection.GetSettings()
                except dbus.exceptions.DBusException, err:
                    # Some connections could not be loaded, e.g. permissions
                    # problems
                    tgcm.warning("Couldn't load %s: %s" % (object_path, err.message))
                    continue

                conn_id = None
                if compareWith == 'ssid':
                    if '802-11-wireless' in connection_nm_settings:
                        def f(x,y): return str(x)+str(y)
                        conn_id = reduce(f, connection_nm_settings['802-11-wireless']['ssid'])
                else:
                    conn_id = str(connection_nm_settings['connection']['id'])

                if conn_id == txt_to_compare:
                    conDict['connection']['uuid'] = connection_nm_settings['connection']['uuid']
                    try:
                        connection.Update(conDict)
                        tgcm.info("Updated Connection %s - %s " % (txt_to_compare, conDict['connection']['uuid']))
                    except Exception as e:
                        tgcm.error("Error updating connection %s - %s" % (txt_to_compare, str(e)))
                    updated = True
                    break

        if not updated:
            try:
                self.nm_settings.AddConnection(conDict)
                tgcm.info("New Connection %s - %s " % (txt_to_compare, conDict['connection']['uuid']))
            except Exception as e:
                tgcm.info("Error adding connection %s - %s" % (txt_to_compare, str(e)))

        return updated

    def __load_connections(self):
        username = pwd.getpwuid(os.getuid())[0]
        for object_path in self.nm_settings.ListConnections():
            # Create a new object ConnectionSettings for this element
            try:
                conn_data = ConnectionSettings(self, object_path)
                if (conn_data is None) or (conn_data.conn_dict is None):
                    continue

                permissions = conn_data.conn_dict['permissions']
                is_applicable = len(permissions) == 0
                for right, value in permissions:
                    if right == 'user' and value == username:
                        is_applicable = True
                        break

                if is_applicable:
                    self.__add_list_connection(conn_data)
            except dbus.exceptions.DBusException, err:
                tgcm.warning("Couldn't load %s: %s" % (object_path, err.message))

    def __connect_signals(self):
        self.nm_settings.connect_to_signal('NewConnection', self.__on_new_connection)

    def __print_known_conns_sett(self):
        for cosetting in self.known_conn_settings.values():
            tgcm.info('%s - "%s"' % (cosetting.get_uuid(), cosetting.get_name()))

    def __sync_config (self):
        self.client.suggest_sync()
        while gtk.events_pending():
            gtk.main_iteration()

    def __add_list_connection(self,conn_settings):
        if self.known_conn_settings.has_key(conn_settings.get_uuid()):
            orig_conn=self.known_conn_settings[conn_settings.get_uuid()]
            orig_type=orig_conn['origin']
        else:
            orig_type=None
            orig_conn=None


        if conn_settings['origin']!='networkmanager' or orig_type==None or orig_type=='networkmanager':
            if orig_conn is not None:
                orig_conn.stop_listeners()

            self.known_conn_settings[conn_settings.get_uuid()] = conn_settings
            self.emit('connection-added',conn_settings)
            tgcm.info('Add List %s - "%s"' % (conn_settings.get_uuid(), conn_settings.get_name()))
            return True
        else:
            conn_settings.stop_listeners()
            return False

    def __del_list_connection(self,uuid):
        if self.known_conn_settings.has_key(uuid):
            conn_settings=self.known_conn_settings[uuid]
            if conn_settings['editable']:
                self.known_conn_settings.pop(uuid)
                self.emit('connection-removed',conn_settings)
                tgcm.info('Removed List %s - "%s"' % (conn_settings.get_uuid(), conn_settings.get_name()))
            else:
                if conn_settings['deviceType'] == DEVICE_MODEM:
                    self.add_wwan_connection(conn_settings)


    def is_wifi_ap_available(self,conn_settings):
        wifi_device = self.device_manager.get_wifi_device()
        if (wifi_device!=None):
            if wifi_device.is_ready():
                #def f(x,y): return str(x)+str(y)
                #ssid=reduce(f,conn_settings['802-11-wireless']['ssid'])
                ssid=conn_settings['ssid']
                for ap in wifi_device.get_access_points():
                    if ap["Ssid"]==ssid:
                        return True

        return False

    ### Signal callbacks ####
    def __on_new_connection(self, object_path):
        conn_settings = ConnectionSettings(self, object_path)
        if self.__add_list_connection(conn_settings):
            tgcm.info('on_new_connection! %s - "%s"' % (conn_settings.get_uuid(), conn_settings.get_name()))


    def _on_remove_connection(self, uuid):
        tgcm.info('on_remove_connection! - %s' % uuid)
        self.__del_list_connection(uuid)


    def _on_conn_properties_changed(self, conn_settings):
        self.emit('connection-changed',conn_settings)
        tgcm.info('_on_conn_properties_changed %s - "%s"' % (conn_settings.get_uuid(), conn_settings.get_name()))


class ConnectionSettings(gobject.GObject):
    __gsignals__ = {
        'properties-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, connection_settings_manager, object_path=None, uuid=None):
        gobject.GObject.__init__(self)

        self.conn_dict = {}
        self._manager = connection_settings_manager
        self.object_path = None

        # It is required at least an object_path or an UUID in order to create the
        # ConnectionSettings instance.
        # FIXME: Return an exception if this criteria is not met.
        if (object_path == None) and (uuid == None):
            return

        # If the object_path is unknown but we have the UUID, get a NM Connection
        # object looking for its UUID.
        if (object_path == None) and  (uuid != None):
            try:
                object_path = self._manager.nm_settings.GetConnectionByUuid(uuid)
            except Exception:
                return

        # Get a pointer to the referred NM object
        proxy = self._manager.bus.get_object(NM_URI, object_path)
        self._nm_cosetting = dbus.Interface(proxy, NM_CONN_SETTINGS_IFACE)

        # Store some interesting values
        self.object_path = self._nm_cosetting.object_path
        self.__load_data()
        if (self.conn_dict is None):
            return None

        # Listen for changes or deletion of the original Connection object
        self.__create_listeners()

    def get_dock_name(self):
        try:
            if self.conn_dict['deviceType'] == DEVICE_WLAN:
                name = self.conn_dict['ssid']
            else:
                name = self.conn_dict['name']
        except:
            name = ''
        return name


    def __load_data(self):
        def int2ip(i_ip):
            if i_ip==0:
                return '0.0.0.0'
            return str(i_ip & 0xFF)+'.'+str(i_ip>>8 & 0xFF)+'.'+str(i_ip>>16 & 0xFF)+'.'+str(i_ip>>24 & 0xFF)

        def byte_array_to_str(byte_array):
            string = ''
            for byte in byte_array:
                string += chr(byte)
            return string

        cs = self._nm_cosetting.GetSettings()
        self.conn_dict['uuid'] = str(cs["connection"]["uuid"])

        device_type = str(cs["connection"]["type"])
        self.conn_dict["type"] = device_type

        self.conn_dict['origin'] = 'networkmanager'
        if 'ask_password' not in self.conn_dict:
            self.conn_dict['ask_password'] = False

        if device_type == "gsm":
            self.conn_dict['editable']=True

            self.conn_dict['deviceType'] = DEVICE_MODEM
            self.conn_dict['apn'] = str(cs['gsm'].get('apn',''))
            self.conn_dict['condition'] = None
            self.conn_dict['username'] = str(cs['gsm'].get('username',''))

            try:
                gsmSecret = self._nm_cosetting.GetSecrets('gsm')
                self.conn_dict['password'] = gsmSecret['gsm']['password']
            except: #No password is set
                pass

        elif device_type == "802-11-wireless":
            self.conn_dict['editable'] = True

            ssid = byte_array_to_str(cs['802-11-wireless']['ssid'])
            self.conn_dict['ssid'] = ssid
            self.conn_dict['deviceType'] = DEVICE_WLAN
            self.conn_dict['username'] = ''
            self.conn_dict['password'] = None

            if 'mode' in cs['802-11-wireless']:
                self.conn_dict['mode'] = str(cs['802-11-wireless']['mode'])
            else:
                # I assume NM profiles without mode have infraestructure mode
                self.conn_dict['mode'] = 'infrastructure'

            try:
                wifiSecret = self._nm_cosetting.GetSecrets('802-11-wireless-security')
                wifiSecurity = wifiSecret['802-11-wireless-security'];
            except:
                wifiSecurity = {}

            if 'wep-key0' in wifiSecurity:
                self.conn_dict['password'] = str(wifiSecurity['wep-key0'])
                self.conn_dict['cipher'] = 'wep-key0'
            elif 'psk' in wifiSecurity:
                self.conn_dict['password'] = str(wifiSecurity['psk'])
                self.conn_dict['cipher'] = 'wpa-psk'

        elif device_type == "802-3-ethernet":
            self.conn_dict['editable'] = True
            self.conn_dict['deviceType'] = DEVICE_WIRED
            self.conn_dict['username'] = ''
            self.conn_dict['password'] = None

        else:
            self.conn_dict = None
            return None

        self.conn_dict['name'] = str(cs['connection']['id'])
        self.conn_dict['cypher_password'] = False

        self.conn_dict['permissions'] = []
        if 'permissions' in cs['connection']:
            for permission in cs['connection']['permissions']:
                foo = [x for x in str(permission).split(':') if len(x) > 0]
                self.conn_dict['permissions'].append(foo)

        self.conn_dict['domain_active'] = None
        if 'ipv4' in cs:
            self.conn_dict['auto_dns'] = not cs['ipv4'].get('ignore-auto-dns',False)
            self.conn_dict['dns_servers'] = map(int2ip,cs['ipv4'].get('dns',[]))
            self.conn_dict['domains'] = map(str,cs['ipv4'].get('dns-search',[]))

            ipaddressed=cs['ipv4'].get('addresses',[]);
            if ipaddressed==[]:
                self.conn_dict['ip_info_active'] = False
            else:
                self.conn_dict['ip_info_active'] = True
                dbus_addr_info=ipaddressed.pop();
                gateway=dbus_addr_info.pop();
                netmask=dbus_addr_info.pop();
                ip_address=dbus_addr_info.pop();
                self.conn_dict['ip_info_address'] = int2ip(ip_address)

        else:
            self.conn_dict['auto_dns'] = True
            self.conn_dict['dns_servers'] = []
            self.conn_dict['domains'] = ''
            self.conn_dict['ip_info_active'] = False
            self.conn_dict['ip_info_address'] = ''

        self.conn_dict['condition']='default'

    def __create_listeners(self):
        # Listen for deletion of its referred NM object
        self.__dbus_signals = []
        signal_id = self._nm_cosetting.connect_to_signal('Updated', self.__on_update)
        self.__dbus_signals.append(signal_id)
        signal_id = self._nm_cosetting.connect_to_signal('Removed', self.__on_remove)
        self.__dbus_signals.append(signal_id)


    def reload_dbus(self):
        if hasattr(self,"__dbus_signals"):
            self.stop_listeners()

        try:
            uuid=self.conn_dict['uuid']
            object_path = self._manager.nm_settings.GetConnectionByUuid(uuid)
        except Exception:
            return
        # Get a pointer to the referred NM object
        proxy = self._manager.bus.get_object(NM_URI, object_path)
        self._nm_cosetting = dbus.Interface(proxy, NM_CONN_SETTINGS_IFACE)

        # Store some interesting values
        self.object_path = self._nm_cosetting.object_path
        self.__create_listeners()


    def stop_listeners(self):
        # Listen for deletion of its referred NM object
        for signal_id in self.__dbus_signals:
            signal_id.remove()


    def delete(self):
        if (self.conn_dict['origin']=='gconf'):
            self._manager.client.recursive_unset (self.conn_dict['gconf_path'], gconf.UNSET_INCLUDING_SCHEMA_NAMES)

            for bookmark in self._manager.client.all_dirs ("%s/bookmarks" % self.conn_dict['gconf_path']):
                if self._manager.client.get_string ("%s/connection" % bookmark) == self.conn_dict['name']:
                    self._manager.client.set_string ("%s/connection" % bookmark, "")

            for action in self._manager.client.all_dirs ("%s/actions" % self.conn_dict['gconf_path']):
                if self._manager.client.get_string ("%s/connection" % action) == self.conn_dict['name']:
                    self._manager.client.set_string ("%s/connection" % action, '')

        self._nm_cosetting.Delete()

    def get(self, key, default):
        if self.conn_dict.has_key(key):
            return self.conn_dict[key]
        else:
            return default

    def get_name(self):
        return self.conn_dict['name']

    def get_nm_settings(self):
        return self._nm_cosetting

    def get_uuid(self):
        return self.conn_dict['uuid']

    def has_key(self,key):
        return self.conn_dict.has_key(key)

    ### Signal callbacks ###

    def __on_update(self):
        #Only editable connections are allowed to change
        if (self.conn_dict['editable']==True):
            if self.conn_dict['origin']=='networkmanager':
                self.__load_data()
            else :
                self.__load_data()
                self.conn_dict['origin']='gconf'
                if ('profiles' not in self.conn_dict):
                    self.conn_dict['profiles']=[]
                    self.conn_dict['profiles'].append(self.conn_dict)
                self._manager.add_regional_info_wwan_connection(self.conn_dict)
        self.emit('properties-changed')
        self._manager._on_conn_properties_changed(self)

    def __on_remove(self):
        self.stop_listeners()
        self._manager._on_remove_connection(self.get_uuid())

    ### Dictionary container type emulation ###

    def __contains__(self, item):
        return item in self.conn_dict

    def __getitem__(self,key):
        if key in self.conn_dict:
            return self.conn_dict[key]
        else:
            return None

    def __len__(self):
        return len(self.conn_dict)

    def __setitem__(self, key, value):
        self.conn_dict[key] = value


gobject.type_register(ConnectionSettingsManager)
gobject.type_register(ConnectionSettings)


def main():
    import __builtin__
    import gettext

    __builtin__._ = gettext.gettext

    cs = ConnectionSettingsManager()
    cl=cs.get_connections_list(show_3G=False)
    i=0;
    for conn in cl:
        i=i+1
        print '%d- %s - "%s"' % (i,conn.get_uuid(), conn.get_name())

    loop = gobject.MainLoop()
    loop.run()

if __name__ == '__main__':
    main()
