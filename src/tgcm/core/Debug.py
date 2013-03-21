#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#
# Copyright (c) 2003-2010, Telefonica Móviles España S.A.U.
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
import inspect
import logging
import sys
import tgcm

ERROR_IGNORE=["GConf-WARNING"]

class ColorFormatter(logging.Formatter):
 
    def color(self, level=None):
        codes = {\
            None:       (0,   0),
            'DEBUG':    (0,   2), # gris
            'INFO':     (0,   0), # normal
            'WARNING':  (1,  34), # azul
            'ERROR':    (1,  31), # rojo
            'CRITICAL': (1, 101), # negro, fondo rojo
            }
        return (chr(27)+'[%d;%dm') % codes[level]
 
    def format(self, record):
        retval = logging.Formatter.format(self, record)
        return self.color(record.levelname) + retval + self.color()

class CustomOutputWriter(object) :
    """Just a simple example for a sys.stdout wrapper"""
    def __init__(self, orig_stdout, ignore_lines=['GConf-WARNING']):
        self.orig_stdout = orig_stdout
        self.line = ""
        self.ignore_lines=ignore_lines

    def write(self, text):
        if "\n" in text :
            lines = text.split("\n")
            self.__print_line(self.line + lines[0] + "\n")
            self.line = ""

            for l in lines[1:-1] :
                self.__print_line(l + "\n")

            if lines[-1] == '' :
                self.__print_line("\n")
            else:
                self.line = lines[-1]
        else:
            self.line = self.line + text

    def __print_line(self, line):
        for ignore in self.ignore_lines :
            if ignore in line :
                return
        if len(line) > 1 :
            self.orig_stdout.write(line)

def init_debug(log_file) :
    config_dir = os.path.join(os.environ["HOME"], ".tgcm")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    logging.basicConfig(level    = logging.DEBUG,
                        format   ='%(asctime)s %(levelname)-7s %(message)s',
                        datefmt  ='%m-%d %H:%M',
                        filename = log_file,
                        filemode ='w+')

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.ERROR)
    formatter = ColorFormatter('%(levelname)s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def debug(msg):
    ret = extra_info()
    logging.debug(ret + str(msg))

def info(msg):
    ret = extra_info()
    logging.info(ret + str(msg))

def warning(msg):
    ret = extra_info()
    logging.warning(ret + str(msg))

def error(msg):
    ret = extra_info()
    logging.error(ret + str(msg))
         
def critical(msg):
    ret = extra_info()
    logging.critical(ret + str(msg))

def extra_info():
    """Returns the current line number in our program."""
    try:
        line = inspect.currentframe().f_back.f_back.f_lineno
        file_name = os.path.basename(inspect.currentframe().f_back.f_back.f_code.co_filename)
        method_name = inspect.currentframe().f_back.f_back.f_code.co_name
        
        extra_msg = "[%s:%i] (%s) " % (file_name, line, method_name)
    except:
        return ""
    
    return extra_msg
