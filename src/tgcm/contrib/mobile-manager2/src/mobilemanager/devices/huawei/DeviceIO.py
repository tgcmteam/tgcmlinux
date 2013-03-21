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

import mobilemanager.devices.DeviceIO

class DeviceIO (mobilemanager.devices.DeviceIO.DeviceIO) :
    def actions_pre_start(self):
        mobilemanager.devices.DeviceIO.DeviceIO.actions_pre_start(self)

        def function(task):
            self.com.add_ignore_strings("^\^BOOT:.*")
            self.com.add_ignore_strings("^\^RSSI:.*")
            self.com.add_ignore_strings("^\^SIMST:.*")
            self.com.add_ignore_strings("^\^SRVST:.*")
            self.com.add_ignore_strings("^\^DSFLOWRPT:.*")
            self.com.add_ignore_strings("^\^MODE:.*")
            self.com.add_ignore_strings("^\^CSNR:.*")
            self.com.send_query({"cmd" : "AT^PORTSEL=1", "task" : task})

        self.task_pool.exec_task(function, task_msg="[Huawei] actions at start")

    def actions_pre_resume(self):
        mobilemanager.devices.DeviceIO.DeviceIO.actions_pre_resume(self)

        def function(task):
            self.com.send_query({"cmd" : "AT^PORTSEL=1", "task" : task})

        self.task_pool.exec_task(function, task_msg="[Huawei] actions at resume")
