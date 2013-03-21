#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
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

import tgcm.core.XMLTheme
import tgcm.ui.widgets.dock
import tgcm.ui.widgets.themedwidgets


class LayoutLoader:
    def __init__ (self, layout, left=0, top=0):
        self.__layout = layout
        self.left = left
        self.top = top

    def get_size (self):
        if self.__layout.has_key ('size'):
            width = self.__layout['size']['width']
            height = self.__layout['size']['height']
            return (width, height)
        else:
            return (None, None)

    def get_min_size (self):
        if self.__layout.has_key ('border'):
            minX = self.__layout['border']['minX']
            minY = self.__layout['border']['minY']

            return (minX, minY)
        else:
            return (None, None)

    def get_services_toolbar(self, ThemedDock, ActManager, ConnManager):
        if self.__layout.has_key ('services'):
            services = self.__layout['services']
            services_toolbar = tgcm.ui.widgets.dock.ServicesToolbar(ThemedDock, ActManager, ConnManager, services, paddingX=services['paddingX'])

            left = services['left']
            top = services['top']
            return (services_toolbar, left, top)
        else:
            return (None, None, None)

    def get_background(self, pixbufs, is_advertising=False):
        if self.__layout.has_key('background'):
            if is_advertising:
                # If it is a dock with advertising, override the background
                # from the theme and use instead the parent one. That is
                # necessary because TGCM/Win creates two different windows
                # with different background. Those windows are glued together,
                # so they move at the same time.
                # In TGCM/Linux is not possible to do that, and instead we
                # create only one gtk.Window with the full background
                pixbuf = pixbufs['dock.bkgnd']
                background = tgcm.ui.widgets.themedwidgets.ThemedBackgroundWithAds()
            else:
                image = self.__layout['background']['image']
                pixbuf = pixbufs[image]
                background = tgcm.ui.widgets.themedwidgets.ThemedBackground()

            background.show_all()
            background.set_fixed_image(pixbuf)

            if self.__layout['background'].has_key('resize'):
                resize = self.__layout['background']['resize']
                if resize['type'] == 'frame':
                    background.set_resizable(resize['left'], resize['top'], resize['right'], resize['bottom'])
                if resize['type'] == 'stretch':
                    background.set_resizable(0, 0, 0, 0)
            else:
                background.set_no_resizable()

            return background
        else:
            return None

    def get_caption (self):
        if self.__layout.has_key ('caption'):
            caption_type = self.__layout['caption']['type']
            caption_top = self.__layout['caption']['top']
            caption_minimize = self.__layout['caption']['minimize']
            caption_maximize = self.__layout['caption']['maximize']

            return (caption_type, caption_top, caption_minimize, caption_maximize)
        else:
            return (None, None, None, None)

    def get_widgets (self):
        widgets = []

        if self.__layout.has_key ('widgets'):
            widgets_layout = self.__layout['widgets']
            for widget_layout in widgets_layout:
                if widget_layout['type'] == 'button':
                    widget = tgcm.ui.widgets.themedwidgets.ThemedButton(widget_layout)
                elif widget_layout['type'] == 'label':
                    widget = tgcm.ui.widgets.themedwidgets.ThemedLabel(widget_layout)
                elif widget_layout['type'] == 'bitmap':
                    widget = tgcm.ui.widgets.themedwidgets.ThemedBitmap(widget_layout)
                elif widget_layout['type'] == 'progress':
                    widget = tgcm.ui.widgets.themedwidgets.ThemedProgress(widget_layout)
                elif widget_layout['type'] == 'animate':
                    widget = tgcm.ui.widgets.themedwidgets.ThemedAnimate(widget_layout)
                elif widget_layout['type'] == 'widgetex':
                    # Do not instantiate this widget unless advertising is
                    # enabled, because it is only used for displaying ads
                    config = tgcm.core.Config.Config(tgcm.country_support)
                    if not config.is_ads_available():
                        continue
                    elif widget_layout['class'] == 'advertising':
                        widget = tgcm.ui.widgets.themedwidgets.ThemedWidgetEx(widget_layout)
                    elif widget_layout['class'] == 'sticky-layout':
                        xml_theme = tgcm.core.XMLTheme.XMLTheme()
                        layout = xml_theme.get_layout(widget_layout['params'])
                        layout_loader = LayoutLoader(layout, \
                                int(widget_layout['left']), \
                                int(widget_layout['top']))
                        widgets.extend(layout_loader.get_widgets())
                else:
                    continue

                if widget_layout.has_key ('resize'):
                    resize = widget_layout['resize']
                    if resize['type'] == 'frame':
                        widget.set_resizable (resize['left'], resize['top'], resize['right'], resize['bottom'])
                    if resize['type'] == 'stretch':
                        widget.set_resizable (0, 0, 0, 0)

                widget.set_margins(self.left, self.top)
                widgets.append(widget)

        return widgets

    def get_accelerators(self):
        substitutions = (('ctrl+', '<Ctrl>'), ('alt+', '<Alt>'), ('caps+', '<Shift>'))
        accelerators = {}
        if self.__layout.has_key('accelerators'):
            for layout_accel in self.__layout['accelerators']:
                # Attempt to sanitize TGCM/Win accelerators
                shortcut = layout_accel['key']
                for orig, final in substitutions:
                    shortcut = shortcut.replace(orig, final)

                # Check accelerator if it is valid
                action_id = layout_accel['action']
                key, mod = gtk.accelerator_parse(shortcut)
                if gtk.accelerator_valid(key, mod):
                    accelerators[action_id] = shortcut

        return accelerators
