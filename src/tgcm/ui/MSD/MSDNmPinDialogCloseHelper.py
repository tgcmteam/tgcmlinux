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

import os
import gtk
import psutil
import wnck

import tgcm


class MSDNmPinDialogCloseHelper:
    def __init__(self):
        self.keywords = ('pin', 'puk')

        self.__find_nm_applet_process()

        # Process pending gtk+ events so that wnck can find out about
        # existing windows
        while gtk.events_pending():
            gtk.main_iteration()

        self.screen = wnck.screen_get_default()
        for window in self.screen.get_windows():
            self.__check_and_close_pin_dialog(window)

        # Listen new dialogs to appear
        self.screen.connect('window-opened', self.__on_window_opened)

    def __find_nm_applet_process(self):
        uid = os.getuid()
        self.nm_applet_process = None
        for process in psutil.process_iter():
            if (process.name == 'nm-applet') and (process.uids.real == uid):
                self.nm_applet_process = process
                break

    def __check_and_close_pin_dialog(self, window):
        if (self.nm_applet_process is None) or \
                (not psutil.pid_exists(self.nm_applet_process.pid)):
            self.__find_nm_applet_process()

        if self.nm_applet_process is None:
            return

        application = window.get_application()
        if application.get_pid() != self.nm_applet_process.pid:
            return

        for key in self.keywords:
            if key in window.get_name().lower():
                tgcm.debug('Closing window "%s" (PID: %d)' % \
                        (window.get_name(), self.nm_applet_process.pid))
                timestamp = gtk.get_current_event_time()
                window.close(timestamp)
                break

    def __on_window_opened(self, screen, window, user_data=None):
        self.__check_and_close_pin_dialog(window)


if __name__ == '__main__':
    example = MSDNmPinDialogCloseHelper()
    gtk.main()
