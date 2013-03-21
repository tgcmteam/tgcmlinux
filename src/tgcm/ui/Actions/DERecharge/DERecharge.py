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
import pango
import gobject

import tgcm
import tgcm.core.FreeDesktop

import tgcm.ui
import tgcm.ui.MSD
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

class DERecharge(tgcm.ui.MSD.MSDAction):
    def __init__(self):
        tgcm.info ("Init DERecharge")

        tgcm.ui.MSD.MSDAction.__init__(self, "prepay")

        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.taskbar_icon_name = 'prepay_taskbar.png'
        self.security_manager = tgcm.ui.MSD.MSDSecurityManager()
        self.action_dir = os.path.join(tgcm.actions_data_dir , self.codename)
        self.theme_manager = tgcm.core.Theme.ThemeManager()
        self.window_icon_path = self.theme_manager.get_icon('icons', self.taskbar_icon_name)

        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir, 'DERecharge_main.ui'), \
                prefix='der')

        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir, 'DERecharge_recharge.ui'), \
                prefix='der')

        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir, 'DERecharge_plan.ui'), \
                prefix='der')

        parent = tgcm.ui.ThemedDock().get_main_window()
        self.recharge_dialog = tgcm.ui.windows.Dialog( \
                parent = parent, buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE), \
                title = "%s - %s" % (self.conf.get_app_name(), "o2credit"))

        # FIXME: We are always loading unnecessary services independently of the
        # country support. Sometimes that situation causes many problems, for example
        # when a theme-related resource is required and it is only available in the
        # theme package of a specific country.
        if self.window_icon_path is not None:
            self.recharge_dialog.set_icon_from_file(self.window_icon_path)

        self.hovering_over_link = False
        self.hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
        self.regular_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)

        self.recharge_button.connect("clicked", self.__recharge_button_cb, None)
        self.balance_button.connect("clicked", self.__balance_button_cb, None)
        self.plan_button.connect("clicked", self.__plan_button_cb, None)
        self.plan_management_textview.connect("key-press-event", self.__key_press_event)
        self.plan_management_textview.connect("event-after", self.__event_after)
        self.plan_management_textview.connect("motion-notify-event", self.__motion_notify_event)
        self.plan_management_textview.connect("visibility-notify-event", self.__visibility_notify_event)

        self.recharge_dialog.add(self.main_widget)

    def launch_action(self, params=None):
        self.recharge_dialog.run()
        self.recharge_dialog.hide()
        return True

    def __recharge_button_cb(self, widget, data):
        self.number_entry.set_text("")
        if self.request_recharge_dialog.run() != gtk.RESPONSE_OK :
            self.request_recharge_dialog.hide()
            return

        self.request_recharge_dialog.hide()
        self.recharge_dialog.hide()
        self.progress = tgcm.ui.MSD.MSDProgressWindow()
        self.progress.set_show_buttons(False)
        self.progress.show(_("Please wait a minute..."), _("Please wait a minute..."))

        mainloop =  gobject.MainLoop(is_running=True)
        context = mainloop.get_context()

        while context.pending() :
            context.iteration()

        ussd_request = self._get_conf_key_value("ussd_recharge").replace("%1%",self.number_entry.get_text())

        dev = self.device_manager.get_main_device()
        if dev == None:
            self.__ussd_call_error_func(None)
        elif dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            tgcm.debug("Sending ussd code : %s" % ussd_request)
            ussd_request = dev.get_cover_key(ussd_request,
                                              self.__ussd_call_func,
                                              self.__ussd_call_error_func)
        else:
            self.__ussd_call_error_func(None)

    def __balance_button_cb(self, widget, data):
        self.recharge_dialog.hide()
        self.progress = tgcm.ui.MSD.MSDProgressWindow()
        self.progress.set_show_buttons(False)
        self.progress.show(_("Please wait a minute..."), _("Please wait a minute..."))

        mainloop =  gobject.MainLoop(is_running=True)
        context = mainloop.get_context()

        while context.pending() :
            context.iteration()

        ussd_request = self._get_conf_key_value("ussd_check")

        dev = self.device_manager.get_main_device()
        if dev == None:
            self.__ussd_call_error_func(None)
        elif dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            tgcm.debug("Sending ussd code : %s" % ussd_request)
            ussd_request = dev.get_cover_key(ussd_request,
                                              self.__ussd_call_func,
                                              self.__ussd_call_error_func)
        else:
            self.__ussd_call_error_func(None)


    def __plan_button_cb(self, button, data):
        self.plan_management_dialog.show()
        self.__show_plan_management_page()
        self.plan_management_dialog.run()
        self.plan_management_dialog.hide()

    def __show_plan_management_page(self, page=None):
        self.progress = tgcm.ui.MSD.MSDProgressWindow()
        self.progress.set_show_buttons(False)
        self.progress.show(_("Please wait a minute..."), _("Please wait a minute..."))

        if page == None :
            ussd_request = "*117*1#"
        else:
            ussd_request = page

        dev = self.device_manager.get_main_device()
        if dev == None:
            self.__plan_management_error_func(None)
        elif dev.get_type() == tgcm.core.DeviceManager.DEVICE_MODEM :
            tgcm.debug("Sending ussd code : %s" % ussd_request)
            ussd_request = dev.get_cover_key(ussd_request,
                                             self.__plan_management_menu_func,
                                             self.__plan_management_error_func)
        else:
            self.__plan_management_error_func(None)

    def __plan_management_menu_func(self, response):
        buffer = self.plan_management_textview.get_buffer()
        buffer.set_text("", 0)
        self.__write_plan_management_menu(buffer, response)
        self.progress.hide()
        self.progress.progress_dialog.destroy()

    def __write_plan_management_menu(self, buffer, response):
        #response = "0044006100730020005000610063006B0020006B006F007300740065007400200035002C003000300020004500750072006F0020006D006F006E00610074006C006900630068002E000A004D00F60063006800740065006E002000530069006500200064006100730020005000610063006B0020005700650065006B0065006E0064002D0046006C006100740072006100740065002000620075006300680065006E003F0020000A000A00310020004A00610020000A0030002000410062006200720075006300680020000A"

        buffer.set_text("", 0)
        iter = buffer.get_iter_at_offset(0)

        #menu_text = u''.join([unichr(int(response[x:x+4], 16)) for x in range(12, len(response), 4)])
        menu_text = response
        for line in menu_text.split("\n") :
            if len(line) == 0 :
                buffer.insert(iter,"\n")
                continue

            if line[0] not in "1234567890" :
                buffer.insert(iter, line + "\n")
            else:
                self.__insert_link(buffer, iter, line + "\n" , line.split(" ")[0])


    def __plan_management_error_func(self, e):
        self.__ussd_call_error_func(e)

    def __key_press_event(self, text_view, event):
        if (event.keyval == gtk.keysyms.Return or
            event.keyval == gtk.keysyms.KP_Enter):
            buffer = text_view.get_buffer()
            iter = buffer.get_iter_at_mark(buffer.get_insert())
            self.__follow_if_link(text_view, iter)
        return False

    # Links can also be activated by clicking.
    def __event_after(self, text_view, event):
        if event.type != gtk.gdk.BUTTON_RELEASE:
            return False
        if event.button != 1:
            return False
        buffer = text_view.get_buffer()

        # we shouldn't follow a link if the user has selected something
        try:
            start, end = buffer.get_selection_bounds()
        except ValueError:
            # If there is nothing selected, None is return
            pass
        else:
            if start.get_offset() != end.get_offset():
                return False

        x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
            int(event.x), int(event.y))
        iter = text_view.get_iter_at_location(x, y)

        self.__follow_if_link(text_view, iter)
        return False


    # Looks at all tags covering the position (x, y) in the text view,
    # and if one of them is a link, change the cursor to the "hands" cursor
    # typically used by web browsers.
    def __set_cursor_if_appropriate(self, text_view, x, y):
        hovering = False

        buffer = text_view.get_buffer()
        iter = text_view.get_iter_at_location(x, y)

        tags = iter.get_tags()
        for tag in tags:
            page = tag.get_data("page")
            if page != 0:
                hovering = True
                break

        if hovering != self.hovering_over_link:
            self.hovering_over_link = hovering

        if self.hovering_over_link:
            text_view.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(self.hand_cursor)
        else:
            text_view.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(self.regular_cursor)

    # Update the cursor image if the pointer moved.
    def __motion_notify_event(self, text_view, event):
        x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
            int(event.x), int(event.y))
        self.__set_cursor_if_appropriate(text_view, x, y)
        text_view.window.get_pointer()
        return False

    # Also update the cursor image if the window becomes visible
    # (e.g. when a window covering it got iconified).
    def __visibility_notify_event(self, text_view, event):
        wx, wy, mod = text_view.window.get_pointer()
        bx, by = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET, wx, wy)

        self.__set_cursor_if_appropriate (text_view, bx, by)
        return False


    def __insert_link(self, buffer, iter, text, page):
        ''' Inserts a piece of text into the buffer, giving it the usual
            appearance of a hyperlink in a web browser: blue and underlined.
            Additionally, attaches some data on the tag, to make it recognizable
            as a link.
        '''
        tag = buffer.create_tag(None,
            foreground="blue", underline=pango.UNDERLINE_SINGLE)
        tag.set_data("page", page)
        buffer.insert_with_tags(iter, text, tag)

    def __follow_if_link(self, text_view, iter):
        ''' Looks at all tags covering the position of iter in the text view,
            and if one of them is a link, follow it by showing the page identified
            by the data attached to it.
        '''
        tags = iter.get_tags()
        for tag in tags:
            page = tag.get_data("page")
            self.__show_plan_management_page(page)
            break

    def __ussd_call_func(self, response):
        self.progress.hide()
        self.progress.progress_dialog.destroy()

        dlg = gtk.MessageDialog(parent = self.recharge_dialog, \
                type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK)
        dlg.set_title (_(u'Sending message'))
        dlg.set_markup(_("<b>Answer received:</b>"))
        dlg.format_secondary_markup("'%s'" % response)
        if self.window_icon_path is not None:
            dlg.set_icon_from_file(self.window_icon_path)

        dlg.run()
        dlg.destroy()

    def __ussd_call_error_func(self, e):
        self.progress.hide()
        self.progress.progress_dialog.destroy()

        dlg = gtk.MessageDialog(parent = self.recharge_dialog, \
                type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK)
        dlg.set_title (_(u'Sending message'))
        dlg.set_markup("<b>Answer received:</b>")
        dlg.format_secondary_markup("'%s'" % _("Service not available"))
        if self.window_icon_path is not None:
            dlg.set_icon_from_file(self.window_icon_path)

        dlg.run()
        dlg.destroy()


