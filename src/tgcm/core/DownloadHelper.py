#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2012, Telefonica Móviles España S.A.U.
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

import gobject
import libproxy
import threading
import urllib2

import tgcm


class DownloadHelper2(object):
    def __init__(self, url):
        self._data = None
        self._headers = {}
        self._url = str(url)
        self._opener = self.__create_opener()

    def __create_opener(self):
        proxy_factory = libproxy.ProxyFactory()
        proxies = proxy_factory.getProxies(self._url)
        if (len(proxies) > 0) and (proxies[0] != 'direct://'):
            proxy_dict = {'http': proxies[0]}
        else:
            proxy_dict = {}
        handler = urllib2.ProxyHandler(proxy_dict)
        return urllib2.build_opener(handler)

    def add_header(self, key, value):
        self._headers[key] = value

    def read(self, report_callback=None, timeout=15, chunk_size=15):
        self.request = urllib2.Request(self._url, self._data, self._headers)
        response = self._opener.open(self.request, None, timeout)
        return self.__chunk_read(response, chunk_size, report_callback)

    def __chunk_read(self, response, chunk_size=8192, report_hook=None):
        total_size = response.info().getheader('Content-Length')
        if total_size is None:
            chunk_size = None
        else:
            total_size = int(total_size.strip())

        bytes_so_far = 0
        data = None
        while True:
            chunk = response.read(chunk_size)
            bytes_so_far += len(chunk)

            if not chunk:
                break

            if data is None:
                data = chunk
            else:
                data += chunk

            if report_hook:
                report_hook(bytes_so_far, chunk_size, total_size)

        return data

    def read_async(self, success_hook, success_param=None, \
            report_hook=None, timeout=15, chunk_size=15):
        self._report_hook = report_hook
        t = threading.Thread(target=self.__read_async, \
                args=(success_hook, success_param, timeout, chunk_size))
        t.start()

    def __read_async(self, success_hook, success_param, timeout, chunk_size):
        self.request = urllib2.Request(self._url, self._data, self._headers)

        try:
            response = self._opener.open(self.request, None, timeout)
            data = self.__chunk_read(response, \
                    report_hook=self.__async_report_hook)
        except urllib2.URLError as err:
            tgcm.error('Error downloading "%s": %s' % (self._url, err))
            data = None
        except urllib2.HTTPError as err:
            tgcm.error('Error downloading "%s": %s' % (self._url, err))
            data = None
        except Exception as err:
            tgcm.error('Error downloading "%s": %s' % (self._url, err))
            data = None

        gobject.idle_add(success_hook, data, success_param)
        return False

    def __async_report_hook(self, bytes_so_far, chunk_size, total_size):
        if self._report_hook is not None:
            gobject.idle_add(self._report_hook, bytes_so_far, chunk_size, \
                    total_size)
        return False


class DownloadHelperTest(object):
    def run(self):
        download_helper = DownloadHelper2('http://www.google.es')
        download_helper.read_async(self.__success_hook)

    def __success_hook(self, data):
        print 'Called async hook'
        print data

if __name__ == '__main__':
    test = DownloadHelperTest()
    test.run()
