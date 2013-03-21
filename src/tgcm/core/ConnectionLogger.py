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

import platform
import time
import dbus
import multiprocessing
import subprocess

import tgcm
import Config
import Singleton

from Constants import TGCM_DEVELOPMENT_REVISION
from DeviceManager import DEVICE_MODEM, DEVICE_WLAN, DEVICE_WIRED

TGCM_LOG_BUS_NAME = 'es.indra.TgcmLogging'
TGCM_LOG_OBJ_PATH = '/es/indra/TgcmLogging'
TGCM_LOG_IFACE = 'es.indra.TgcmLogging'


class ConnectionLogger(object):
    __metaclass__ = Singleton.Singleton

    def __init__(self):
        self._conf = Config.Config(tgcm.country_support)
        self._bus = dbus.SystemBus()

        # Attempt to connect to a hypothetical existing TGCM
        # logging service. That must fail because that service
        # must be executed by TGCM exclusively
        try:
            self.__attempt_connection_logging_service()

            # There is an existing TGCM logging service in the
            # system, so it must be closed
            tgcm.warning('Existing TGCM Logging Service found!')
            self.__call_exit()
        except dbus.exceptions.DBusException:
            # It's not necessary to do nothing because that is the
            # expected behavior
            pass

        # Start the TGCM logging service and attempt to connect
        # to it
        try:
            self.__start_tgcm_logging_service()
            self.__attempt_connection_logging_service()
            self.__configure_connection_log()
        except OSError, err:
            tgcm.error('Could not execute TGCM Logging Service: %s' % err)
        except dbus.exceptions.DBusException, err:
            tgcm.error('Could not connect to TGCM Logging Service_ %s' % err)

    def __attempt_connection_logging_service(self):
        self._service = self._bus.get_object(TGCM_LOG_BUS_NAME, TGCM_LOG_OBJ_PATH)

        # Get a reference to some TGCM Logging service methods
        self.__log_lines = self._service.get_dbus_method('LogLines')
        self.__reset_log = self._service.get_dbus_method('ResetLog')
        self.__call_exit = self._service.get_dbus_method('CallExit')

    def __start_tgcm_logging_service(self):
        tgcm.debug('Attempting to start TGCM Logging service')

        command = ['tgcm-logging']
        command.append('-c')
        command.append(tgcm.country_support)
        self._logging_desc = subprocess.Popen(command)

        # Wait a little to give a change to TGCM Logger to
        # create its D-Bus services
        time.sleep(1)

    def __configure_connection_log(self):
        # Reset line number count, every time the connection log starts
        # it begins with the line number 1
        self.__reset_log()

        # Log header must be printed every time the log is enabled
        self.register_tgcm_log_init()

    def quit(self):
        self.__call_exit()

    def register_tgcm_log_init(self):
        '''
        The header is printed every time the logging system is enabled. E.g.:

        00000001 | 2012-may-09 10:06:48.580707 | Escritorio Movistar 8.8.development
        00000002 | 2012-may-09 10:06:48.580830 | Ubuntu 12.04 (i686)
        00000003 | 2012-may-09 10:06:48.580859 | i686, 4 CPU(s)
        '''
        entries = []

        app_name = self._conf.get_app_name()
        app_version = self._conf.get_version()
        build_rev = TGCM_DEVELOPMENT_REVISION()
        entries.append('%s %s.%s' % (app_name, app_version, build_rev))

        dist_info = platform.linux_distribution()
        arch_type = platform.processor()
        entries.append('%s %s (%s)' % (dist_info[0], dist_info[1], arch_type))

        num_cores = multiprocessing.cpu_count()
        entries.append('%s, %d CPU(s)' % (arch_type, num_cores))

        self.__write_lines(entries)

    def register_new_device(self, device):
        '''
        This is printed every time a device appears in the system.

        E.g. Wi-Fi devices:
        00000007 | 2012-May-10 11:38:58.140000 | WiFi device name: Intel(R) PRO/Wireless 3945ABG Network Connection - Minipuerto del administrador de paquetes
        00000008 | 2012-May-10 11:38:58.140000 | WiFi device physical address: 00:13:02:52:D6:54

        E.g. WWAN devices:
        00000009 | 2012-May-10 11:39:39.640000 | WWAN device model: MF190
        00000010 | 2012-May-10 11:39:39.640000 | WWAN device manufacturer: ZTE CORPORATION
        00000011 | 2012-May-10 11:39:39.640000 | WWAN device revision: MF190V1.0.0B05
        00000012 | 2012-May-10 11:39:39.640000 | WWAN device IMEI: 359728030008422
        00000013 | 2012-May-10 11:39:39.640000 | WWAN device IMSI: 214075527144750
        00000014 | 2012-May-10 11:39:39.640000 | WWAN device ICC: 2100218363144
        '''
        entries = []
        device_type = device.get_type()
        driver = device.nm_dev['Driver']
        interface = device.nm_dev['Interface']
        if device_type == DEVICE_MODEM:
            device_info = device.device_info()
            if device_info is not None:
                entries.append('WWAN device found: %s (%s)' % (interface, driver))
                entries.append('WWAN device model: %s' % device_info['model'])
                entries.append('WWAN device manufacturer: %s' % device_info['manufacturer'])
                entries.append('WWAN device revision: %s' % device_info['firmware'])
                entries.append('WWAN device IMEI: %s' % device.get_IMEI())
                entries.append('WWAN device IMSI: %s' % device.get_imsi())
                entries.append('WWAN device ICC: %s' % device.get_ICCID())
        elif device_type == DEVICE_WLAN:
            entries.append('WiFi device found: %s (%s)' % (interface, driver))
        elif device_type == DEVICE_WIRED:
            entries.append('Ethernet device found: %s (%s)' % (interface, driver))
        self.__write_lines(entries)

    def register_remove_device(self, device):
        '''
        This is printed every time a device is removed in the system.

        E.g. Wi-Fi devices:
        00000010 | 2012-May-10 11:39:39.640000 | WiFi device removed

        E.g. WWAN devices:
        00000010 | 2012-May-10 11:39:39.640000 | WWAN device removed
        '''
        entries = []
        entries.append('WWAN device removed')
        self.__write_lines(entries)

    def register_wwan_carrier_change(self, carrier):
        '''
        This is printed every time the WWAN carrier change.

        E.g.:
        00000015 | 2012-May-10 11:39:41.609000 | WWAN operator: movistar
        '''
        if len(carrier) == 0:
            return

        entries = []
        entries.append('WWAN operator: %s' % carrier)
        self.__write_lines(entries)

    def register_wwan_signal_change(self, signal):
        '''
        This is printed every time the signal strength is updated.

        E.g.:
        00000016 | 2012-May-10 11:39:41.625000 | WWAN signal strength: -63 dBm
        '''
        entries = []
        entries.append('WWAN signal strength: %d%%' % signal)
        self.__write_lines(entries)

    def register_wwan_technology_change(self, technology):
        '''
        This is printed every time the connection technology is updated.

        E.g.:
        00000017 | 2012-May-10 11:39:41.625000 | WWAN network technology: 3G
        '''
        if len(technology) == 0:
            return

        entries = []
        entries.append('WWAN network technology: %s' % technology)
        self.__write_lines(entries)

    def register_connection_attempt(self, conn_settings):
        '''
        This is printed every time a it happens a connection attempt

        E.g. WWAN networks:
        00000024 | 2012-May-10 11:42:43.156000 | Connecting to 'Movistar Internet'
        00000025 | 2012-May-10 11:42:43.156000 | Type: WWAN
        00000026 | 2012-May-10 11:42:43.156000 | APN: movistar.es
        00000027 | 2012-May-10 11:42:43.156000 | Username: MOVISTAR
        00000028 | 2012-May-10 11:42:43.156000 | DNS assigned by the network
        00000029 | 2012-May-10 11:42:43.156000 | No proxy

        E.g. Wi-Fi networks:
        00000044 | 2012-May-10 11:44:28.765000 | Connecting to 'INVITADOS'
        00000045 | 2012-May-10 11:44:28.765000 | Type: WiFi
        00000046 | 2012-May-10 11:44:28.765000 | SSID: INVITADOS
        '''
        entries = []
        name = conn_settings['name']
        entries.append('Connecting to \'%s\'' % name)

        device_type = conn_settings['deviceType']
        if device_type == DEVICE_MODEM:
            entries.append('Type: WWAN')
            entries.append('APN: %s' % conn_settings['apn'])
            entries.append('Username: "%s"' % conn_settings['username'])
        elif device_type == DEVICE_WLAN:
            ssid = conn_settings['ssid']
            entries.append('Type: WiFi')
            entries.append('SSID: %s' % ssid)
        elif device_type == DEVICE_WIRED:
            entries.append('Type: Ethernet')

        # DNS info section
        is_auto_dns = conn_settings['auto_dns']
        if is_auto_dns:
            entries.append('DNS assigned by the network')
        else:
            dns_servers = conn_settings['dns_servers']
            if len(dns_servers) > 0:
                entries.append('Primary DNS: %s' % dns_servers[0])
            if len(dns_servers) > 1:
                entries.append('Secondary DNS: %s' % dns_servers[1])

        # Proxy info section
        is_proxy = conn_settings['proxy']
        if not is_proxy:
            entries.append('No proxy')
        else:
            is_same_proxy = conn_settings['proxy_same_proxy']
            http_ip = conn_settings['proxy_ip']
            http_port = conn_settings['proxy_port']
            if is_same_proxy:
                entries.append('Proxy: %s:%s' % (http_ip, http_port))
            else:
                https_ip = conn_settings['proxy_https_ip']
                https_port = conn_settings['proxy_https_port']
                ftp_ip = conn_settings['proxy_ftp_ip']
                ftp_port = conn_settings['proxy_ftp_port']
                socks_ip = conn_settings['proxy_socks_ip']
                socks_port = conn_settings['proxy_socks_port']
                entries.append('Proxy: ftp=%s:%s;http=%s:%s;https=%s:%s;socks=%s:%s' % \
                        (ftp_ip, ftp_port, http_ip, http_port, https_ip, \
                         https_port, socks_ip, socks_port))

        self.__write_lines(entries)

    def register_connecting_event(self, conn_settings):
        '''
        This is printed every time the system is connecting to a network.

        '''
        entries = []
        device_type = conn_settings['deviceType']
        if device_type == DEVICE_MODEM:
            entries.append('Establishing WWAN connection')
            entries.append('WWAN connection authenticating')
        elif device_type == DEVICE_WLAN:
            entries.append('Establishing WiFi connection')
            entries.append('Negotiating IP address...')
        elif device_type == DEVICE_WIRED:
            entries.append('Establishing Ethernet connection')
            entries.append('Negotiating IP address...')

        self.__write_lines(entries)

    def register_connected_event(self, conn_settings):
        '''
        This is printed every time the system is connected to a network.

        E.g.:
        00000036 | 2012-may-16 13:04:30.929972 | Ethernet connection established
        '''
        entries = []
        device_type = conn_settings['deviceType']
        if device_type == DEVICE_MODEM:
            entries.append('WWAN connection established')
        elif device_type == DEVICE_WLAN:
            entries.append('WiFi connection established')
        elif device_type == DEVICE_WIRED:
            entries.append('Ethernet connection established')

        self.__write_lines(entries)

    def register_cancel(self, conn_settings):
        pass

    def register_invalid_imsi(self):
        entries = []
        entries.append('WWAN device does not have a valid SIM card')
        self.__write_lines(entries)

    def register_disconnection_attempt(self, conn_settings=None):
        entries = []
        if conn_settings is not None:
            device_type = conn_settings['deviceType']
            if device_type == DEVICE_MODEM:
                entries.append('WWAN user disconnection')
            elif device_type == DEVICE_WLAN:
                entries.append('WiFi user disconnection')
            elif device_type == DEVICE_WIRED:
                entries.append('Ethernet user disconnection')
        else:
            entries.append('User disconnection')

        self.__write_lines(entries)

    def register_disconnection_event(self, conn_settings=None):
        entries = []
        if conn_settings is not None:
            device_type = conn_settings['deviceType']
            if device_type == DEVICE_MODEM:
                entries.append('WWAN connection dropped')
            elif device_type == DEVICE_WLAN:
                entries.append('WiFi connection dropped')
            elif device_type == DEVICE_WIRED:
                entries.append('Ethernet connection dropped')
        else:
            entries.append('Connection dropped')

        self.__write_lines(entries)

    def __write_lines(self, entries):
        # If the log is not enabled just do nothing
        if not self._conf.is_connection_log_enabled():
            return

        try:
            self.__log_lines(entries)
        except Exception, err:
            print err

    ## Configuration settings change callbacks

    def __on_log_enable_changed(self, sender, value):
        # Reconfigure connection log
        self.__configure_connection_log()
