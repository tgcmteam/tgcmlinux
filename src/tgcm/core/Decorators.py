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

import logging
import os
import inspect


def where_i_come():
    try:
        file_name = ""
        func_name = ""
        lineno = 0
        inspector = inspect.currentframe().f_back
        last_inspector = None
        while True:
            if not inspector.f_code.co_filename.endswith("Decorators.py"):
                if inspector.f_code.co_filename.endswith("Singleton.py") :
                    file_name = os.path.basename(inspector.f_back.f_code.co_filename)
                    lineno = inspector.f_back.f_lineno
                    func_name = None
                    return file_name, lineno, func_name

                if inspector.f_code.co_name == "__init__" :
                    file_name = os.path.basename(inspector.f_code.co_filename)
                    lineno = inspector.f_lineno
                    func_name = None
                    return file_name, lineno, func_name
                
                file_name = os.path.basename(inspector.f_code.co_filename)
                lineno = inspector.f_lineno
                if last_inspector != None :
                    func_name = inspector.f_code.co_name
                break
            last_inspector = inspector
            inspector = inspector.f_back
            
    except:
        file_name = "X"
        lineno = "1"

    return file_name, lineno, func_name
    
def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def newFunc(*args, **kwargs):
        file_name, lineno, func_name = where_i_come()
        if func_name != None :
            logging.warning ("[%s:%s:%s] The '%s' method is deprecated" % (file_name, lineno, func_name, func.func_code.co_name))
        else:
            logging.error ("[%s:%s] Using deprecated class" % (file_name, lineno))
        
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

    
def mobile_manager_crash(func):
    def newFunc(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except:
            file_name, lineno, func_name = where_i_come()
            logging.error ("[%s:%s:%s]  Cause Mobile Manager Crash" % (file_name,
                                                                       lineno ,
                                                                       func_name))
            return None
        
        return ret
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

