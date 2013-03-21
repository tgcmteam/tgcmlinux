#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2013, Telefonica Móviles España S.A.U.
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

import datetime
import gobject
import gtk
import md5
import random
import string
import tempfile
import xml.etree.cElementTree as ET

import tgcm
import Config
import DownloadHelper
import FreeDesktop
import Singleton
import Theme


class Advertising(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'updated': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.config = Config.Config()
        theme_manager = Theme.ThemeManager()

        self._static_images = {}
        for url_id in ('main', 'service'):
            image_file = theme_manager.get_icon('ads', 'banner_%s.png' % url_id)
            image = (gtk.gdk.pixbuf_new_from_file(image_file), None)
            self._static_images[url_id] = image

        self._advertising = {}
        self.__load_static_images()

        device_dialer = FreeDesktop.DeviceDialer()
        device_dialer.connect('connected', self.__on_connected_cb)
        device_dialer.connect('disconnected', self.__on_disconnected_cb)

    def __load_static_images(self):
        for url_id in ('main', 'service'):
            image = self._static_images[url_id]
            self._advertising[url_id] = image

    def get_dock_advertising(self):
        return self._advertising['main']

    def get_service_advertising(self):
        return self._advertising['service']

    def refresh(self):
        now = datetime.datetime.now()
        service_id = self.config.get_ads_service_id()
        sp_id = self.config.get_ads_sp_id()
        sp_password = self.config.get_ads_sp_password()
        consumer_key = '%s@%s' % (service_id, sp_id)
        timestamp = now.strftime('%Y%m%d%H%M%S')

        m = md5.new()
        m.update('%s%s%s' % (sp_id, sp_password, timestamp))
        signature = m.hexdigest().upper()

        ui = self.config.get_ads_ui()
        ai = 'rqid0001'

        token = ''.join(random.choice(string.ascii_uppercase + string.digits) \
                for x in range(8))

        header = []
        header.append('SDPBasicAuth realm="SDPAPIs"')
        header.append('consumer_key="%s"' % consumer_key)
        header.append('signature_method="MD5"')
        header.append('signature="%s"' % signature)
        header.append('requestor_type="1"')
        header.append('requestor_id="%s"' % ui)
        header.append('token="%s"' % token)
        header.append('timestamp="%s"' % timestamp)
        header.append('version="0.1"')
        header = ', '.join(header)

        for url_id in ('main', 'service'):
            url = self.config.get_ads_url(url_id)
            url = url.replace('%ui%', ui)
            url = url.replace('%ai%', ai)

            tgcm.debug('Advertising petition (%s): %s, %s' % \
                    (url_id, url, header))
            request = DownloadHelper.DownloadHelper2(url)
            request.add_header('Authorization', header)
            request.read_async(self.__refresh_ads_success_hook, \
                    success_param=url_id)

    def __refresh_ads_success_hook(self, raw_xml, url_id):
        if raw_xml is None:
            return

        tgcm.debug('Advertising petition (%s) successful' % url_id)

        try:
            image_url, ad_url = self.__process_advertising_xml(raw_xml)
            ad_info = (url_id, image_url, ad_url)
            tgcm.debug('Download advertising image (%s): %s' % \
                    (url_id, image_url))

            request = DownloadHelper.DownloadHelper2(image_url)
            request.read_async(self.__download_ad_success_hook, \
                    success_param=ad_info)
        except ET.ParseError, err:
            tgcm.error('Error parsing advertising XML: %s' % err)
        except Exception, err:
            tgcm.error('Unknown advertising error: %s' % err)

    def __download_ad_success_hook(self, raw_image, ad_info):
        if raw_image is None:
            return

        url_id = ad_info[0]
        ad_url = ad_info[2]
        tgcm.debug('Download advertising image (%s) successful' % url_id)

        tmp_file = tempfile.NamedTemporaryFile()
        tmp_file.write(raw_image)
        tmp_file.seek(0)

        self._advertising[url_id] = \
                (gtk.gdk.pixbuf_new_from_file(tmp_file.name), ad_url)
        tmp_file.close()

        self.emit('updated')

    def __process_advertising_xml(self, raw_xml):
        image_url = None
        url = None
        root = ET.fromstring(raw_xml)

        server_response = root.findall(".//returncode")[0].text
        tgcm.debug("Advertising server response: %s" % server_response)

        image_node = root.findall(".//attribute[@type='locator']")
        if len(image_node) > 0:
            image_url = image_node[0].text

        url_node = root.findall(".//attribute[@type='URL']")
        if len(url_node) > 0:
            url = url_node[0].text

        return image_url, url

    def __on_connected_cb(self, sender):
        self.refresh()

    def __on_disconnected_cb(self, sender):
        self.__load_static_images()
        self.emit('updated')

gobject.type_register(Advertising)
