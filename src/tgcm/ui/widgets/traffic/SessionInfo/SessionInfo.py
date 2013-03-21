#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
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

import os
import gtk

import tgcm
import tgcm.core.TrafficManager

from tgcm.ui.MSD.MSDUtils import format_to_maximun_unit, gtk_builder_magic
from tgcm.ui.widgets.traffic import TrafficGraph

class SessionInfo (gtk.HBox) :
    def __init__(self):
        gtk.HBox.__init__(self)
        self.traffic_manager = tgcm.core.TrafficManager.TrafficManager()

        self.widget_dir = os.path.join(tgcm.widgets_dir , 'traffic', self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'SessionInfo.ui'), \
                prefix='si')

        self.traffic_widget = TrafficGraph()
        self.traffic_widget_area.add(self.traffic_widget)
        self.traffic_widget.show()
        self.add(self.main_widget)
        self.main_widget.show_all()

        self.main_widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.data_transfered_label.set_markup("<small><b>--</b></small>")

        self.max_speed = 0

        #Signals
        self.traffic_manager.connect("update-session-time", self.__update_session_time_cb)
        self.traffic_manager.connect("update-session-data-transfered" , self.__update_session_data_transfered_cb)
        self.traffic_manager.connect("reset-session-data-transfered"  , self.__reset_session_data_transfered_cb)
        # -- The received speed must be in kilo bytes per second
        self.traffic_manager.connect("update-session-max-speed" , self.__update_session_max_speed_cb)
        self.traffic_manager.connect("reset-session-max-speed"  , self.__reset_session_max_speed_cb)

    def __update_session_time_cb(self, traffic_manager, h, m, s):
        self.session_time_label.set_markup("<small>%02d:%02d:%02d</small>" % (h,m,s))

    def __update_session_data_transfered_cb(self, traffic_manager, bytes):
        self.data_transfered_label.set_markup("<small><b>%s</b></small>" % \
                format_to_maximun_unit(bytes,"GB","MB","KB","Bytes") )

    def __reset_session_data_transfered_cb(self, traffic_manager):
        self.data_transfered_label.set_markup("<small><b>--</b></small>")

    # -- The received speed must be in kilo bytes per second
    def __update_session_max_speed_cb(self, trafficm, data):
        new_speed = float(data * 8) / 1024.0
        _str = "<small><b>%.2f Kbits/s</b></small>" % new_speed
        self.maximum_speed_label.set_markup(_str)

    def __reset_session_max_speed_cb(self, trafficm):
        self.maximum_speed_label.set_markup("--")

if __name__ == '__main__':
    w = gtk.Window()
    b = SessionInfo()
    w.add(b)
    b.show()
    w.show()
    gtk.main()
