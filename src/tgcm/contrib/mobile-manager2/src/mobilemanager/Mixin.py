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

import inspect
def mixin(cls):
    """
    mixes-in a class (or a module) into another class. must be called from within
    a class definition. `cls` is the class/module to mix-in
    """
    locals = inspect.stack()[1][0].f_locals
    if "__module__" not in locals:
        raise TypeError("mixin() must be called from within a class definition")

    # copy the class's dict aside and perform some tweaking
    dict = cls.__dict__.copy()
    dict.pop("__doc__", None)
    dict.pop("__module__", None)

    # __slots__ hell
    slots = dict.pop("__slots__", [])
    if slots and "__slots__" not in locals:
        locals["__slots__"] = ["__dict__"]
    for name in slots:
        if name.startswith("__") and not name.endswith("__"):
            name = "_%s%s" % (cls.__name__, name)
        dict.pop(name)
        locals["__slots__"].append(name)

    # mix the namesapces
    locals.update(dict)
