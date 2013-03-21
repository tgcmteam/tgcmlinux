#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2011, Telefonica Móviles España S.A.U.
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

import logging
import optparse
import os.path
import re
import subprocess
import sys
import StringIO

# Configure logging
logger = logging.getLogger('convert_trayicons')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def main():
    parser = optparse.OptionParser()
    parser.add_option('-q', '--quiet', action='store_true', dest='quiet', default=False,
            help='turn of any output')
    parser.add_option('-d', '--debug', action='store_true', dest='debug', default=False,
            help='print debugging messages to standard output')
    parser.add_option('-s', '--add-suffix', action='store_true', dest='create_suffix', default=False,
            help='add to the output file a suffix to identify the type of the resource')
    parser.add_option('-k', '--taskbar-icon', action='store_true', dest='taskbar', default=False,
            help='try to choose the most suitable image for a taskbar icon')
    parser.add_option('-m', '--main-icon', action='store_true', dest='main', default=False,
            help='try to choose the most suitable image for an application icon')
    parser.add_option('-e', '--service-icon', action='store_true', dest='service', default=False,
            help='try to choose the most suitable image for a service icon')
    parser.add_option('-t', '--tray-icon', action='store_true', dest='trayicon', default=False,
            help='try to choose the most suitable image for a trayicon')
    parser.add_option('-o', '--output', dest='output', metavar='FILE',
            help='save image to FILE')
    (option, args) = parser.parse_args()

    # Configure logging
    console_level = logging.INFO
    if option.quiet:
        console_level = logging.ERROR
    if option.debug:
        console_level = logging.DEBUG
    logger.setLevel(console_level)

    # Check if 'icotool' binary is somewhere in PATH
    icotool_available = False
    for path in os.environ['PATH'].split(os.pathsep):
        exe_file = os.path.join(path, 'icotool')
        if os.path.exists(exe_file) and os.access(exe_file, os.X_OK):
            icotool_available = True
    if not icotool_available:
        logger.error('Package "icoutils" is not installed in the system.')
        sys.exit(-1)

    ### Image requirements table ###
    # It will try to select the best resource in the
    # icon according to the requirements in this table.
    requirements = []
    if option.trayicon:
        requirements.append({'width' : 16, 'height' : 16, 'bit-depth' : 32})
        requirements.append({'width' : 16, 'height' : 16})
    elif option.taskbar:
        requirements.append({'width' : 16, 'height' : 16, 'bit-depth' : 32})
        requirements.append({'width' : 16, 'height' : 16})
        requirements.append({'width' : 32, 'height' : 32, 'bit-depth' : 32})
        requirements.append({'width' : 32, 'height' : 32})
    elif option.main:
        requirements.append({'width' : 256, 'height' : 256, 'bit-depth' : 32})
        requirements.append({'width' : 64, 'height' : 64, 'bit-depth' : 32})
        requirements.append({'width' : 32, 'height' : 32, 'bit-depth' : 32})
        requirements.append({'width' : 64, 'height' : 64})
        requirements.append({'width' : 32, 'height' : 32})
        requirements.append({})
    elif option.service:
        requirements.append({'width' : 32, 'height' : 32, 'bit-depth' : 32})
        requirements.append({'width' : 32, 'height' : 32})
    else:
        requirements.append({})
        suffix = None

    # Optionally add a suffix to output file
    suffix = None
    if option.create_suffix:
        if option.trayicon:
            suffix = 'trayicon'
        elif option.taskbar:
            suffix = 'taskbar'
        elif option.main:
            suffix = 'main'
        elif option.service:
            suffix = 'service'

    # Extract the best resource of each icon file passed as a argument
    for filepath in args:
        if not os.path.exists(filepath):
            logger.error('File "%s" does not exist!\nExisting.' % filepath)
            sys.exit(-1)

        logger.debug('Extracting best resource for "%s" file' % filepath)

        if (suffix is not None) and (len(suffix) > 0):
            output = '%s_%s.png' % (os.path.splitext(filepath)[0], suffix)
        else:
            output = '%s.png' % os.path.splitext(filepath)[0]

        if (option.output is not None) and (len(option.output) > 0):
            output = option.output

        icon = IconResource(filepath, output)
        if icon.extract_best_resource(requirements):
            logger.info('File "%s" created successfully!' % icon.output)
        else:
            logger.error('A problem has occurred processing file "%s"!\nExiting.' % icon.filepath)
            sys.exit(-1)


class IconResource():
    def __init__(self, filepath, output):
        self.regex = re.compile('--([a-z-]+)=(\d+)')
        self.filepath = os.path.abspath(filepath)
        self.output = os.path.abspath(output)
        self.resources = {}
        self._load_info()

    def extract_best_resource(self, requirements):
        index = self._get_resource_index(requirements)
        return self._extract_resource(index) == 0

    def _get_resource_index(self, requirements):
        for required_values in requirements:
            logger.debug('Looking for properties: %s' % required_values)
            for index, resource in self.resources.iteritems():
                resource_found = True
                for key, required_value in required_values.iteritems():
                    resource_found = resource_found and (resource[key] == required_value)
                if resource_found:
                    logger.debug('> Suitable resource found at index "%d"' % index)
                    return index
                else:
                    logger.debug('> Not suitable, trying the next one...')
        return None

    def _load_info(self):
        command = ['icotool']
        command.append('--list')
        command.append(self.filepath)

        # Call icotool binary with the proper parameters
        logger.debug('Calling: "%s"' % ' '.join(command))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = StringIO.StringIO(stdout)
        stderr = StringIO.StringIO(stderr)

        # Check icotool return code
        logger.debug('Return code is "%s"' % process.returncode)
        if process.returncode != 0:
            logger.error('Return code was different from 0!!')  # Error condition

            logger.debug('Contents of stderr:')
            for line in stderr.readlines():
                logger.debug('> %s' % line.strip())

            logger.debug('Exiting...')
            sys.exit(-1)

        # Process icotool stdout line by line
        logger.debug('Contents of stdout:')
        for line in stdout.readlines():
            logger.debug('> %s' % line.strip())
            (index, info) = self._process_info_line(line)
            if index is not None:   # Check if the output line was correctly processed
                self.resources[index] = info

        # Check that data structure was correctly created
        attribs = ('width', 'height', 'bit-depth', 'palette-size')
        for index, resource in self.resources.iteritems():
            for key in attribs:
                assert resource.has_key(key), 'Index "%s" does not have key "%s"' % (index, key)

    def _process_info_line(self, line):
        image_index = None
        image_info = {}
        for argument in line.split():
            m = self.regex.match(argument)
            if m is not None:
                key = m.group(1)
                value = m.group(2)
                if key == 'index':
                    image_index = int(value)
                else:
                    image_info[key] = int(value)
        return (image_index, image_info)

    def _extract_resource(self, index):
        command = ['icotool']
        command.append('--extract')
        command.append('-i')
        command.append(str(index))
        command.append(self.filepath)
        command.append('-o')
        command.append(self.output)

        logger.debug('Calling: "%s"' % ' '.join(command))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        return process.returncode


if __name__ == '__main__':
    main()
