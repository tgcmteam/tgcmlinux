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

import tgcm.ui
import tgcm.ui.widgets.traffic

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

class DataUsedInfo (gtk.HBox) :
    def __init__(self, external_traffic_history_label):
        gtk.HBox.__init__(self)
        self.traffic_manager = tgcm.core.TrafficManager.TrafficManager()

        self.widget_dir = os.path.join(tgcm.widgets_dir , 'traffic', self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.widget_dir, 'DataUsedInfo.ui'), \
                prefix='dui')

        self.traffic_history_widget = tgcm.ui.widgets.traffic.TrafficHistoryGraph(external_traffic_history_label)
        self.traffic_history_widget_area.add(self.traffic_history_widget)
        self.traffic_history_widget.show()
        self.add(self.main_widget)
        self.main_widget.show_all()

        self.main_widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

    def reload_graph (self):
        self.traffic_history_widget.reload_data()

if __name__ == '__main__':
    tgcm.country_support="es"
    w = gtk.Window()
    b = DataUsedInfo()
    w.add(b)
    b.show()
    w.show()
    gtk.main()
