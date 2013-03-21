#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import os
import sys
import threading
import thread
import re
import time
import gobject
import glib

from Singleton import *

BITS_PER_SECOND   = 1
KBITS_PER_SECOND  = 2
BYTES_PER_SECOND  = 3
KBYTES_PER_SECOND = 4
MBYTES_PER_SECOND = 5

class TrafficUpdaterError(Exception):
    pass

#
# -- Circular buffer with two entries
# -- IMPORTANT: It stores the RELATIVE traffic statistics, it means, the first append value
# -- is used as offset for further probes
#
class CircBuffer():
    def __init__(self):
        self.__offset = 0
        self.__values = [ None, None ]
        self.__deltas = [ 0, 0 ]

    def __append(self, list, val):
        list.pop(0)
        list.append(int(val))

    # -- By the first probe set the offset
    def append(self, val):
        if self.last() is None:
            self.__offset = val
        self.__append(self.__values, val - self.__offset)
        self.__delta()

    def last(self):
        return self.__values[1]

    def previous(self):
        return self.__values[0]

    # -- Returns zero if only ONE or none entry was stored
    def __delta(self):
        if None in self.__values:
            ret = 0
        else:
            ret = (self.__values[1] - self.__values[0])
            ret = 0 if ret < 0 else ret

        self.__append(self.__deltas, ret)
        return ret

    def delta(self):
        return self.__deltas[1]

    def deltaPrevious(self):
        return self.__deltas[0]

    # -- Returns the average of the last with the previous delta
    def deltaAverage(self):
        return ((self.__deltas[1] + self.__deltas[0]) / 2)

class TrafficBytes(CircBuffer):

    def __init__(self, timev):
        CircBuffer.__init__(self)
        self.__time   = float(timev)

    # -- The time unit is seconds
    def update(self, bytes, time=None):
        self.append(bytes)
        if time is not None:
            self.__time = float(time)

    def __rate(self, diff, unit):
        if BITS_PER_SECOND == unit:
            divisor = 1
            multi   = 8
        elif KBITS_PER_SECOND == unit:
            divisor = 1024
            multi   = 8
        elif BYTES_PER_SECOND == unit:
            divisor = 1
            multi   = 1
        elif KBYTES_PER_SECOND == unit:
            divisor = 1024
            multi   = 1
        elif MBYTES_PER_SECOND == unit:
            divisor = 1024 * 1024
            multi   = 1
        else:
            raise TrafficUpdaterError, "Got invalid RATE unit type!"

        divisor = float(divisor) * self.__time
        diff = float( diff * multi )
        return float(diff / divisor)

    def rate(self, unit):
        return self.__rate(self.delta(), unit)

    def ratePrevious(self, unit):
        return self.__rate(self.deltaPrevious(), unit)

class Interface():
    def __init__(self, name, interval):
        self.__name     = name
        self.__interval = float(interval)

        self.rx = TrafficBytes(self.__interval)
        self.tx = TrafficBytes(self.__interval)

    def rx(self):
        return self.rx

    def tx(self):
        return self.tx

    def interval(self, value=None):
        if value is not None:
            self.__interval = float(value)
        return self.__interval

    def update(self, rx, tx):
        # -- Update the new data of this interface
        self.rx.update(rx)
        self.tx.update(tx)

# -- This class updates the traffic statistics of ALL the available interfaces
class TrafficUpdater(gobject.GObject):

    __gsignals__ = {
        'traffic-updater-trigger' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_FLOAT, )) ,
    }

    class Debug():

        GLOBAL_DISABLE = 1

        def __init__(self, debug):
            self.__debug = debug

        def __call__(self, func):
            def newf(*args, **kwargs):
                if self.__debug and not self.GLOBAL_DISABLE:
                    print "[TrafficUpdater] Calling '%s()'" % func.__name__
                func(*args, **kwargs)
            return newf

    STATE_IDLE    = 0
    STATE_RUNNING = 1

    def __init__(self, path="/proc/net/dev", interval=1.0):

        gobject.GObject.__init__(self)

        self.__path       = path
        self.__stop_event = threading.Event()
        self.__fd         = None
        self.__ifaces     = { }
        self.__interval   = float(interval)
        self.__state      = self.STATE_IDLE

        # -- Open the file here so we pass the exceptions to the caller at this point
        self.__open_netdev()

    # -- Open the passed proc file
    def __open_netdev(self):
        try:
            self.__fd = open(self.__path, "r")
        except Exception, err:
            raise TrafficUpdaterError, "Couldn't open file: %s (%s)" % (self.__path, err)

    def start(self):
        if self.__state != self.STATE_RUNNING:
            self.__state = self.STATE_RUNNING
            self.__stop_event.clear()
            thread.start_new_thread(self.__start, ( ))

    @Debug(1)
    def __start(self):

        if self.__fd is None:
            self.__open_netdev()

        while True:
            try:
                self.__process()

                # -- Wait for the timeout or the event is set
                self.__stop_event.wait(self.__interval)
                if self.__stop_event.is_set():
                    break
            except Exception, err:
                print "@FIXME: Unexpected failure starting thread (%s)" % err
                break

        # -- Cleanup
        self.__cleanup()

    @Debug(1)
    def __cleanup(self):
        try:
            self.__fd.close()
        except:
            pass
        finally:
            self.__ifaces = { }
            self.__fd     = None
            self.__state  = self.STATE_IDLE

    # -- Process the statistics data
    @Debug(0)
    def __process(self):

        self.__fd.seek(0)
        lns = self.__fd.read()

        # -- Skip the two first lines (headers)
        for ln in lns.split("\n")[2:]:

            # -- Remove the leading and trailing blank spaces
            ln = ln.strip(" ")

            # -- Split in an array separeated by one or more blank spaces
            ln = re.sub('\s+|:\s+', ' ', ln)
            vals = ln.split(" ")

            # -- Get the interface associated to this line and the RX, TX bytes
            try:
                name = vals[0]
                rx = int(vals[1])
                tx = int(vals[9])
                self.__ifaces[name].update(rx, tx)
            except IndexError:
                continue
            except KeyError:
                self.__ifaces[name] = Interface(name, self.__interval)
                self.__ifaces[name].update(rx, tx)
            except Exception, err:
                print "@FIXME: Unexpected failure in TrafficUpdater, %s" % err

        glib.idle_add(self.emit, 'traffic-updater-trigger', self.__interval)

    @Debug(1)
    def __stop(self):
        if self.__state == self.STATE_RUNNING:
            self.__stop_event.set()

    def stop(self):
        self.__stop()

    def is_running(self):
        return (not self.__stop_event.is_set())

    # -- Return the instance to a passed interface
    def iface(self, name):
        try:
            return self.__ifaces[name]
        except KeyError:
            raise TrafficUpdaterError

