#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#
# Copyright (c) 2003-2012, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import tgcm
import tgcm.core.Actions


class MSDActionsManager:
    def __init__(self, conn_manager):
        tgcm.info("Init tgcmActionsManager")
        self._actions_manager = tgcm.core.Actions.ActionManager()
        self.conn_manager = conn_manager
        self.systray = None

        self.action_list = self._actions_manager.get_actions()

    def set_systray(self, systray):
        self.systray = systray

    def set_connections_model(self, model):
        for x in self.action_list.keys():
            obj = self.action_list[x]
            obj.set_connections_model(model)

    def connect_signals(self):
        for x in self.action_list.keys():
            obj = self.action_list[x]
            obj.connect_signals()

    def launch_action(self, action_codename):
        obj = self.action_list[action_codename]
        obj.launch(self.conn_manager)

    def launch_help(self, action_codename):
        obj = self.action_list[action_codename]
        obj.launch_help()
