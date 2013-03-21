#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
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

import os.path

import tgcm
from Singleton import *

class ThemeManager (gobject.GObject):
    __metaclass__ = Singleton

    def __init__(self) :
        gobject.GObject.__init__(self)
        self.paths = self.__get_icon_hierarchy ()

    def get_icon (self, directory, icon):
        for path in self.paths:
            icon_name = os.path.join (path, directory, icon)
            if os.path.exists (icon_name):
                return icon_name
            else:
                icon_filename, dot, icon_extension = icon.rpartition ('.')
                icon_name_aux = '%s_normal.%s' % (icon_filename, icon_extension)
                icon_name_aux = os.path.join (path, directory, icon_name_aux)
                if os.path.exists (icon_name_aux):
                    return icon_name

        return None

    def __get_icon_hierarchy (self):
        icon_path = os.path.join (tgcm.icons_files_dir, 'theme')
        path0 = os.path.join (tgcm.themes_dir, tgcm.country_support, 'default')
        if tgcm.country_support == 'cz':
            path1 = os.path.join (icon_path, 'cz')
            path2 = os.path.join (icon_path, 'o2')
            path3 = os.path.join (icon_path, 'default')
            return [path0,path1, path2, path3]
        elif tgcm.country_support == 'de':
            path1 = os.path.join (icon_path, 'de')
            path2 = os.path.join (icon_path, 'o2')
            path3 = os.path.join (icon_path, 'default')
            return [path0,path1, path2, path3]
        elif tgcm.country_support == 'es':
            path1 = os.path.join (icon_path, 'default')
            return [path0,path1]
        elif tgcm.country_support == 'ie':
            path1 = os.path.join (icon_path, 'default')
            return [path0, path1]
        elif tgcm.country_support == 'uk':
            path1 = os.path.join (icon_path, 'uk')
            path2 = os.path.join (icon_path, 'o2')
            path3 = os.path.join (icon_path, 'default')
            return [path0,path1, path2, path3]
        else:
            path0 = os.path.join(tgcm.themes_dir, 'latam', 'ar', 'default')
            path1 = os.path.join (icon_path, 'latam')
            path2 = os.path.join (icon_path, 'default')
            return [path0,path1, path2]
