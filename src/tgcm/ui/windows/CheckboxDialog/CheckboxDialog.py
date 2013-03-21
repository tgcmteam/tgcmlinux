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
import tgcm.core.Config
import tgcm.core.Theme

class CheckboxDialog(gtk.MessageDialog):
    def __init__(self, dialog_id, default_response=gtk.RESPONSE_YES, \
            title=None, icon = None, parent=None, \
            flags=(gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), \
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE, message_format=None):
        gtk.MessageDialog.__init__(self, parent=parent, flags=flags, type=type, \
                buttons=buttons, message_format=message_format)
        self.set_deletable(False)

        self._dialog_id = dialog_id
        self._default_response = default_response
        self._config = tgcm.core.Config.Config(tgcm.country_support)

        if title is None:
            title = self._config.get_app_name()
        self.set_title(title)

        if icon is not None:
            if isinstance(icon, str):
                manager = tgcm.core.Theme.ThemeManager()
                icon = manager.get_icon('icons', icon)
            self.set_icon_from_file(icon)

        self.checkbox = gtk.CheckButton(_('_Do not show this message again'))
        self.checkbox.show()
        self.get_content_area().add(self.checkbox)

    def run(self):
        is_dialog_shown = self._config.is_dialog_shown(self._dialog_id)
        if not is_dialog_shown:
            return self._default_response

        response = gtk.MessageDialog.run(self)

        is_dialog_shown = not self.checkbox.get_active()
        self._config.set_is_dialog_shown(self._dialog_id, is_dialog_shown)

        return response

if __name__ == '__main__':
    tgcm.country_support = 'es'
    dialog = CheckboxDialog('foo-dialog', message_format='foo')
    dialog.run()
