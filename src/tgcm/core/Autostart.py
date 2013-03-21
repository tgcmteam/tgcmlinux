#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2013, Telefonica Móviles España S.A.U.
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

import os
import shutil
import gio
import gobject
from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry

import tgcm
import Config


class Autostart(gobject.GObject):
    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.config = Config.Config(tgcm.country_support)

        # Determine the path for XDG autostart dirs
        self.autofile_name = 'tgcm-%s.desktop' % tgcm.country_support
        self.user_autodir = None
        for foo in BaseDirectory.load_config_paths('autostart'):
            if foo.startswith(os.path.expanduser('~')):
                self.user_autodir = foo
            else:
                self.system_autodir = foo

        self.__create_desktop_entry_if_necessary()

        # Listen to file changes
        myfile = gio.File(self.user_autofile)
        self.desktopentry_monitor = myfile.monitor_file()
        self.desktopentry_monitor.connect('changed', self.on_desktopentry_changed)

    def __create_desktop_entry_if_necessary(self):
        # Create user autostart dir if it does not exists
        if self.user_autodir is None:
            self.user_autodir = BaseDirectory.save_config_path('autostart')

        # It it does not exists an autostart file for TGCM in userdir,
        # create a copy from the global one
        self.user_autofile = os.path.join(self.user_autodir, self.autofile_name)
        if not os.path.exists(self.user_autofile):
            autofile_path = os.path.join(self.system_autodir, self.autofile_name)
            shutil.copy(autofile_path, self.user_autofile)

            # Honor 'launch-startup' policy in regional-info.xml file
            self.desktopentry = DesktopEntry(self.user_autofile)
            is_autostart = self.config.check_policy('launch-startup')
            self.set_enabled(is_autostart)
        else:
            self.desktopentry = DesktopEntry(self.user_autofile)


    def is_enabled(self):
        self.__create_desktop_entry_if_necessary()

        # Check if the DesktopEntry object has an autostart attribute
        if self.desktopentry.hasKey('X-GNOME-Autostart-enabled'):
            is_autostart = self.desktopentry.get('X-GNOME-Autostart-enabled', \
                    type='boolean')
        else:
            is_autostart = True

        if self.desktopentry.hasKey('Hidden'):
            is_shown = not self.desktopentry.get('Hidden', type='boolean')
        else:
            is_shown = True

        return is_shown and is_autostart

    def set_enabled(self, value):
        self.__create_desktop_entry_if_necessary()

        value = str(value).lower()
        self.desktopentry.set('X-GNOME-Autostart-enabled', value)
        self.desktopentry.removeKey('Hidden')
        self.desktopentry.write()

    def on_desktopentry_changed(self, monitor, myfile, other_file, event):
        if event == gio.FILE_MONITOR_EVENT_DELETED:
            self.__create_desktop_entry_if_necessary()

        is_enabled = self.is_enabled()
        self.emit('changed', is_enabled)

gobject.type_register(Autostart)


if __name__ == '__main__':
    tgcm.country_support = 'es'
    autostart = Autostart()
