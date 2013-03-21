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

import tgcm.core.TrafficManager
from tgcm.ui.widgets.chart.Chart import Chart, LINE_TYPE


class TrafficGraph (Chart):

    # -- The callback becomes the rates in bytes per second but we need it in kilo bits per second
    PROBE_UNIT    = (8.0 / 1024.0)
    NUMBER_PROBES = (300)
    X_STEP        = (NUMBER_PROBES / 5)

    chart_options = {
        'padding': {'left': 50,},
        'shouldFill' : False,
        'legend': {
            'hide': False,
            'opacity' : 0.5,
            'position': {'top': 0, 'right': 30},
            },

        'background': {'baseColor': '#FFFFFF'},
        'axis': {
            'x': {
                'ticks': [{'label': '5m', 'v': 0 * X_STEP },
                          {'label': '4m', 'v': 1 * X_STEP },
                          {'label': '3m', 'v': 2 * X_STEP },
                          {'label': '2m', 'v': 3 * X_STEP },
                          {'label': '1m', 'v': 4 * X_STEP },
                          {'label': _('Now'), 'v': 5 * X_STEP }],
                'label': _('Time'),
                },
            'y': {'label': 'Kbits/s'},
            },

        'stroke': {'hide' : True},

        'colorScheme': {
            'name': 'fixed',
            'args': {
                'colors': ['#8def88', '#2584e5'],
                },
            },
    }


    class Probes():

        def __init__(self, probes):
            self.__rx     = [0.0] * (probes)
            self.__tx     = [0.0] * (probes)
            self.__probes = probes

        # -- For avoiding spikes which can lead to diagram distortions:
        # -- 1) add a probe with the average value between new and last probe
        # -- 2) duplicate the last probe
        def __add(self, axis, value):

            # -- First drop three probes
            axis.pop(0)
            axis.pop(0)
            axis.pop(0)

            # -- Calculate the average between the last probe and the new one
            average = (axis[-1] + value) / 2
            axis.append(average)

            # -- Duplicate the last probe
            axis.append(value)
            axis.append(value)

        # -- Add new probes to the graphic
        def add(self, rx, tx):
            self.__add(self.__rx, rx)
            self.__add(self.__tx, tx)

        # -- Return the values of the Rx rate
        def rx(self):
            _rx = map(lambda a, b: [a, b], range(self.__probes), self.__rx)
            return _rx

        # -- Return the values of the Tx rate
        def tx(self):
            _tx = map(lambda a, b: [a, b], range(self.__probes), self.__tx)
            return _tx

        # -- Return the maximal value included in both lists
        def max(self):
            _rx = max(self.__rx)
            _tx = max(self.__tx)
            return max(_rx, _tx)

        def reset(self):
            self.__rx = [0.0] * self.__probes
            self.__tx = [0.0] * self.__probes

        def lastRx(self):
            return self.__rx[-1]

        def lastTx(self):
            return self.__tx[-1]

        def lastSum(self):
            return (self.__rx[-1] + self.__tx[-1])

    def __init__(self):
        Chart.__init__(self, LINE_TYPE, self.chart_options)
        self.traffic_manager = tgcm.core.TrafficManager.TrafficManager()

        self.default_rows_number = 5
        self.default_row_step    = 10
        self.max_value           = self.default_row_step * self.default_rows_number

        self.traffic_manager.connect('update-instant-velocity' , self.__updated_traffic_info_cb)
        self.traffic_manager.connect('reset-instant-velocity'  , self.__reset_instant_velocity_cb)

        self.__probes            = self.Probes(self.NUMBER_PROBES)
        self.__probes_max        = 0.0

        self.__updated_traffic_info_cb(None, 0.0, 0.0)

    def __updated_traffic_info_cb(self, manager, rx, tx):
        self.__probes.add(rx * self.PROBE_UNIT, tx * self.PROBE_UNIT)
        self.__update_graph()

    def __update_graph(self):
        self.__recalculate_scale()
        self.options = self.__update_scale_options()

        self.set_data(((_('Received'), self.__probes.rx()), (_('Sent'), self.__probes.tx()), ))
        self.set_tooltip_text (_("Average Speed: %.2f Kbits/s\nDownload Speed: %.2f Kbits/s\nUpload Speed: %.2f Kbits/s") %
                              (self.__probes.lastSum(), self.__probes.lastRx(), self.__probes.lastTx()))

    def __update_scale_options(self):

        options   = self.chart_options

        options["axis"]["y"]['interval']  = self.max_value / self.default_rows_number
        options["axis"]["y"]['range']     = (0.0, self.max_value)

        return options

    # -- @XXX: Quick and dirty
    def __next_multiple(self, value):
        return value + (10 - (value % 10))

    def __recalculate_scale(self):

        _max = self.__probes.max()
        if self.__probes_max == _max:
            return

        # -- @TODO: Check if the value is inside the allowed range

        self.__probes_max = _max

        # # -- Get the next value to a multiple
        self.max_value = self.__next_multiple(_max)

        # -- For avoiding some wrong graphic pixels outside the maximal Y-axis, add a difference between
        # -- the maximal value and the max. probe
        if (self.max_value - _max) < (self.max_value * 0.02):
            self.max_value += self.__next_multiple(self.max_value * 0.04)

    def __reset_graph(self):
        self.__probes.reset()
        self.__probex_max = 0.0
        self.__update_graph()

    def __reset_instant_velocity_cb(self, traffic):
        self.__reset_graph()

if __name__ == '__main__':
    w = gtk.Window()
    c = TrafficGraph()
    w.add(c)
    w.show_all()

    gtk.main()
