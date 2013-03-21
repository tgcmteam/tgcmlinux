#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           Roberto Majadas <roberto.majadas@openshine.com>
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
from tgcm.ui.widgets.themedwidgets import ThemedWidget

class ThemedProgress (ThemedWidget):
    def __init__ (self, params):
        self.hittest = params['hittest']
        if self.hittest == 'client':
            super (ThemedProgress, self).__init__(params, windowless=False)
        elif self.hittest == 'transparent':
            super (ThemedProgress, self).__init__(params, windowless=True)

        self.id = params['id']
        #self.resize = params['resize']
        self.tooltip = params['tooltip']
        self.states = params['states']
        self.image = params['image']

        self.visible = params['visible']
        self.status = params['status']

    def check_vars (self):
        try:
            exec ("visible = %s" % self.parse_var_string (self.visible))
        except:
            visible = False
        finally:
            if visible:
                self.show_all ()
            else:
                self.hide_all ()
                return

        try:
            exec ("state = %s" % self.parse_var_string (self.status))
        except:
            state = 0
        finally:
            if len(self.states) > state:
                self.set_fixed_image (self.states[state])
            else:
                self.set_fixed_image (self.states[0])

        exec ("tooltip = '%s'" % self.parse_text_string (self.tooltip))
        self.container.set_tooltip_text (tooltip)
