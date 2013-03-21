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
import time
import gio

class DeviceIO (mobilemanager.devices.DeviceIO.DeviceIO) :
    
    def actions_pre_start(self):
        
        def function(task):
            self.com.send_query({"cmd" : "AT$NWDMAT=1" , "task" : task})

        self.task_pool.exec_task(function, task_msg="[Novatel] actions at start")
        mobilemanager.devices.DeviceIO.DeviceIO.actions_pre_start(self)

    def actions_pre_resume(self):
        mobilemanager.devices.DeviceIO.DeviceIO.actions_pre_resume(self)

        def function(task):
            self.com.send_query({"cmd" : "AT$NWDMAT=1" , "task" : task})

        self.task_pool.exec_task(function, task_msg="[Novatel] actions at resume", timeout=10)

        # -- Some Novatel Modems, like the MC996D, request the PIN after resuming and need a long delay
        ret = self.device.mgc_refresh_unlock_status()
        if ret is False:
            time.sleep(4)
            self.device.mgc_refresh_unlock_status()
