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
import sys
import gobject

class ModemStateMachine:
    def __init__(self, dev):
        self.dev = dev
        self.watchers = {}
        self.watchers_next_try = []
        self.loop_step = 0
        self.in_pause = False
    
    def start(self):
        self.init_watchers()

    def init_watchers(self):
        for item in dir(self.dev):
            if item.endswith("_init_st_m_watchers") :
                exec("self.dev.%s()" % item)

        self.watcher_executor_available=True
        gobject.timeout_add(1000, self.watcher_executor)
        
    def pause(self):
        self.execute_pre_pause_actions()
        self.in_pause = True

    def resume(self):
        self.execute_pre_resume_actions()
        self.in_pause = False

    def execute_pre_pause_actions(self):
        for item in dir(self.dev):
            if item.endswith("_st_m_pre_pause") :
                exec("self.dev.%s()" % item)

    def execute_pre_resume_actions(self):
        for item in dir(self.dev):
            if item.endswith("_st_m_pre_resume") :
                exec("self.dev.%s()" % item)

    def stop(self):
        self.watcher_executor_available=False

    def register_watcher(self, time_steps_list, func):
        for t in time_steps_list :
            if t not in self.watchers :
                self.watchers[t] = [func]
            else:
                self.watchers[t].append(func)
        

    def watcher_executor(self):
        if self.in_pause == True :
            return True
        
        if self.watcher_executor_available == False :
            return False

        next_try = False 

        n = len(self.watchers_next_try)
        a = 1
        while True:
            if self.watchers_next_try == [] :
                break
            else:
                func = self.watchers_next_try.pop(0)
                try:
                    info("retry %s of %s" % (a,n))
                    a += 1
                    func()
                except:
                    break

        if self.loop_step == 0 and len(self.watchers_next_try) > 0 :
            self.watchers_next_try = []

        self.loop_step = (self.loop_step + 1) % 60
        if self.loop_step in self.watchers :
            for func in self.watchers[self.loop_step] :
                if next_try == False :
                    try:
                        func()
                    except:
                        next_try = True
                else:
                    self.watchers_next_try.append(func)
        
        gobject.timeout_add(1000, self.watcher_executor)
        return False
    
    

  
