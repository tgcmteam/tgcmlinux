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

import tgcm
import tgcm.core.FreeDesktop
import tgcm.ui
from tgcm.core.DeviceExceptions import DeviceIncorrectPassword
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, replace_wrap_label,\
    info_dialog, error_dialog


class UnlockDeviceDialog(gtk.Dialog):
    def __init__(self, device, parent=None, turn_off_if_cancel=False, \
            on_success_callback=None):
        self.device = device
        self.turn_off_if_cancel = turn_off_if_cancel
        self.on_success_callback = on_success_callback
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()

        title = _('Enter network PIN code')
        gtk.Dialog.__init__(self, title, parent, \
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, \
                 gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.windows_dir = os.path.join(tgcm.windows_dir, 'UnlockDeviceDialog')
        filename = os.path.join(self.windows_dir, 'UnlockDeviceDialog.ui')
        gtk_builder_magic(self, \
                filename=filename, \
                prefix='ud')

        self.set_border_width(6)
        self.vbox.pack_start(self.contents_vbox)
        if parent is None:
            parent = tgcm.ui.ThemedDock().get_main_window()
        self.set_transient_for(parent)
        self.unlock_code_entry.grab_focus()

        # Ugly hack to wrap a gtk.Label
        labels = (self.info_label, self.num_retries_label)
        for label in labels:
            text = label.get_label()
            replace_wrap_label(label, text)

        # Listen for removal of main WWAN device
        self.device_manager.connect('device-removed', self._on_device_removed)

        # Disable OK button if unlock code field is empty
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        self.unlock_code_entry.connect('changed', self._on_unlock_code_entry_changed)

        # Events necessary to avoid dialog to close
        self.connect('response', self._on_dialog_response)
        self.connect('close', self._on_dialog_close)
        self.connect('delete_event', self._on_dialog_close)

    def _unlock_device(self, unlock_code):
        try:
            self.device.unlock_operator(unlock_code)
            title = _('Unlocking succeeded')
            markup = '<b>%s</b>' % title
            message = _('You succeed in unlocking your device network lock.')
            info_dialog(message, title=title, markup=markup, parent=self)
            return True

        # Incorrect password case
        except DeviceIncorrectPassword:
            title = _('Error unlocking network PIN')
            markup = '<b>%s</b>' % title
            message = _('The network PIN code entered is incorrect. Please try again.')
            error_dialog(message, title=title, markup=markup, parent=self)

        # Unknown case, e.g. device locked
        except:
            title = _('Error unlocking network PIN')
            markup = '<b>%s</b>' % title
            message = _('It is not possible to unlock the device. Please contact your operator.')
            error_dialog(message, title=title, markup=markup, parent=self)

        return False

    # Device Manager callbacks

    def _on_device_removed(self, sender, object_path):
        if self.device.object_path == object_path:
            self.hide()

    # UI callbacks

    def _on_unlock_code_entry_changed(self, widget, *args):
        # Only enable OK button if the unlock code field is not empty
        unlock_code = self.unlock_code_entry.get_text()
        is_not_empty = len(unlock_code) > 0
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, is_not_empty)

    def _on_dialog_response(self, dialog, response, *args):
        if response == gtk.RESPONSE_ACCEPT:
            # Attempt to unlock device
            unlock_code = self.unlock_code_entry.get_text()
            is_unlocked = self._unlock_device(unlock_code)

            if is_unlocked:
                # Call success callback if possible
                if self.on_success_callback is not None:
                    self.on_success_callback()

                # Only hide dialog if the device was properly unlocked
                self.hide()
            else:
                # Delete the contents of unlock code field if the
                # unlocking process fails
                self.unlock_code_entry.set_text('')
                self.unlock_code_entry.grab_focus()
        else:
            # Turn off device if requested explicitly
            if self.turn_off_if_cancel:
                self.device.turn_off()
            self.hide()

    def _on_dialog_close(self, dialog, widget=None, event=None):
        # Avoid the dialog to be closed except explicitly requested
        return True

if __name__ == '__main__':
    tgcm.country_support = 'es'
    dialog = UnlockDeviceDialog(None)
    dialog.run()
    dialog.destroy()
    gtk.main()
