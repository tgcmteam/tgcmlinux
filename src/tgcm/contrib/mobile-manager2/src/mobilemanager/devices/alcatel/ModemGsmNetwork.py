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

from mobilemanager.mmdbus.service import method, signal
from mobilemanager.mmdbus.properties import prop

from mobilemanager.devices.ModemGsm import *

MM_URI='org.freedesktop.ModemManager.Modem.Gsm.Network'

ALCATEL_MODE_AUTO = 0
ALCATEL_MODE_GSM_ONLY = 1
ALCATEL_MODE_WCDMA_ONLY = 2

ALCATEL_ORDER_AUTO = 0
ALCATEL_ORDER_WCDMA_THEN_GSM = 1
ALCATEL_ORDER_GSM_THEN_WCDMA = 2

ALCATEL_DOMAIN_CS_PS = 0
ALCATEL_DOMAIN_CS = 1
ALCATEL_DOMAIN_PS = 2

class ModemGsmNetwork(object):
    @method(MM_URI,
            in_signature = '', out_signature = 'u',
            method_name="GetAllowedMode")
    def mgn_get_allowed_mode(self):
        def function(task):
            res = self.__get_alcatel_system_selection_settings(task)

            # Default mode is AUTO
            mode = ALLOWED_MODE_ANY

            # Determine current mode
            if (res["mode"] is ALCATEL_MODE_AUTO) and \
                    (res["order"] is ALCATEL_ORDER_WCDMA_THEN_GSM):
                mode = ALLOWED_MODE_3G_PREFERRED
            elif (res["mode"] is ALCATEL_MODE_AUTO) and \
                    (res["order"] is ALCATEL_ORDER_GSM_THEN_WCDMA):
                mode = ALLOWED_MODE_2G_PREFERRED
            elif res["mode"] is ALCATEL_MODE_WCDMA_ONLY:
                mode = ALLOWED_MODE_3G_ONLY
            elif res["mode"] is ALCATEL_MODE_GSM_ONLY:
                mode = ALLOWED_MODE_2G_ONLY

            return mode

        task_msg = "[Alcatel] Get Allowed Mode"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI,
            in_signature = 'u', out_signature = '',
            method_name="SetAllowedMode")
    def mgn_set_allowed_mode(self, mode):
        def function(task):
            # Get current system selection settings to determine current
            # domain mode
            res = self.__get_alcatel_system_selection_settings(task)
            prev_domain = res["domain"]

            # Default mode is ALLOWED_MODE_ANY
            new_mode = ALCATEL_MODE_AUTO
            new_order = ALCATEL_ORDER_AUTO

            # Translate MM2 mode code to Alcatel codes
            if mode == ALLOWED_MODE_2G_ONLY:
                new_mode = ALCATEL_MODE_GSM_ONLY
            elif mode == ALLOWED_MODE_3G_ONLY:
                new_mode = ALCATEL_MODE_WCDMA_ONLY
            elif mode == ALLOWED_MODE_2G_PREFERRED:
                new_order = ALCATEL_ORDER_GSM_THEN_WCDMA
            elif mode == ALLOWED_MODE_3G_PREFERRED:
                new_order = ALCATEL_ORDER_WCDMA_THEN_GSM

            # Write new system selection settings
            self.__set_system_selection_settings(task, new_mode, new_order, prev_domain)

        task_msg = "[Alcatel] Set Allowed Mode (mode %i)" % mode
        self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI,
            in_signature = '', out_signature = 'u',
            method_name="GetDomain")
    def mgn_get_domain(self):
        def function(task):
            res = self.__get_alcatel_system_selection_settings(task)

            translation_table = {
                ALCATEL_DOMAIN_CS_PS : DOMAIN_CS_PS,
                ALCATEL_DOMAIN_CS    : DOMAIN_CS,
                ALCATEL_DOMAIN_PS    : DOMAIN_PS,
            }

            # Translate Alcatel domain modes to MM2 ones
            if res["domain"] in translation_table:
                mm_domain = translation_table[res["domain"]]
            else:
                mm_domain = DOMAIN_ANY

            return mm_domain

        task_msg = "[Alcatel] Get Domain"
        return self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI,
            in_signature = 'u', out_signature = '',
            method_name="SetDomain")
    def mgn_set_domain(self, domain):
        def function(task):
            # Determine current mode and order
            res = self.__get_alcatel_system_selection_settings(task)
            prev_mode = int(res["mode"])
            prev_order = int(res["order"])

            # Translation table between MM2 domain codes and Alcatel ones
            translation_table = {
                DOMAIN_ANY   : ALCATEL_DOMAIN_CS_PS,
                DOMAIN_CS_PS : ALCATEL_DOMAIN_CS_PS,
                DOMAIN_CS    : ALCATEL_DOMAIN_CS,
                DOMAIN_PS    : ALCATEL_DOMAIN_PS,
            }
            new_domain = translation_table[domain]

            # Write new system selection settings
            self.__set_system_selection_settings(task, prev_mode, prev_order, new_domain)

        task_msg = "[Alcatel] Set Domain (domain %i)" % domain
        self.io.task_pool.exec_task(function, task_msg=task_msg)


    def __get_alcatel_system_selection_settings(self, task):
        cmd = "AT+SYSSEL?"
        regex = "\+SYSSEL: +(?P<band>\d*),(?P<mode>\d*),(?P<order>\d*),(?P<domain>\d*)"
        r_values = ["band", "mode", "order", "domain"]

        res = self.io.com.send_query({
            "type"     : "regex",
            "cmd"      : cmd,
            "task"     : task,
            "regex"    : regex,
            "r_values" : r_values,
        })

        # Build a new result dictionary with integer codes
        result = {}
        if res is not None:
            for key, value in res.iteritems():
                result[key] = int(value)

        # That seems improbable, but fallback to the default values
        else:
            for key in r_values:
                result[key] = 0

        return result

    def __set_system_selection_settings(self, task, mode, order, domain):
        cmd = "AT+SYSSEL=0,%d,%d,%d" % (mode, order, domain)
        self.io.com.send_query({
            "type"  : "simple",
            "cmd"   : cmd,
            "task"  : task,
        })
