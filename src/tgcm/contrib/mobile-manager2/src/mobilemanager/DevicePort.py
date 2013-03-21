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

import gudev
import usb
import re
import os
import termios
import select
import threading
import time

import devices.SerialPort

from mobilemanager.Logging import debug, info, warning, error

class TestError(Exception):
    pass

class PortError(Exception):
    pass

class TimeMeasure():
    def __init__(self):
        self.__t1   = time.time()

    def diff(self):
        t2 = time.time()
        di = t2 - self.__t1
        return self.__fmt(di)

    # -- Return value is in miliseconds
    def __fmt(self, di):
        return "%5d ms" % int(1000 * di)

# -- This class represents a TTY port of an USB device
class Port():

    AT_TEST_OK    = 0
    AT_TEST_ERROR = 1

    def __init__(self, parent, dev, usbdev):

        self.__parent     = parent
        self.__dev        = dev
        self.__usbdev     = usbdev
        self.__fd         = None

        self.__minor      = int(dev.get_property("MINOR"))

        self.__devnode    = dev.get_device_file()
        self.__sysfs_path = dev.get_sysfs_path()

        self.__iface      = None

    # -- @TODO: Add support for the mode parameter
    def open(self, mode=None, flush=False):

        if self.__fd is not None:
            return

        self.__fd = os.open(self.__devnode, os.O_RDWR | os.O_NONBLOCK | os.O_NOCTTY | os.O_NDELAY)
        devices.SerialPort.configure_port(self.__fd)

        if flush is True:
            self.__flush()

    def close(self, flush=True):
        if self.__fd is not None:
            try:
                self.__flush()
                os.close(self.__fd)
            except Exception, err:
                error("Closing port %s, %s" % (self.__devnode, err))
            finally:
                self.__fd = None

    def __flush(self):
        try:
            termios.tcflush(self.__fd, termios.TCIOFLUSH)
        except:
            pass

    def write(self, msg):
        _len = len(msg)

        while True:
            ret = os.write(self.__fd, msg)
            if ret < 0:
                raise IOError, "Got write() failure, %i" % ret

            # -- @FIXME: Evaluate the return value!
            if ret != _len:
                error("@XXX: Coulnd't write all the data!")

            break

    # -- Send a command to the port and wait until timeout for read data
    def cmd(self, cmd, timeout, event=None):
        self.open()
        self.write(cmd)
        msg = self.read(timeout, event)
        self.close()
        return msg

    # -- Read data from the port until the timeout has expired
    def read(self, timeout, event=None):
        select_timeout = 0.050
        loops = int(timeout / select_timeout)

        msg = ""
        while loops:
            ready = select.select([ self.__fd ], [ ], [ ], select_timeout)
            loops = loops  - 1
            if self.__fd in ready[0]:
                msg += os.read(self.__fd, 32)

            if (event is not None) and event.isSet():
                break

        return msg

    # -- Returns true if the value is read before the timeout
    def expect(self, pattern, timeout, event=None):
        select_timeout = 0.010
        loops = int(timeout / select_timeout)

        msg = ""
        while loops:
            ready = select.select([ self.__fd ], [ ], [ ], select_timeout)
            loops = loops  - 1
            if self.__fd in ready[0]:
                msg += os.read(self.__fd, 1)
                if re.search(pattern, msg) is not None:
                    return True

            if (event is not None) and event.isSet():
                return False

        if msg != "":
            warning("Got unexpected data '%s' testing '%s'" % (repr(msg), self.__devnode))

        return False

    def minor(self):
        return self.__minor

    def devnode(self):
        return self.__devnode

    def property(self, name):
        return self.__dev.get_property(name)

    def property_keys(self):
        return self.__dev.get_property_keys()

    def sysfs_path(self):
        return self.__sysfs_path

    def has_ep_type(self, ep_type):
        self.__get_interface_number()
        if self.__iface is not None:
            for ep in self.__iface.endpoints:
                if ep.type == ep_type:
                    return True
        return False

    def has_bulk_ep(self):
        return self.has_ep_type(usb.ENDPOINT_TYPE_BULK)

    def has_interrupt_ep(self):
        return self.has_ep_type(usb.ENDPOINT_TYPE_INTERRUPT)

    def __get_interface_number(self):
        if self.__iface is None:

            ifacenr = -1

            # -- In some fucking cases, the gudev device doesn't provide the interface number!
            # -- So we need to get it from the sysfs path file!
            try:
                iface_path = os.path.dirname(self.__sysfs_path) + "/../../bInterfaceNumber"
                fd = open(iface_path)
                ifacenr = int(fd.read())
                fd.close()

                # -- @XXX: Always choice the configuration index zero?
                # -- Ubuntu and Fedora provide different tupples with the interfaces
                for x in self.__usbdev.configurations[0].interfaces:
                    for y in x:
                        if y.interfaceNumber == ifacenr:
                            self.__iface = y
                            return
            except Exception, err:
                error("*** @FIXME: No interface '%i' for port %s, %s" % (ifacenr, self.__devnode, err))
                error(" --> sysfs path     : %s" % iface_path)
                error(" --> configurations : %s" % repr(self.__usbdev.configurations))
                error(" --> interfaces     : %s" % repr(self.__usbdev.configurations[0].interfaces))

            # -- At this point we have a problem, so inform our caller about this
            raise PortError, "Couldn't assign an USB interface to port '%s'" % self.__devnode

    def AT_test(self, retries, timeout, write=None, read=None):

        retval = self.AT_TEST_ERROR
        write  = "AT"    if write is None else write
        read   = "AT|OK" if read  is None else read

        for retry in range(0, retries):
            try:
                self.open(flush=True)
                self.write(write + "\r")

                # -- Wait for the response from the port
                if self.expect(read, timeout) is True:
                    retval = self.AT_TEST_OK
                    #self.write("ATZ\r")
            except Exception, err:
                warning("Got error testing port %s, %s" % (self.__devnode, err))
            finally:
                self.close()
                if retval is self.AT_TEST_OK:
                    return retval

        return self.AT_TEST_ERROR

class PortsHandler():
    def __init__(self):
        self.__ports  = [ ]
        self.__minors = [ ]

    def add(self, parent, device, usbdev):

        minor = int(device.get_property("MINOR"))
        if self.__minors.__contains__(minor):
            return None

        port = Port(parent, device, usbdev)
        self.__minors.append(minor)
        self.__minors.sort()
        self.__ports.append(port)
        return port

    def get_port_by_index(self, index):
        if index >= len(self.__minors) or index < 0:
            raise PortError, "Port index %i outside of range 0...%i" % (index, len(self.__minors) - 1)

        minor = self.__minors[index]
        return self.__get_port_by_minor(minor)

    def get_port_by_minor(self, minor):
        return self.__get_port_by_minor(minor)

    def __get_port_by_minor(self, minor):
        for port in self.__ports[:]:
            if port.minor() == minor:
                return port

        raise PortError, "Couldn't find port with minor %s" % minor

    def get_port_index(self, port):
        minor = port.minor()
        try:
            return self.__minors.index(minor)
        except:
            raise PortError, "No port found with minor %i" % minor

    def number_ports(self):
        return len(self.__minors)

    def remove_all(self):
        for port in self.__ports[:]:
            port.close()

        self.__ports  = [ ]
        self.__minors = [ ]

    def ports(self):
        return self.__ports

    def get_ports_with_interrupt_ep(self):
        return self.__get_ports_with_ep_type(usb.ENDPOINT_TYPE_INTERRUPT)

    def get_ports_without_interrupt_ep(self):
        return self.__get_ports_with_ep_type(usb.ENDPOINT_TYPE_BULK, ep_without = usb.ENDPOINT_TYPE_INTERRUPT)

    def __get_ports_with_ep_type(self, ep_type, ep_without=None):
        retval = [ ]
        for port in self.__ports:
            if port.has_ep_type(ep_type) is True:
                if (ep_without is not None) and (port.has_ep_type(ep_without)):
                    continue
                retval.append(port)
        return retval

class PortTester(threading.Thread):

    RESULT_NONE    = 0
    RESULT_OK      = 1
    RESULT_ERROR   = 2
    RESULT_PENDING = 3

    def __init__(self, port, retries, timeout, write=None, read=None):
        threading.Thread.__init__(self)
        self.__port     = port
        self.__duration = None
        self.__result   = self.RESULT_NONE
        self.__retries  = retries
        self.__timeout  = timeout
        self.__write    = write
        self.__read     = read

    def run(self):
        self.__result = self.RESULT_PENDING
        td = TimeMeasure()
        if self.__port.AT_test(self.__retries, self.__timeout, write=self.__write, read=self.__read) == self.__port.AT_TEST_OK:
            self.__result = self.RESULT_OK
        else:
            self.__result = self.RESULT_ERROR
        self.__duration = td.diff()

        # -- @XXX: This is probably not the correct place for this debug message
        msg = "AT" if self.__result == self.RESULT_OK else "No"
        info("%s answer on %s | Duration %s" % (msg, self.__port.devnode(), self.__duration))

    def result(self):
        return self.__result

    def duration(self):
        return self.__duration

    def port(self):
        return self.__port

class PortTesters(threading.Thread):

    def __init__(self, ports, retries, timeout, sequential=True, stop_first=True, write=None, read=None):

        threading.Thread.__init__(self)

        self.__tests      = self.__create_tests(ports, retries, timeout, write, read)
        self.__sequential = sequential
        self.__stop_first = stop_first

    def __create_tests(self, ports, retries, timeout, write, read):
        if type(ports) != type([ ]):
            ports = [ports]

        tests = [ ]
        for port in ports[:]:
            test = PortTester(port, retries, timeout, write=write, read=read)
            tests.append(test)
        return tests

    def run(self):
        if self.__sequential is True:
            self.__run_sequential()
        else:
            self.__run_threaded()

    # -- Test port sequentially and return if stop_first is True
    def __run_sequential(self):
        for test in self.__tests[:]:
            test.start()
            test.join()

            # -- Check for the stop condition
            if (self.__stop_first is True) and (test.result() == test.RESULT_OK):
                break

    # -- Test all the ports parallel and return a list with the results of the tests
    def __run_threaded(self):

        for test in self.__tests[:]: test.start()

        # -- Wait until all the tests have finished
        for test in self.__tests[:]: test.join()

    def results(self):
        retval =  [ ]
        for test in self.__tests[:]:
            retval.append(test.result())
        return retval

    # -- Return the first port with test result OK
    def port_ok(self):
        for test in self.__tests[:]:
            if test.result() == test.RESULT_OK:
                return test.port()

        return None

    # -- Return all the ports with test result OK
    def ports_ok(self):
        retval = [ ]
        for test in self.__tests[:]:
            if test.result() == test.RESULT_OK:
                retval.append(test.port())
        return retval

    # -- Return the first port with test result OK and an Interrupt Endpoint
    def port_ok_with_interrupt_ep(self):
        ports = self.ports_ok()
        for port in ports[:]:
            if port.has_interrupt_ep() is True:
                return port
        return None

    def tests(self):
        return self.__tests

    def all_ok(self):
        for test in self.__tests[:]:
            if test.result() != test.RESULT_OK:
                return False
        return True
