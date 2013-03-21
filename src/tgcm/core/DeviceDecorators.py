#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2003-2010, Telefonica Móviles España S.A.U.
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

import os
import sys
import gobject
import time
import dbus
import dbus.glib
import gtk
import tgcm

from MobileManager.MobileStatus import *
from MobileManager.MobileManagerDbus import MOBILE_MANAGER_CONTROLLER_PATH,MOBILE_MANAGER_CONTROLLER_URI,MOBILE_MANAGER_CONTROLLER_INTERFACE_URI,MOBILE_MANAGER_DEVICE_PATH,MOBILE_MANAGER_DEVICE_URI,MOBILE_MANAGER_DEVICE_ADDRESSBOOK_INTERFACE_URI,MOBILE_MANAGER_DEVICE_INFO_INTERFACE_URI,MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI,MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI,MOBILE_MANAGER_DEVICE_SMS_INTERFACE_URI,MOBILE_MANAGER_DEVICE_XZONE_INTERFACE_URI, MOBILE_MANAGER_DIALER_INTERFACE_URI

from DeviceExceptions import *

def addressbook_interface_required(func):
    def newFunc(*args, **kwargs):
        device = args[0]
        if not device.has_capability(MOBILE_MANAGER_DEVICE_ADDRESSBOOK_INTERFACE_URI) :
            raise DeviceHasNotCapability
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def sms_interface_required(func):
    def newFunc(*args, **kwargs):
        device = args[0]
        if not device.has_capability(MOBILE_MANAGER_DEVICE_SMS_INTERFACE_URI) :
            raise DeviceHasNotCapability
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def auth_interface_required(func):
    def newFunc(*args, **kwargs):
        device = args[0]
        if not device.has_capability(MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI) :
            raise DeviceHasNotCapability
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def state_interface_required(func):
    def newFunc(*args, **kwargs):
        device = args[0]
        if not device.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) :
            tgcm.error("Raise DeviceHasNotCapability")
            raise DeviceHasNotCapability
        
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def device_ready_required(func):
    def newFunc(*args, **kwargs):
        device = args[0]
        if device.get_card_status() != CARD_STATUS_READY :
            raise DeviceNotReady
        
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc    

def check_device(func):
    def newFunc(*args, **kwargs):
        device = args[0]
        if device.get_card_status() == CARD_STATUS_READY :
            if device.device_dialer.status() != PPP_STATUS_DISCONNECTED and not device.is_multiport_device():
                raise DeviceBusy
        else:
            raise DeviceNotReady
                
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def mobile_manager(func):
    def newFunc(*args, **kwargs):
##         try:
##             ret = func(*args, **kwargs)
##         except:
##             raise MobileManagerIOError
            
        return func(*args, **kwargs)
    
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc
