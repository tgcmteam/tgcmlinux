#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
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

from dbus.exceptions import DBusException

class PhoneFailure(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.PhoneFailure'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NoConnection(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NoConnection'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class LinkReserved(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.LinkReserved'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class OperationNotAllowed(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.OperationNotAllowed'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class OperationNotSupported(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.OperationNotSupported'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class PhSimPinRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.PhSimPinRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class PhFSimPinRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.PhFSimPinRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class PhFSimPukRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.PhFSimPukRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimNotInserted(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimNotInserted'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimPinRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimPinRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimPukRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimPukRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimFailure(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimFailure'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimBusy(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimBusy'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimWrong(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimWrong'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class IncorrectPassword(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.IncorrectPassword'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimPin2Required(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimPin2Required'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class SimPuk2Required(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.SimPuk2Required'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class MemoryFull(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.MemoryFull'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class InvalidIndex(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.InvalidIndex'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NotFound(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NotFound'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class MemoryFailure(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.MemoryFailure'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class TextTooLong(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.TextTooLong'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class InvalidChars(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.InvalidChars'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class DialStringTooLong(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.DialStringTooLong'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class InvalidDialString(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.InvalidDialString'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NoNetwork(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NoNetwork'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NetworkTimeout(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NetworkTimeout'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NetworkNotAllowed(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NetworkNotAllowed'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NetworkPinRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NetworkPinRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NetworkPukRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NetworkPukRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NetworkSubsetPinRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NetworkSubsetPinRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class NetworkSubsetPukRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.NetworkSubsetPukRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class ServicePinRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.ServicePinRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class ServicePukRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.ServicePukRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class CorporatePinRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.CorporatePinRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class CorporatePukRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.CorporatePukRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class HiddenKeyRequired(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.HiddenKeyRequired'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class EapMethodNotSupported(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.EapMethodNotSupported'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class IncorrectParams(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.IncorrectParams'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class Unknown(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.Unknown'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsIllegalMs(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsIllegalMs'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsIllegalMe(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsIllegalMe'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsPlmnNotAllowed(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsPlmnNotAllowed'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsLocationNotAllowed(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsLocationNotAllowed'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsRoamingNotAllowed(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsRoamingNotAllowed'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsOptionNotSupported(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsOptionNotSupported'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsNotSubscribed(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsNotSubscribed'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsOutOfOrder(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsOutOfOrder'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsPdpAuthFailure(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsPdpAuthFailure'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsUnspecified(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsUnspecified'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class GprsInvalidClass(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.GprsInvalidClass'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

