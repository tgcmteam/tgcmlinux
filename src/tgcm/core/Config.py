#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
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
import glib
import gobject
import functools
import md5
import calendar
import datetime
import random
import string
import time
import gconf

from types import IntType, BooleanType

import tgcm
import Connections
import Constants
import Singleton
import GSettings

### Decorators ###

def imsi_required(func):
    '''
    A really small decorator to check that the first parameter of a function is not None or
    a zero-length string.
    '''
    def decor(*args, **kwargs):
        imsi = args[1]
        if (imsi is None) or (len(imsi) == 0):
            raise AttributeError('A valid IMSI is required!')
        return func(*args, **kwargs)
    return decor


class delayed_call(object):
    '''
    A decorator used to delaying calls to save functions.

    E.g., imagine a function which is continuously called in a small amount of time
    to save a value, which is rarely read. The save process is quite expensive and it
    is only necessary to save the value from time to time. This decorator would be
    useful because it stores the last call value, and it will only call the original
    function one time per timeout
    '''

    def __init__(self, func, timeout = 1):
        self._func = func
        self._timeout = timeout

        self._cache = None
        self._call_id = None

    def __call__(self, *args):
        self._cache = args

        if self._call_id is None:
            self._call_id = glib.timeout_add_seconds(self._timeout, self.__do_call)

    def __do_call(self):
        self._func(*self._cache)
        self._call_id = None

    def __repr__(self):
        ''' Return the function's docstring '''
        return self._func.__doc__

    def __get__(self, obj, objtype):
        ''' Support instance methods '''
        return functools.partial(self.__call__, obj)


class Config(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'launcher-items-order-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'bookmark-added' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'bookmark-deleted' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'bookmark-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'connection-added' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'connection-deleted' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'connection-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'connection-log-enable-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
        'service-conf-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'hide-uninstalled-services-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'services-order-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'billing-day-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'monthly-limit-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'alerts-info-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'sms-counter-reset' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'sms-counter-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'ui-general-key-value-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'user-prepay-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
        'user-mobile-broadband-number-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'last-imsi-seen-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'fixed-billing-day-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
    }

    def __init__(self, country):
        gobject.GObject.__init__(self)
        self.gconf_path = "%s/%s" % (tgcm.gconf_path, country)

        self.client = gconf.client_get_default()
        #self.client.add_dir(self.gconf_path, gconf.CLIENT_PRELOAD_RECURSIVE)

        self.__update_from_8_to_9()
        self.__check_init_values()


    def __sync_config(self):
        self.client.suggest_sync()
        while gtk.events_pending():
            gtk.main_iteration()

    def get_install_date(self):
        value = self.client.get_string('%s/install_date' % self.gconf_path)
        install_date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        return install_date

    def set_install_date(self, install_date):
        value = install_date.isoformat()
        self.client.set_string('%s/install_date' % self.gconf_path, value)
        self.__sync_config()

    def get_last_execution_datetime(self):
        last_exec_key = '%s/last_execution_datetime' % self.gconf_path
        install_date = self.get_install_date()
        last_exec_datetime = self.__get_datetime(last_exec_key, install_date)
        return last_exec_datetime

    def update_last_execution_datetime(self):
        last_exec_key = '%s/last_execution_datetime' % self.gconf_path
        now_datetime = datetime.datetime.now()
        self.__save_datetime(last_exec_key, now_datetime)

    @imsi_required
    def get_last_reset_datetime(self, imsi):
        last_reset_key = '%s/imsi/%s/last_reset_datetime' % (self.gconf_path, imsi)
        install_date = self.get_install_date()
        last_reset_datetime = self.__get_datetime(last_reset_key, install_date)
        return last_reset_datetime

    @imsi_required
    def update_last_reset_datetime(self, imsi):
        last_reset_key = '%s/imsi/%s/last_reset_datetime' % (self.gconf_path, imsi)
        now_datetime = datetime.datetime.now()
        self.__save_datetime(last_reset_key, now_datetime)

    def __get_datetime(self, key, default_value):
        value = self.client.get_without_default(key)
        if value is None:
            value_str = default_value.strftime('%Y-%m-%d %H:%M:%S')
            self.client.set_string(key, value_str)
            self.__sync_config()
        else:
            value_str = value.get_string()

        value_date = datetime.datetime.strptime(value_str, '%Y-%m-%d %H:%M:%S')
        return value_date

    def __save_datetime(self, key, value):
        value_str = value.strftime('%Y-%m-%d %H:%M:%S')
        self.client.set_string(key, value_str)
        self.__sync_config()

    # Section "profile-info"

    # Region
    def get_region(self):
        return self.client.get_string ("%s/region" % self.gconf_path).strip()

    def set_region (self, value):
        if value is not None:
            self.client.set_string ("%s/region" % self.gconf_path, value)
            self.__sync_config ()

    # Provider
    def get_provider(self):
        return self.client.get_string('%s/provider' % self.gconf_path).strip()

    def set_provider(self, value):
        if value is not None:
            self.client.set_string('%s/provider' % self.gconf_path, value)
            self.__sync_config ()

    # App name
    def get_app_name (self):
        app_name = "%s" % self.client.get_string ("%s/app_name" % self.gconf_path).strip()
        if self.is_latam() is True:
            # -- @XXX: Quick and dirty
            return app_name.replace(' Latam', '')
        else:
            return app_name
        #return self.client.get_string ("%s/app_name" % self.gconf_path).strip()

    def set_app_name (self, value):
        if value is not None:
            self.client.set_string ("%s/app_name" % self.gconf_path, value)
            self.__sync_config ()

    # Version
    def get_version(self):
        return self.client.get_string ("%s/version" % self.gconf_path).strip()

    def set_version (self, value):
        if value is not None:
            self.client.set_string ("%s/version" % self.gconf_path, value)
            self.__sync_config ()


    # Section "user-profile"

    # Name
    def get_user_profile_name(self):
        return self.client.get_string('%s/user_profile_name' % self.gconf_path).strip()

    def set_user_profile_name(self, value):
        if value is not None:
            self.client.set_string('%s/user_profile_name' % self.gconf_path, value)
            self.__sync_config ()


    # Section "boem"

    # boem available
    def is_boem_available(self):
        return self.client.get_bool('%s/boem_available' % self.gconf_path)

    def set_boem_available(self, value):
        if value is not None:
            self.client.set_bool('%s/boem_available' % self.gconf_path, value)
            self.__sync_config ()

    # url
    def get_boem_url(self):
        return self.client.get_string('%s/boem_url' % self.gconf_path)

    def set_boem_url(self, value):
        if value is not None:
            self.client.set_string('%s/boem_url' % self.gconf_path, value)
            self.__sync_config ()

    # show warning
    def is_boem_show_warning(self):
        return self.client.get_bool('%s/boem_show_warning' % self.gconf_path)

    def set_boem_show_warning(self, value):
        if value is not None:
            self.client.set_bool('%s/boem_show_warning' % self.gconf_path, value)
            self.__sync_config ()


    # Section "client-info"

    # Selfcare URL
    def get_selfcare_url (self):
        return self.client.get_string ("%s/selfcare_url" % self.gconf_path).strip()

    def set_selfcare_url (self, value):
        if value is not None:
            self.client.set_string ("%s/selfcare_url" % self.gconf_path, value)
            self.__sync_config ()

    # Support URL
    def get_support_url (self):
        return self.client.get_string ("%s/support_url" % self.gconf_path).strip()

    def set_support_url (self, value):
        if value is not None:
            self.client.set_string ("%s/support_url" % self.gconf_path, value)
            self.__sync_config ()

    # Help phone
    def get_help_phone(self):
        return self.client.get_string ("%s/help_phone" % self.gconf_path).strip()

    def set_help_phone(self, value):
        if value is not None:
            self.client.set_string ("%s/help_phone" % self.gconf_path, value)
            self.__sync_config ()


    # Section "coverage"

    # wifi-url
    def get_wifi_url (self):
        return self.client.get_string ("%s/wifi_url" % self.gconf_path).strip()

    def set_wifi_url (self, value):
        if value is not None:
            self.client.set_string ("%s/wifi_url" % self.gconf_path, value)
            self.__sync_config ()

    # wwan-url
    def get_wwan_url(self):
        return self.client.get_string ("%s/wwan_url" % self.gconf_path).strip()

    def set_wwan_url(self, value):
        if value is not None:
            self.client.set_string ("%s/wwan_url" % self.gconf_path, value)
            self.__sync_config ()


    # Section "device"

    # Device mode
    def get_default_device_mode(self):
        return self.client.get_int("%s/devices/default_device_mode" % self.gconf_path)

    def set_default_device_mode(self, mode):
        self.client.set_int("%s/devices/default_device_mode" % self.gconf_path, mode)
        self.__sync_config()

    def get_last_device_mode(self):
        device_mode_key = "%s/devices/current_device_mode" % self.gconf_path

        device_mode_value = self.client.get_without_default(device_mode_key)
        if device_mode_value is None:
            value = self.get_default_device_mode()
            self.client.set_int(device_mode_key, value)
            self.__sync_config()

        return self.client.get_int(device_mode_key)

    def set_last_device_mode(self, mode):
        self.client.set_int("%s/devices/current_device_mode" % self.gconf_path, mode)
        self.__sync_config()

    # Device domain
    def get_default_device_domain(self):
        return self.client.get_int("%s/devices/default_device_domain" % self.gconf_path)

    def set_default_device_domain(self, domain):
        self.client.set_int("%s/devices/default_device_domain" % self.gconf_path, domain)
        self.__sync_config()

    def get_last_domain(self):
        device_domain_key = "%s/devices/current_device_domain" % self.gconf_path

        device_domain_value = self.client.get_without_default(device_domain_key)
        if device_domain_value is None:
            value = self.get_default_device_domain()
            self.client.set_int(device_domain_key, value)
            self.__sync_config()

        return self.client.get_int(device_domain_key)

    def set_last_device_domain(self, domain):
        self.client.set_int("%s/devices/current_device_domain" % self.gconf_path, domain)
        self.__sync_config()

    # Section "sim-locks"

    # sim-locks
    def get_sim_locks (self):
        ret = self.client.get_list ("%s/sim_locks" % self.gconf_path, gconf.VALUE_STRING)
        return ret

    def set_sim_locks (self,  value):
        self.client.set_list ("%s/sim_locks" % self.gconf_path, gconf.VALUE_STRING, value)
        self.__sync_config ()


    # Section "services"

    def get_actions_order(self):
        return self.client.get_list ("%s/actions_general/actions_order" % self.gconf_path, gconf.VALUE_STRING)

    def set_actions_order (self, actions):
        self.client.set_list ("%s/actions_general/actions_order" % self.gconf_path, gconf.VALUE_STRING, actions)
        self.__sync_config()

    def get_original_actions_order(self):
        return self.client.get_list ("%s/actions_general/original_actions_order" % self.gconf_path, gconf.VALUE_STRING)

    def set_original_actions_order (self, actions):
        self.client.set_list ("%s/actions_general/original_actions_order" % self.gconf_path, gconf.VALUE_STRING, actions)
        self.__sync_config()

    def reset_original_actions_order(self):
        original_list = self.client.get_list ("%s/actions_general/original_actions_order" % self.gconf_path, gconf.VALUE_STRING)
        self.client.set_list ("%s/actions_general/actions_order" % self.gconf_path, gconf.VALUE_STRING, original_list)
        self.__sync_config()

    def get_original_services_order(self):
        return self.client.get_list ("%s/actions_general/original_services_order" % self.gconf_path, gconf.VALUE_STRING)

    def set_original_services_order (self, actions):
        self.client.set_list ("%s/actions_general/original_services_order" % self.gconf_path, gconf.VALUE_STRING, actions)
        self.__sync_config()

    def exists_action_conf (self, codename):
        for action in self.client.all_dirs ("%s/actions" % self.gconf_path):
            if action == "%s/%s" % (self.gconf_path, codename):
                return True
        return False

    def set_action_key_value (self, codename, key, value):
        for action in self.client.all_dirs ("%s/actions" % self.gconf_path):
            if action == "%s/actions/%s" % (self.gconf_path, codename):
                entry_path = "%s/%s" % (action, key)
                entry = self.client.get_entry (entry_path, None, True)
                gvalue = entry.get_value()
                if gvalue == None:
                    return
                elif gvalue.type == gconf.VALUE_STRING:
                    if value is not None:
                        self.client.set_string (entry_path, value)
                    else:
                        self.client.set_string (entry_path, "")
                elif gvalue.type == gconf.VALUE_BOOL:
                    self.client.set_bool (entry_path, value)
                elif gvalue.type == gconf.VALUE_INT:
                    self.client.set_int (entry_path, value)
                elif gvalue.type == gconf.VALUE_LIST:
                    self.client.set_list (entry_path, gconf.VALUE_STRING, value)

                self.__sync_config()
                return

    def get_action_key_value (self, codename, key):
        for action in self.client.all_dirs ("%s/actions" % self.gconf_path):
            if action == "%s/actions/%s" % (self.gconf_path, codename):
                entry_path = "%s/%s" % (action, key)
                entry = self.client.get_entry (entry_path, None, True)
                if entry == None:
                    return None

                gvalue = entry.get_value()
                if gvalue == None:
                    return None
                elif gvalue.type == gconf.VALUE_STRING:
                    return gvalue.get_string()
                elif gvalue.type == gconf.VALUE_BOOL:
                    return gvalue.get_bool()
                elif gvalue.type == gconf.VALUE_INT:
                    return gvalue.get_int()
                elif gvalue.type == gconf.VALUE_LIST:
                    gconf_list = gvalue.get_list (gconf.VALUE_STRING)
                    list = []
                    for element in gconf_list:
                        if element.type == gconf.VALUE_STRING:
                            list.append (element.get_string())
                        elif element.type == gconf.VALUE_BOOL:
                            list.append (element.get_bool())
                        elif element.type == gconf.VALUE_INT:
                            list.append (element.get_int())
                    return list

        return None

    def set_action_installed(self, codename) :
        for action in self.client.all_dirs ("%s/actions" % self.gconf_path):
            if action == "%s/actions/%s" % (self.gconf_path, codename):
                entry_path = "%s/%s" % (action, "installed")
                self.client.set_bool (entry_path, True)
                self.__sync_config()

                launcher_items = self.get_launcher_items_order ()
                launcher_items.append (codename)
                self.set_launcher_items_order (launcher_items)
                self.__sync_config()
                return

    def is_action_installed (self, codename):
        for action in self.client.all_dirs ("%s/actions" % self.gconf_path):
            if action == "%s/actions/%s" % (self.gconf_path, codename):
                entry_path = "%s/%s" % (action, "installed")
                return self.client.get_bool (entry_path)

    def set_action_uninstalled(self, codename) :
        for action in self.client.all_dirs ("%s/actions" % self.gconf_path):
            if action == "%s/actions/%s" % (self.gconf_path, codename):
                entry_path = "%s/%s" % (action, "installed")
                self.client.set_bool (entry_path, False)

                launcher_items = self.get_launcher_items_order ()
                if codename in launcher_items:
                    launcher_items.remove (codename)
                    self.set_launcher_items_order (launcher_items)
                self.__sync_config()
                return

    def get_wifi_service_name(self):
        key = '%s/%s' % (self.gconf_path, 'actions/wifi/name')
        return self.client.get_string(key)

    # Section "dock"

    def get_dock_appearance (self):
        return self.client.get_int ("%s/dock/appearance" % self.gconf_path)

    def set_dock_appearance (self, value):
        self.client.set_int ("%s/dock/appearance" % self.gconf_path, int(value))
        self.__sync_config()

    def get_dock_status (self):
        return self.client.get_int ("%s/dock/status" % self.gconf_path)

    def set_dock_status (self, value):
        self.client.set_int ("%s/dock/status" % self.gconf_path, int(value))
        self.__sync_config()

    def get_dock_size (self):
        return self.client.get_int ("%s/dock/size" % self.gconf_path)

    def set_dock_size (self, dock_size):
        self.client.set_int ("%s/dock/size" % self.gconf_path, int(dock_size))
        self.__sync_config()

    def get_dock_width(self):
        return self.client.get_int('%s/dock/width' % self.gconf_path)

    @delayed_call
    def set_dock_width(self, value):
        self.client.set_int('%s/dock/width' % self.gconf_path, value)
        self.__sync_config()

    def get_dockables_list (self):
        return self.client.get_list ("%s/dock/dockables" % self.gconf_path, gconf.VALUE_STRING)

    def set_dockables_list (self, dockables):
        self.client.set_list ("%s/dock/dockables" % self.gconf_path, gconf.VALUE_STRING, dockables)
        self.__sync_config()

    def get_dockable_url(self, name, key):
        return self.client.get_string('%s/dockables/%s/%s' % (self.gconf_path, name, key))

    def set_dockable_url(self, name, key, url):
        self.client.set_string('%s/dockables/%s/%s' % (self.gconf_path, name, key), url)
        self.__sync_config()

    def set_launcher_items_order (self, launcher_items_order):
        launcher_items = []
        for item in launcher_items_order:
            if item in tgcm.dockables_info:
                launcher_items.append(item)
            elif item in self.get_url_launchers(only_installed=True):
                launcher_items.append(item)
            else:
                if self.is_action_installed (item):
                    launcher_items.append (item)

        self.client.set_list ("%s/dock/items_order" % self.gconf_path, gconf.VALUE_STRING, launcher_items)
        self.__sync_config()
        self.emit ('launcher-items-order-changed')

    def get_launcher_items_order (self):
        return self.client.get_list ("%s/dock/items_order" % self.gconf_path, gconf.VALUE_STRING)

    def move_up_launcher_item (self, item):
        launcher_items = self.get_launcher_items_order ()

        count = 0
        for launcher_item in launcher_items:
            if count > 0 and launcher_item == item:
                tmp = launcher_items[count]
                launcher_items[count] = launcher_items[count-1]
                launcher_items[count-1] = tmp
                self.set_launcher_items_order (launcher_items)
                break

            count = count + 1

    def move_down_launcher_item (self, item):
        launcher_items = self.get_launcher_items_order ()

        count = len (launcher_items) - 1
        for launcher_item in launcher_items.reverse():
            if count < len(launcher_items)-1 and launcher_item == item:
                tmp = launcher_items[count]
                launcher_items[count] = launcher_items[count+1]
                launcher_items[count+1] = tmp
                self.set_launcher_items_order (launcher_items)
                break

            count = count - 1


    # Section "favorite-list"

    def add_bookmark(self, name, url, connection_name=None, userdata=None, readonly=False, overwrite=False):
        bookmark_path = None
        signal_to_issue = 'bookmark-added'

        if overwrite:
            for path in self.client.all_dirs("%s/bookmarks" % self.gconf_path):
                if self.client.get_string("%s/name" % path) == name:
                    bookmark_path = path
                    signal_to_issue = 'bookmark-changed'
                    break

        if bookmark_path is None:
            counter = 0
            path = "%s/bookmarks/bookmark%d" % (self.gconf_path, counter)
            while self.client.dir_exists(path):
                counter += 1
                path = "%s/bookmarks/bookmark%d" % (self.gconf_path, counter)
            bookmark_path = path

        self.__write_bookmark_changes(bookmark_path, name, url, connection_name, userdata, readonly)
        self.emit(signal_to_issue, name)

    def modify_bookmark(self, old_name, new_name, url, connection_name=None, userdata=None, readonly=False):
        bookmark_path = None
        for path in self.client.all_dirs("%s/bookmarks" % self.gconf_path):
            if self.client.get_string("%s/name" % path) == old_name:
                bookmark_path = path
                break

        if bookmark_path is None:
            return

        self.__write_bookmark_changes(bookmark_path, new_name, url, connection_name, userdata, readonly)
        self.emit('bookmark-changed', new_name)

    def __write_bookmark_changes(self, bookmark_path, name, url, connection_name=None, userdata=None, readonly=False):
        btime = time.time()
        self.client.set_string("%s/name" % bookmark_path, name)
        self.client.set_string("%s/url" % bookmark_path, url)
        self.client.set_int("%s/timestamp" % bookmark_path, long(btime))
        self.client.set_bool("%s/readonly" % bookmark_path, readonly)

        if connection_name is None:
            connection_name = ''
        self.client.set_string("%s/connection" % bookmark_path, connection_name)

        if userdata is None:
            userdata = 0
        self.client.set_int("%s/userdata" % bookmark_path, userdata)

        self.__sync_config()

    def del_bookmark(self, name):
        for bookmark in self.client.all_dirs ("%s/bookmarks" % self.gconf_path):
            if self.client.get_string ("%s/name" % bookmark) == name:
                self.client.recursive_unset (bookmark, gconf.UNSET_INCLUDING_SCHEMA_NAMES)
                self.__sync_config()

                self.emit ('bookmark-deleted', name)
                return True
        return False


    # Section "policies"

    #Policies
    def add_policy (self, name, value):
        if name is not None and value is not None:
            self.client.set_bool ("%s/policies/%s" % (self.gconf_path, name), value)
            self.__sync_config ()

    def check_policy (self, name):
        for policy in self.client.all_entries ("%s/policies" % self.gconf_path):
            if policy.get_key() == "%s/policies/%s" % (self.gconf_path, name):
                value = policy.get_value()
                return value.get_bool ()
        return True

    # Connect on startup
    def get_connect_on_startup (self):
        return self.client.get_bool("%s/connect_on_startup" % self.gconf_path)

    def set_connect_on_startup (self, value):
        self.client.set_bool ("%s/connect_on_startup" % self.gconf_path, value)
        self.__sync_config()

    #Connections conf

    def get_default_connection_name (self):
        conn_manager = Connections.ConnectionManager()
        connections_model=conn_manager.get_connections_model()
        iter= connections_model.get_iter_first();
        connection_name=connections_model.get_value(iter, 1)
        return connection_name


    def get_connection_name_from_index (self,connection_index):
        conn_manager = Connections.ConnectionManager()
        connections_model=conn_manager.get_connections_model()
        iter= connections_model.get_iter_first()
        for i in range(0,connection_index):
            iter= connections_model.iter_next(iter)
            if (iter==None):
                return None

        connection_name=connections_model.get_value(iter, 1)
        return connection_name

    def del_all_readonly_connections (self):
        print "TODO: Rewrite this function in ConnectionSettingsManager"
        for connection in self.client.all_dirs ("%s/connections/wwan" % self.gconf_path):
            if self.client.get_bool ("%s/editable" % connection) == False:
                self.del_connection (self.client.get_string ("%s/name" % connection))
                some_deleted = True

        # Dock position
    def get_window_position (self):
        x = self.client.get_int ("%s/dock/x_pos" % self.gconf_path)
        y = self.client.get_int ("%s/dock/y_pos" % self.gconf_path)

        return (x, y)

    @delayed_call
    def set_window_position (self, x, y):
        self.client.set_int ("%s/dock/x_pos" % self.gconf_path, x)
        self.client.set_int ("%s/dock/y_pos" % self.gconf_path, y)
        self.__sync_config ()


    # Section "news"

    # RSS Feed
    def is_news_available(self) :
        return self.client.get_bool ("%s/news_available" % self.gconf_path)

    def set_news_available(self, value) :
        self.client.set_bool ("%s/news_available" % self.gconf_path, value)
        self.__sync_config()

    def get_updater_feed_url(self):
        return self.client.get_string ("%s/updater_feed_url" % self.gconf_path)

    def set_updater_feed_url (self, value):
        if value == None:
            value = ""
        self.client.set_string ("%s/updater_feed_url" % self.gconf_path, value)
        self.__sync_config()

    def get_updater_feed_date(self):
        return self.client.get_string ("%s/updater_feed_date" % self.gconf_path)

    def set_updater_feed_date(self, date):
        self.client.set_string ("%s/updater_feed_date" % self.gconf_path, date)
        self.__sync_config()

    def get_release_date(self):
        return self.client.get_string ("%s/release_date" % self.gconf_path)

    def get_release_datetime(self):
        release_time_struct = time.strptime(self.get_release_date(), "%Y-%m-%d %H:%M:%S")
        return datetime.datetime.fromtimestamp(time.mktime(release_time_struct))


    # Section "traffic"

    ## Billing day ##
    def get_default_billing_day(self):
        return self.client.get_int("%s/billing_day" % self.gconf_path)

    def set_default_billing_day(self, value):
        if type(value) is not IntType:
            raise TypeError('Billing day must be integer')

        if not value or value == 0:
            now = datetime.datetime.now()
            value = now.day
        self.client.set_int("%s/billing_day" % self.gconf_path, value)
        self.__sync_config()

    def is_default_fixed_billing_day (self):
        return self.client.get_bool ("%s/fixed_billing_day" % self.gconf_path)

    def set_is_default_fixed_billing_day (self, value):
        self.client.set_bool("%s/fixed_billing_day" % self.gconf_path, value)
        self.__sync_config()

    @imsi_required
    def is_imsi_based_fixed_billing_day(self, imsi):
        gconf_key = '%s/imsi/%s/fixed_billing_day' % (self.gconf_path, imsi)

        gconf_value = self.client.get_without_default(gconf_key)
        if gconf_value is None:
            value = self.is_default_fixed_billing_day()
            self.client.set_bool(gconf_key, value)
            self.__sync_config()

        return self.client.get_bool(gconf_key)

    @imsi_required
    def set_is_imsi_based_fixed_billing_day(self, imsi, value):
        if type(value) is not BooleanType:
            raise TypeError('Monthly limits must be integers')

        self.client.set_bool('%s/imsi/%s/fixed_billing_day' % (self.gconf_path, imsi), value)
        self.__sync_config()
        self.emit('fixed-billing-day-changed', value)

    @imsi_required
    def get_imsi_based_billing_day(self, imsi):
        billing_day_key = '%s/imsi/%s/billing_day' % (self.gconf_path, imsi)

        billing_day_value = self.client.get_without_default(billing_day_key)
        if billing_day_value is None:
            value = self.get_default_billing_day()
            self.client.set_int(billing_day_key, value)
            self.__sync_config()

        return self.client.get_int(billing_day_key)

    @imsi_required
    def set_imsi_based_billing_day(self, imsi, value):
        self.client.set_int("%s/imsi/%s/billing_day" % (self.gconf_path, imsi), value)
        self.__sync_config()
        self.emit ('billing-day-changed')


    def get_default_billing_period(self, day = None):
        if (day is not None) and (type(day) is not datetime.date):
            raise TypeError('Day must be an instance of datetime.date')

        billing_day = self.get_default_billing_day()
        return self.__get_billing_period(billing_day, day)

    @imsi_required
    def get_imsi_based_billing_period(self, imsi, day = None):
        if (day is not None) and (type(day) is not datetime.date):
            raise TypeError('Day must be an instance of datetime.date')

        imsi = self.get_last_imsi_seen()
        billing_day = self.get_imsi_based_billing_day(imsi)
        return self.__get_billing_period(billing_day, day)

    def __get_billing_period(self, billing_day, today = None):
        # There are three possible scenarios in "billing period" calculation:
        # 1. Start and end dates of the billing period are in the very same month.
        #    E.g. the billing day is 1 and today is 15/1/2011. The current billing
        #    period must be from 1/1/2011 to 31/1/2011.
        # 2. The start date of the billing period is in this month, and the
        #    end date is in the following.
        #    E.g. the billing day is 15 and today is 18/1/2011. The current billing
        #    period must be from 15/1/2011 to 14/2/2011.
        # 3. The start date of the billing period was in the previous month, and the
        #    end date is in this month.
        #    E.g. the billing day is 15 and today is 12/1/2011. The current billing
        #    period must be from 15/12/2010 to 14/1/2011.
        #
        # Additionally, there are various checks that are needed to be performed in
        # order to have correct dates in the billing period:
        # a. Check that the billing day is valid for the current month. E.g. if the
        #    billing day is 31 it would not be a valid date for February.
        # b. When decreasing the billing day (necessary for the end date of the period),
        #    check it it is a valid date for the current month. E.g. 0 is not a valid
        #    month day.
        # c. When increasing the month number, check it it s a valid number.
        #    E.g. 13 is not a valid month number.
        # d. When decreasing the month number, check it is a valid number.
        #    E.g. 0 is not a valid month number.
        #
        # The algorithm is fairly simple:
        # 1. It attempts to determine the month and year of the start and end of the
        #    billing period. It is necessary to perform the checks described above in
        #    points 'c' and 'd'.
        # 2. It determines the day of the start date of the billing period. It is
        #    necessary to perform the check described above in point 'a'.
        # 3. It determines the day of the end date of the billing period. It is
        #    necessary to perform the checks described above in points 'a' and 'b'.

        # By default the reference date will be today
        if today is None:
            today = datetime.date.today()

        start_date = {}
        end_date = {}

        ## Calculate the month and year for the start and end dates of the billing period ##

        # Calculate the effective billing day for current month, in case the month has less
        # days than the billing day number
        month_billing_day = billing_day
        num_days_month = calendar.monthrange(today.year, today.month)[1]
        if billing_day > num_days_month:
            month_billing_day = num_days_month

        # First scenario: start and end dates of the billing period are in the same month
        if month_billing_day == 1:
            start_date['month'] = today.month
            start_date['year'] = today.year

            end_date['month'] = today.month
            end_date['year'] = today.year

        # Second scenario: start date of the billing period is in the current month, the end
        # date is in the following
        elif today.day >= month_billing_day:
            start_date['month'] = today.month
            start_date['year'] = today.year

            # Check if the month is valid; the billing period might jump to the next year
            if (today.month + 1) > 12:
                end_date['month'] = 1
                end_date['year'] = today.year + 1
            else:
                end_date['month'] = today.month + 1
                end_date['year'] = today.year

        # Third scenario: start date of the billing period was in the previous month, the end
        # date is in the current month
        else:
            # Check if the month is valid; the start of the billing period might be in the
            # previous year
            if (today.month - 1) < 1:
                start_date['month'] = 12
                start_date['year'] = today.year - 1
            else:
                start_date['month'] = today.month - 1
                start_date['year'] = today.year

            end_date['month'] = today.month
            end_date['year'] = today.year

        ## Calculate the day number for the start date of the billing period ##

        # Perform check 'a' described above
        num_days_month = calendar.monthrange(start_date['year'], start_date['month'])[1]
        if billing_day > num_days_month:
            start_date['day'] = num_days_month
        else:
            start_date['day'] = billing_day

        ## Calculate the day number for the end of the billing period ##

        # Perform check 'a' described above
        num_days_month = calendar.monthrange(end_date['year'], end_date['month'])[1]
        if billing_day > num_days_month:
            end_date['day'] = num_days_month
        else:
            end_date['day'] = billing_day

        # Perform check 'b' described above
        if end_date['day'] - 1 < 1:
            end_date['day'] = num_days_month
        else:
            end_date['day'] = end_date['day'] - 1

        # Build a tuple of datetime.date objects for the billing period
        year = start_date['year']
        month = start_date['month']
        day = start_date['day']
        start = datetime.date(year, month, day)

        year = end_date['year']
        month = end_date['month']
        day = end_date['day']
        end = datetime.date(year, month, day)

        return (start, end)

    # Section "prepay"


    # Section "eapsim"


    # Section "userdata"

    def is_userdata_available(self):
        return self.client.get_bool ("%s/userdata" % self.gconf_path)

    def set_userdata_available(self, value):
        self.client.set_bool ("%s/userdata" % self.gconf_path, value)
        self.__sync_config ()


    # Section "addressbook"

    def get_country_code(self):
        return self.client.get_string ("%s/country_code" % self.gconf_path).strip()

    def set_country_code(self, value):
        self.client.set_string ("%s/country_code" % self.gconf_path, value)
        self.__sync_config ()

    def get_phone_match (self):
        return self.client.get_string ("%s/addressbook/phone_match" % self.gconf_path).strip()

    def set_phone_match (self, value):
        self.client.set_string ("%s/addressbook/phone_match" % self.gconf_path, value)
        self.__sync_config ()

    def get_phone_format (self):
        return self.client.get_list ("%s/addressbook/phone_format" % self.gconf_path, gconf.VALUE_INT)

    def set_phone_format (self,  value):
        self.client.set_list ("%s/addressbook/phone_format" % self.gconf_path, gconf.VALUE_INT, value)
        self.__sync_config ()

    #Bookmarks conf

    def get_bookmarks_list(self):
        bookmarks_list = []
        bookmarks = list(self.client.all_dirs ("%s/bookmarks" % self.gconf_path))

        def sort_func(x,y):
            x_tmp = int(os.path.basename(x).replace("bookmark",""))
            y_tmp = int(os.path.basename(y).replace("bookmark",""))
            if x_tmp > y_tmp :
                return 1
            elif x_tmp < y_tmp :
                return -1
            else:
                return 0

        bookmarks.sort(cmp=sort_func)
        for bookmark in bookmarks:
            bookmark_dict = {}
            bookmark_dict['name'] = self.client.get_string("%s/name" % bookmark)
            bookmark_dict['url'] = self.client.get_string("%s/url" % bookmark)
            bookmark_dict['connection'] = self.client.get_string("%s/connection" % bookmark)
            bookmark_dict['timestamp'] = self.client.get_int("%s/timestamp" % bookmark)
            bookmark_dict['readonly'] = self.client.get_bool("%s/readonly" % bookmark)
            bookmark_dict['userdata'] = self.client.get_int("%s/userdata" % bookmark)
            bookmarks_list.append(bookmark_dict)
        return bookmarks_list

    def get_bookmark(self, name):
        for bookmark in self.client.all_dirs("%s/bookmarks" % self.gconf_path):
            if self.client.get_string("%s/name" % bookmark) == name:
                bookmark_dict = {}
                bookmark_dict['name'] = self.client.get_string("%s/name" % bookmark)
                bookmark_dict['url'] = self.client.get_string("%s/url" % bookmark)
                bookmark_dict['connection'] = self.client.get_string("%s/connection" % bookmark)
                bookmark_dict['timestamp'] = self.client.get_int("%s/timestamp" % bookmark)
                bookmark_dict['readonly'] = self.client.get_bool("%s/readonly" % bookmark)
                bookmark_dict['userdata'] = self.client.get_int("%s/userdata" % bookmark)
                return bookmark_dict
        return None

    def set_bookmark_url (self, name, url):
        for bookmark in self.client.all_dirs ("%s/bookmarks" % self.gconf_path):
            if self.client.get_string ("%s/name" % bookmark) == name:
                self.client.set_string ("%s/url" % bookmark, url)
        self.__sync_config ()
        self.emit ('bookmark-changed', name)

    def get_bookmark_connection (self, name):
        for bookmark in self.client.all_dirs ("%s/bookmarks" % self.gconf_path):
            if self.client.get_string ("%s/name" % bookmark) == name:
                return self.client.get_string ("%s/connection" % bookmark)
        return None

    def set_bookmark_connection (self, name, connection_name):
        for bookmark in self.client.all_dirs ("%s/bookmarks" % self.gconf_path):
            if self.client.get_string ("%s/name" % bookmark) == name:
                self.client.set_string ("%s/connection" % bookmark, connection_name)
        self.__sync_config ()
        self.emit ('bookmark-changed', name)

    def set_proxy (self, conn):
        if (conn!=None and conn.get('proxy',0) == 1):

            self.client.set_bool('/system/http_proxy/use_http_proxy',True)
            self.client.set_bool('/system/http_proxy/use_authentication',False)
            self.client.set_string('/system/proxy/mode','manual')

            self.client.set_bool('/system/http_proxy/use_same_proxy',conn['proxy_same_proxy'])

            self.client.set_string('/system/http_proxy/host',conn['proxy_ip'])
            self.client.set_int('/system/http_proxy/port',conn['proxy_port'])

            if (conn['proxy_ftp_ip']!=None):
                self.client.set_string('/system/proxy/ftp_host',conn['proxy_ftp_ip'])
                self.client.set_int('/system/proxy/ftp_port',conn['proxy_ftp_port'])

            if (conn['proxy_https_ip']!=None):
                self.client.set_string('/system/proxy/secure_host',conn['proxy_https_ip'])
                self.client.set_int('/system/proxy/secure_port',conn['proxy_https_port'])

            if (conn['proxy_socks_ip']!=None):
                self.client.set_string('/system/proxy/socks_host',conn['proxy_socks_ip'])
                self.client.set_int('/system/proxy/socks_port',conn['proxy_socks_port'])

            if (conn['proxy_ignore']!=None):
                self.client.set_list('/system/http_proxy/ignore_hosts',gconf.VALUE_STRING,conn['proxy_ignore'])


            backend = GSettings.GSettingsCustom()
            backend.set_bool('org.gnome.system.proxy.http', 'enabled',True)
            backend.set_bool('org.gnome.system.proxy.http', 'use-authentication',True)
            backend.set_string('org.gnome.system.proxy', 'mode', 'manual')
            backend.set_bool('org.gnome.system.proxy', 'use-same-proxy', conn['proxy_same_proxy'])


            backend.set_string('org.gnome.system.proxy.http','host',conn['proxy_ip'])
            backend.set_integer('org.gnome.system.proxy.http','port',conn['proxy_port'])

            if (conn['proxy_ftp_ip']!=None):
                backend.set_string('org.gnome.system.proxy.ftp','host',conn['proxy_ftp_ip'])
                backend.set_integer('org.gnome.system.proxy.ftp','port',conn['proxy_ftp_port'])
            if (conn['proxy_https_ip']!=None):
                backend.set_string('org.gnome.system.proxy.https','host',conn['proxy_https_ip'])
                backend.set_integer('org.gnome.system.proxy.https','port',conn['proxy_https_port'])
            if (conn['proxy_socks_ip']!=None):
                backend.set_string('org.gnome.system.proxy.socks','host',conn['proxy_socks_ip'])
                backend.set_integer('org.gnome.system.proxy.socks','port',conn['proxy_socks_port'])
            if (conn['proxy_ignore']!=None):
                backend.set_list('org.gnome.system.proxy','ignore-hosts',conn['proxy_ignore'])



        else:
            self.client.set_bool('/system/http_proxy/use_http_proxy',False)
            self.client.set_string('/system/proxy/mode','none')

            backend = GSettings.GSettingsCustom()
            backend.set_bool('org.gnome.system.proxy.http', 'enabled',False)
            backend.set_string('org.gnome.system.proxy', 'mode', 'none')


    def del_all_readonly_bookmarks (self):
        boomarks_to_delete=[];
        for bookmark in self.client.all_dirs ("%s/bookmarks" % self.gconf_path):
            if self.client.get_bool ("%s/readonly" % bookmark) == 1:
                boomarks_to_delete.append(bookmark)


        if len(boomarks_to_delete)>0:
            for bookmark in boomarks_to_delete:
                name = self.client.get_string ("%s/name" % bookmark)
                self.client.recursive_unset (bookmark, gconf.UNSET_INCLUDING_SCHEMA_NAMES)
                self.emit ('bookmark-deleted', name)

            self.__sync_config()

    def exists_bookmark (self, name):
        for bookmark in self.client.all_dirs ("%s/bookmarks" % self.gconf_path):
            if self.client.get_string ("%s/name" % bookmark) == name:
                return True
        return False



    def get_ask_before_connect_to_action (self):
        return False
        #return self.client.get_bool ("%s/connections_general/ask_before_connect_to_action" % self.gconf_path)

    def set_ask_before_connect_to_action (self, value):
        if value == True:
            self.client.set_bool ("%s/connections_general/ask_before_connect_to_action" % self.gconf_path, True)
        else:
            self.client.set_bool ("%s/connections_general/ask_before_connect_to_action" % self.gconf_path, False)
        self.__sync_config()

    def get_ask_before_change_connection(self):
        return self.client.get_bool ("%s/connections_general/ask_before_change_connection" % self.gconf_path)

    def set_ask_before_change_connection (self, value):
        if value == True:
            self.client.set_bool ("%s/connections_general/ask_before_change_connection" % self.gconf_path, True)
        else:
            self.client.set_bool ("%s/connections_general/ask_before_change_connection" % self.gconf_path, False)
        self.__sync_config()

    def get_ask_before_connect(self):
        return self.client.get_bool("%s/connections_general/ask_before_connect" % self.gconf_path)

    def set_ask_before_connect (self, value):
        self.client.set_bool("%s/connections_general/ask_before_connect" % self.gconf_path, value)
        self.__sync_config()

    def get_connection_log_filepath(self):
        return tgcm.connection_log_file

    def is_connection_log_enabled(self):
        return self.client.get_bool("%s/connections_general/log_activate" % self.gconf_path)

    def set_connection_log_enabled(self, value):
        self.client.set_bool("%s/connections_general/log_activate" % self.gconf_path, value)
        self.__sync_config()
        self.emit("connection-log-enable-changed", value)

    #Security conf

    def get_auth_activate(self):
        return self.client.get_bool ("%s/security/auth_on" % self.gconf_path)

    def set_auth_activate(self, value):
        if value == True:
            self.client.set_bool ("%s/security/auth_on" % self.gconf_path, True)
        else:
            self.client.set_bool ("%s/security/auth_on" % self.gconf_path, False)
        self.__sync_config()

    def get_celular_info(self):
        number = self.client.get_string ("%s/security/celular_number" % self.gconf_path)
        password = self.client.get_string ("%s/security/celular_password" % self.gconf_path)
        return [number, password]

    def set_celular_info(self, number, password):
        if number is not None:
            self.client.set_string ("%s/security/celular_number" % self.gconf_path, number)
        if password is not None:
            self.client.set_string ("%s/security/celular_password" % self.gconf_path, password)

        self.__sync_config()

    def get_ask_password_activate(self):
        return self.client.get_bool ("%s/security/ask_password" % self.gconf_path)

    def set_ask_password_activate(self, value):
        if value == True:
            self.client.set_bool ("%s/security/ask_password" % self.gconf_path, True)
        else:
            self.client.set_bool ("%s/security/ask_password" % self.gconf_path, False)
        self.__sync_config()

    # Devices conf
    def get_device_selected(self):
        return self.client.get_int ("%s/devices/selected" % self.gconf_path)

    def set_device_selected(self, device_number):
        self.client.set_int ("%s/devices/selected" % self.gconf_path, device_number)
        self.__sync_config()

    # -- Add a new device to the main selected
    def add_device_main_modem_selected(self, vid, pid):
        current = self.get_device_main_modem_selected()
        if not vid in current:
            current.append(vid)
            self.client.set_list("%s/devices/selected_main_modems" % self.gconf_path, gconf.VALUE_INT, current)

    # Return the list of the already selected main modems
    def get_device_main_modem_selected(self):
        return self.client.get_list("%s/devices/selected_main_modems" % self.gconf_path, gconf.VALUE_INT)

    #Actions Conf

    def add_url_launcher (self, id, url, caption, install_status):
        counter = 0
        while True:
            if self.client.dir_exists ("%s/url_launchers/url_launcher%d" % (self.gconf_path, counter)):
                counter += 1
            else:
                break

        self.client.set_string ("%s/url_launchers/url_launcher%d/id" % (self.gconf_path, counter), id)
        self.client.set_string ("%s/url_launchers/url_launcher%d/url" % (self.gconf_path, counter), url)
        self.client.set_string ("%s/url_launchers/url_launcher%d/caption" % (self.gconf_path, counter), caption)
        self.client.set_bool ("%s/url_launchers/url_launcher%d/installed" % (self.gconf_path, counter), install_status)

    def get_url_launchers(self, only_installed=False):
        counter = 0
        installed_url_launchers = []

        while True:
            if self.client.dir_exists ("%s/url_launchers/url_launcher%d" % (self.gconf_path, counter)):
                if only_installed==False or self.client.get_bool ("%s/url_launchers/url_launcher%d/installed" % (self.gconf_path, counter)):
                    id = self.client.get_string ("%s/url_launchers/url_launcher%d/id" % (self.gconf_path, counter))
                    installed_url_launchers.append (id)
                counter += 1
            else:
                break

        return installed_url_launchers

    def get_url_launcher(self, id):
        counter = 0
        while True:
            if self.client.dir_exists ("%s/url_launchers/url_launcher%d" % (self.gconf_path, counter)):
                if id == self.client.get_string ("%s/url_launchers/url_launcher%d/id" % (self.gconf_path, counter)):
                    break
                counter += 1
            else:
                return None

        url = self.client.get_string ("%s/url_launchers/url_launcher%d/url" % (self.gconf_path, counter))
        caption = self.client.get_string ("%s/url_launchers/url_launcher%d/caption" % (self.gconf_path, counter))
        installed = self.client.get_bool ("%s/url_launchers/url_launcher%d/installed" % (self.gconf_path, counter))

        return url, caption, installed

    def set_url_launcher_installed (self, id, install_status):
        counter = 0
        while True:
            if self.client.dir_exists ("%s/url_launchers/url_launcher%d" % (self.gconf_path, counter)):
                if id == self.client.get_string ("%s/url_launchers/url_launcher%d/id" % (self.gconf_path, counter)):
                    break
                counter += 1
            else:
                return None

        self.client.set_bool ("%s/url_launchers/url_launcher%d/installed" % (self.gconf_path, counter), install_status)
        launcher_items = self.get_launcher_items_order ()
        launcher_items.append (id)
        self.set_launcher_items_order (launcher_items)


    #UI General key value

    def get_ui_general_key_value(self, key):
        return self.client.get_bool ("%s/ui_general/%s" % (self.gconf_path, key))

    def set_ui_general_key_value(self, key, value):
        self.client.set_bool ("%s/ui_general/%s" % (self.gconf_path, key), value)
        self.__sync_config()
        self.emit("ui-general-key-value-changed", key, value)

    #To use only for windo titles
    def get_caption(self):
        app_name = "%s" % self.client.get_string ("%s/app_name" % self.gconf_path).strip()
        if self.is_latam() is True:
            # -- @XXX: Quick and dirty
            return app_name.replace(' Latam', '')
        else:
            return app_name

    def get_network_mnemonic(self):
        if tgcm.country_support != "de":
            return "WWAN"
        else:
            return "2G/3G/4G"

    # Consumo y velocidad acumulada

    def get_sms_sent (self, roaming, imsi):
        if imsi=="" :
            if roaming == False:
                ret = self.client.get_int ("%s/expenses/sms_sent" % self.gconf_path)
            else:
                ret = self.client.get_int ("%s/expenses/sms_sent_roaming" % self.gconf_path)
        else:
            if roaming == False:
                ret = self.client.get_int ("%s/imsi/%s/expenses/sms_sent" % (self.gconf_path, imsi))
            else:
                ret = self.client.get_int ("%s/imsi/%s/expenses/sms_sent_roaming" % (self.gconf_path, imsi))

        if ret == None or ret == False :
            return 0
        else:
            return ret

    def set_sms_sent (self, value, roaming, imsi):
        value = int(value)
        if imsi == "" :
            if roaming == False:
                self.client.set_int ("%s/expenses/sms_sent" % self.gconf_path, value)
            else:
                self.client.set_int ("%s/expenses/sms_sent_roaming" % self.gconf_path, value)
        else:
            if roaming == False:
                self.client.set_int ("%s/imsi/%s/expenses/sms_sent" % (self.gconf_path, imsi), value)
            else:
                self.client.set_int ("%s/imsi/%s/expenses/sms_sent_roaming" % (self.gconf_path, imsi), value)

        self.__sync_config()
        self.emit("sms-counter-changed", imsi)

    def reset_sms_sent (self, imsi):
        self.set_sms_sent (0, True, imsi)
        self.set_sms_sent (0, False, imsi)
        self.emit("sms-counter-reset")

    def get_show_mb_warning(self, roaming):
        if roaming == False:
            return self.client.get_bool ("%s/expenses/show_mb_warning" % self.gconf_path)
        else:
            return self.client.get_bool ("%s/expenses/show_mb_warning_roaming" % self.gconf_path)

    def set_show_mb_warning(self, value, roaming):
        if roaming == False:
            self.client.set_bool ("%s/expenses/show_mb_warning" % self.gconf_path, value)
        else:
            self.client.set_bool ("%s/expenses/show_mb_warning_roaming" % self.gconf_path, value)
        self.__sync_config()

    def get_show_percent_warning(self):
        return self.client.get_bool ("%s/expenses/show_percent_warning" % self.gconf_path)

    def set_show_percent_warning(self, value):
        self.client.set_bool ("%s/expenses/show_percent_warning" % self.gconf_path, value)
        self.__sync_config()

    def get_warning_mb_combo(self):
        return self.client.get_int ("%s/expenses/warning_mb_combo" % self.gconf_path)

    def set_warning_mb_combo(self, value):
        self.client.set_int ("%s/expenses/warning_mb_combo" % self.gconf_path, int(round(value)))
        self.__sync_config()

    def get_warning_mb(self, roaming):
        if roaming == False:
            return self.client.get_int ("%s/expenses/warning_mb" % self.gconf_path)
        else:
            return self.client.get_int ("%s/expenses/warning_mb_roaming" % self.gconf_path)

    def set_warning_mb(self, value, roaming):
        if roaming == False:
            self.client.set_int ("%s/expenses/warning_mb" % self.gconf_path, int(round(value)))
        else:
            self.client.set_int ("%s/expenses/warning_mb_roaming" % self.gconf_path, int(round(value)))
        self.__sync_config()

    def get_warning_percent(self):
        return self.client.get_int ("%s/expenses/warning_percent" % self.gconf_path)

    def get_user_id(self):
        user_id = self.client.get_string ("%s/user_id" % self.gconf_path)
        if user_id is None or user_id == "":
            user_id = md5.new("EMLIN-%s" % str(time.time())).hexdigest()
            self.client.set_string ("%s/user_id" % self.gconf_path, user_id)

        return user_id

    def is_default_prepaid(self):
        is_prepay_key = '%s/is_default_prepaid' % self.gconf_path
        is_prepay_value = self.client.get_without_default(is_prepay_key)
        if is_prepay_value is None:
            self.client.set_bool(is_prepay_key, True)
        return self.client.get_bool(is_prepay_key)

    def set_is_default_prepaid(self, value):
        self.client.set_bool('%s/is_default_prepaid' % self.gconf_path, value)
        self.__sync_config()

    @imsi_required
    def is_imsi_based_prepaid(self, imsi):
        prepaid_key = '%s/imsi/%s/user_connection_prepaid' % (self.gconf_path, imsi)
        prepaid_value = self.client.get_without_default(prepaid_key)
        if prepaid_value is None:
            value = self.is_default_prepaid()
            self.client.set_bool(prepaid_key, value)
            self.__sync_config()
        return self.client.get_bool(prepaid_key)

    @imsi_required
    def set_is_imsi_based_prepaid(self, imsi, value):
        self.client.set_bool('%s/imsi/%s/user_connection_prepaid' % (self.gconf_path, imsi), value)
        self.__sync_config()
        self.emit('user-prepay-changed', value)

    @imsi_required
    def get_user_mobile_broadband_number (self, imsi):
        ret = self.client.get_string ("%s/imsi/%s/user_mobile_broadband_number" % (self.gconf_path, imsi))
        if ret == None :
            return ""
        else:
            return ret

    @imsi_required
    def set_user_mobile_broadband_number (self, imsi, value):
        self.client.set_string("%s/imsi/%s/user_mobile_broadband_number" % (self.gconf_path, imsi), value)
        self.__sync_config()
        self.emit('user-mobile-broadband-number-changed', value)

    def set_user_phone (self, value):
        self.client.set_string ('%s/user_phone' % self.gconf_path, value)
        self.__sync_config()

    def get_user_phone (self):
        return self.client.get_string ('%s/user_phone' % self.gconf_path).strip()


    ## Monthly limits ##

    def get_monthly_limits(self, is_roaming):
        if not is_roaming:
            conf_path = '%s/alerts/normal/monthly_limits' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/monthly_limits' % self.gconf_path

        return self.client.get_list(conf_path, gconf.VALUE_INT)

    def set_monthly_limits(self, limit_values, is_roaming):
        # Check that the parameter is a list of integers
        for value in limit_values:
            if type(value) is not IntType:
                raise TypeError('Monthly limits must be integers')

        if not is_roaming:
            conf_path = '%s/alerts/normal/monthly_limits' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/monthly_limits' % self.gconf_path

        self.client.set_list(conf_path, gconf.VALUE_INT, limit_values)
        self.__sync_config()

    def get_default_selected_monthly_limit(self, is_roaming):
        if not is_roaming:
            conf_path = '%s/alerts/normal/default_monthly_limit' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/default_monthly_limit' % self.gconf_path

        return self.client.get_int(conf_path)

    def set_default_selected_monthly_limit(self, value, is_roaming):
        # Check the value is an integer
        if type(value) is not IntType:
            raise TypeError('Monthly limits must be integers')

        monthly_limits = self.get_monthly_limits(is_roaming)
        if value not in monthly_limits:
            raise AttributeError('Default selected value not in monthly limits')

        if not is_roaming:
            conf_path = '%s/alerts/normal/default_monthly_limit' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/default_monthly_limit' % self.gconf_path

        self.client.set_int(conf_path, value)
        self.__sync_config()

    @imsi_required
    def get_imsi_based_selected_monthly_limit(self, imsi, is_roaming):
        if not is_roaming:
            conf_path = '%s/imsi/%s/selected_monthly_limit' % (self.gconf_path, imsi)
        else:
            conf_path = '%s/imsi/%s/selected_roaming_monthly_limit' % (self.gconf_path, imsi)

        value = self.client.get_without_default(conf_path)
        if value is None:
            default_value = self.get_default_selected_monthly_limit(is_roaming)
            self.client.set_int(conf_path, default_value)
            self.__sync_config()

        return self.client.get_int(conf_path)

    @imsi_required
    def set_imsi_based_selected_monthly_limit(self, imsi, value, is_roaming):
        # Check the value is an integer
        if type(value) is not IntType:
            raise TypeError('Monthly limits must be integers')

        monthly_limits = self.get_monthly_limits(is_roaming)
        if value not in monthly_limits:
            raise AttributeError('Default selected value not in monthly limits')

        if not is_roaming:
            conf_path = '%s/imsi/%s/selected_monthly_limit' % (self.gconf_path, imsi)
        else:
            conf_path = '%s/imsi/%s/selected_roaming_monthly_limit' % (self.gconf_path, imsi)

        self.client.set_int(conf_path, value)
        self.__sync_config()
        self.emit('monthly-limit-changed')

    @imsi_required
    def get_imsi_based_other_monthly_limit(self, imsi, is_roaming):
        if not is_roaming:
            conf_path = '%s/imsi/%s/other_monthly_limit' % (self.gconf_path, imsi)
        else:
            conf_path = '%s/imsi/%s/other_roaming_monthly_limit' % (self.gconf_path, imsi)

        value = self.client.get_without_default(conf_path)
        if value is None:
            default_value = 1
            self.client.set_int(conf_path, default_value)
            self.__sync_config()

        return self.client.get_int(conf_path)

    @imsi_required
    def set_imsi_based_other_monthly_limit(self, imsi, value, is_roaming):
        if type(value) is not IntType:
            raise TypeError('Monthly limits must be integers')

        if not is_roaming:
            conf_path = '%s/imsi/%s/other_monthly_limit' % (self.gconf_path, imsi)
        else:
            conf_path = '%s/imsi/%s/other_roaming_monthly_limit' % (self.gconf_path, imsi)

        self.client.set_int(conf_path, value)
        self.__sync_config()
        self.emit('monthly-limit-changed')


    ## Alerts ##

    def get_alerts(self, is_roaming):
        if not is_roaming:
            conf_path = '%s/alerts/normal/alerts' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/alerts' % self.gconf_path

        return self.client.get_list(conf_path, gconf.VALUE_INT)

    def set_alerts(self, alert_values, is_roaming):
        # Check that the parameter is a list of integers
        for value in alert_values:
            if type(value) is not IntType:
                raise TypeError('Monthly limits must be integers')

        if not is_roaming:
            conf_path = '%s/alerts/normal/alerts' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/alerts' % self.gconf_path

        self.client.set_list(conf_path, gconf.VALUE_INT, alert_values)
        self.__sync_config()

    def get_default_enabled_alerts(self, is_roaming):
        if not is_roaming:
            conf_path = '%s/alerts/normal/default_enabled_alerts' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/default_enabled_alerts' % self.gconf_path

        return self.client.get_list(conf_path, gconf.VALUE_INT)

    def enable_default_alert(self, alert_value, is_enabled, is_roaming):
        # Check the value is an integer
        if type(alert_value) is not IntType:
            raise TypeError('Monthly limits must be integers')

        alerts = self.get_alerts(is_roaming)
        if alert_value not in alerts:
            raise AttributeError('Alert value not in alerts')

        if not is_roaming:
            conf_path = '%s/alerts/normal/default_enabled_alerts' % self.gconf_path
        else:
            conf_path = '%s/alerts/roaming/default_enabled_alerts' % self.gconf_path

        enabled_alerts = self.get_default_enabled_alerts(is_roaming)
        if (alert_value not in enabled_alerts) and is_enabled:
            enabled_alerts.append(alert_value)
        elif (alert_value in enabled_alerts) and (not is_enabled):
            enabled_alerts.remove(alert_value)

        self.client.set_list(conf_path, gconf.VALUE_INT, enabled_alerts)
        self.__sync_config()

    @imsi_required
    def get_imsi_based_enabled_alerts(self, imsi, is_roaming):
        if not is_roaming:
            conf_path = '%s/imsi/%s/enabled_alerts' % (self.gconf_path, imsi)
        else:
            conf_path = '%s/imsi/%s/enabled_roaming_alerts' % (self.gconf_path, imsi)

        value = self.client.get_without_default(conf_path)
        if value is None:
            default_value = self.get_default_enabled_alerts(is_roaming)
            self.client.set_list(conf_path, gconf.VALUE_INT, default_value)
            self.__sync_config()

        return self.client.get_list(conf_path, gconf.VALUE_INT)

    @imsi_required
    def enable_imsi_based_alert(self, imsi, alert_value, is_enabled, is_roaming):
        # Check the value is an integer
        if type(alert_value) is not IntType:
            raise TypeError('Monthly limits must be integers')

        alerts = self.get_alerts(is_roaming)
        if alert_value not in alerts:
            raise AttributeError('Alert value not in alerts')

        if not is_roaming:
            conf_path = '%s/imsi/%s/enabled_alerts' % (self.gconf_path, imsi)
        else:
            conf_path = '%s/imsi/%s/enabled_roaming_alerts' % (self.gconf_path, imsi)

        enabled_alerts = self.get_imsi_based_enabled_alerts(imsi, is_roaming)

        changed = False
        if (alert_value not in enabled_alerts) and is_enabled:
            enabled_alerts.append(alert_value)
            changed = True
        elif (alert_value in enabled_alerts) and (not is_enabled):
            enabled_alerts.remove(alert_value)
            changed = True

        if changed:
            self.client.set_list(conf_path, gconf.VALUE_INT, enabled_alerts)
            self.__sync_config()
            self.emit('alerts-info-changed')

    #rss on connect
    def get_rss_on_connect(self):
        return self.client.get_bool ("%s/rss_on_connect" % self.gconf_path)

    def set_rss_on_connect(self, value):
        if value == None:
            value = ""
        self.client.set_bool("%s/rss_on_connect" % self.gconf_path, value)
        self.__sync_config()

    #re_connect
    def get_reconnect_on_disconnect(self):
        return self.client.get_bool ("%s/reconnect_on_disconnect" % self.gconf_path)

    def set_reconnect_on_disconnect(self, value):
        if value == None:
            value = ""
        self.client.set_bool("%s/reconnect_on_disconnect" % self.gconf_path, value)
        self.__sync_config()

    # IMSI preferred

    def is_last_imsi_seen_valid(self):
        imsi = self.get_last_imsi_seen()
        return (imsi is not None) and (len(imsi) > 0)

    def get_last_imsi_seen(self):
        return self.client.get_string("%s/last_imsi_seen" % self.gconf_path)

    def set_last_imsi_seen(self, imsi):
        self.client.set_string("%s/last_imsi_seen" % self.gconf_path, imsi)
        self.__sync_config()
        self.emit ('last-imsi-seen-changed', imsi)

    @imsi_required
    def is_first_time_imsi(self, imsi):
        conf_path = '%s/imsi/%s/is_first_time' % (self.gconf_path, imsi)

        value = self.client.get_without_default(conf_path)
        if value is None:
            self.client.set_bool(conf_path, True)
            self.__sync_config()

        return self.client.get_bool(conf_path)

    @imsi_required
    def set_is_first_time_imsi(self, imsi, value):
        if type(value) is not BooleanType:
            raise TypeError('Value must be boolean')

        conf_path = '%s/imsi/%s/is_first_time' % (self.gconf_path, imsi)
        self.client.set_bool(conf_path, value)


    # Prepay section

    def get_prepay_method(self):
        return self.client.get_string('%s/prepay_method' % self.gconf_path)

    def set_prepay_method(self, value):
        self.client.set_string('%s/prepay_method' % self.gconf_path, value)
        self.__sync_config()

    #Dock interface options

    def show_settings_on_toolbar (self):
        if tgcm.country_support == "uk":
            return False
        else:
            return True

    def show_help_on_toolbar (self):
        if tgcm.country_support == "uk":
            return False
        else:
            return True

    def get_traffic_zone_style (self):
        """ Returns 0 if Traffic Zone should show "Data used".
            Returns 1 if Traffic Zone should show "Available data".
        """
        if tgcm.country_support == "uk":
            return 0
        else:
            return 1

    def is_traffic_available(self):
        return self.client.get_bool('%s/traffic_available' % self.gconf_path)

    def set_traffic_available(self, traffic_available):
        self.client.set_bool('%s/traffic_available' % self.gconf_path, traffic_available)
        self.__sync_config()

    def is_alerts_available(self):
        is_alerts_available = self.client.get_bool('%s/alerts_available' % self.gconf_path)
        return self.is_traffic_available() and is_alerts_available

    def set_alerts_available(self, alerts_available):
        self.client.set_bool('%s/alerts_available' % self.gconf_path, alerts_available)
        self.__sync_config()

    def get_company_name (self):
        if tgcm.country_support in ("uk", "cz"):
            return "O2"
        elif tgcm.country_support == "de":
            return "o2"
        else:
            return "Movistar"

    def is_latam (self, country = None):
        if country is None:
            country = tgcm.country_support
        return (country in ("ar", "cl", "co", "ec", "gt", "mx", "ni", "pa", "pe", "sv", "uy", "ve","cr"))

    def is_first_time (self):
        return not self.client.get_bool ("%s/initialized" % self.gconf_path)

    def done_first_time (self):
        self.client.set_bool("%s/initialized" % self.gconf_path, True)


    ## Do not show again dialog options

    def is_dialog_shown(self, dialog_id):
        gconf_key = '%s/dialogs/%s' % (self.gconf_path, dialog_id)

        gconf_value = self.client.get_without_default(gconf_key)
        if gconf_value is None:
            self.client.set_bool(gconf_key, True)
            self.__sync_config()

        return self.client.get_bool(gconf_key)

    def set_is_dialog_shown(self, dialog_id, value):
        self.client.set_bool('%s/dialogs/%s' % (self.gconf_path, dialog_id), value)
        self.__sync_config()

    ## Ads related

    def is_ads_available(self):
        return self.client.get_bool('%s/ads_available' % self.gconf_path)

    def set_ads_available(self, value):
        self.client.set_bool('%s/ads_available' % self.gconf_path, value)
        self.__sync_config()

    def get_ads_url(self, url_id):
        if url_id == 'main':
            conf_path = '%s/ads/main_url' % self.gconf_path
        elif url_id == 'service':
            conf_path = '%s/ads/service_url' % self.gconf_path
        else:
            return

        return self.client.get_string(conf_path)

    def add_ads_url(self, url_id, url):
        if url_id == 'main':
            conf_path = '%s/ads/main_url' % self.gconf_path
        elif url_id == 'service':
            conf_path = '%s/ads/service_url' % self.gconf_path
        else:
            return

        self.client.set_string(conf_path, url)
        self.__sync_config()

    def is_ads_auth_sdp_available(self):
        return self.client.get_bool('%s/ads/auth_sdp_available' % self.gconf_path)

    def set_ads_auth_sdp_available(self, value):
        self.client.set_bool('%s/ads/auth_sdp_available' % self.gconf_path, value)
        self.__sync_config()

    def get_ads_service_id(self):
        return self.client.get_string('%s/ads/service-id' % self.gconf_path)

    def set_ads_service_id(self, value):
        self.client.set_string('%s/ads/service-id' % self.gconf_path, value)
        self.__sync_config()

    def get_ads_sp_id(self):
        return self.client.get_string('%s/ads/sp-id' % self.gconf_path)

    def set_ads_sp_id(self, value):
        self.client.set_string('%s/ads/sp-id' % self.gconf_path, value)
        self.__sync_config()

    def get_ads_sp_password(self):
        return self.client.get_string('%s/ads/sp-password' % self.gconf_path)

    def set_ads_sp_password(self, value):
        self.client.set_string('%s/ads/sp-password' % self.gconf_path, value)
        self.__sync_config()

    def get_ads_ui(self):
        gconf_key = '%s/ads/ui' % self.gconf_path
        value = self.client.get_without_default(gconf_key)
        if value is None:
            country_code = str(int(self.get_country_code()))
            now = datetime.datetime.now().strftime('%H%M%S')
            foo = ''.join(random.choice(string.ascii_uppercase + string.digits) \
                    for x in range(6))

            value = country_code + now + foo

            self.client.set_string(gconf_key, value)
            self.__sync_config()
        else:
            value = value.get_string()
        return value

    def __check_init_values (self):
        if not self.client.dir_exists (self.gconf_path):
            key = '%s/%s' % (self.gconf_path, 'app_name')
            self.client.set_string(key, 'Escritorio movistar')
            key = '%s/%s' % (self.gconf_path, 'version')
            self.client.set_string(key, '7.0')
            key = '%s/%s' % (self.gconf_path, 'release_date')
            self.client.set_string(key, Constants.TGCM_BUILD_DATE())
            key = '%s/%s' % (self.gconf_path, 'initialized')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'connect_on_startup')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'addressbook/phone_match')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'addressbook/phone_format')
            self.client.set_list (key, gconf.VALUE_INT, [])
            key = '%s/%s' % (self.gconf_path, 'connections_general/ask_before_connect_to_action')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'connections_general/ask_before_change_connection')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'connections_general/ask_before_connect')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'user_id')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'user_connection_prepaid')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'user_phone')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'security/auth_on')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'security/celular_number')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'security/celular_password')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'security/ask_password')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'devices/selected')
            self.client.set_int(key, 4)
            key = '%s/%s' % (self.gconf_path, 'expenses/sms_sent')
            self.client.set_int(key, 0)
            key = '%s/%s' % (self.gconf_path, 'expenses/show_mb_warning')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'expenses/show_mb_warning_roaming')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'expenses/show_percent_warning')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'expenses/warning_mb')
            self.client.set_int(key, 200)
            key = '%s/%s' % (self.gconf_path, 'expenses/warning_mb_roaming')
            self.client.set_int(key, 10)
            key = '%s/%s' % (self.gconf_path, 'expenses/warning_mb_combo')
            self.client.set_int(key, 0)
            key = '%s/%s' % (self.gconf_path, 'expenses/warning_percent')
            self.client.set_int(key, 80)
            key = '%s/%s' % (self.gconf_path, 'actions_general/actions_order')
            self.client.set_list (key, gconf.VALUE_STRING, [])
            key = '%s/%s' % (self.gconf_path, 'actions_general/original_actions_order')
            self.client.set_list (key, gconf.VALUE_STRING, [])
            key = '%s/%s' % (self.gconf_path, 'actions_general/original_services_order')
            self.client.set_list (key, gconf.VALUE_STRING, [])
            key = '%s/%s' % (self.gconf_path, 'ui_general/main_expander_on')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'ui_general/welcome_warning_show')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'ui_general/show_new_bookmark_confirmation')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'ui_general/systray_showing_mw')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'selfcare_url')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'support_url')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'help_phone')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'wifi_url')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'wwan_url')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'updater_feed_date')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'country_code')
            self.client.set_string(key, '+34')
            key = '%s/%s' % (self.gconf_path, 'region')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'rss_on_connect')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/name')
            if tgcm.country_support != "uk" :
                self.client.set_string(key, _('SMS'))
            else:
                self.client.set_string(key, _('Text'))
            key = '%s/%s' % (self.gconf_path, 'actions/sms/id')
            self.client.set_string(key, 'MSDASendSMS')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/tooltip')
            self.client.set_string(key, 'Envía mensajes de texto')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/url')
            self.client.set_string(key, 'http://www.mensajeriaweb.movistar.es')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/special_number')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/smsc_any')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/smsc_prepay')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/smsc_postpay')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/smsc_sim')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/connection')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/connection_mandatory')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/conversations_show_received')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/conversations_show_sended')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/notifications_available')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/notifications_gsm7_method')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/notifications_gsm7_prefix')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/notifications_ucs2_method')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/notifications_ucs2_prefix')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/sending_notifications')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/last_notifications_state')
            if tgcm.country_support != "uk" :
                self.client.set_bool(key, True)
            else:
                self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/editable_smsc')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/use_custom_smsc')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/custom_smsc')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/sms/popup_sms_available')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/sms/popup_sms_numbers')
            self.client.set_list (key, gconf.VALUE_STRING, [])
            key = '%s/%s' % (self.gconf_path, 'actions/internet/name')
            self.client.set_string(key, _('Internet'))
            key = '%s/%s' % (self.gconf_path, 'actions/internet/id')
            self.client.set_string(key, 'MSDAInternet')
            key = '%s/%s' % (self.gconf_path, 'actions/internet/tooltip')
            self.client.set_string(key, 'Accede a Internet desde el Escritorio movistar')
            key = '%s/%s' % (self.gconf_path, 'actions/internet/open_browser_by_default')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'actions/internet/url')
            self.client.set_string(key, 'http://www.movistar.es')
            key = '%s/%s' % (self.gconf_path, 'actions/internet/connection')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/internet/connection_mandatory')
            self.client.set_bool(key, True)
            key = '%s/%s' % (self.gconf_path, 'actions/intranet/name')
            if tgcm.country_support == "cz" :
                self.client.set_string(key, 'Firemní VPN')
            else:
                self.client.set_string(key, _(u'Intranet'))
            key = '%s/%s' % (self.gconf_path, 'actions/intranet/id')
            self.client.set_string(key, 'MSDAIntranet')
            key = '%s/%s' % (self.gconf_path, 'actions/intranet/tooltip')
            self.client.set_string(key, 'Accede a la intranet de tu empresa')
            key = '%s/%s' % (self.gconf_path, 'actions/intranet/open_browser_by_default')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/intranet/url')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/intranet/connection')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/intranet/connection_mandatory')
            self.client.set_bool(key, True)

            if tgcm.country_support == "cz" :
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/name')
                self.client.set_string(key, 'Dobijení kreditu')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/id')
                self.client.set_string(key, 'CZRecharge')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/tooltip')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/open_browser_by_default')
                self.client.set_bool(key, False)
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/url')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/connection')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/connection_mandatory')
                self.client.set_bool(key, False)
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/ussd_recharge')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/ussd_check')
                self.client.set_string(key, '')

                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/name')
                self.client.set_string(key, _(u'Selfcare'))
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/id')
                self.client.set_string(key, 'CZSelfcare')
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/tooltip')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/open_browser_by_default')
                self.client.set_bool(key, False)
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/url')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/connection')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/connection_mandatory')
                self.client.set_bool(key, False)
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/selfcare_url')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/selfcare/apn_list')
                self.client.set_list(key, gconf.VALUE_STRING, [])

            if tgcm.country_support == "de" :
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/name')
                self.client.set_string(key, _('o2Credit'))
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/id')
                self.client.set_string(key, 'DERecharge')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/tooltip')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/open_browser_by_default')
                self.client.set_bool(key, False)
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/url')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/connection')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/connection_mandatory')
                self.client.set_bool(key, False)
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/ussd_recharge')
                self.client.set_string(key, '')
                key = '%s/%s' % (self.gconf_path, 'actions/prepay/ussd_check')
                self.client.set_string(key, '')

            key = '%s/%s' % (self.gconf_path, 'actions/favorites/name')
            self.client.set_string(key, 'Favourites')
            key = '%s/%s' % (self.gconf_path, 'actions/favorites/id')
            self.client.set_string(key, 'MSDABookmarks')
            key = '%s/%s' % (self.gconf_path, 'actions/favorites/tooltip')
            self.client.set_string(key, 'Bla bla bla')
            key = '%s/%s' % (self.gconf_path, 'actions/favorites/open_browser_by_default')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/favorites/url')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/favorites/connection')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/favorites/connection_mandatory')
            self.client.set_bool(key, False)

            # -- This seems to be the wifi service name, or?
            key = '%s/%s' % (self.gconf_path, 'actions/wifi/name')
            if tgcm.country_support == "uk" :
                self.client.set_string(key, _('Find Hotspots'))
            elif self.is_latam():
                self.client.set_string(key, _("Wi-Fi areas"))
            else:
                self.client.set_string(key, _("Wi-Fi Zone"))

            key = '%s/%s' % (self.gconf_path, 'actions/wifi/id')
            self.client.set_string(key, 'MSDAMovilidad')
            key = '%s/%s' % (self.gconf_path, 'actions/wifi/tooltip')
            self.client.set_string(key, 'Gestiona el acceso a la Zona Wi-Fi de tu Tarifa Banda Ancha Móvil con Wi-Fi')
            key = '%s/%s' % (self.gconf_path, 'actions/wifi/open_browser_by_default')
            self.client.set_bool(key, False)
            key = '%s/%s' % (self.gconf_path, 'actions/wifi/url')
            self.client.set_string(key, 'http://www.correomovil.movistar.es')
            key = '%s/%s' % (self.gconf_path, 'actions/wifi/connection')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/wifi/ussd')
            self.client.set_string(key, '')
            key = '%s/%s' % (self.gconf_path, 'actions/wifi/connection_mandatory')
            self.client.set_bool(key, False)

    def __update_from_8_to_9(self):
        if self.client.dir_exists (self.gconf_path):
            v=self.get_version()
            if (v == '8.8'):
                os.remove(os.path.join(tgcm.config_dir, 'regional-info.%s.xml' % tgcm.country_support))
                self.client.recursive_unset(self.gconf_path, gconf.UNSET_INCLUDING_SCHEMA_NAMES)
                self.client.suggest_sync()



gobject.type_register(Config)
