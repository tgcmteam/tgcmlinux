#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2012, Telefonica Móviles España S.A.U.
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

import os
import subprocess

class GSettingsCustom(object):
    def __init__(self):
        self.__check_gsettings_binary_exists()

    def __check_gsettings_binary_exists(self):
        self._gsettings_bin = None

        # Is 'gsettings' binary accesible somewhere in $PATH?
        for path in os.environ['PATH'].split(os.pathsep):
            gsettings_bin = os.path.join(path, 'gsettings')
            if os.path.exists(gsettings_bin) and os.access(gsettings_bin, os.X_OK):
                self._gsettings_bin = gsettings_bin

        if self._gsettings_bin is None:
            raise GSettingsCustomException('GSettings seems not available in the system')

    def get_string(self, schema, key):
        stdout = self.__get_something(schema, key)
        return stdout[1:-2]

    def get_bool(self, schema, key):
        stdout = self.__get_something(schema, key)
        stdout = stdout[0:-1]

        if stdout == 'false':
            return False
        elif stdout == 'true':
            return True
        else:
            raise GSettingsCustomException('Return value is not a boolean')

    def get_integer(self, schema, key):
        stdout = self.__get_something(schema, key)
        stdout = stdout[0:-1]
        return int(stdout)

    def get_list(self, schema, key):
        stdout = self.__get_something(schema, key)
        entries = [entry.strip("'") for entry in stdout[1:-2].split(', ')]
        return entries

    def __get_something(self, schema, key):
        command = [self._gsettings_bin]
        command.append('get')
        command.append(schema)
        command.append(key)

        command_desc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = command_desc.communicate()

        if stderr != '':
            exception = GSettingsCustomException(stderr)
            raise exception

        return stdout

    def set_string(self, schema, key, value):
        self.__set_something(schema, key, value)

    def set_bool(self, schema, key, value):
        value_str = str(value).lower()
        self.__set_something(schema, key, value_str)

    def set_integer(self, schema, key, value):
        value_str = str(value)
        self.__set_something(schema, key, value_str)

    def set_list(self, schema, key, value):
        value_str = repr(value)
        self.__set_something(schema, key, value_str)

    def __set_something(self, schema, key, value):
        command = [self._gsettings_bin]
        command.append('set')
        command.append(schema)
        command.append(key)
        command.append(value)

        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, err:
            raise GSettingsCustomException('GSettings failed to write key "%s" with value "%s": %s' % (key, repr(value), err.output))

class GSettingsCustomException(Exception):
    pass

if __name__ == '__main__':
    backend = GSettingsCustom()
    output = backend.get_string('org.gnome.system.proxy', 'mode')
    print output, repr(output), type(output)

    backend.set_string('org.gnome.system.proxy', 'mode', 'auto')

    output = backend.get_string('org.gnome.system.proxy', 'mode')
    print output, repr(output), type(output)

    ## Read and write booleans

    value = backend.get_bool('org.gnome.system.proxy.http', 'enabled')
    print value, repr(value), type(value)

    backend.set_bool('org.gnome.system.proxy.http', 'enabled', not value)

    value = backend.get_bool('org.gnome.system.proxy.http', 'enabled')
    print value, repr(value), type(value)


    ## Read and write integers

    value = backend.get_integer('org.gnome.system.proxy.http', 'port')
    print value, repr(value), type(value)

    backend.set_integer('org.gnome.system.proxy.http', 'port', value + 1)

    value = backend.get_integer('org.gnome.system.proxy.http', 'port')
    print value, repr(value), type(value)


    ## Read and write strings

    output = backend.get_string('org.gnome.system.proxy.http', 'host')
    print output, repr(output), type(output)

    backend.set_string('org.gnome.system.proxy.http', 'host', 'moco')

    output = backend.get_string('org.gnome.system.proxy.http', 'host')
    print output, repr(output), type(output)


    ## Read and write lists

    values_list = backend.get_list('org.gnome.system.proxy', 'ignore-hosts')
    print values_list, repr(values_list), type(values_list)

    backend.set_list('org.gnome.system.proxy', 'ignore-hosts', ['localhost', '127.0.0.0/8', '*.indra.es', '10,*', '172.*', '192.168.*', 'moco'])

    values_list = backend.get_list('org.gnome.system.proxy', 'ignore-hosts')
    print values_list, repr(values_list), type(values_list)


    ## Key not found exception

#    output = backend.get_string('org.gnome.system.foo', 'bar')
#    print output, repr(output), type(output)


    ## Invalid value set exception

#    backend.set_integer('org.gnome.system.proxy.http', 'port', 'moco')

    ## Invalid enum value

    backend.set_string('org.gnome.system.proxy', 'mode', 'moco')
