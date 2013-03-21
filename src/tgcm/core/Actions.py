#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
#
# Copyright (c) 2003-2007, Telefonica Móviles España S.A.U.
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

import gobject
import compileall
import os
import imp

import tgcm
import Config
from Singleton import *

class ActionManager (gobject.GObject):
    __metaclass__ = Singleton

    __gsignals__ = {
        'action-install-status-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, \
                (gobject.TYPE_PYOBJECT, gobject.TYPE_BOOLEAN)),
        'url-launcher-install-status-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, \
                (gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)),
    }

    def __init__ (self):
        gobject.GObject.__init__(self)

        self.actions_names = {
            'MSDAInternet'  : 'internet',
            'MSDAIntranet'  : 'intranet',
            'MSDAMovilidad' : 'wifi',
            'MSDABookmarks' : 'favorites',
            'MSDASendSMS'   : 'sms'
        }

        if tgcm.country_support == 'cz':
            self.actions_names['CZRecharge'] = 'prepay'
            self.actions_names['CZSelfcare'] = 'selfcare'
        elif tgcm.country_support == 'de' :
            self.actions_names['DERecharge'] = 'prepay'

        self.conf = Config.Config()

        compileall.compile_dir(tgcm.actions_py_dir, quiet=1)
        self.__actions = self.__load_actions()

    def get_original_services_order (self):
        return self.conf.get_original_services_order ()

    def get_actions (self):
        available_actions = self.conf.get_original_actions_order()

        action_list = {}
        for action in self.__actions:
            if action in available_actions:
                action_list[action] = self.__actions[action]
        return action_list

    def get_action (self, codename):
        for action in self.__actions:
            if action == codename:
                obj = self.__actions[action]
                return obj

    def get_action_list(self):
        acts_list ={}
        actions = self.conf.get_launcher_items_order()

        for x in actions:
            if self.__actions.has_key(x):
                obj = self.__actions[x]
                acts_list[x] = obj

        return acts_list

    def launch_action(self, codename):
        obj = self.__actions[self.actions_names[codename]]
        obj.launch_action()

    def launch_help(self, codename):
        obj = self.__actions[codename]
        obj.launch_help()

    def __import_action_compiled (self, filecode, name):
        module = imp.load_compiled(name, filecode)
        return module

    def __load_actions (self):
        action_list = {}

        is_latam = self.conf.is_latam(tgcm.country_support)
        for action in os.listdir(tgcm.actions_py_dir):
            # Do not attempt to load not-services directories
            if action == ".svn":
                continue

            # Do not load "MSDAMovilidad" in Latam
            elif is_latam and action == 'MSDAMovilidad':
                continue

            # Do not load some country-specific service if it is not necessary
            elif tgcm.country_support != "de" and action == "DERecharge":
                continue
            elif tgcm.country_support != "cz" and action == "CZRecharge":
                continue
            elif tgcm.country_support != "cz" and action == "CZSelfcare":
                continue

            if (action[0:8]!='Makefile'):
                module = self.__import_action_compiled(os.path.join(tgcm.actions_py_dir , "%s/%s.pyc" % (action,action)), action)
                exec ("action_obj = module.%s()" % action)
                action_list[action_obj.config_key] = action_obj
                action_obj.connect ('install-status-changed', self.__on_action_install_status_changed)

        return action_list

    def set_url_launcher_installed (self, url_launcher_id, installed):
        self.conf.set_url_launcher_installed (url_launcher_id, installed)
        self.emit ('url-launcher-install-status-changed', url_launcher_id, installed)

    def __on_action_install_status_changed (self, action_obj, installed, data=None):
        self.emit ('action-install-status-changed', action_obj, installed)
