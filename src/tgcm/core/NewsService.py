#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
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
import pickle
import gobject
import time
import feedparser
import tempfile
from datetime import datetime
from xml.etree import ElementTree

import tgcm
import Config
import ConnectionManager
import DownloadHelper
import FreeDesktop
import MainModem
import HotSpotsService
import Importer
import Singleton


def sort_entry_func(x, y):
    if x["updated_parsed"] == y["updated_parsed"] :
        return 0
    else:
        if x["updated_parsed"] > y["updated_parsed"] :
            return -1
        else:
            return 1

UNKNOWN = 0
APP_START = 1
APP_CONNECTED = 2
ITEM_UPDATED = 3
DEVICE_CHANGED = 4
DEVICE_REMOVED = 5


class NewsService (gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'news-updated' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, )),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.conf = Config.Config(tgcm.country_support)
        self.modem_manager = MainModem.MainModem()
        self.conn_manager = ConnectionManager.ConnectionManager()
        self.device_dialer = FreeDesktop.DeviceDialer()
        self.importer = Importer.Importer()
        self.hs_service = HotSpotsService.HotSpotsService()

        self.install_callback = None
        self.refresh_callback = None

        if not self.conf.is_news_available() :
            return

        # Load news and updates database
        self.db_name = 'news-%s.db' % tgcm.country_support
        self.db_filepath = os.path.join(tgcm.config_dir, self.db_name)
        if os.path.exists(self.db_filepath):
            db_file = open(self.db_filepath, 'r')
            self.db_contents = pickle.load(db_file)
            db_file.close()
        else:
            self.db_contents = {}
            self.db_contents['news'] = {}
            self.db_contents['updates'] = {}

        self.__update_rss_db_if_possible(APP_START)
        self.device_dialer.connect("connected", self.__connected_cb)
        self.modem_manager.connect('main-modem-changed', self.__main_modem_changed_cb)
        self.modem_manager.connect('main-modem-removed', self.__main_modem_removed_cb)

    def refresh_async(self, reason=UNKNOWN, callback=None):
        self.refresh_callback = callback

        update_url = self.conf.get_updater_feed_url()
        tgcm.debug('Attempting to download RSS "%s"' % update_url)

        download_helper = DownloadHelper.DownloadHelper2(update_url)
        download_helper.read_async(self.__rss_success_callback, success_param=reason)

    def __rss_success_callback(self, rss_data, reason=None):
        if rss_data is None:
            tgcm.debug('Error: empty RSS data!')
            self.__call_refresh_callback_if_possible()
            return

        # Attempt to parse RSS data
        f = feedparser.parse(rss_data)
        if f.bozo:
            tgcm.debug('Error parsing RSS data: %s' % f.bozo_exception)
            self.__call_refresh_callback_if_possible()
            return

        # Get the time when the RSS feed was updated for the last time
        if 'updated_parsed' not in f['feed']:
            last_update = None
            for rss_entry in f['entries']:
                entry_last_update = rss_entry['updated_parsed']
                if (last_update is None) or (last_update < entry_last_update):
                    last_update = entry_last_update

            f['feed']['updated_parsed'] = last_update

        # Check if this RSS feed has been already parsed
        if ('updated_parsed' in self.db_contents) and \
                (self.db_contents['updated_parsed'] == f['feed']['updated_parsed']):
            tgcm.debug("Refreshed RSS, not necessary")
            self.__call_refresh_callback_if_possible()
            return

        # Is this RSS feed empty?
        if len(f['entries']) == 0:
            tgcm.debug("Refreshed RSS, not necessary (no entries)")
            self.__call_refresh_callback_if_possible()
            return

        # Manually parse XML for some non-standard RSS elements
        items_with_device_node = {}
        root = ElementTree.fromstring(rss_data)
        for item in root.iterfind('.//device/../..'):
            guid = item.find('guid').text
            items_with_device_node[guid] = item

        # Process every entry found in the RSS feed
        tgcm.debug("Release date %s" % self.conf.get_release_date())
        release_date = time.strptime(self.conf.get_release_date(), "%Y-%m-%d %H:%M:%S")
        emit_signal = False
        for entry in f['entries']:
            # This is a very ugly hack, but python-feedparser is not able to
            # deal with our non-standard RSS feed (it's our fault).
            entry['devices'] = []
            guid = entry['guid']
            if guid in items_with_device_node:
                self.__process_device_info(entry, items_with_device_node[guid])

            if entry['updated_parsed'] > release_date:
                emit_signal = True
            self.__save_entry(entry)

        self.db_contents['updated_parsed'] = f['feed']['updated_parsed']
        self.__save()

        tgcm.debug("Refreshed RSS")
        self.__call_refresh_callback_if_possible()

        if emit_signal:
            self.emit("news-updated", reason)

    def __call_refresh_callback_if_possible(self):
        if self.refresh_callback:
            self.refresh_callback()
            self.refresh_callback = None

    def __process_device_info(self, entry, root_node):
        for device_node in root_node.iterfind('*/device'):
            device_dict = {}
            for tag in ('vendor', 'model', 'firmware'):
                tag_node = device_node.find(tag)
                if tag_node is not None:
                    device_dict[tag] = tag_node.text
            entry['devices'].append(device_dict)

    def __save_entry(self, entry):
        # Some metadata common to all new entries
        entry['unseen'] = True
        entry['unread'] = True
        entry['not_installed'] = True

        # Check entry type and store it in the corresponding database
        is_news = True
        if entry.has_key('tags') and (len(entry['tags']) > 0) and \
                entry['tags'][0].has_key('term'):
            entry_term = entry['tags'][0]['term']

            if entry_term in ('update-hotspots', 'update-favorites', \
                    'update-connections'):
                is_news = False

        entry_id = entry['id']
        if is_news:
            database = self.db_contents['news']
        else:
            database = self.db_contents['updates']

        # Only store the current entry if it wasn't saved before
        if not entry_id in database:
            database[entry_id] = entry

    def __save(self):
        # Use pickle to store the dictionaries
        db_file = open(self.db_filepath, 'wb')
        pickle.dump(self.db_contents, db_file)
        db_file.close()

    def get_news(self):
        entries = self.db_contents['news']
        return [x for x in entries.values() if self.__is_applicable(x)]

    def get_updates(self):
        entries = self.db_contents['updates']
        return [x for x in entries.values() if self.__is_applicable(x)]

    def __is_applicable(self, entry):
        # Check TGCM version
        if ('from' in entry) and ('to' in entry):
            current_v = float(self.conf.get_version().strip())
            from_v = float(entry['from'].strip())
            to_v = float(entry['to'].strip())

            # Don't show the entry if the version of TGCM is not among the
            # lower and upper limit
            if (current_v < from_v) or (to_v < current_v):
                return False

        # Publication date
        entry_datetime = datetime.fromtimestamp(time.mktime(entry['updated_parsed']))
        release_datetime = self.conf.get_release_datetime()
        if entry_datetime < release_datetime:
            return False

        # Check user contract type:
        # - A value of '1' means the message only applies to prepay users
        # - A value of '2' means the message only applies to postpaid users
        if 'usercontract' in entry:
            is_entry_prepay = entry['usercontract'] == '1'
            if not self.conf.is_last_imsi_seen_valid():
                is_prepay = self.conf.is_default_prepaid()
            else:
                imsi = self.conf.get_last_imsi_seen()
                is_prepay = self.conf.is_imsi_based_prepaid(imsi)

            # Don't show the entry if the user type destination of the entry
            # does not correspond to the type of the current IMSI
            if is_prepay != is_entry_prepay:
                return False

        # Check device-related entry
        if ('devices' in entry) and (len(entry['devices']) > 0):
            main_modem = self.modem_manager.current_device()

            # Don't show a device-related entry if a WWAN device is not
            # available in the system
            if main_modem is None:
                return False

            modem_device_info = main_modem.device_info()
            device_info = {}
            device_info['model'] = str(modem_device_info['model']).lower()
            device_info['firmware'] = str(modem_device_info['firmware']).lower()
            device_info['vendor'] = str(modem_device_info['manufacturer']).lower()

            is_applicable = False
            for device_entry in entry['devices']:
                device_entry_applies = True
                for tag in ('model', 'firmware', 'vendor'):
                    if tag in device_entry:
                        if device_info[tag].lower() != device_entry[tag].lower():
                            device_entry_applies = False
                            break
                is_applicable = is_applicable or device_entry_applies

            if not is_applicable:
                return False

        return True

    def mark_as_read(self, entry_id):
        entry = self.__get_item(entry_id)
        if entry is not None:
            entry['unseen'] = False
            entry['unread'] = False
            self.__save()

    def mark_as_seen(self, entry_id):
        entry = self.__get_item(entry_id)
        if entry is not None:
            entry['unseen'] = False
            self.__save()

    def mark_as_installed(self, entry_id):
        entry = self.__get_item(entry_id)
        if entry is not None:
            entry['not_installed'] = False
            self.__save()
            self.emit('news-updated', ITEM_UPDATED)

    def install_async(self, entry_id, callback):
        self.install_callback = callback
        item_to_install = self.__get_item(entry_id)
        if item_to_install is not None:
            url = item_to_install['link']

            tgcm.debug('Download item from %s' % url)
            download_helper = DownloadHelper.DownloadHelper2(url)
            download_helper.read_async(self.__install_item_success_hook, \
                    success_param=item_to_install)

    def __install_item_success_hook(self, entry_data, item_to_install):
        if entry_data is None:
            tgcm.debug('Error: empty item data!')
            self.__call_install_callback_if_possible(False)
            return False

        tgcm.debug('Item download successful')

        tmp_file = tempfile.NamedTemporaryFile()
        tmp_file.write(entry_data)
        tmp_file.seek(0)

        entry_tag = item_to_install['tags'][0]['term']
        is_success = False
        if entry_tag == 'update-hotspots':
            is_success = self.hs_service.register_new_hotspot_file(tmp_file.name)
        else:
            is_success = self.importer.update_bookmarks_and_connections_from_file (tmp_file.name)

        tmp_file.close()

        if is_success:
            self.mark_as_installed(item_to_install['id'])

        self.__call_install_callback_if_possible(is_success)

        return False

    def __call_install_callback_if_possible(self, is_success):
        if self.install_callback:
            self.install_callback(is_success)
            self.install_callback = None

    def __get_item(self, entry_id):
        for database in self.db_contents.values():
            if entry_id in database:
                entry = database[entry_id]
                return entry
        return None

    def __update_rss_db_if_possible(self, reason):
        # Do not event attempt to update news if we are not connected to
        # a network
        if not self.conn_manager.is_connected():
            return

        self.refresh_async(reason=reason)

    def __connected_cb(self, dialer=None):
        self.__update_rss_db_if_possible(APP_CONNECTED)

        # Emit news updated signal, because it is possible that  we are
        # connected with a new device which has not shown its related news
        # before
        self.emit("news-updated", APP_CONNECTED)

    def __main_modem_changed_cb(self, *args):
        self.emit("news-updated", DEVICE_CHANGED)

    def __main_modem_removed_cb(self, *args):
        self.emit("news-updated", DEVICE_REMOVED)


gobject.type_register(NewsService)
