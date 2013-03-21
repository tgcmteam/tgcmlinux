#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2012, Telefonica Móviles España S.A.U.
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

import tgcm
import tgcm.core.Advertising

import tgcm.ui
from tgcm.ui.widgets.themedwidgets import ThemedWidget


class ThemedWidgetEx(ThemedWidget):
    def __init__(self, params):
        super(ThemedWidgetEx, self).__init__(params)

        self.id = params['id']
        self.params = params['params']

        self.advertising = tgcm.core.Advertising.Advertising()
        self.refresh_image()

        self.connect_after('button_release_event', \
                self.__on_button_release_event)
        self.ad_signal = self.advertising.connect('updated', \
                self.__on_advertising_updated)

    def check_vars(self):
        self.show_all()

    def destroy(self):
        self.ad_signal.disconnect()
        ThemedWidget.destroy(self)

    def refresh_image(self):
        if self.params == 'main':
            pixbuf = self.advertising.get_dock_advertising()[0]
        else:
            pixbuf = self.advertising.get_service_advertising()[0]
        pixbuf = pixbuf.scale_simple( \
                self.width, self.height, gtk.gdk.INTERP_BILINEAR)
        self.set_fixed_image(pixbuf)

    def set_visible(self, visible):
        pass

    def __on_button_release_event(self, widget, event, params=None):
        self.set_sensitive(False)
        dock = tgcm.ui.ThemedDock()
        dock.functions['app.open_ad'](self.params, event=event)
        self.set_sensitive(True)

    def __on_advertising_updated(self, sender):
        self.refresh_image()
