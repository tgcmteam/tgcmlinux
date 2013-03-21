#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2012, Telefonica Móviles España S.A.U.
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
import gconf

import tgcm


class TgcmLoggingConfig(object):

    def __init__(self, country):
        self.gconf_path = '%s/%s' % (tgcm.gconf_path, country)
        self.client = gconf.client_get_default()

    def get_connection_log_filepath(self):
        return tgcm.connection_log_file

    def is_connection_log_enabled(self):
        return self.client.get_bool( \
                '%s/connections_general/log_activate' % self.gconf_path)
