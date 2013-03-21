#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2010, Telefonica Móviles España S.A.U.
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

'''
Device Dispatcher is the class that detect and construct the device
driver and notify it to ModemManager.
'''

import os
import sys
import re
import StringIO

import gobject
import gudev
import usb
import time
import dbus
from mmdbus.service import Object as DbusObject

from mobilemanager.Logging import debug, info, warning, error

import threading
import thread
import commands
import termios
import select

import DeviceTable
import DevicePort

from Singleton import *

MM_DEVICE_PATH='/org/freedesktop/ModemManager/Modems/'

# -- Return the parent ID which consists in the bus and device number. This is
# -- an unique number for each USB device.
def create_parent_id(parent):
    try:
        _busnum = parent.get_property("BUSNUM")
        _devnum = parent.get_property("DEVNUM")
        return "%s/%s" % (_busnum, _devnum)
    except AttributeError:
        return None

def parent_from_device(device):
    try:
        return device.get_parent().get_parent().get_parent()
    except AttributeError:
        return None

def print_properties(dev):
    for k in dev.get_property_keys():
        print "%s = %s" % (k, dev.get_property(k))

# -- Return an unique ID
# -- @XXX: Protect this shared list
_modem_ids = [ ]
def alloc_modem_id():
    for x in range(0, 1000):
        if _modem_ids.__contains__(x) is False:
            _modem_ids.append(x)
            return x

# -- Free an already allocated ID
def free_modem_id(num):
    if _modem_ids.__contains__(num) is True:
        _modem_ids.remove(num)
    else:
        error("Couldn't free invalid Modem ID %i" % int(num))

class DriverError(Exception):
    pass

class ModemError(Exception):
    pass

class DeviceManager(gobject.GObject):
    '''
    DeviceManager Class
    '''

    __metaclass__ = Singleton

    __gsignals__ = {
        'device-added'   : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)) ,
        'device-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)) ,
    }

    # -- Internal device class for assuring that some resources (like the Gobject signals) are
    # -- freed after the modem was removed
    class _Device():
        def __init__(self, parent, busname, mm_path, id, signals):
            self.__dev = DeviceDriverBuilder(parent, busname, mm_path, id)

            # -- Methods we need to link from the device driver class
            self.mm_device_path = self.__dev.mm_device_path
            self.remove         = self.__dev.remove
            self.devpath        = self.__dev.devpath
            self.remove         = self.__dev.remove
            self.vid            = self.__dev.vid
            self.pid            = self.__dev.pid
            self.ports_nr       = self.__dev.ports_nr

            # -- Connect to the Gobject signals of the device
            self.__signals = [ ]
            for [ name, cb ] in signals[:]:
                signal = self.__dev.connect(name, cb)
                self.__signals.append(signal)

        # -- Disconnect the already connected Gobject signals
        def disconnect(self):
            for signal in self.__signals[:]:
                self.__dev.disconnect(signal)
            self.__signals = [ ]

    def __init__(self, bus_name):
        gobject.GObject.__init__(self)
        self.bus_name        = bus_name
        self.device_list     = { }
        self.__devtable      = DeviceTable.DeviceTable()
        self.udev_client     = gudev.Client(["tty"])
        self.udev_client_usb = gudev.Client(["usb/usb_device"])

        thread.start_new_thread(self.__check_available_devices, ( ))

    def enumerate_devices(self):
        ret = []
        for dev in self.device_list.values():
            ret.append(dev.mm_device_path())

        return ret

    def __check_available_devices(self):
        info("Checking tty's availables")
        for device in self.udev_client.query_by_subsystem("tty"):
            self.__on_tty_event(self.udev_client, "add", device)
        info("Checking tty's availables finished")

        for device in self.udev_client_usb.query_by_subsystem("usb"):
            self.__on_usb_event(self.udev_client_usb, "add", device)

        self.udev_client.connect("uevent", self.__on_tty_event)
        self.udev_client_usb.connect("uevent", self.__on_usb_event)

    # -- This function checks for devices that are not handled by the MM as they are not
    # -- included in the devices table
    def __on_usb_event(self, client, action, device):
        if action == "add":
            vid = device.get_property("ID_VENDOR_ID")
            if vid in self.__devtable.vids:
                pid = device.get_property("ID_MODEL_ID")
                if pid not in self.__devtable.pids(vid):
                    vendor = self.__devtable.vendor(vid)
                    warning("New USB parent %s:%s | Vendor %s | Pending 'usb_modeswitch' rule?" % (vid, pid, vendor.name()))

    # -- Wait for state changes of TTY ports
    def __on_tty_event(self, client, action, device):

        # -- By new TTY ports only create the object and store the corresponding ID
        if action == "add":

            _parent = parent_from_device(device)
            _id = create_parent_id(_parent)
            if _id is None:
                return

            if self.device_list.has_key(_id) is False:
                try:
                    # -- @XXX: Correct place for defining the Gobject signals with the callbacks?
                    DEVICE_SIGNALS = [
                        [ "modem-ready"    , self.__modem_ready_cb    ],
                        [ "modem-removed"  , self.__modem_removed_cb  ],
                        [ "modem-failure"  , self.__modem_failure_cb  ],
                        [ "device-removed" , self.__device_removed_cb ],
                    ]

                    dev = self._Device(_parent, self.bus_name, MM_DEVICE_PATH, _id, DEVICE_SIGNALS)
                    self.device_list[_id] = dev
                except Exception, err:
                    error("Unexpected failure adding device, %s" % err)

        elif action == "remove":

            # -- @FIXME: As the parent could be already destroyed during this callback is
            # -- executed, we use another mechanism for obtaining the parent that corresponds
            # -- to this device
            found = False
            path = device.get_property("DEVPATH")
            for dev in self.device_list.values():
                if path.startswith(dev.devpath() + "/"):
                    # -- We must assure that the device is gone, in some cases it doesn't (why?)
                    for bus in usb.busses():
                        for x in bus.devices:
                            if x.idVendor == dev.vid(int) and x.idProduct == dev.pid(int):
                                return

                    dev.remove()
                    warning("Removed USB parent %s:%s" % (dev.vid(), dev.pid()))
                    found = True
                    break

            if found is False:
                warning("Unknown remove event of device '%s'" % (path))

    # -- Trigger the signal DeviceAdded in the NM
    def __modem_ready_cb(self, driver, mm_device_path):
        self.emit("device-added", mm_device_path)

    # -- Trigger the signal DeviceRemoved in the NM
    def __modem_removed_cb(self, driver, mm_device_path):
        self.emit("device-removed", mm_device_path)

    def __device_removed_cb(self, driver, mm_device_path):
        try:
            info("Going to remove the device '%s'" % mm_device_path)
            self.__remove(driver)
        except Exception, err:
            error("Unexpected failure removing device, %s" % err)

    # -- Disconnect the Gobject signals and remove the device from the internal list
    def __remove(self, driver):
        dm_id = driver.dm_id()
        dev = self.device_list[dm_id]
        dev.disconnect()
        self.device_list.__delitem__(dm_id)

    def __modem_failure_cb(self, driver, mm_device_path):
        pass

class DeviceDriverBuilder(gobject.GObject):

    TIMEOUT_TEST_DEFAULT = 0.5

    __gsignals__ = {
        'modem-ready'    : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)) ,
        'modem-removed'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)) ,
        'modem-failure'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)) ,
        'device-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)) ,
    }

    def __init__(self, parent, bus_name, mm_path, dm_id):
        gobject.GObject.__init__(self)

        self.__vid        = parent.get_property("ID_VENDOR_ID")
        self.__pid        = parent.get_property("ID_MODEL_ID")

        # -- Hell! In some cases the get_property() of the parent is returning None
        if (self.__vid is None) or (self.__pid is None):
            raise DriverError, "Got 'None' for the parent's VID/PID!"

        self.__vid_pid    = "%s:%s" % (self.__vid, self.__pid)
        self.__id         = create_parent_id(parent)
        self.__sysfs_path = parent.get_sysfs_path()
        self.__devpath    = parent.get_property("DEVPATH")

        self.__udev       = gudev.Client("tty")
        self.__dev        = parent
        self.__dm_id      = dm_id

        # -- Get the libusb device for this parent
        self.__usbdev = None
        busses = usb.busses()
        for bus in busses:
            for dev in bus.devices:
                if (dev.idVendor == int(self.__vid, 16)) and (dev.idProduct == int(self.__pid, 16)):

                    # -- @XXX: Dont know why but in some cases the HUB is passed to
                    if dev.deviceClass  == usb.CLASS_HUB:
                        raise DriverError, "Device with VID %s PID %s is a HUB" % (self.__vid, self.__pid)

                    self.__usbdev = dev
                    break

        if self.__usbdev is None:
            raise DriverError, "No Libusb device with VID %s PID %s" % (self.__vid, self.__pid)

        # -- IMPORTANT: This dict uses the port minor numbers as keys! This is required for searching
        # -- the ports that belong to a product from the devices table
        self.__ports      = DevicePort.PortsHandler()
        self.__ports_nr   = self.__get_number_ports()
        if self.__ports_nr <= 1:
            raise DriverError, "USB parent %s has %i TTY ports (not enough)" % (self.__id, self.__ports_nr)

        self.__portCom     = None
        self.__portAux     = None
        self.__driver      = None
        self.__portLock    = threading.Lock()

        self.bus_name         = bus_name
        self.__modem_id       = alloc_modem_id()
        self.__mm_device_path = os.path.join(mm_path, str(self.__modem_id))
        self.__device_service = None

        self.__devtable       = DeviceTable.DeviceTable()
        self.__measure        = DevicePort.TimeMeasure()

        info("Plugged-in USB parent %s | Ports %i | Sysfs %s" % (self.__vid_pid, self.__ports_nr, self.__sysfs_path))
        thread.start_new_thread(self.__scan, ( ))

    def portCom(self):
        return self.__portCom

    def portAux(self):
        return self.__portAux

    def ports_nr(self):
        return self.__ports_nr

    def vid(self, type=None):
        if type == int:
            return int(self.__vid, 16)
        else:
            return self.__vid

    def pid(self, type=None):
        if type == int:
            return int(self.__pid, 16)
        else:
            return self.__pid

    def dm_id(self):
        return self.__dm_id

    def debug(self, msg):
        info("%s: %s" % (self.__id, msg))

    def error(self, msg):
        error("%s: %s" % (self.__vid_pid, msg))

    def info(self, msg):
        info("%s: %s" % (self.__vid_pid, msg))

    def warning(self, msg):
        warning("%s: %s" % (self.__vid_pid, msg))

    def remove(self):
        thread.start_new_thread(self.__remove, ( ))

    def mm_device_path(self):
        return self.__mm_device_path

    def devpath(self):
        return self.__devpath

    def product(self):
        return self.__devtable.product(self.__vid, self.__pid)

    def vendor(self):
        return self.__devtable.vendor(self.__vid)

    def __reset(self, delay=5):
        try:
            delay = 5 if (delay <= 0) else delay
            time.sleep(delay)
            self.warning("Going to execute a device RESET!")
            hd = self.__usbdev.open()
            hd.reset()
        except Exception, err:
            self.error("Device reset failed, %s" % err)

    # -- Call this method for sending a reset to the USB device
    # -- The reset will be applied only if the device was already correctly detected, otherwise
    # -- it is too risky during the device startup (led to libusb segfaults under FC16)
    def reset(self, threaded=True):
        if self.__device_service is None:
            self.error("Skipping device reset as service not started yet!")
            return

        if threaded is True:
            thread.start_new_thread(self.__reset, ( ))
        else:
            self.__reset()

    # -- Remove the complete device
    def __remove(self):

        # -- Before entering check if a thread is already processing this function. In that case
        # -- return only as all the ports will be removed now
        _unblocked = self.__portLock.acquire(False)
        if _unblocked is False:
            self.debug("Skipping device remove due locked function")
            return

        self.debug("Entering driver remove function")

        try:
            # -- Check if the job was already done
            if self.__ports.number_ports() == 0:
                self.debug("No ports to remove for this parent")
                return

            # -- Inform the device manager about the stopped device and stop the service
            if (self.__portCom is not None) and (self.__portAux is not None):

                # -- This function seems to fail when the ports is not available
                try:
                    self.__device_service.stop()
                except Exception, err:
                    self.error("Failure stopping device service, %s" % err)

                self.emit("modem-removed", self.__mm_device_path)
                self.__portCom = None
                self.__portAux = None

            # -- Remove all the ports and emit the signal
            self.__ports.remove_all()
            self.emit("device-removed", self.__mm_device_path)

        except Exception, err:
            self.error("Unexpected failure removing port, %s" % err)
        finally:

            if self.__modem_id is not None:
                free_modem_id(self.__modem_id)
                self.__modem_id = None

            # -- Dont forget to release the lock
            self.__portLock.release()

    def __scan(self, start_detection=True):
        self.debug("Starting to scan for TTY devices...")
        for path in self.__sysfs_find_devices():
            try:
                path = os.path.dirname(path)
                dev = self.__udev.query_by_sysfs_path(path)

                if dev is not None and dev.get_subsystem() == "tty":
                    port = self.__ports.add(self.__dev, dev, self.__usbdev)
                    self.debug("Found TTY port %s | Minor %s | Interrupt EP: %s" % (port.devnode(), port.minor(), port.has_interrupt_ep()))

                    # -- If we have all the ports of the parent USB device, search for a modem
                    if (start_detection is True) and (port is not None) and (self.__ports_nr == self.__ports.number_ports()):
                        self.debug("Starting to search for a MODEM...")
                        self.__detect_modem_ports()

            except Exception, err:
                self.error("Unexpected failure scanning, %s" % err)

    # -- Raises a
    def __test_modem_ports(self, com, aux, sequential=False):
        # -- If the passed port doesn't have an INT endpoint, search for a new one
        if not com.has_interrupt_ep():
            raise DevicePort.TestError, "Selected COM port '%s' doesn't have an INTERRUPT endpoint" % com.devnode()
        #     candidates = self.__ports.get_ports_with_interrupt_ep()
        #     if len(candidates) == 0:
        #     else:
        #         com = candidates[0]
        #         self.warning("Using new COM port '%s' as old one doesn't have an INTERRUPT endpoint" % com.devnode())

        #if aux.has_interrupt_ep():
        #     candidates = self.__ports.get_ports_without_interrupt_ep()
        #     aux = candidates[0]

        test = DevicePort.PortTesters([ com, aux ], 1, self.TIMEOUT_TEST_DEFAULT, sequential=sequential, stop_first=False)
        test.start()
        test.join()
        if test.all_ok() is False:
            raise DevicePort.TestError, "Ports test failed, not all tests returned OK"

    # -- This test uses a different strategy, it evaluates the return value of the AT_test
    def __test_strategy_response_evaluation(self, complete=False):

        ports = [ ]
        for port in self.__ports.ports():
            ports.append(port)

        test = DevicePort.PortTesters(ports, 1, self.TIMEOUT_TEST_DEFAULT, sequential=True, stop_first=True, read="AT")
        test.start()
        test.join()
        aux = test.port_ok()

        # -- Stop at this point if there is no AUX port and no complete test requested
        if (aux is None) and (complete is False):
            return None, None

        # -- Remove the AUX port (dont to test it again)
        if aux is not None:
            ports.remove(aux)
        test = DevicePort.PortTesters(ports, 1, self.TIMEOUT_TEST_DEFAULT, sequential=True, stop_first=False, read="OK")
        test.start()
        test.join()
        com = test.port_ok_with_interrupt_ep()

        return com, aux

    # -- This function checks for specific modem ports depending on the its vendor
    def __check_vendor_specific_ports(self, com_ports, aux_ports):
        try:
            com_found = None
            aux_found = None
            vendor = self.__devtable.vendor(self.__vid)
        except Exception, err:
            self.error("Checking vendor specific ports, %s" % err)
            return

        # -- Check special case for the Huawei: The COM port has the minor number zero
        if vendor.is_huawei():
            port = self.__ports.get_port_by_index(0)
            if port.has_interrupt_ep():
                com_found = port
                self.debug("Huawei >> Auto selection of COM port %s" % com_found.devnode())

                # -- If there is only one AUX port select it
                if len(aux_ports) == 1:
                    aux_found = aux_ports[0]
                    self.debug("Huawei >> Auto selection of AUX port %s" % aux_found.devnode())

        return com_found, aux_found

    # -- Test all the ports and search for the COM and AUX ports
    def __test_strategy_interrupt_endpoint(self):
        com_ports = self.__ports.get_ports_with_interrupt_ep()
        aux_ports = self.__ports.get_ports_without_interrupt_ep()

        # -- First get the list of ports with an interrupt EP -> COM ports
        com_msg = ', '.join(map(lambda x : x.devnode(), com_ports))
        aux_msg = ', '.join(map(lambda x : x.devnode(), aux_ports))
        self.debug("Checking COM port on: %s" % com_msg)
        self.debug("Checking AUX port on: %s" % aux_msg)

        # -- If the checking of the vendor specific ports fails, continue any way for
        # -- dynamic detection
        try:
            com_found, aux_found = self.__check_vendor_specific_ports(com_ports, aux_ports)
        except Exception, err:
            self.error("Reading vendor specific ports failed, %s" % err)
            com_found = None
            aux_found = None

        if com_found is None:
            com_test = DevicePort.PortTesters(com_ports, 2, self.TIMEOUT_TEST_DEFAULT, sequential=True, stop_first=True)
            com_test.start()

        if aux_found is None:
            aux_test = DevicePort.PortTesters(aux_ports, 2, self.TIMEOUT_TEST_DEFAULT, sequential=True, stop_first=True)
            aux_test.start()

        if com_found is None:
            com_test.join()
            com_found = com_test.port_ok()
        if aux_found is None:
            aux_test.join()
            aux_found = aux_test.port_ok()

        return com_found, aux_found

    def __start_modem(self, com, aux):
        if (com is None) or (aux is None):
            if (com is None) and (aux is None):
                missing = "both ports"
            elif aux is None:
                missing = "AUX port"
            else:
                missing = "COM port"
            raise ModemError, "Modem couldnt be started as %s missing" % missing

        self.debug("Starting modem | COM %s | AUX %s | Detection duration %s" % (com.devnode(), aux.devnode(), self.__measure.diff()))
        self.__portCom = com
        self.__portAux = aux
        self.__driver  = self.__devtable.driver(self.__vid)
        self.__build_device_driver()

    # -- Check if the device is already in the table
    def __get_ports_from_device_table(self):
        try:
            product = self.__devtable.product(self.__vid, self.__pid)
            comIdx  = product.com()
            auxIdx  = product.aux()
            info("Product needs ports with index %i and %i (COM and AUX)" % (comIdx, auxIdx))
            return self.__ports.get_port_by_index(comIdx), self.__ports.get_port_by_index(auxIdx)
        except Exception, err:
            self.error("Failure reading a table product, %s" % err)
            raise DeviceTable.TableError, err

    # -- Check if the detected tty ports are part of a modem
    def __detect_modem_ports(self):
        try:
            new_product = False
            com, aux = self.__get_ports_from_device_table()

            # -- Check if this device is included in the black list of devices to test
            if not DeviceTable.SkipPortTest(self.__vid, self.__pid):
                self.__test_modem_ports(com, aux, sequential=False)

            self.__start_modem(com, aux)
            return
        except DeviceTable.TableError, err:
            new_product = True
        except DevicePort.TestError, err:
            # -- A test error means the device is present in the devices table but the read ports are
            # -- not responding as expected. So, remove the configuration from the table so we can update it
            self.warning("Removing product from table as test failed, %s" % err)
            self.__devtable.removeProduct(self.__vid, self.__pid)
            new_product = True
        except Exception, err:
            self.error("Modem detection exception, %s" % err)
            new_product = True

        # -- OK, it seems the device is not available in the devices table, so scan all the available ports by
        # -- using the different test strategies
        tests = (
            ( "Interrupt Endpoint"  , self.__test_strategy_interrupt_endpoint  ) ,
            ( "AT command response" , self.__test_strategy_response_evaluation ) ,
        )
        for name, test in tests[:]:
            try:
                com, aux = test()
                self.__start_modem(com, aux)
                self.info("Modem correctly detected with strategy '%s'" % name)
                if new_product is True:
                    com_minor = self.__ports.get_port_index(com)
                    aux_minor = self.__ports.get_port_index(aux)
                    self.__devtable.add(self.__vid, self.__pid, com_minor, aux_minor)
                return
            except ModemError, err:
                self.error("Detection strategy '%s' failed, %s" % (name, err))
            except Exception, err:
                self.error("Unexpected failure by detection strategy '%s', %s" % (name, err))

            # -- Fuck, the test has failed even we have had valid ports, so need to rescan again
            self.__ports.remove_all()
            self.__scan(start_detection=False)

        # -- Here we have an issue, the modem detection has failed
        self.emit("modem-failure", self.__mm_device_path)
        self.reset(threaded=True)

    def __sysfs_find_devices(self):
        # -- @XXX: Quick and dirty, most probably the worst and ugliest choice
        _cmd = 'find %s -type f -name "uevent"' % self.__sysfs_path
        _res = commands.getoutput(_cmd)
        return _res.split("\n")

    def __get_number_ports(self):
        _ret = 0
        for _path in self.__sysfs_find_devices():
            try:
                _path = os.path.dirname(_path)
                _dev  = self.__udev.query_by_sysfs_path(_path)
                if _dev is not None and _dev.get_subsystem() == "tty":
                    _ret += 1
            except Exception, err:
                self.error("Unexpected failure getting number of ports, %s" % err)

        return _ret

    def __get_device_io(self, vid, mid):
        obj = 'DeviceIO'
        dio =  StringIO.StringIO()
        print >> dio, 'try:'
        print >> dio, '    from devices.%s.m%s.%s import %s' % (vid, mid, obj, obj)
        print >> dio, 'except:'
        print >> dio, '    try:'
        print >> dio, '        from devices.%s.%s import %s' % (vid, obj, obj)
        print >> dio, '    except:'
        print >> dio, '        from devices.%s import %s' % (obj, obj)
        exec(dio.getvalue())
        dio.close()

        return DeviceIO

    def __get_state_machine(self, vid, mid):
        obj = 'ModemStateMachine'
        dio =  StringIO.StringIO()
        print >> dio, 'try:'
        print >> dio, '    from devices.%s.%s import %s' % (vid, obj, obj)
        print >> dio, 'except Exception, err:'
        print >> dio, '    warning("Importing state machine, %s" % err)'
        print >> dio, '    from devices.%s import %s' % (obj, obj)
        exec(dio.getvalue())
        dio.close()

        return ModemStateMachine

    def __build_device_driver(self):
        di = StringIO.StringIO()

        vid = self.__driver
        mid = self.__pid

        obj_list = ['DeviceProperties', 'Modem', 'ModemGsmCard', 'ModemGsmNetwork',
                    'ModemGsmSMS', 'ModemSimple', 'ModemGsmUssd', 'ModemGsmContacts']

        print >> di, 'from Mixin import mixin'

        for obj in obj_list :
            print >> di, 'try:'
            print >> di, '    from devices.%s import %s' % (obj, obj)
            print >> di, '    mixin(%s)' % (obj)
            print >> di, '    from devices.%s.%s import %s as %s_v' % (vid, obj, obj, obj)
            print >> di, '    mixin(%s_v)' % (obj)
            print >> di, '    from devices.%s.m%s.%s import %s as %s_vm' % (vid, mid, obj, obj, obj)
            print >> di, '    mixin(%s_vm)' % (obj)
            print >> di, 'except Exception, err:'
            print >> di, '    pass'
            #print >> di, '    error("Importing driver modules, %s" % err)'

        class device(DbusObject):
            exec(di.getvalue())

            def __init__(self, driver, bus_name, path, com_path, aux_path, io, st_m):
                self.io     = io(self, com_path, aux_path)
                self.st_m   = st_m(self)
                self.cache  = {}

                self.driver = driver
                self.path   = path

                DbusObject.__init__(self, bus_name, path)

            # -- This method will send the first AT-commands: CFUN + PORTSEL
            def start(self):
                retval = self.io.start()
                if retval == self.io.RETURN_FAILURE:
                    raise DriverError, "Start of device service failed, aborting!"

                self.st_m.start()
                info("Start device '%s' (COM: %s | AUX: %s)" % (self.path, self.io.modem_path, self.io.com_path))

            def stop(self):
                info("Stopping device : %s" % self.path)
                self.st_m.stop()
                self.io.stop()
                try:
                    self.remove_from_connection(path = self.path)
                except:
                    pass
                return True

            def reset(self):
                info("Going to reset the device!")
                self.stop()
                self.driver.reset()

            def disconnect(self):
                try:
                    self.remove_from_connection(path = self.path)
                except:
                    pass

        di.close()

        io = self.__get_device_io(vid, mid)
        st_m = self.__get_state_machine(vid, mid)

        self.__device_service = device(self,
                                       self.bus_name,
                                       self.__mm_device_path,
                                       self.__portCom.devnode(),
                                       self.__portAux.devnode(),
                                       io,
                                       st_m)

        # -- If the start fails assure that the device is disconnected from DBus and forward the
        # -- exception to our caller
        try:
            self.__device_service.start()
            self.emit("modem-ready", self.__mm_device_path)
        except Exception, err:
            self.__device_service.disconnect()
            self.__device_service = None
            raise Exception, err

gobject.type_register(DeviceManager)
gobject.type_register(DeviceDriverBuilder)

if __name__ == "__main__":

    import glib
    import dbus
    import mmdbus
    from mmdbus.service import method, signal, BusName

    MM_SERVICE = "org.freedesktop.ModemManager"

    glib.threads_init()

    bus_name = BusName(MM_SERVICE, dbus.SystemBus())

    x = DeviceManager(bus_name)

    loop = glib.MainLoop()
    loop.run()
