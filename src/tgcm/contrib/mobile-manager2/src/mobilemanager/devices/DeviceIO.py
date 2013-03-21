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

import os
import gobject

from mobilemanager.Logging import debug, info, warning, error
from SerialPort import ModemPort, CommunicationPort, TaskPool

class DeviceIO :

    RETURN_SUCCESS = 0
    RETURN_FAILURE = 1

    def __init__(self, device, modem_path, com_path):
        self.modem_path = modem_path
        self.com_path   = com_path
        self.device     = device

        self.task_pool     = TaskPool(device)
        self.modem         = ModemPort(modem_path, self.task_pool)
        self.com           = CommunicationPort(com_path, self.task_pool)
        self.modem_is_open = False

    def start(self):
        try:
            self.task_pool.start()
            self.com.open()
            self.actions_pre_start()
            return self.RETURN_SUCCESS
        except:
            return self.RETURN_FAILURE
        
    def stop(self):
        try:
            self.actions_pre_stop()
            self.task_pool.stop()
            self.com.close()
            if self.modem_is_open == True :
                self.modem.close()
            
            return True
        except:
            return False

    def pause(self):
        try:
            self.actions_pre_pause()
            self.task_pool.stop()
            self.com.close()
            if self.modem_is_open == True :
                self.modem.close()
            
            return True
        except:
            return False
    
    def resume(self):
        try:
            self.task_pool.start()
            self.com.open()
            self.actions_pre_resume()
            return True
        except:
            return False

    def actions_pre_start(self):
        def function(task):
            cmd = 'AT+CFUN?'
            regex = '\+CFUN:\ +(?P<is_on>\d*)'
            r_values = ["is_on"]

            res = self.com.send_query({"type"     : "regex",
                                       "cmd"      : cmd,
                                       "task"     : task,
                                       "regex"    : regex,
                                       "r_values" : r_values})

            if res != None and bool(int(res["is_on"])) == False :
                self.com.send_query({"cmd" : "AT+CFUN=1" , "task" : task})

        self.task_pool.exec_task(function, task_msg="[Generic] actions at start")

    def actions_pre_stop(self):
        pass

    def actions_pre_pause(self):
        def function(task):
            self.com.send_query({"cmd"  : "AT+CFUN=0" ,
                                 "task" : task})

        self.task_pool.exec_task(function, task_msg="[Generic] actions at pause")

    def actions_pre_resume(self):        
        def function(task):
            self.com.send_query({"cmd"  : "AT+CFUN=1" ,
                                 "task" : task})

        self.task_pool.exec_task(function, task_msg="[Generic] actions at resume")

    def enable_modem_port(self, enable):
        if enable == True and self.modem_is_open == False :
            self.modem.open()
            self.modem_is_open = True
        elif enable == False and self.modem_is_open == True :
            self.modem.close()
            self.modem_is_open = False
    
    def is_modem_port_enabled(self):
        return self.modem_is_open

