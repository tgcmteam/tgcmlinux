#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
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


import gtk
import cairo
import tgcm

from pycha.chart import DEFAULT_OPTIONS
from pycha.bar import HorizontalBarChart, VerticalBarChart
from pycha.line import LineChart
from pycha.pie import PieChart
from pycha.scatter import ScatterplotChart
from pycha.stackedbar import StackedVerticalBarChart, StackedHorizontalBarChart

CHART_TYPES = (
    VerticalBarChart,
    HorizontalBarChart,
    LineChart,
    PieChart,
    ScatterplotChart,
    StackedVerticalBarChart,
    StackedHorizontalBarChart,
    )

(VERTICAL_BAR_TYPE,
 HORIZONTAL_BAR_TYPE,
 LINE_TYPE,
 PIE_TYPE,
 SCATTER_TYPE,
 STACKED_VERTICAL_BAR_TYPE,
 STACKED_HORIZONTAL_BAR_TYPE) = range(len(CHART_TYPES))

class Chart (gtk.DrawingArea):
    def __init__(self, chart_type=0, options=None):
        gtk.DrawingArea.__init__(self)
        if options == None :
            self.options = DEFAULT_OPTIONS
        else:
            self.options = options
        self.data_sets = None
        self.chart_type = chart_type
        self.chart = None

        self.connect('expose_event',
                     self.__expose_event)
        self.connect('size_allocate',
                     self.__size_allocate_event)

        self.__surface = None
        self.__chart_factory = CHART_TYPES[self.chart_type]

    def __get_chart(self, width, height):

        # -- Create the surface only if required
        if self.__surface is None or (self.__surface.get_width() != width or self.__surface.get_height() != height):
            self.__surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)

        chart = self.__chart_factory(self.__surface, self.options)
        chart.addDataset(self.data_sets)
        chart.render()
        return chart

    def __expose_event(self, widget, event, data=None):
        if self.chart is None:
            return

        cr = widget.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y,
                     event.area.width, event.area.height)
        cr.clip()
        cr.set_source_surface(self.chart.surface, 0, 0)
        cr.paint()

    def __size_allocate_event(self, widget, event, data=None):
        if self.chart is not None:
            self.__refresh()

    def __refresh(self, action=None):
        alloc = self.get_allocation()
        self.chart = self.__get_chart(alloc.width, alloc.height)
        self.queue_draw()

    def set_data (self, data) :
        self.data_sets = data
        self.__refresh()

    def set_options (self, options):
        self.options = options
        self.__refresh()

if __name__ == '__main__':
    w = gtk.Window()
    c = Chart(LINE_TYPE)
    w.add(c)
    c.set_data(
        (
            ('dataSet 1', ((0, 1), (1, 3), (2, 2.5))),
            ('dataSet 2', ((0, 2), (1, 4), (2, 3))),
            ('dataSet 3', ((0, 5), (1, 1), (2, 0.5))),
        )
        )
    w.show_all()
    gtk.main()
