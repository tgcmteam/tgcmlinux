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

from Singleton import *
from xml.dom import minidom
import os

# -- For importing the MM logging need root permissions, but for testing purposes isn't required
try:
    import mobilemanager
    from mobilemanager.Logging import info, warning, error
except Exception, err:
    from logging import info, warning, error

"""
In early versions of the Mobile Manager, an internal device table was used for selecting
the modem ports. This mechanism was problematic as the modem ports (COM and AUX)
changed in some cases, mainly depending on the install kernel. For avoiding this problem, the
device table is used now *only* for caching the modem ports after the modem was correctly
detected by the DeviceManager.

The table is stored in a XML file, so it can be copied to other systems, but it doesn' belong
to the installation package.
"""

# -- Default values to be used when the external devices table doesn't exist
HUAWEI_VID  = '12d1'
NOVATEL_VID = '1410'
SIERRA_VID  = '1199'
ZTE_VID     = '19d2'
OPTION_VID  = '0af0'
ALCATEL_VID = '1bbb'

# -- This list includes the devices that doen't need a port test when they are included in the
# -- devices table
_TableSkipPortTest = {
    HUAWEI_VID  : [ '1003' ],
    NOVATEL_VID : [ ],
    SIERRA_VID  : [ ],
    ZTE_VID     : [ '0124' ],
    OPTION_VID  : [ ],
    ALCATEL_VID : [ '0017' ],
}

# -- By some devices (like the ZTE MF110), the ports test leads to a broken modem operation, means the modem
# -- can't be started correctly and remains in an endless loop. For this reason we mantain a black list with
# -- the devices that should not be tested.
def SkipPortTest(vid, pid):
    # -- Check if need to convert to string type
    if type(vid) != type(""): vid = "%x" % vid
    if type(pid) != type(""): pid = "%x" % pid

    if _TableSkipPortTest.has_key(vid):
        if pid in _TableSkipPortTest[vid]:
            return True
    return False


class TableError(Exception):
    pass


class _Product():
    def __init__(self, vid, pid, com_minor, aux_minor, driver, vendor):
        self.__vid       = vid
        self.__pid       = pid
        self.__com_minor = int(com_minor)
        self.__aux_minor = int(aux_minor)
        self.__driver    = driver
        self.__vendor    = vendor

    def com(self):
        return self.__com_minor

    def aux(self):
        return self.__aux_minor

    def driver(self):
        return self.__driver

    def pid(self):
        return self.__pid

    def vendor(self):
        return self.__vendor


class _Vendor():
    def __init__(self, name, driver, vid, pids):

        self.__vid    = vid
        self.__name   = name
        self.__driver = driver
        self.__pids   = { }
        self.pids     = [ ]

        for (pid, com, aux, drv) in pids:
            pid = pid.lower()
            drv = self.__driver if (drv is None) else (drv)
            prod = _Product(vid, pid, com, aux, drv, self)
            self.__pids[pid] = prod

            # -- Cache the PIDs for faster access
            self.pids.append(pid)

    # -- Add a new PID to this vendor
    def add(self, pid, com, aux, drv=None):
        pid = pid.lower()
        drv = self.__driver if (drv is None) else drv
        prod = _Product(self.__vid, pid, com, aux, drv, self)
        self.__pids[pid] = prod

        if self.pids.__contains__(pid):
            self.pids.remove(pid)

        self.pids.append(pid)

    # -- Removed a PID of this vendor
    def remove(self, pid):
        pid = pid.lower()
        if self.pids.__contains__(pid):
            self.pids.remove(pid)

        if self.__pids.__contains__(pid):
            self.__pids.__delitem__(pid)

    def product(self, pid):
        return self.__pids[pid]

    def name(self):
        return self.__name

    def driver(self):
        return self.__driver

    def vid(self):
        return self.__vid

    def products(self):
        return self.__pids

    def is_huawei(self):
        return (self.__vid == HUAWEI_VID)

    def is_novatel(self):
        return (self.__vid == NOVATEL_VID)

    def is_sierra(self):
        return (self.__vid == SIERRA_VID)

    def is_zte(self):
        return (self.__vid == ZTE_VID)

    def is_option(self):
        return (self.__vid == OPTION_VID)

    def is_alcatel(self):
        return (self.__vid == ALCATEL_VID)


class DeviceTable():
    __metaclass__ = Singleton

    DEVICE_TABLE_XML = "device-table.xml"

    def __init__(self):

        self.vids  = [ ]
        self.__cfg = ConfigFile(os.path.join(mobilemanager.DEVICE_TABLE_DIR(), self.DEVICE_TABLE_XML))

        try:
            self.__vendors = self.__cfg.read()
            info("Using XML devices table '%s'" % self.__cfg.fpath())
        except Exception, err:
            warning("Error reading '%s', %s" % (self.__cfg.fpath(), err))
            info("Using default vendors table")
            self.__vendors = { }
            self.__add( "Huawei"  , "huawei"  , HUAWEI_VID  , [ ( '1003', 1, 0, None ) ] )
            self.__add( "Novatel" , "novatel" , NOVATEL_VID , [ ] )
            self.__add( "Sierra"  , "sierra"  , SIERRA_VID  , [ ] )
            self.__add( "ZTE"     , "zte"     , ZTE_VID     , [ ] )
            self.__add( "Option"  , "option"  , OPTION_VID  , [ ] )
            self.__add( "Alcatel" , "alcatel" , ALCATEL_VID , [ ] )
            self.__save()

    # -- Use this method only for adding new default vendors to the devices table
    def __add(self, name, drv, vid, pids):
        vid = vid.lower()
        self.vids.append(vid)
        _vendor = _Vendor(name, drv, vid, pids)
        self.__vendors[vid] = _vendor

    # -- Return a list with the supported PIDs of a passed vendor
    def pids(self, vid):
        try:
            _vendor = self.__vendors[vid]
            return _vendor.pids
        except KeyError:
            raise TableError, "VID '%s' isn't included in devices table" % str(vid)

    def product(self, vid, pid):
        try:
            _vendor = self.__vendors[vid.lower()]
            return _vendor.product(pid.lower())
        except KeyError:
            raise TableError, "Product (VID %s | PID %s) not found in devices table" % (vid, pid)

    def vendor(self, vid):
        try:
            return self.__vendors[vid.lower()]
        except KeyError:
            raise TableError, "Unknown vendor with VID %s" % vid.lower()

    def driver(self, vid):
        try:
            vendor = self.__vendors[vid.lower()]
            return vendor.driver()
        except KeyError:
            return "Unknown"

    # -- Add a new device
    def add(self, vid, pid, com_minor, aux_minor, driver=None):
        try:
            vendor = self.__vendors[vid.lower()]
            vendor.add(pid, com_minor, aux_minor, driver)
            info("Added new product (VID %s | PID %s) of vendor %s | Minors: %s COM and %s AUX" % (vid, pid, vendor.name(), com_minor, aux_minor))
            self.__save()
        except Exception, err:
            raise TableError, "Couldn't add new device, %s" % err

    # -- Remove a device/product from the table
    def removeProduct(self, vid, pid):
        try:
            vendor = self.__vendors[vid.lower()]
            vendor.remove(pid)
            info("Removed product (VID %s | PID %s) of vendor %s" % (vid, pid, vendor.name()))
            self.__save()
        except Exception, err:
            raise TableError, "Couldn't remove the device %s:%s, %s" % (str(vid), str(pid), err)

    def removeVendor(self, vid):
        raise TableError, "Sorry, method not implemented yet!"

    def vendors(self):
        return self.__vendors

    def __save(self):
        try:
            self.__cfg.save(self.__vendors)
        except Exception, err:
            error("Couldn't update '%s', %s" % (self.__cfg.fpath(), err))


class ConfigFile():

    NODE_VENDORS = "vendors"
    NODE_VENDOR  = "vendor"
    NODE_PRODUCT = "product"
    NODE_COM     = "com"
    NODE_AUX     = "aux"

    def __init__(self, fpath):
        self.__fpath = os.path.abspath(fpath)

    def fpath(self):
        return self.__fpath

    def __readFirstChildNodeValue(self, node, name):
        try:
            ret = node.getElementsByTagName(name)[0].firstChild.nodeValue
            ret = ret.strip(" \n\t\r")
        except AttributeError:
            ret = ""
        return ret

    def __appendTextNode(self, doc, node, name, value):
        n = doc.createElement(name)
        t = doc.createTextNode(str(value))
        n.appendChild(t)
        node.appendChild(n)

    def __parseProductNode(self, nprod):
        pid = nprod.getAttribute("pid")
        drv = nprod.getAttribute("driver")
        com = self.__readFirstChildNodeValue(nprod, self.NODE_COM)
        aux = self.__readFirstChildNodeValue(nprod, self.NODE_AUX)
        return [ pid, com, aux, drv ]

    def __parseVendorNode(self, nven):
        name = nven.getAttribute("name")
        vid  = nven.getAttribute("vid")
        drv  = nven.getAttribute("driver")

        # -- Get all the products of this vendors
        products =  [ ]
        for nprod in nven.getElementsByTagName(self.NODE_PRODUCT)[:]:
            prod = self.__parseProductNode(nprod)
            products.append(prod)

        return _Vendor(name, drv, vid, products)

    # -- Return value is a dictionary with VID as key and _Vendor class as value
    def read(self):
        vendors = { }
        try:
            docdom = minidom.parse(self.__fpath)
            nroot = docdom.documentElement
        except Exception, err:
            raise TableError, err

        nvens = nroot.getElementsByTagName(self.NODE_VENDORS)[0]
        for nven in nvens.getElementsByTagName(self.NODE_VENDOR)[:]:
            vendor = self.__parseVendorNode(nven)
            vendors[vendor.vid()] = vendor

        return vendors

    # -- Iput parameters is a dictionary, the same that returned by the read method
    def save(self, vendors):
        self.__saveas(self.__fpath, vendors)

    # -- This function will overwrite the file if it's already exists
    def __saveas(self, fpath, vendors):

        impl  = minidom.getDOMImplementation()
        doc   = impl.createDocument(None, "MobileManagerDevices", None)
        nroot = doc.documentElement

        # -- Create the inputs elements for the different sources
        nvens = doc.createElement("vendors")
        doc.childNodes[0].appendChild(nvens)

        for vendor in vendors.values():
            nven = doc.createElement("vendor")
            nven.setAttribute("name", vendor.name())
            nven.setAttribute("vid", vendor.vid())
            nven.setAttribute("driver", vendor.driver())

            # -- Add the products of this vendors
            for prod in vendor.products().values():
               nprod = doc.createElement("product")
               nprod.setAttribute("pid", prod.pid())
               nprod.setAttribute("driver", prod.driver())

               self.__appendTextNode(doc, nprod, self.NODE_COM, prod.com())
               self.__appendTextNode(doc, nprod, self.NODE_AUX, prod.aux())

               # -- Append the nodes/childs of this product
               nven.appendChild(nprod)

            # -- Append the vendor
            nvens.appendChild(nven)

        # -- Write to the output file
        try:
            fd = open(fpath, 'w+')
            fd.write(doc.toprettyxml())
            fd.write("\n\n")
            fd.close()
        except Exception, err:
            print err
            raise TableError, err
