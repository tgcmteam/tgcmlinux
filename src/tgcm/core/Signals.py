#!/usr/bin/python
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

class _Signal():
    def __init__(self, obj, name, callback):
        self.obj      = obj
        self.name     = name
        self.callback = callback
        self.match    = None
        self.blocked  = False

    def is_connected(self):
        return (self.match is not None)

    def is_disconnected(self):
        return (self.match is None)

    def is_blocked(self):
        return self.blocked

    def disconnect(self):
        if self.is_connected():
            self._disconnect()
            self.match = None

    def connect(self):
        if self.is_disconnected():
            try:
                self.match = self._connect()
            except Exception, err:
                print "@FIXME: Couldn't connect signal '%s' to class '%s'" % (self.name, self.obj.__class__.__name__)
                print "  => %s" % err

    def block(self):
        if self.is_connected() and (not self.is_blocked()):
            self._block()
            self.blocked = True

    def unblock(self):
        if (self.is_connected()) and (self.is_blocked()):
            self._unblock()
            self.blocked = False

class _Signals():
    def __init__(self, signals):
        self.signals = { }
        for [ _key, _obj, _name, _callback ] in signals[:]:

            if self.signals.has_key(_key) is True:
                raise KeyError, "Signal key '%s' already exists" % _key

            _sig = self.Signal(_obj, _name, _callback)
            self.signals[_key] = _sig

    def connect_all(self):
        for _sig in self.signals.values():
            _sig.connect()

    def disconnect_all(self):
        for _sig in self.signals.values():
            _sig.disconnect()

    def __convert_keys_to_list(self, keys):
        if type(keys) not in (type([ ]), type(( ))):
            retval = ( keys, )
        else:
            retval = keys
        return retval

    def block_by_key(self, keys):
        keys = self.__convert_keys_to_list(keys)
        for key in keys:
            self.__block_by_key(key)

    def unblock_by_key(self, keys):
        keys = self.__convert_keys_to_list(keys)
        for key in keys:
            self.__unblock_by_key(key)

    def __unblock_by_key(self, key):
        if self.signals.has_key(key) is False:
            raise KeyError, "Signal key %s doesn't exist" % repr(key)

        sig = self.signals[key]
        sig.unblock()

    def __block_by_key(self, key):
        if self.signals.has_key(key) is False:
            raise KeyError, "Signal key %s doesn't exist" % repr(key)

        sig = self.signals[key]
        sig.block()

# -- This class provides a comfortable way for activating/deactivating a list of DBUS signals.
# -- This is required as some DBUS signals must be removed/disconnected on the fly by some events, e.g. 
# -- when a modem is disconnected (see ticket 3986).
class DBusSignals(_Signals):

    class Signal(_Signal):
        def __init__(self, obj, name, callback):
            _Signal.__init__(self, obj, name, callback)

        def _disconnect(self):
            self.match.remove()

        def _connect(self):
            return self.obj.connect_to_signal(self.name, self.callback)

        def _block(self):
            pass

        def _unblock(self):
            pass

    # -- The parameter 'signals' is a list with components like [ ProxyObject, SignalName, CallbackFunction ]
    def __init__(self, signals):
        _Signals.__init__(self, signals)

        # -- And connect the signals
        self.connect_all()

class GobjectSignals(_Signals):

    class Signal(_Signal):
        def __init__(self, obj, name, callback):
            _Signal.__init__(self, obj, name, callback)

        def _disconnect(self):
            self.obj.disconnect(self.match)

        def _connect(self):
            return self.obj.connect(self.name, self.callback)

        def _block(self):
            self.obj.handler_block(self.match)

        def _unblock(self):
            self.obj.handler_unblock(self.match)

    # -- The parameter 'signals' is a list with components like [ ClassObject, SignalName, CallbackFunction ]
    def __init__(self, signals):
        _Signals.__init__(self, signals)

        # -- And connect the signals
        self.connect_all()
