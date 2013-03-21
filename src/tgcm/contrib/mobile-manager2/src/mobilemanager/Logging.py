#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2010, 2011, Telefonica Móviles España S.A.U.
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

import dbus
import logging
import sys
import signal

LOG_FILENAME = '/var/log/mobile-manager.log'

TGCM_BUS_NAME = 'es.indra.TgcmLogging'
TGCM_OBJECT_PATH = '/es/indra/TgcmLogging'
TGCM_LOG_IFACE = 'es.indra.TgcmLogging'

# -- Create Logger object
_mylogger    = logging.getLogger('MobileManagerLogger')
_mylogger_sh = logging.StreamHandler(sys.stdout)
_mylogger_fh = logging.FileHandler(LOG_FILENAME)
_mylogger_init_level = None

# -- For external access
debug    = _mylogger.debug
info     = _mylogger.info
warning  = _mylogger.warning
error    = _mylogger.error
critical = _mylogger.critical

# -- Init the logging system
def init(level):
    global _mylogger_init_level, _mylogger, _mylogger_sh, _mylogger_fh

    formatter = logging.Formatter('[%(asctime)s] %(levelname)-7s %(module)-14s %(message)s')

    # -- Set up logging to STDOUT for all levels DEBUG and higher
    _mylogger_sh.setLevel(level)
    _mylogger_sh.setFormatter(formatter)

    # -- Set up logging to a file for all levels DEBUG and higher
    _mylogger_fh.setLevel(level)
    _mylogger_fh.setFormatter(formatter)

    # -- Init the logger
    _mylogger.setLevel(level)
    _mylogger.addHandler(_mylogger_sh)
    _mylogger.addHandler(_mylogger_fh)

    _mylogger_init_level = level

    # -- Change the loglevel by using the command: kill -s SIGUSR1 <MM PID>
    signal.signal(signal.SIGUSR1, _signal_toggle_info_level)

def _signal_toggle_info_level(signum, frame):
    global _mylogger, _mylogger_init_level
    level = _mylogger.getEffectiveLevel()
    if level > logging.INFO:
        set_level(logging.INFO)
        info("Logging level switched to INFO")
    else:
        info("Restoring initial log level")
        set_level(_mylogger_init_level)

# -- Change the logging level
def set_level(level):
    global _mylogger, _mylogger_sh, _mylogger_fh
    _mylogger_sh.setLevel(level)
    _mylogger_fh.setLevel(level)
    _mylogger.setLevel(level)

def register_at_command(command, response):
    bus = dbus.SystemBus()
    try:
        debug("Attempting to log AT command in TGCM")
        service = bus.get_object(TGCM_BUS_NAME, TGCM_OBJECT_PATH)
        dbus_method = service.get_dbus_method('LogATCommand', TGCM_LOG_IFACE)
        dbus_method(command, response)
    except dbus.exceptions.DBusException, err:
        debug("Could not log AT command: %s" % err)
