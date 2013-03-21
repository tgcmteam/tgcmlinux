#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2003-2012, Telefonica Móviles España S.A.U.
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

class NoDevice(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "No device Available"

class DeviceHasNotCapability(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "Has not the capability to do this"

class DeviceBusy(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "The device can't do this because is working"

class DeviceNotReady(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "The device not ready"

class MobileManagerIOError(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "Mobile Manager Crash"

class DeviceIncorrectPassword(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "The password is incorrect"

class DeviceOperationNotAllowed(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "The operation is not allowed"
