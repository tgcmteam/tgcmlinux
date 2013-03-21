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

import gtk
import gobject

import tgcm
from tgcm.ui.widgets.themedwidgets import ThemedWidget
from tgcm.ui.MSD.MSDUtils import get_subbitmaps

class ThemedAnimate (ThemedWidget):
    def __init__ (self, params):
        self.hittest = params['hittest']
        if self.hittest == 'client':
            super (ThemedAnimate, self).__init__(params, windowless=False)
        elif self.hittest == 'transparent':
            super (ThemedAnimate, self).__init__(params, windowless=True)

        self.id = params['id']
        self.image = params['image']
        self.frames = int (params['frames'])
        self.fps = int (params['fps'])
        self.horizontal = params['horizontal']
        #self.resize = params['resize']
        self.tooltip = params['tooltip']
        self.visible = params['visible']
        self.play = params['play']

        self.pixbufs = get_subbitmaps (self.image, self.frames, self.width, self.height, self.horizontal)

        self.__is_playing = False
        self.__animation_frame = 1

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
            exec ("play = %s" % self.parse_var_string (self.play))
        except:
            play = False
        finally:
            if play:
                self.__do_animation ()
            else:
                self.__is_playing = False
                self.set_fixed_image (self.pixbufs[0])

    def __do_animation (self):
        if self.__is_playing:
            return False

        self.__is_playing = True
        self.__animation_frame = 1
        timeout = int((1/float(self.fps))*1000)
        gobject.timeout_add(timeout, self.__on_timeout)

    def __on_timeout(self, *args):
        if not self.__is_playing:
            return False

        self.set_fixed_image (self.pixbufs[self.__animation_frame])
        self.__animation_frame = (self.__animation_frame + 1) % self.frames
        if self.__animation_frame == 0:
            self.__animation_frame = 1

        while gtk.events_pending():
            gtk.main_iteration()

        return True
