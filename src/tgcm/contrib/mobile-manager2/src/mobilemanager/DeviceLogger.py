#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import thread
import threading
import SimpleXMLRPCServer
import xmlrpclib
import os

from mobilemanager.Logging import debug, info, warning, error

class DeviceLoggerError(Exception):
    pass

def create_xmlrpc_addr(addr, port):
    return "http://" + str(addr) + ":" + str(port)

class XmlRpcDeviceLogger():

    def __init__(self, addr, port):
        server        = SimpleXMLRPCServer.SimpleXMLRPCServer((addr, port), logRequests=False)
        self.__hosts  = { }
        self.__server = server
        self.__addr   = create_xmlrpc_addr(addr, port)

        server.register_introspection_functions()
        server.register_instance(self._Rpcs(self.__hosts))

        # -- Get the repository revision for returning this value with the RPC
        self.__revision = "@TODO"
        
        info("Created new XML-RPC device logger (revision %s)" % self.__revision)

    def start(self, background=True):
        info("Starting XML-RPC device logger (%s)" % self.__addr)
        if background is True:
            thread.start_new_thread(self.__start, ( ))
        else:
            self.__start()

    def __start(self):
        self.__server.serve_forever()

    # -- @XXX: Here we should start a thread for avoiding that one remote host
    # -- blocks further calls

    # -- Call this method for informing about a new detected device
    def device_plugged(self, vid, pid, vendor):
        for url, srv in self.__hosts.items():
            try:
                srv.device_plugged(vid, pid, vendor)
            except xmlrpclib.Fault, err:
                error("Removing XML-RPC server '%s' due error, %s" % (url, err))
                self.__hosts.__delitem__(url)

    def modem_detected(self, vid, pid, ports_nr):
        for url, srv in self.__hosts.items():
            try:
                srv.modem_detected(vid, pid, ports_nr)
            except xmlrpclib.Fault, err:
                error("Removing XML-RPC server '%s' due error, %s" % (url, err))
                self.__hosts.__delitem__(url)

    def modem_ready(self, vid, pid, com_minor, aux_minor, model, revision):
        for url, srv in self.__hosts.items():
            try:
                srv.modem_ready(vid, pid, com_minor, aux_minor, model, revision)
            except xmlrpclib.Fault, err:
                error("Removing XML-RPC server '%s' due error, %s" % (url, err))
                self.__hosts.__delitem__(url)

    def modem_removed(self, vid, pid):
        for url, srv in self.__hosts.items():
            try:
                srv.modem_removed(vid, pid)
            except xmlrpclib.Fault, err:
                error("Removing XML-RPC server '%s' due error, %s" % (url, err))
                self.__hosts.__delitem__(url)

    def modem_failure(self, vid, pid):
        for url, srv in self.__hosts.items():
            try:
                srv.modem_failure(vid, pid)
            except xmlrpclib.Fault, err:
                error("Removing XML-RPC server '%s' due error, %s" % (url, err))
                self.__hosts.__delitem__(url)

    def device_removed(self, vid, pid):
        for url, srv in self.__hosts.items():
            try:
                srv.device_removed(vid, pid)
            except xmlrpclib.Fault, err:
                error("Removing XML-RPC server '%s' due error, %s" % (url, err))
                self.__hosts.__delitem__(url)

    # -- Call this when the processing of an AT command has failed
    def at_error(self, cmd, msg):
        pass

    class _Rpcs():

        def __init__(self, hosts):
            self.__hosts = hosts

        def register(self, url):
            info("Register request for URL %s" % repr(url))
            if type(url) != type(""):
                raise DeviceLoggerError, "register(): Got invalid URL (not a string), %s" % repr(url)
            elif len(url) == 0:
                raise DeviceLoggerError, "register(): Got empty string."

            if self.__hosts.has_key(url):
                raise DeviceLoggerError, "register(): Passed URL '%s' already registered" % url

            # -- Ok, we are safe, create the proxy object and store it for further operations
            try:
                srv = xmlrpclib.Server(url)
                #val = srv.ping_from_device_manager()
                self.__hosts[url] = srv
                return 0
            except xmlrpclib.Fault, err:
                raise DeviceLoggerError, "xmlrpclib failure, %s" % err

        def unregister(self, url):
            info("Unregister request for URL %s" % repr(url))
            try:
                self.__hosts.__delitem__(url)
                return 0
            except KeyError:
                raise DeviceLoggerError, "unregister(): URL %s doesn't exist." % url

        # -- Returns the kernel version installed on the system
        def kernel(self):
            return os.uname()[2]

        def distribution(self):
            UBUNTU = "/etc/lsb-release"
            FEDORA = "/etc/fedora-release"

            DISTRIB_DESCRIPTION = ""
            DISTRIB_RELEASE = ""
            
            if os.path.exists(FEDORA):
                fd = open(FEDORA, "r")
                ret = fd.read().strip()
                fd.close()
            elif os.path.exists(UBUNTU):
                fd = open(UBUNTU, "r")
                data = fd.read().strip()
                fd.close()
                for val in data.split("\n")[:]:
                    name, value = val.split("=")
                    exec("%s='%s'" % (name, value.strip('"')))

                ret = "%s %s" % (DISTRIB_DESCRIPTION, DISTRIB_RELEASE)
            else:
                ret = "Unknown"

            return ret
            
        # -- Return the revision installed on this system
        def revision(self):
            return "@Unknown"

        def ping(self):
            return "pong"
