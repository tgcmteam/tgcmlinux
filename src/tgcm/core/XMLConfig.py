#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
#           Roberto Majadas <telemaco@openshine.com>
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

import os
import shutil
import types
import datetime
from xml.etree import ElementTree

import tgcm
import Config
import ConnectionSettingsManager
import Singleton

from tgcm.ui.MSD.MSDUtils import decode_password
from DeviceManager import DEVICE_WLAN, DEVICE_MODEM


class XMLConfig:
    __metaclass__ = Singleton.Singleton

    def __init__ (self):
        self.conf = Config.Config()

        self.connection_settings_manager = ConnectionSettingsManager.ConnectionSettingsManager()
        self.conf_file = os.path.join (tgcm.regional_info_dir, tgcm.country_support, "regional-info.xml")

        self.xml = None

    def import_regional_info (self):
        if os.path.exists(os.path.join(tgcm.config_dir, 'regional-info.%s.xml' % tgcm.country_support)):
            return

        self.conf.set_install_date(datetime.date.today())

        tgcm.debug("IMPORTING %s" % self.conf_file)
        self.xml = ElementTree.parse (self.conf_file)
        root = self.xml.getroot()

        for node in root:
            if node.tag == 'profile-info':
                self.import_profile_info(node)
            elif node.tag == 'user-profile':
                self.import_user_profile(node)
            elif node.tag == 'boem':
                self.import_boem(node)
            elif node.tag == 'client-info':
                self.import_client_info(node)
            elif node.tag == 'coverage':
                self.import_coverage(node)
            elif node.tag == 'device':
                self.import_device(node)
            elif node.tag == 'services':
                self.import_services(node)
            elif node.tag == 'dock':
                self.import_dock(node)
            elif node.tag == 'favorite-list':
                self.import_favorite_list(node)
            elif node.tag == 'policies':
                self.import_policies (node)
            elif node.tag == 'connection-list':
                self.import_connection_list(node)
            elif node.tag == 'news':
                self.import_news (node)
            elif node.tag == 'traffic':
                self.import_traffic (node)
            elif node.tag == 'spec-ssids':
                self.import_spec_ssids (node)
            elif node.tag == 'homezone':
                self.import_homezone (node)
            elif node.tag == 'prepay':
                self.import_prepay (node)
            elif node.tag == 'eapsim':
                self.import_eapsim (node)
            elif node.tag == 'userdata':
                self.import_userdata (node)
            elif node.tag == 'addressbook':
                self.import_addressbook (node)
            elif node.tag == 'sim-locks':
                self.import_sim_locks(node)
            elif node.tag == 'ads':
                self.import_ads(node)

        shutil.copy (self.conf_file, os.path.join(tgcm.config_dir, 'regional-info.%s.xml' % tgcm.country_support))
        self.import_em7_info()

    def import_em7_info(self):
        if tgcm.country_support == "es" :
            if os.path.exists(os.path.join(os.environ["HOME"], ".movistar_desktop", "conf")) :
                import pickle

                old_conf = pickle.load(open(os.path.join(os.environ["HOME"],
                                         ".movistar_desktop",
                                         "conf"), "r"))

                for name in old_conf["connections"] :
                    if name == 'movistar Internet directo' or name == 'movistar Internet' :
                        continue

                    old_dict = old_conf["connections"][name]
                    if old_dict["profile_name"] == None:
                        apn = ''
                    else:
                        apn = old_dict["profile_name"]

                    dns_servers = ['0.0.0.0','0.0.0.0']
                    try:
                        if old_dict["secondary_dns"] != None :
                            dns_servers.insert(0, str(old_dict["secondary_dns"]))

                        if old_dict["primary_dns"] != None :
                            dns_servers.insert(0, str(old_dict["primary_dns"]))
                    except:
                        print "DNS import failed from EM7 profile"

                    dns_servers = dns_servers[:2]

                    if old_dict["proxy_ip"] == None:
                        proxy_ip = ''
                    else:
                        proxy_ip = old_dict["proxy_ip"]

                    password = ''
                    if old_dict["pass"] == None :
                        password = ''
                    else:
                        password = old_dict["pass"]

                    new_conn = {'default': False,
                                'editable': True,
                                'name': name,
                                'profiles': [{'apn': apn,
                                              'ask_password': old_dict["ask_password"] ,
                                              'auto_dns': old_dict["auto_dns"],
                                              'condition': 'default',
                                              'cypher_password': False,
                                              'dns_servers': dns_servers,
                                              'domain_active': False,
                                              'ip_info_active': False,
                                              'ip_info_address': '0.0.0.0',
                                              'password': password,
                                              'proxy': int(old_dict["proxy"]),
                                              'proxy_ip': proxy_ip,
                                              'proxy_port': int(old_dict["proxy_port"]),
                                              'username': old_dict["user"] }]}

                    self.connection_settings_manager.add_wwan_connection(new_conn)


                os.system("rm %s" % os.path.join(os.environ["HOME"], ".movistar_desktop", "conf"))

    def import_profile_info(self, root_node):
        for node in root_node:
            if node.tag == 'region':
                self.conf.set_region(node.text)
            elif node.tag == 'provider':
                self.conf.set_provider(node.text)
            elif node.tag == 'app-name':
                self.conf.set_app_name(node.text)
            elif node.tag == 'app-version':
                self.conf.set_version(node.text)
            elif node.tag == 'comment':
                pass

    def import_user_profile(self, root_node):
        value = root_node.get('name')
        self.conf.set_user_profile_name(value)

    def import_boem(self, root_node):
        value = root_node.get('available')
        self.conf.set_boem_available(value == '1')
        for node in root_node:
            if node.tag == 'url':
                self.conf.set_boem_url(node.text)
            elif node.tag == 'show-warning':
                self.conf.set_boem_show_warning(value == '1')

    def import_client_info (self, root_node):
        if root_node.attrib.has_key('name') and root_node.attrib['name'] != 'default':
            return
        else:
            for node in root_node:
                if node.tag == 'selfcare-url':
                    self.conf.set_selfcare_url (node.text)
                elif node.tag == 'support-url':
                    self.conf.set_support_url (node.text)
                elif node.tag == 'help-phone':
                    self.conf.set_help_phone (node.text)

    def import_coverage (self, root_node):
        for node in root_node:
            if node.tag == 'wifi-url':
                self.conf.set_wifi_url (node.text)
            elif node.tag == 'wwan-url':
                self.conf.set_wwan_url (node.text)

    def import_device(self, root_node):
        # FIXME:
        # The reason behind copying these constant values instead of just import them
        # is to make future (and highly hypothetical) tests easier to perform.

        CARD_DOMAIN_CS = 0
        CARD_DOMAIN_PS = 1
        CARD_DOMAIN_CS_PS = 2
        CARD_DOMAIN_ANY = 4

        CARD_TECH_SELECTION_GPRS = 0
        CARD_TECH_SELECTION_UMTS = 1
        CARD_TECH_SELECTION_GRPS_PREFERED = 2
        CARD_TECH_SELECTION_UMTS_PREFERED = 3
        CARD_TECH_SELECTION_AUTO = 5

        for node in root_node:
            if node.tag == 'domain':
                if node.text == 'cs_ps':
                    domain = CARD_DOMAIN_CS_PS
                elif node.text == 'cs':
                    domain = CARD_DOMAIN_CS
                elif node.text == 'ps':
                    domain = CARD_DOMAIN_PS
                elif node.text == 'any':
                    domain = CARD_DOMAIN_ANY
                self.conf.set_default_device_domain(domain)

            if node.tag == 'mode':
                mode = CARD_TECH_SELECTION_AUTO
                if node.text == 'auto':
                    mode = CARD_TECH_SELECTION_AUTO
                elif node.text == 'gsm':
                    mode = CARD_TECH_SELECTION_GPRS
                elif node.text == 'gsm_first':
                    mode = CARD_TECH_SELECTION_GRPS_PREFERED
                elif node.text == 'wcdma':
                    mode = CARD_TECH_SELECTION_UMTS
                elif node.text == 'wcdma_first':
                    mode = CARD_TECH_SELECTION_UMTS_PREFERED
                self.conf.set_default_device_mode(mode)

    def import_services (self, root_node):
        self.conf.set_original_actions_order([])
        self.conf.set_original_services_order([])
        for node in root_node:
            if node.tag == 'service':
                self.import_service (node)

        self.conf.reset_original_actions_order()

    def import_service (self, root_node):
        if root_node.attrib.has_key('id'):
            if root_node.attrib['id'] == 'internet':
                self.check_service_availability (root_node)
                for node in root_node:
                    if node.tag == 'url':
                        self.conf.set_action_key_value('internet', 'url', node.text)
            elif root_node.attrib['id'] == 'intranet':
                self.check_service_availability (root_node)
            elif root_node.attrib['id'] == 'favorites':
                self.check_service_availability (root_node)
            elif root_node.attrib['id'] == 'wifi':
                self.check_service_availability (root_node)
                for node in root_node:
                    if node.tag == 'ussd':
                        self.conf.set_action_key_value ('wifi', 'ussd', node.text)
            elif root_node.attrib['id'] == 'prepay':
                self.check_service_availability (root_node)
                for node in root_node:
                    if node.tag == 'ussd':
                        if node.attrib.has_key ('name'):
                            if node.attrib['name'] == 'recharge':
                                self.conf.set_action_key_value ('prepay', 'ussd_recharge', node.text)
                            elif node.attrib['name'] == 'check':
                                self.conf.set_action_key_value ('prepay', 'ussd_check', node.text)
            elif root_node.attrib['id'] == 'selfcare':
                self.check_service_availability (root_node)
                for node in root_node :
                    if node.tag == 'url' :
                        self.conf.set_action_key_value ('selfcare', 'selfcare_url', node.text)
                    if node.tag == 'apn-list' :
                        apn_list = []
                        for apnnode in node :
                            if apnnode.tag == 'apn' :
                                apn_list.append(apnnode.text)
                        self.conf.set_action_key_value ('selfcare', 'apn_list', apn_list)
            elif root_node.attrib['id'] == 'sms':
                self.check_service_availability (root_node)
                for node in root_node:
                    if node.tag == 'special-number':
                        self.conf.set_action_key_value('sms', 'special_number', node.text)
                    elif node.tag == 'smsc':
                        if node.attrib.has_key('type'):
                            if node.attrib['type'] == 'any':
                                self.conf.set_action_key_value('sms', 'smsc_any', node.text)
                            elif node.attrib['type'] == 'prepay':
                                self.conf.set_action_key_value('sms', 'smsc_prepay', node.text)
                            elif node.attrib['type'] == 'postpay':
                                self.conf.set_action_key_value('sms', 'smsc_postpay', node.text)
                            elif node.attrib['type'] == 'sim':
                                self.conf.set_action_key_value('sms', 'smsc_sim', node.text)
                        else:
                            self.conf.set_action_key_value('sms', 'smsc_any', node.text)
                    elif node.tag == 'notify-sms':
                        if node.attrib.has_key('available') and node.attrib['available'] == '0':
                            self.conf.set_action_key_value('sms', 'notifications_available', False)
                            self.conf.set_action_key_value('sms', 'notifications_gsm7_method', '')
                            self.conf.set_action_key_value('sms', 'notifications_gsm7_prefix', '')
                            self.conf.set_action_key_value('sms', 'notifications_ucs2_method', '')
                            self.conf.set_action_key_value('sms', 'notifications_ucs2_prefix', '')
                        else:
                            self.conf.set_action_key_value('sms', 'notifications_available', True)
                            if node.attrib.has_key('methodGSM7'):
                                method = node.attrib['methodGSM7']
                                if method.startswith('prefix:'):
                                    prefix = method[7:]
                                    self.conf.set_action_key_value('sms', 'notifications_gsm7_method', 'prefix')
                                    self.conf.set_action_key_value('sms', 'notifications_gsm7_prefix', prefix)
                                elif method == 'status-report':
                                    self.conf.set_action_key_value('sms', 'notifications_gsm7_method', 'status-report')
                                    self.conf.set_action_key_value('sms', 'notifications_gsm7_prefix', '')
                                else:
                                    continue
                            if node.attrib.has_key('methodUCS2'):
                                method = node.attrib['methodUCS2']
                                if method.startswith('prefix:'):
                                    prefix = method[7:]
                                    self.conf.set_action_key_value('sms', 'notifications_ucs2_method', 'prefix')
                                    self.conf.set_action_key_value('sms', 'notifications_ucs2_prefix', prefix)
                                elif method == 'status-report':
                                    self.conf.set_action_key_value('sms', 'notifications_ucs2_method', 'status-report')
                                    self.conf.set_action_key_value('sms', 'notifications_ucs2_prefix', '')
                                else:
                                    continue
                            if not node.attrib.has_key('methodGSM7') and not node.attrib.has_key('methodUCS2'):
                                self.conf.set_action_key_value('sms', 'notifications_available', False)
                                self.conf.set_action_key_value('sms', 'notifications_gsm7_method', '')
                                self.conf.set_action_key_value('sms', 'notifications_gsm7_prefix', '')
                                self.conf.set_action_key_value('sms', 'notifications_ucs2_method', '')
                                self.conf.set_action_key_value('sms', 'notifications_ucs2_prefix', '')
                    elif node.tag == 'pop-up-sms':
                        if node.attrib.has_key('available') and node.attrib['available'] == '1':
                            self.conf.set_action_key_value('sms', 'popup_sms_available', True)
                            numbers = []
                            for number_node in node:
                                if number_node.tag == 'number':
                                    numbers.append (number_node.text)
                            self.conf.set_action_key_value('sms', 'popup_sms_numbers', numbers)
                        else:
                            self.conf.set_action_key_value('sms', 'popup_sms_available', False)
                    elif node.tag == 'policy':
                        if node.attrib.has_key('name') and node.attrib['name'] == 'edit-smsc':
                            if node.attrib.has_key('value') and node.attrib['value'] == '1':
                                self.conf.set_action_key_value('sms', 'editable_smsc', True)
                            else:
                                self.conf.set_action_key_value('sms', 'editable_smsc', False)
                        else:
                            self.conf.set_action_key_value('sms', 'editable_smsc', False)
            elif root_node.attrib.has_key('class') and root_node.attrib['class'] == 'url-launcher':
                self.import_url_launcher (root_node)

    def check_service_availability (self, root_node):
        service_id = root_node.attrib['id']
        actions_list = self.conf.get_original_actions_order()
        services_list = self.conf.get_original_services_order()

        if root_node.attrib.has_key ('install-status'):
            status = int(root_node.attrib['install-status'])
            if status == 0:
                pass
            else:
                if status == 1:
                    self.conf.set_action_uninstalled(service_id)
                elif status == 2:
                    self.conf.set_action_installed(service_id)
                actions_list.append(service_id)
                services_list.append("service,%s" % service_id)
                self.conf.set_original_actions_order(actions_list)
                self.conf.set_original_services_order(services_list)

    def import_url_launcher (self, root_node):
        id = root_node.attrib['id']
        services_list = self.conf.get_original_services_order()
        services_list.append("url-launcher,%s" % id)
        self.conf.set_original_services_order(services_list)
        if root_node.attrib.has_key('install-status'):
            install_status = int(root_node.attrib['install-status'])
        else:
            pass

        if install_status == 1:
            install_status = False
        elif install_status == 2:
            install_status = True
        else:
            pass

        url = ""
        caption = ""

        for node in root_node:
            if node.tag == 'url':
                url = node.text.strip()
            elif node.tag == 'caption':
                caption = node.text.strip()

        if len(url) > 0 and len (caption) > 0:
            self.conf.add_url_launcher (id, url, caption, install_status)

    def import_dock (self, root_node):
        for node in root_node:
            if node.tag == 'appearance':
                self.conf.set_dock_appearance(int(node.text))
            elif node.tag == 'status':
                self.conf.set_dock_status(int(node.text))
            elif node.tag == 'dockables':
                self.import_dockables(node)
            elif node.tag == 'launcher':
                self.import_launcher(node)

    def import_dockables (self, root_node):
        dockables = []
        for node in root_node:
            if node.tag == 'dockable':
                if node.attrib.has_key ('id'):
                    dockables.append (node.attrib['id'])
                    self.import_dockable_urls(node.attrib['id'], node)
        self.conf.set_dockables_list (dockables)

    def import_dockable_urls(self, name, root_node):
        for node in root_node:
            self.conf.set_dockable_url(name, node.tag, node.text)

    def import_launcher (self, root_node):
        if root_node.attrib.has_key('size'):
            self.conf.set_dock_size (root_node.attrib['size'])

        launcher_items_order = []
        for node in root_node:
            if node.tag == 'item':
                if node.attrib.has_key('id'):
                    service_id = node.attrib['id']
                    launcher_items_order.append (service_id)
        self.conf.set_launcher_items_order (launcher_items_order)

    def import_favorite_list (self, root_node):
        if root_node.attrib.has_key('name') and root_node.attrib['name'] != 'default':
            return
        else:
            for node in root_node:
                self.import_favorite (node)

    def get_favorite_info (self, node):
        favorite = {}

        if node.tag == 'favorite':
            if node.attrib.has_key('readonly'):
                favorite['readonly'] = node.attrib['readonly']
            else:
                favorite['readonly'] = "0"

            if node.attrib.has_key('userdata'):
                favorite['userdata'] = node.attrib['userdata']
            else:
                favorite['userdata'] = "0"

            #favorite['name'] = node.find('name').text.replace('/', '\\')
            favorite['name'] = node.find('name').text
            type = int(node.find('type').text)
            if type == 0:
                favorite['url'] = node.find('url').text
            else:
                favorite['url'] = node.find('file').text

            favorite['connection_name'] = ""
            if node.find('use-connection') is not None:
                use_connection = int(node.find('use-connection').text)
                if use_connection == 1:
                    favorite['connection_name'] = node.find('connection-name').text

            return favorite

    def import_favorite (self, node, overwrite=False, force_readonly=False):
        favorite = self.get_favorite_info(node)

        if force_readonly == True:
            readonly = True
        else:
            readonly = favorite['readonly'] == '1'

        self.conf.add_bookmark(favorite['name'], \
                favorite['url'], \
                favorite['connection_name'], \
                int(favorite['userdata']), \
                readonly, \
                overwrite)

    def import_policies (self, root_node):
        for node in root_node:
            if node.tag == 'policy' and node.attrib.has_key('name'):
                name = node.attrib['name']
                if node.attrib.has_key('value'):
                    if node.attrib['value'] == '1':
                        value = True
                    else:
                        value = False
                else:
                    value = True

                self.conf.add_policy (name, value)

                if name == 'connect-startup':
                    self.conf.set_connect_on_startup (value)

                if name == 'reconnect':
                    self.conf.set_reconnect_on_disconnect (value)

    def import_connection_list (self, root_node):
        default_connection = True
        conn_list = []
        for node in root_node:
            if node.tag == 'wwan-connection':
                conn_uuid = self.import_wwan_connection(node, default_connection)
                conn_list.insert(0,(conn_uuid, DEVICE_MODEM))
                default_connection = False
            elif node.tag == 'wifi-connection':
                conn_uuid = self.import_wifi_connection(node)
                conn_list.insert(0,(conn_uuid, DEVICE_WLAN))
            elif node.tag == 'wwan-prototype':
                self.import_wwan_connection(node, default=False, wwan_prototype=True)
#            elif node.tag == 'wifi-prototype':
#                pass

        for conn_tuple in conn_list:
            conn_name=conn_tuple[0]
            conn_type=conn_tuple[1]
            self.connection_settings_manager.set_first_in_list_device_type(conn_name,conn_type)

    def import_wwan_connection (self, root_node, default=False, wwan_prototype=False, overwrite=False, force_readonly=False):
        conn = self.get_wwan_connection_info(root_node, default, wwan_prototype, force_readonly)

        if wwan_prototype == False :
            #self.conf.add_regional_info_wwan_connection (conn)
            conn_data = self.connection_settings_manager.add_wwan_connection(conn, must_write_gconf=True, update_if_possible=True)
            conn_uuid = conn_data['uuid']
        else:
            #self.conf.add_regional_info_wwan_connection (conn,wwan_prototype=True)
            self.connection_settings_manager.add_regional_info_wwan_connection(conn, wwan_prototype=True)
            conn_uuid = None

        return conn_uuid

    def get_wwan_connection_info (self, root_node, default=False, wwan_prototype=False, force_readonly=False):
        conn = {}

        if wwan_prototype == True :
            conn['name'] = ""
        else:
            conn['name'] = root_node.find('name').text.strip()

        conn['deviceType'] = DEVICE_MODEM
        conn['default'] = default
        conn['origin']='xml'
        if force_readonly:
            conn['editable'] = False
        else:
            if root_node.attrib.has_key('readonly'):
                if root_node.attrib['readonly'] == '0':
                    conn['editable'] = True
                else:
                    conn['editable'] = False
            else:
                conn['editable'] = True

        conn['profiles'] = []
        profile_nodes = root_node.findall('profile')
        for profile_node in profile_nodes:
            profile = {}
            if profile_node.attrib.has_key('condition'):
                profile['condition'] = profile_node.attrib['condition']
            else:
                profile['condition'] = False

            try:
                profile['username'] = profile_node.find('auth-info/username').text.strip()
                if profile['username'] == None:
                    profile['username'] = ''
            except:
                profile['username'] = ''

            try:
                coded_password = profile_node.find('auth-info/password').text.strip()
                if coded_password is None:
                    profile['password'] = ''
                else:
                    profile['password'] = decode_password(coded_password)
            except:
                profile['password'] = ''

            profile['ask_password'] = int(profile_node.find('auth-info/ask-password').text) == 1
            profile['cypher_password'] = int(profile_node.find('auth-info/cypher-password').text) == 1

            profile['auto_dns'] = int(profile_node.find('dns-info/manual-dns-server').text) == 0
            dns_servers = []
            nodes = profile_node.findall('dns-info/dns-server-list/dns-server')
            for node in nodes:
                node_str=node.text;
                if (node_str!=None):
                    dns_servers = dns_servers + [node.text.strip()]


            profile['dns_servers'] = dns_servers

            profile['domain_active'] = int(profile_node.find('dns-info/dns-suffixes/active').text) == 1
            if profile['domain_active']:
                try:
                    profile['domains'] = [suffix.strip() for suffix in profile_node.find('dns-info/dns-suffixes/suffixes').text.split(';')]
                except:
                    profile['domains'] = []

            proxy_tag=profile_node.find('proxy-info/configuration')
            if proxy_tag!=None:
                proxyVal=profile_node.find('proxy-info/configuration').text.strip()
                try:
                    profile['proxy'] = int(proxyVal)
                except ValueError:
                    profile['proxy'] = 0;

                profile['proxy_ip'] = ""
                profile['proxy_port'] = 0
                profile['proxy_https_ip'] = ""
                profile['proxy_https_port'] = 0
                profile['proxy_socks_ip'] = ""
                profile['proxy_socks_port'] = 0
                profile['proxy_ftp_ip'] = ""
                profile['proxy_ftp_port'] = 0
                profile['proxy_same_proxy'] = False
                profile['proxy_ignore'] = []

                if profile['proxy']:
                    proxies = profile_node.findall('proxy-info/proxy-list/proxy')
                    for proxy in proxies:
                        if proxy.attrib.has_key('type') and proxy.attrib['type'] == 'any':
                            proxy_data = [substring.strip() for substring in proxy.text.split(':')]
                            profile['proxy_ip'] = proxy_data[0]
                            profile['proxy_port'] = int(proxy_data[1])
                            profile['proxy_same_proxy'] = True
                            break
                        if proxy.attrib.has_key('type') and proxy.attrib['type'] == 'http':
                            proxy_data = [substring.strip() for substring in proxy.text.split(':')]
                            profile['proxy_ip'] = proxy_data[0]
                            profile['proxy_port'] = int(proxy_data[1])
                            profile['proxy_same_proxy'] = False
                        if proxy.attrib.has_key('type') and proxy.attrib['type'] == 'https':
                            proxy_data = [substring.strip() for substring in proxy.text.split(':')]
                            profile['proxy_https_ip'] = proxy_data[0]
                            profile['proxy_https_port'] = int(proxy_data[1])
                            profile['proxy_same_proxy'] = False
                        if proxy.attrib.has_key('type') and proxy.attrib['type'] == 'socks':
                            proxy_data = [substring.strip() for substring in proxy.text.split(':')]
                            profile['proxy_socks_ip'] = proxy_data[0]
                            profile['proxy_socks_port'] = int(proxy_data[1])
                            profile['proxy_same_proxy'] = False
                        if proxy.attrib.has_key('type') and proxy.attrib['type'] == 'ftp':
                            proxy_data = [substring.strip() for substring in proxy.text.split(':')]
                            profile['proxy_ftp_ip'] = proxy_data[0]
                            profile['proxy_ftp_port'] = int(proxy_data[1])
                            profile['proxy_same_proxy'] = False

                    bypass_proxies = profile_node.findall('proxy-info/bypass-proxy/bypass-addresses')
                    if bypass_proxies != None and len(bypass_proxies)>0:
                        if (bypass_proxies[0].text!=None):
                            profile['proxy_ignore']=bypass_proxies[0].text.rsplit(';')

            else:
                profile['proxy'] = 0

            try:
                profile['apn'] = profile_node.find('apn').text.strip()
                if profile['apn'] == None :
                    profile['apn'] = ''
            except:
                profile['apn'] = ''

            profile['ip_info_active'] = int(profile_node.find('ip-info/active').text) == 1
            ip_info_address=profile_node.find('ip-info/address').text
            if (ip_info_address!=None):
                profile['ip_info_address'] = ip_info_address.strip()
            else:
                profile['ip_info_address']=''

            conn['profiles'] = conn['profiles'] + [profile]

        return conn

    def import_wifi_connection(self, root_node, default=False, prototype=False, overwrite=False, force_readonly=False):
        conn = self.get_wifi_connection_info(root_node, default, prototype, force_readonly)

        if prototype == False:
            conn_data = self.connection_settings_manager.add_wifi_connection(conn, must_write_gconf=True, update_if_possible=True)
            conn_uuid = str(conn_data['uuid'])

        return conn_uuid

    def get_wifi_connection_info(self, root_node, default=False, prototype=False, force_readonly=False):
        conn = {}

        if prototype:
            conn['name'] = ''
        else:
            conn['name'] = root_node.find('name').text.strip()

        conn['deviceType'] = DEVICE_WLAN
        conn['default'] = default
        conn['origin'] = 'xml'

        conn['editable'] = True
        if force_readonly:
            conn['editable'] = False
        elif root_node.attrib.has_key('readonly'):
            conn['editable'] = root_node.attrib['readonly'] == '0'

        conn['profiles'] = []
        profile_nodes = root_node.findall('profile')
        for profile_node in profile_nodes:
            profile = {}
            if profile_node.attrib.has_key('condition'):
                profile['condition'] = profile_node.attrib['condition']
            else:
                profile['condition'] = False

            # Unused, but just for the record
            #
            # AUT802_1X{
            #   AUT802_1X_NINGUNA = 0,
            #   AUT802_1X_EAP_MD5 = 4,
            #   AUT802_1X_EAP_SIM = 18,
            #   AUT802_1X_EAP_PEAP = 25,
            #   AUT802_1X_EAP_MSCHAPV2 = 26,
            #   AUT802_1X_EAP_WISPR = 100,
            #   AUT802_1X_EAP_THE_CLOUD = 105,
            #   AUT802_1X_EAP_LANDING_PAGE = 1000,
            # };
            fields = (('', 'ssid', ''), \
                ('', 'mac', '0.0.0.0.0.0'), \
                ('', 'encryption', 0), \
                ('', 'authentication', 0), \
                ('', 'network-password', ''), \
                ('', 'hidden', False), \
                ('auth-802-1x', 'type', '0'), \
                ('auth-802-1x', 'user', ''), \
                ('auth-802-1x', 'password', ''))
            profile = self.__import_block(profile_node, fields)
            profile['password'] = decode_password(profile['network-password'])
            conn['profiles'].append(profile)

            return conn

    def __import_block(self, root_node, fields):
        block = {}
        for root, name, default_value in fields:
            if len(root) == 0:
                keypath = name
            else:
                keypath = '%s/%s' % (root, name)
            if root_node.find(keypath) is not None and root_node.find(keypath).text is not None:
                value = root_node.find(keypath).text.strip()
                if type(default_value) is types.BooleanType:
                    value = value == '1'
                block[name] = value
            else:
                block[name] = default_value
        return block

    def import_news (self, root_node):
        if root_node.attrib['available'] == '0':
            self.conf.set_updater_feed_url("")
            self.conf.set_news_available(False)
            return
        else:
            self.conf.set_news_available(True)

        for node in root_node:
            if node.tag == 'url' and node.attrib.has_key('os') and node.attrib['os'] == 'linux':
                self.conf.set_updater_feed_url(node.text)
                return

        self.conf.set_updater_feed_url("")

    def import_traffic (self, root_node):
        value = root_node.get('available')
        self.conf.set_traffic_available((value is None) or (value == '1'))
        value = root_node.get('alerts-available')
        self.conf.set_alerts_available((value is None) or (value == '1'))
        for node in root_node:
            if node.tag == 'billing-day':
                self.conf.set_default_billing_day(int(node.text))
                if node.attrib.has_key('type') and node.attrib['type'] == 'custom':
                    self.conf.set_is_default_fixed_billing_day(False)
                else:
                    self.conf.set_is_default_fixed_billing_day(True)
            elif node.tag == 'monthly-limits' :
                self.import_monthly_limits(node, False)
            elif node.tag == 'monthly-roaming-limits' :
                self.import_monthly_limits(node, True)
            elif node.tag == 'alert-list' :
                self.import_alert_list(node, False)
            elif node.tag == 'alert-roaming-list' :
                self.import_alert_list(node, True)

    def import_monthly_limits(self, root_node, is_roaming):
        limits = []
        default_limit = None
        for node in root_node:
            if node.tag == 'limit' :
                limit = int(node.text)
                limits.append(limit)
                if node.attrib.has_key('default') and (node.attrib['default'] == '1'):
                    default_limit = limit

        self.conf.set_monthly_limits(limits, is_roaming)
        if default_limit is not None:
            self.conf.set_default_selected_monthly_limit(default_limit, is_roaming)

    def import_alert_list(self, root_node, is_roaming):
        alerts = []
        enabled_alerts = []
        for node in root_node:
            if node.tag == 'alert' :
                alert = int(node.text)
                alerts.append(alert)
                if node.attrib.has_key('active') and (node.attrib["active"] == '1'):
                    enabled_alerts.append(alert)

        self.conf.set_alerts(alerts, is_roaming)
        for alert in alerts:
            enabled = alert in enabled_alerts
            self.conf.enable_default_alert(alert, enabled, is_roaming)

    def import_spec_ssids (self, root_node):
        pass

    def import_homezone (self, root_node):
        pass

    def import_prepay (self, root_node):
        if root_node.attrib.has_key('method'):
            self.conf.set_prepay_method(root_node.attrib['method'])
        if root_node.attrib.has_key('default'):
            value = root_node.attrib['default'] == 1
            self.conf.set_is_default_prepaid(value)
#        if root_node.attrib.has_key('disable-traffic'):
#            value = root_node.attrib['disable-traffic'] == 1
#            self.conf.set_traffic_available(value)

    def import_eapsim (self, root_node):
        pass

    def import_userdata (self, root_node):
        if root_node.attrib.has_key ('available') :
            if root_node.attrib['available'] == "0" :
                self.conf.set_userdata_available(False)
            else:
                self.conf.set_userdata_available(True)

    def import_addressbook (self, root_node):
        for node in root_node:
            if node.tag == 'phone-number':
                for ca_node in node:
                    if ca_node.tag == 'country-code':
                        self.conf.set_country_code (ca_node.text)
                    elif ca_node.tag == 'match':
                        self.conf.set_phone_match (ca_node.text)
                    elif ca_node.tag == 'format':
                        format_list = ca_node.text.split('$')
                        while True:
                            if '' in format_list:
                                format_list.remove ('')
                            else:
                                break
                        format_list = [int(aux) for aux in format_list]

                        self.conf.set_phone_format (format_list)

    def import_sim_locks(self, root_node):
        sim_locks = []
        for node in root_node:
            if node.tag == 'sim-lock':
                sim_locks.append(node.text)
        if len(sim_locks) > 0 :
            self.conf.set_sim_locks(sim_locks)

    def import_ads(self, root_node):
        ads_available = False
        if root_node.attrib.has_key('available'):
            ads_available = root_node.attrib['available'] == '1'
            self.conf.set_ads_available(ads_available)

        if not ads_available:
            return

        for node in root_node:
            if node.tag == 'url':
                url_id = node.attrib['id']
                url = node.text
                self.conf.add_ads_url(url_id, url)

            elif node.tag == 'auth-sdp':
                self.import_auth_sdp(node)

    def import_auth_sdp(self, root_node):
        if root_node.attrib.has_key('available'):
            is_available = root_node.attrib['available'] == '1'
            self.conf.set_ads_auth_sdp_available(is_available)

        for node in root_node:
            if node.tag == 'service-id':
                self.conf.set_ads_service_id(node.text)
            elif node.tag == 'sp-id':
                self.conf.set_ads_sp_id(node.text)
            elif node.tag == 'sp-password':
                self.conf.set_ads_sp_password(node.text)
