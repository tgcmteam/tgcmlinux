#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
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

import os
import re
import time
import math
import datetime
import operator
import colorsys
import webbrowser
import threading
import thread
import gtk
import pango
import gobject
import urlparse
import subprocess

import tgcm
import tgcm.core.Actions
import tgcm.core.Addressbook
import tgcm.core.Messaging
import tgcm.core.DocManager
import tgcm.core.FreeDesktop
import tgcm.core.Notify

import tgcm.ui.MSD
import tgcm.ui.windows
import tgcm.ui.widgets.themedwidgets
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, error_dialog, escape_markup, \
        info_dialog, question_dialog, wait_dialog, warning_dialog

from tgcm.core.DeviceExceptions import *

from MobileManager import CARD_STATUS_READY
from MobileManager.messaging.gsm0338 import is_valid_gsm_text
from freedesktopnet.networkmanager.networkmanager import NetworkManager

POPUP_SIZE = (350,100)

SENDING_ERROR_PREPAID=_("An error has occurred when trying to send the message. Please check the numbers and assure that you have enough credit. If you have not enough credit, recharge and try again.")
SENDING_ERROR_POSTPAID=_("An error has occurred when trying to send the message. Please check the numbers and if you are allowed to send messages to premium services, then try again.")
SENDING_ERROR_PREPAID_URL_TXT=_("Top up your credit")

SENDING_NO_MODEM_INFO = _("The message could not be sent because the Mobile Internet Device is not available.\n\nThe outstanding messages will be saved as pending in the Sent Messages folder and they will be send as soon as the Mobile Internet Device is ready.")

SENDING_MAX_CONCATENATED_ERROR = _("It is not possible to send more than %s SMS simultaneously. Please check the number of SMS to sent and try again.")


class MSDASendSMS(tgcm.ui.MSD.MSDAction):

    MAX_CONCATENATED_SMS = 6
    SENT_ERROR_TEXT = _("Error")
    SEND_PENDING_TEXT = _("Pending")
    SEND_PENDING_MARK = 'pending'

    class _TreeViewSelection():
        def __init__(self, name):
            self.__name = name

        def __call__(self, func):
            _TreeViewSelection_name = self.__name

            # -- Skip the method execution if the treeview is empty
            # -- IMPORTANT: Extends the keywork arguments with the treeview selection
            def newf(self, *args, **kwargs):
                execute = True
                if hasattr(self, _TreeViewSelection_name):
                    tree = getattr(self, _TreeViewSelection_name)
                    model = tree.get_model()
                    if len(model) == 0:
                        execute = False
                    else:
                        selection = tree.get_selection()
                        kwargs[_TreeViewSelection_name] = selection.get_selected_rows()

                if execute is True:
                    return func(self, *args, **kwargs)

            return newf

    def __init__(self):
        tgcm.info("Init MSDASendSMS")
        tgcm.ui.MSD.MSDAction.__init__(self, "sms")

        self.taskbar_icon_name = 'sms_taskbar.png'
        self.window_icon_path = self._theme_manager.get_icon('icons', self.taskbar_icon_name)

        self.conf = tgcm.core.Config.Config()
        self._addr_manager = tgcm.core.Addressbook.AddressbookManager()
        self._messaging_manager = tgcm.core.Messaging.MessagingManager()
        self._doc_manager = tgcm.core.DocManager.DocManager()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.main_modem = self.device_manager.main_modem
        self.sms_storage = self.device_manager.sms_storage
        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.connection_manager = tgcm.core.Connections.ConnectionManager()
        self.themed_dock = tgcm.ui.ThemedDock()
        self.security_manager = tgcm.ui.MSD.MSDSecurityManager()

        self.device_dialer.connect("connecting", self.__connection_status_changed_cb)
        self.device_dialer.connect("disconnected", self.__connection_status_changed_cb)
        self.device_manager.connect("active-dev-card-status-changed", self.__active_device_card_status_changed)
        self.device_manager.connect('active-dev-sms-flash-received', self.__flash_sms_received)
        self.device_manager.connect('active-dev-sms-spool-changed', self.__on_sms_spool_changed)

        self.main_modem.connect('main-modem-changed', self.__main_modem_changed_cb)
        self.main_modem.connect('main-modem-removed', self.__main_modem_removed_cb)

        self.themed_dock.connect('app-closing',self.__on_app_close)

        self.__sending_event = threading.Event()
        self.__sending_result = self.SENDING_RESULT_NONE
        self.__unreaded_received_messages_count = 0
        self.__draft_messages_count = 0
        self.__new_messages_count = 0
        self.action_dir = os.path.join(tgcm.actions_data_dir, self.codename)

        self._notify = tgcm.core.Notify.Notify()
        self.__new_message_icon = os.path.join(self.action_dir, "bandejaentrada_40x40.png")

        gtk_builder_magic(self, \
                filename=os.path.join(self.action_dir,'MSDASendSMS_main.ui'), \
                prefix='mw')

        self.__main_window_running = False

        if tgcm.country_support == "uk":
            window_title = "%s - %s" % (self.conf.get_caption(), _("Text"))
        else:
            window_title = "%s - %s" % (self.conf.get_caption(), _("Messages"))

        self.main_window.set_title(window_title)
        self.main_window.set_skip_taskbar_hint(False)
        self.main_window.set_icon_from_file(self.window_icon_path)

        # @XXX: Remove the menubar from the Glade file
        self.main_menubar.set_no_show_all(True)
        self.main_menubar.hide()
        self.main_notebook.set_border_width(10)

        # Sendto TextViewer helper class
        self.sendto_helper = SendToTextViewerHelper(self.main_window, \
                self.newmessage_sendto_textview, \
                self._addr_manager)

        # Banner
        xml_theme = tgcm.core.XMLTheme.XMLTheme()
        layout = xml_theme.get_layout('banner.sms')
        if layout:
            banner = tgcm.ui.widgets.themedwidgets.ThemedBanner(layout)
            self.main_banner_space.pack_end(banner)

        if tgcm.country_support == "uk":
            self.newmessage_contacts_label.set_text(_("Contacts:"))
            self.newmessage_receipt_checkbutton.set_label(_("Send delivery report"))
            self.conversations_contacts_label.set_text(_("From:"))

        # Signals
        self.main_window.connect("delete-event", self.__close_window_cb)

        self.newmessage_contacts_treeview.connect("button_press_event", self.__newmessage_contacts_treeview_button_event_cb)
        self.newmessage_contacts_treeview.connect("key_press_event", self.__newmessage_contacts_treeview_key_event_cb)
        self.newmessage_send_button.connect("clicked", self.__on_newmessage_message_send_button_clicked)
        self.newmessage_reset_button.connect("clicked", self.__on_newmessage_reset_button_clicked)
        self.newmessage_save_button.connect("clicked", self.__on_newmessage_save_button_clicked)

        self.newmessage_searchcontacts_entry.connect("changed", self.__on_newmessage_searchcontacts_entry_changed)
        self.newmessage_searchcontacts_entry.connect("focus-in-event", self.__on_newmessage_searchcontacts_entry_focus_in)
        self.newmessage_searchcontacts_entry.connect("focus-out-event", self.__on_newmessage_searchcontacts_entry_focus_out)
        self.newmessage_searchcontacts_entry.connect("icon-press",self.__newmessage_searchcontacts_entry_icon_press)
        self.newmessage_receipt_checkbutton.connect("toggled", self.__on_newmessage_receipt_checkbutton_toggled)

        self.newmessage_searchcontacts_entry_init_text = _("Text to find")
        self.newmessage_searchcontacts_entry.set_text(self.newmessage_searchcontacts_entry_init_text)
        self.newmessage_sendto_textview.get_buffer().set_text("")
        self.newmessage_sendto_textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.sendto_helper.connect('changed', self.__on_sendto_helper_changed)
        self.newmessage_message_textview.get_buffer().set_text("")
        self.newmessage_message_textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.newmessage_message_textview.get_buffer().connect('changed', self.__on_newmessage_message_textview_changed)
        self.__set_newmessage_summary_label("")
        self.__newmessage_set_activate_notifications(self._get_conf_key_value("sending_notifications"))

        self.__refresh_newmessage_buttons_state()

        self.received_from_label.set_text("")
        self.received_date_label.set_text("")
        self.received_message_textview.get_buffer().set_text("")
        self.received_message_textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.received_message_textview.connect("button-press-event", self.__textview_button_press_event)
        self.received_message_textview.connect("motion-notify-event", self.__textview_motion_notify_event)
        self.received_message_textview.connect("visibility-notify-event", self.__textview_visibility_notify_event)

        self.received_list_treeview.connect("button_press_event", self.__on_received_list_button_pressed)
        self.received_list_treeview.connect("key_press_event",self.__on_received_list_key_pressed)
        self.received_list_treeview.set_headers_clickable(True)
        self.received_deleteselected_button.connect("clicked", self.__on_received_deleteselected_button_clicked)
        self.received_answer_button.connect("clicked", self.__on_received_reply_button_clicked)
        self.received_forward_button.connect("clicked", self.__on_received_forward_button_clicked)

        self.sended_for_label.set_text("")
        self.sended_date_label.set_text("")
        self.sended_message_textview.get_buffer().set_text("")
        self.sended_message_textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.sended_message_textview.connect("button-press-event", self.__textview_button_press_event)
        self.sended_message_textview.connect("motion-notify-event", self.__textview_motion_notify_event)
        self.sended_message_textview.connect("visibility-notify-event", self.__textview_visibility_notify_event)
        self.sended_list_treeview.connect("button_press_event", self.__on_sended_list_button_pressed)
        self.sended_list_treeview.connect("key_press_event",self.__on_sended_list_key_pressed)
        self.sended_deleteselected_button.connect("clicked", self.__on_sended_deleteselected_button_clicked)
        self.sended_edit_button.connect("clicked", self.__on_sended_edit_button_clicked)
        self.sended_forward_button.connect("clicked", self.__on_sended_forward_button_clicked)

        self.hovering_over_link = False
        self.hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
        self.regular_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)

        conversations_show_sended = self._get_conf_key_value("conversations_show_sended")
        conversations_show_sended = conversations_show_sended if conversations_show_sended != None else True
        self.conversations_sended_checkbutton.set_active(conversations_show_sended)

        conversations_show_received = self._get_conf_key_value("conversations_show_received")
        conversations_show_received = conversations_show_received if conversations_show_received != None else True
        self.conversations_received_checkbutton.set_active(conversations_show_received)

        self.conversations_received_checkbutton.connect("toggled", self.__on_conversations_received_checkbutton_toggled)
        self.conversations_sended_checkbutton.connect("toggled", self.__on_conversations_sended_checkbutton_toggled)
        self.conversations_answer_button.connect("clicked", self.__on_conversations_answer_button_clicked)
        self.conversations_forward_button.connect("clicked", self.__on_conversations_forward_button_clicked)
        self.conversations_deleteselected_button.connect("clicked", self.__on_conversations_deleteselected_button_clicked)
        self.conversations_messages_treeview.connect("button_press_event", self.__on_conversations_messages_treeview_button_pressed)
        self.conversations_messages_treeview.connect("key_press_event",self.__on_conversations_messages_treeview_key_pressed)

        self.draft_for_label.set_text("")
        self.draft_date_label.set_text("")
        self.draft_message_textview.get_buffer().set_text("")
        self.draft_message_textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.draft_message_textview.connect("button-press-event", self.__textview_button_press_event)
        self.draft_message_textview.connect("motion-notify-event", self.__textview_motion_notify_event)
        self.draft_message_textview.connect("visibility-notify-event", self.__textview_visibility_notify_event)
        self.draft_list_treeview.connect("button_press_event", self.__on_draft_list_button_pressed)
        self.draft_list_treeview.connect("key_press_event",self.__on_draft_list_key_pressed)
        self.draft_deleteselected_button.connect("clicked", self.__on_draft_deleteselected_button_clicked)
        if tgcm.country_support == "uk":
            self.draft_deleteselected_button.set_label(_("Delete"))
        self.draft_edit_button.connect("clicked", self.__on_draft_edit_button_clicked)

        # -- Set the filter function and enable the sorting over the clickable column headers
        model = self._addr_manager.get_treeview_model()
        model = model.filter_new()
        model.set_visible_func(self.__search_contacts_filter_func, self.newmessage_searchcontacts_entry)
        model = gtk.TreeModelSort(model)
        self.newmessage_contacts_treeview.set_model(model)
        self._addr_manager.connect('addressbook-model-updated', self.__addressbook_manager_model_updated_cb)

        self.__build_newmessage_contacts_treeview()
        self.__build_received_list_treeview()
        self.__build_sended_list_treeview()
        self.__build_draft_list_treeview()
        self.__build_conversations_contacts_treeview()
        self.__build_conversations_messages_treeview()

        # CONFIGURATION SECTION

        self.activate_notifications_radiobutton = self.get_prefs_widget("activate_notifications_radiobutton")
        self.notifications_frame = self.get_prefs_widget("notifications_frame")
        self.ask_always_radiobutton = self.get_prefs_widget("ask_always_radiobutton")
        self.change_smsc_checkbutton = self.get_prefs_widget("change_smsc_checkbutton")
        self.smsc_entry = self.get_prefs_widget("smsc_entry")
        self.activate_notifications_radiobutton.connect("toggled", self.__on_activate_notifications_radiobutton_toggled)

        if self._get_conf_key_value("notifications_available") == True:
            self.newmessage_receipt_checkbutton.set_sensitive(True)
            self.notifications_frame.show_all()

            if self._get_conf_key_value("sending_notifications") == True:
                self.activate_notifications_radiobutton.set_active(True)
            else:
                self.ask_always_radiobutton.set_active(True)
        else:
            self.newmessage_receipt_checkbutton.destroy()
            self.notifications_frame.destroy()

        editable_smsc = self._get_conf_key_value("editable_smsc")
        if editable_smsc:
            use_custom_smsc = self._get_conf_key_value("use_custom_smsc")
            if use_custom_smsc != False:
                self.change_smsc_checkbutton.set_active(True)
                self.smsc_entry.set_sensitive(True)
                custom_smsc = self._get_conf_key_value("custom_smsc")
                custom_smsc = custom_smsc if custom_smsc != None else ""
                self.smsc_entry.set_text(custom_smsc)
            else:
                self.change_smsc_checkbutton.set_active(False)
                self.smsc_entry.set_sensitive(False)
                self.smsc_entry.set_text("")
            self.change_smsc_checkbutton.connect("toggled", self.__on_change_smsc_checkbutton_toggled)
        else:
            self.change_smsc_checkbutton.set_active(False)
            self.change_smsc_checkbutton.set_sensitive(False)
            self.smsc_entry.set_sensitive(False)
            self.smsc_entry.set_text("")

        self.__set_newmessage_mode(False)
        self.__connect_to_device()

        self.sms_popup_dialog=None

        # -- Arbitrary timeout
        gobject.timeout_add_seconds(4, self.__post_init)

    def __post_init(self):
        # -- Can't connect to Settings as it's not available when the constructor is called
        _settings = tgcm.ui.windows.Settings()
        _settings.connect("is-closing", self.__on_settings_closing)
        return False

    def __get_widget_parent(self, widget):
        '''
        Attempt to determine the parent of a widget
        '''

        # If the SMS service window is being displayed, assume that it
        # is the parent
        if self.main_window.get_visible():
            parent = self.main_window

        # But sometimes it could come from a pop-up dialog, e.g. flash
        # or type 0 messages. This is buggy because only one dialog is
        # registered a time
        elif (self.sms_popup_dialog is not None) and \
                (self.sms_popup_dialog.get_visible()):
            parent = self.sms_popup_dialog

        # If anything else works, use the main ThemedDock window as the
        # main window
        else:
            parent = self.themed_dock.get_main_window()

        return parent

    def __textview_button_press_event(self, textview, event):
        # Do not nothing if it's not a left or right button click
        if event.button not in (1, 3):
            return False
        text_buffer = textview.get_buffer()

        # we shouldn't follow a link if the user has selected something
        try:
            start, end = text_buffer.get_selection_bounds()
        except ValueError:
            # If there is nothing selected, None is return
            pass
        else:
            if start.get_offset() != end.get_offset():
                return False

        # Obtain a TextIterator related to the event
        x, y = textview.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
            int(event.x), int(event.y))
        text_iter = textview.get_iter_at_location(x, y)

        if len(text_iter.get_tags())==0:
            return

        # Obtain the TextTag related to the TextIterator object
        tag = text_iter.get_tags()[0]
        tag_data = tag.get_data('page')
        tag_type = tag.get_data('type')

        # Execute a different callback depending on the TextTag type
        if tag_type == 'url':
            return self.__textview_process_link(textview, tag_data, event)
        elif tag_type == 'email':
            return self.__textview_process_email(textview, tag_data, event)
        elif tag_type == 'phone':
            return self.__textview_process_phone(textview, tag_data, event)

    def __textview_process_link(self, textview, url, event):
        # Left click event: open the url
        if event.button == 1:
            self.__textview_open_url_cb(textview, url, False)
            return False

        # Right click event: show a pop-up menu
        else:
            actions_manager = tgcm.core.Actions.ActionManager()
            favorites_action = actions_manager.get_action('favorites')

            menu_entries = [(_('Open url'), self.__textview_open_url_cb)]
            if favorites_action.is_installed():
                menu_entries.append((_('Add to favourites'), self.__textview_add_to_favourites_cb))
            return self.__textview_build_popup_menu(textview, event, menu_entries, url, False)

    def __textview_process_email(self, textview, email, event):
        # Left click event: open the default email client
        if event.button == 1:
            self.__call_mail_user_agent(email)
            return False

        # Right click event: show a pop-up menu
        else:
            menu_entries = ((_('Send e-mail'), self.__textview_send_message_cb), \
                (_('Add to contact list'), self.__textview_add_to_contact_list_cb), \
                (_('Assign to contact'), self.__textview_assign_to_contact_cb))
            return self.__textview_build_popup_menu(textview, event, menu_entries, email, True)

    def __textview_process_phone(self, textview, phone, event):
        # Independently of the click event show a pop-up menu
        menu_entries = ((_('Send message'), self.__textview_send_message_cb), \
                (_('Add to contact list'), self.__textview_add_to_contact_list_cb), \
                (_('Assign to contact'), self.__textview_assign_to_contact_cb))
        return self.__textview_build_popup_menu(textview, event, menu_entries, phone, False)

    def __textview_build_popup_menu(self, widget, event, menu_entries, text, is_email):
        menu = gtk.Menu()
        entry = gtk.MenuItem(text)
        entry.set_sensitive(False)
        menu.append(entry)

        entry = gtk.SeparatorMenuItem()
        menu.append(entry)

        for label, callback in menu_entries:
            menuitem = gtk.MenuItem(label)
            menuitem.connect('activate', callback, text, is_email)
            menu.append(menuitem)

        evt_button = event.button if event is not None else 0
        evt_time = event.time if event is not None else 0

        menu.show_all()
        menu.popup(None, None, None, evt_button, evt_time, data=widget)

        return True

    def __textview_open_url_cb(self, widget, url, is_email):
        if self.device_dialer.nmConnectionState() != NetworkManager.State.CONNECTED:
            title = _('Not connected')
            markup = _('The web page cannot be opened because you are not connected')
            message = _('Please connect and try again')
            parent = self.__get_widget_parent(widget)
            warning_dialog(message, markup=markup, title=title, parent=parent)
        else:
            o = urlparse.urlparse(url)
            if len(o.scheme) == 0:
                url = 'http://%s' % url
            webbrowser.open(url)

    def __textview_add_to_favourites_cb(self, widget, url, is_email):
        actions_manager = tgcm.core.Actions.ActionManager()
        favorites_action = actions_manager.get_action('favorites')
        if favorites_action.is_installed():
            parent = self.__get_widget_parent(widget)
            favorites_action.create_bookmark(parent, url=url)

    def __textview_send_message_cb(self, widget, data, is_email):
        if is_email:
            self.__call_mail_user_agent(data)
        else:
            name = self._addr_manager.get_name_from_number(data)
            contact = self.sendto_helper.get_contact(name, data)
            self.__refresh_newmessage_tab_with_contact(contact, '', False)

    def __textview_add_to_contact_list_cb(self, widget, data, is_email):
        phone = None if is_email else data
        email = None if not is_email else data

        parent = self.__get_widget_parent(widget)
        contact_dialog = tgcm.ui.windows.ContactEditor(parent)
        response = contact_dialog.run(email=email, phone=phone)
        if response == gtk.RESPONSE_OK:
            d = contact_dialog.get_dict()
            self._addr_manager.get_new_contact( \
                    d['name'], d['phone'], d['email'], True)

    def __textview_assign_to_contact_cb(self, widget, data, is_email):
        # Create a new contact search dialog
        parent = self.__get_widget_parent(widget)
        search_contact_dialog = tgcm.ui.windows.SearchContactDialog(parent, data)
        response = search_contact_dialog.run()

        # Update selected contact if requested
        if response == gtk.RESPONSE_OK:
            contact = search_contact_dialog.get_selected_contact()
            if is_email:
                contact.email = data
            else:
                contact.phone = data
            contact.save()

        search_contact_dialog.destroy()

    # Looks at all tags covering the position (x, y) in the text view,
    # and if one of them is a link, change the cursor to the "hands" cursor
    # typically used by web browsers.
    def __textview_set_cursor_if_appropriate(self, text_view, x, y):
        hovering = False
        text_iter = text_view.get_iter_at_location(x, y)

        tags = text_iter.get_tags()
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
    def __textview_motion_notify_event(self, text_view, event):
        x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
            int(event.x), int(event.y))
        self.__textview_set_cursor_if_appropriate(text_view, x, y)
        text_view.window.get_pointer()
        return False

    # Also update the cursor image if the window becomes visible
    # (e.g. when a window covering it got iconified).
    def __textview_visibility_notify_event(self, text_view, event):
        wx, wy, mod = text_view.window.get_pointer()
        bx, by = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET, wx, wy)
        self.__textview_set_cursor_if_appropriate(text_view, bx, by)
        return False

    def alt_text(self):
        messaging_available = self._messaging_manager.is_messaging_available()
        if not messaging_available:
            return "X"

        unread_messages = 0

        messages = self.sms_storage.sms_list_received()
        for msg_id, readed, number, date in messages:
            if not readed:
                unread_messages += 1

        if unread_messages == 0:
            return False
        else:
            return str(unread_messages)

    def __main_modem_changed_cb(self, main_modem, device_manager, dev):
        self.__connect_to_device()

    def __main_modem_removed_cb(self, *args):
        # -- Inform the SMS sending thread that the modem is gone
        self.__sending_result = self.SENDING_RESULT_ABORT
        self.__sending_event.set()

    def __active_device_card_status_changed(self, device_manager, status):
        self.__connect_to_device(status)

        if status == CARD_STATUS_READY:
            self.__send_offline_messages()

    def __connection_status_changed_cb(self, dialer):
        self.__connect_to_device()

    def __connect_to_device(self, status=None):
        self.main_window.set_sensitive(True)

        self.__fill_newmessage_contacts_treeview()
        self.__fill_received_list_treeview()
        self.__fill_sended_list_treeview()
        self.__fill_draft_list_treeview()
        self.__fill_conversations_contacts_treeview()
        return

    def __addressbook_manager_model_updated_cb(self, *args):
        self.__update_treeviews_with_contact()

    def __update_treeviews_with_contact(self):
        self.__fill_received_list_treeview()
        self.__fill_sended_list_treeview()
        self.__fill_draft_list_treeview()
        self.__fill_conversations_contacts_treeview()

    def __newmessage_contacts_treeview_selection_foreach_cb(self, model, path, text_iter, selected_ids):
        selected_ids.append(model.get_value(text_iter, 2))

    def __newmessage_contacts_base_model_foreach_cb(self, model, path, text_iter, selected_ids):
        selection = self.newmessage_contacts_treeview.get_selection()
        msg_id = model.get_value(text_iter, 2)
        if msg_id in selected_ids:
            iter_aux = self.newmessage_contacts_treeview.get_model().get_model().convert_child_iter_to_iter(text_iter)
            iter_aux2 = self.newmessage_contacts_treeview.get_model().convert_child_iter_to_iter(None, iter_aux)
            selection.select_iter(iter_aux2)

    def __flash_sms_received(self, device_manager, number, text):
        self.__show_popup_sms(number, text, flash_sms=True)

    def __on_sms_spool_changed(self, device_manager, operation):
        if operation == self.sms_storage.SPOOL_RECEIVED:
            self.__fill_received_list_treeview()
            self.__fill_conversations_contacts_treeview()
            self.__show_new_message_notification()

        if operation == self.sms_storage.SPOOL_RECEIVED_DELETED:
            self.__fill_received_list_treeview()
            self.__fill_conversations_contacts_treeview()

        elif operation == self.sms_storage.SPOOL_RECEIVED_READ:
            unread = 0
            for msg_id, read, number, date in self.sms_storage.sms_list_received():
                unread = (unread + 1) if (read is False) else unread
            self.__set_received_messages_tab_title(unread)
        elif operation == self.sms_storage.SPOOL_SENT:
            self.__fill_sended_list_treeview()
            self.__fill_conversations_contacts_treeview()
        elif operation == self.sms_storage.SPOOL_DRAFT:
            self.__fill_draft_list_treeview()

    def __on_app_close(self, sender):
        # -- Save the new message that is being edited without any user confirmation
        self.__newmessage_save_draft()

        messages=self.sms_storage.sms_list_to_send()
        if messages and len(messages) > 0:
            response    = gtk.RESPONSE_CLOSE
            main_window = self.themed_dock.get_main_window()
            dlg = gtk.Dialog(parent=main_window, \
                    flag=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    title=_("Pending messages"), \
                    buttons=(gtk.STOCK_CLOSE, response))
            dlg.set_border_width(10)

            # -- Set the button label 'Accept' like Windows
            button = dlg.get_widget_for_response(response)
            button.set_label(_("Accept"))

            label = gtk.Label(_("There are pending messages to be sent. What do you want to do?"))
            label.set_padding(0, 5)
            radio_save = gtk.RadioButton(None, _("Save pending messages and close"))
            radio_remove = gtk.RadioButton(radio_save, _("Delete all pending messages and close"))

            box = dlg.get_content_area()
            vbox = gtk.VBox(False, 0)
            vbox.set_spacing(5)

            vbox.pack_start(label, False, True, 0)
            vbox.pack_start(radio_save, False, True, 0)
            vbox.pack_start(radio_remove, False, True, 0)
            box.add(vbox)
            dlg.show_all()
            dlg.run()

            if (radio_save.get_active()):
                for msg_id, readed, number, date in messages:
                    sms_to_send=self.sms_storage.sms_get_to_send(msg_id)
                    self.sms_storage.sms_set_draft(number, sms_to_send[4])

            for msg_id, readed, number, date in messages:
                self.sms_storage.sms_delete_to_send(msg_id)

    def __newmessage_contacts_treeview_sort(self, column, number):
        if column.get_sort_order() == gtk.SORT_ASCENDING:
            column.set_sort_order(gtk.SORT_DESCENDING)
        else:
            column.set_sort_order(gtk.SORT_ASCENDING)

        for col in self.newmessage_contacts_treeview.get_columns():
            col.set_sort_indicator(False)

        column.set_sort_indicator(True)
        ls = self.newmessage_contacts_treeview.get_model()
        ls.set_sort_column_id(number, column.get_sort_order())

    def __build_newmessage_contacts_treeview(self):
        base_id = 0
        if tgcm.country_support != "uk":
            fields = ["id", _("Name"),_("Telephone")]
        else:
            fields = ["id", _("Name"),_("Phone number")]

        for field in fields:
            col = gtk.TreeViewColumn(field)
            self.newmessage_contacts_treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            col.set_resizable(True)
            col.set_clickable(True)
            col.set_reorderable(True)

            if field == _('Name'):
                col.set_expand(True)
            else:
                col.set_min_width(120)

            if field == "id":
                col.set_visible(False)
            else:
                col.connect('clicked', self.__newmessage_contacts_treeview_sort, base_id)

            col.set_cell_data_func(cell,self.__new_message_contacts_cell_render_func,self.newmessage_searchcontacts_entry)

            base_id = base_id + 1

        # -- Set the tooltips column
        colnr = self._addr_manager.get_column_number_tooltip()
        self.newmessage_contacts_treeview.set_tooltip_column(colnr)

        selection = self.newmessage_contacts_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)

    def __new_message_contacts_cell_render_func(self, column, cell_renderer, model, text_iter, search_entry):
        if column.get_title() == "id":
            return

        search_text = search_entry.get_text().strip().lower()

        idx =  self.newmessage_contacts_treeview.get_columns().index(column)
        value = model.get_value(text_iter, idx)

        if value == None:
            return

        idx = value.lower().find(search_text)
        if idx >=0:
            prefix = gobject.markup_escape_text(value[:idx])
            body = gobject.markup_escape_text(value[idx: idx +len(search_text)])
            suffix = gobject.markup_escape_text(value[idx +len(search_text):])
            cell_renderer.set_property('markup','%s<span background="blue" foreground="white">%s</span>%s' % (prefix,body,suffix))

    def __fill_newmessage_contacts_treeview(self, contacts=None):
        pass

    def __search_contacts_filter_func(self, model, text_iter, search_entry):
        phone = model.get_value(text_iter, self._addr_manager.COLUMN_PHONE)
        if phone == None or phone == "":
            return False

        search_text = search_entry.get_text()
        if search_text == self.newmessage_searchcontacts_entry_init_text:
            search_text = ""

        # -- Filter the value only in the name and phone columns
        for i in (self._addr_manager.COLUMN_PHONE, self._addr_manager.COLUMN_NAME):
            value = model.get_value(text_iter, i)
            if value is not None:
                if search_text.lower() in value.strip().lower():
                    return True

        return False

    def __newmessage_contacts_treeview_button_event_cb(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.__newmessage_add_selected_contact()
            return False
        elif event.button == 3:
            time = event.time
            path = self.newmessage_contacts_treeview.get_path_at_pos(int(event.x),int(event.y))
            if path is None:
                return False

            selection = self.newmessage_contacts_treeview.get_selection()
            rows = selection.get_selected_rows()
            if path[0] not in rows[1]:
                selection.unselect_all()
                selection.select_path(path[0])

            if selection.count_selected_rows() > 1:
                add_menuitem = gtk.ImageMenuItem(_("Add recipients"))
            else:
                add_menuitem = gtk.ImageMenuItem(_("Add recipient"))
            add_menuitem.connect("activate", self.__newmessage_contacts_add_menuitem_clicked)
            img = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
            add_menuitem.set_image(img)

            menu = gtk.Menu()
            menu.append(add_menuitem)
            menu.popup( None, None, None, event.button, time)
            menu.show_all()

            return True

    def __newmessage_contacts_add_menuitem_clicked(self, widget):
        self.__newmessage_add_selected_contact()

    def __newmessage_contacts_treeview_key_event_cb(self, widget, event):
        if (event.keyval == gtk.gdk.keyval_from_name('Return')):
            self.__newmessage_add_selected_contact()
        return False

    def __newmessage_add_selected_contact(self):
        selection = self.newmessage_contacts_treeview.get_selection()
        model, paths = selection.get_selected_rows()
        valid_contacts = []
        duplicated_contacts = []
        for path in paths:
            name = model.get_value(model.get_iter(path), 1)
            phone = model.get_value(model.get_iter(path), 2)
            contact_name = '%s <%s>' % (name, phone)

            if not self.sendto_helper.is_duplicated(phone):
                valid_contacts.append((name, phone))
            else:
                duplicated_contacts.append(contact_name)

        for name, phone in valid_contacts:
            contact = self.sendto_helper.get_contact(name, phone)
            self.sendto_helper.add_contact(contact)

        if len(duplicated_contacts) > 0:
            if len(duplicated_contacts) > 1:
                message = _("The contacts %s are already in the receiver list.") % ", ".join(duplicated_contacts)
            else:
                message = _("The contact %s is already in the receiver list.") % duplicated_contacts[0]
            info_dialog(escape_markup(message), parent=self.main_window)

    def __build_received_list_treeview(self):
        base_id = 0
        fields = ["id", _("From"), _("Content"), _("Date"), "date"]
        for field in fields:
            col = gtk.TreeViewColumn(field)
            self.received_list_treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'markup', base_id)
            col.set_resizable(True)
            col.set_reorderable(True)
            col.set_sort_column_id(base_id)
            if field == _("From"):
                col.set_min_width(120)
            else:
                col.set_min_width(100)
            if field in ("id", "date"):
                col.set_visible(False)
                col.set_expand(False)
            elif field == _("Content") or field == _("Message"):
                col.set_visible(True)
                col.set_expand(True)
            else:
                col.set_expand(False)
                col.set_visible(True)
                if field == _("Date"):
                    cell.set_property('xalign', 1.0)
                    col.set_sort_column_id(base_id + 1)
            base_id = base_id + 1

        selection = self.received_list_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.__on_received_list_treeview_selection_changed_h = selection.connect('changed', self.__on_received_list_treeview_selection_changed)

    def __fill_received_list_treeview(self):
        try:
            self.__received_messages_selection = []
            selection = self.received_list_treeview.get_selection()
            model, paths = selection.get_selected_rows()
            if paths:
                for path in paths:
                    self.__received_messages_selection.append(model.get_value(model.get_iter(path), 0))

            model = gtk.ListStore(gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING)

            messages = self.sms_storage.sms_list_received()
            self.__unreaded_received_messages_count = 0
            if messages and len(messages) > 0:
                messages.sort(reverse=True, key=operator.itemgetter(3))
                for id, readed, number, date in messages:
                    number_aux = self._addr_manager.normalize_number(number)
                    name = self._addr_manager.get_name_from_number(number_aux)
                    if name == None:
                        name = number

                    date_string = self.__get_date_string(date)
                    try:
                        a, readed, b, c, text = self.sms_storage.sms_get_received(id)
                    except:
                        continue

                    text = self.__lstrip_notification_prefix(text)
                    text = escape_markup(text.replace('\n', ' '))
                    name = escape_markup(name)

                    if readed:
                        model.append([id, name, text, date_string, date])
                    else:
                        self.__unreaded_received_messages_count = self.__unreaded_received_messages_count + 1
                        model.append([id, "<b>%s</b>" % name, "<b>%s</b>" % text, "<b>%s</b>" % date_string, date])

            self.__set_received_messages_tab_title(self.__unreaded_received_messages_count)

            self.received_list_treeview.set_model(model)

            model.foreach(self.__received_list_treeview_model_foreach_cb, self.__received_messages_selection)
        except DeviceNotReady:
            tgcm.error("Device Not Ready Exception")
        except DeviceHasNotCapability:
            tgcm.error("Device Has not Capability")

    def __received_list_treeview_model_foreach_cb(self, model, path, text_iter, selected_ids):
        selection = self.received_list_treeview.get_selection()
        msg_id = model.get_value(text_iter, 0)
        if msg_id in selected_ids:
            selection.select_iter(text_iter)

    def __set_received_messages_tab_title(self, unread):
        if unread > 0:
            self.received_tab_label.set_text(_("Inbox")+" (%d)" % unread)
        else:
            self.received_tab_label.set_text(_("Inbox"))

    def __build_sended_list_treeview(self):
        base_id = 0
        fields = ["id", _("To"), _("Content"), _("Date"), "date"]
        for field in fields:
            col = gtk.TreeViewColumn(field)
            self.sended_list_treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'markup', base_id)
            col.set_resizable(True)
            col.set_reorderable(True)
            col.set_sort_column_id(base_id)
            if field == _("To"):
                col.set_min_width(120)
            else:
                col.set_min_width(100)
            if field == "id" or field == "date":
                col.set_visible(False)
                col.set_expand(False)
            elif field == _("Content") or field == _("Message"):
                col.set_visible(True)
                col.set_expand(True)
            else:
                col.set_expand(False)
                col.set_visible(True)
                if field == _("Date"):
                    cell.set_property('xalign', 1.0)
                    col.set_sort_column_id(base_id + 1)
            base_id = base_id + 1

        selection = self.sended_list_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.__on_sended_list_treeview_selection_changed_h = selection.connect('changed', self.__on_sended_list_treeview_selection_changed)

    def __fill_sended_list_treeview(self):
        try:
            model = gtk.ListStore(gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING)

            count_unsended = 0

            messages = self.sms_storage.sms_list_to_send()
            if messages and len(messages) > 0:
                messages.sort(reverse=True, key=operator.itemgetter(3))
                for msg_id, readed, number, date in messages:
                    number_aux = self._addr_manager.normalize_number(number)
                    name = self._addr_manager.get_name_from_number(number_aux)
                    if name == None:
                        name = number

                    date_string = self.__get_date_string(date)

                    a, readed, b, c, text = self.sms_storage.sms_get_to_send(msg_id)
                    text = self.__lstrip_notification_prefix(text)
                    text = escape_markup(text.replace('\n', ' '))
                    name = escape_markup(name)
                    date_string = self.SEND_PENDING_TEXT
                    if readed is False:
                        count_unsended = count_unsended + 1
                        name, text, date_string = map(lambda p : "<b>%s</b>" % p, [name, text, date_string])
                    model.append([msg_id, name, text, date_string, self.SEND_PENDING_MARK])

            messages = self.sms_storage.sms_list_sent()
            if messages and len(messages) > 0:
                messages.sort(reverse=True, key=operator.itemgetter(3))
                for msg_id, readed, number, date, error in messages:
                    number_aux = self._addr_manager.normalize_number(number)
                    name = self._addr_manager.get_name_from_number(number_aux)
                    if name == None:
                        name = number

                    date_string = self.__get_date_string(date)

                    a, readed, b, c, text, error = self.sms_storage.sms_get_sent(msg_id)
                    text = self.__lstrip_notification_prefix(text)
                    text = escape_markup(text.replace('\n', ' '))
                    name = escape_markup(name)

                    if error is True:
                        date_string = self.SENT_ERROR_TEXT

                    if readed is False:
                        name, text, date_string = map(lambda p : "<b>%s</b>" % p, [name, text, date_string])
                        count_unsended = count_unsended + 1

                    model.append([msg_id, name, text, date_string, date])

            self.sended_list_treeview.set_model(model)

            if count_unsended > 0:
                self.sended_tab_label.set_text(_("Sent")+" (%d)" % count_unsended)
            else:
                self.sended_tab_label.set_text(_("Sent"))

        except DeviceNotReady:
            tgcm.error("Device Not Ready Exception")

    def __build_draft_list_treeview(self):
        base_id = 0

        fields = ["id", _("To"), _("Content"), _("Date"), "date"]

        for field in fields:
            col = gtk.TreeViewColumn(field)
            self.draft_list_treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'markup', base_id)
            col.set_resizable(True)
            col.set_reorderable(True)
            col.set_sort_column_id(base_id)
            if field == _("To"):
                col.set_min_width(120)
            else:
                col.set_min_width(100)
            if field == "id" or field == "date":
                col.set_visible(False)
                col.set_expand(False)
            elif field == _("Content") or field == _("Message"):
                col.set_visible(True)
                col.set_expand(True)
            else:
                col.set_expand(False)
                col.set_visible(True)
                if field == _("Date"):
                    cell.set_property('xalign', 1.0)
                    col.set_sort_column_id(base_id + 1)
            base_id = base_id + 1

        selection = self.draft_list_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.__on_draft_list_treeview_selection_changed)

    def __fill_draft_list_treeview(self):
        model = gtk.ListStore(gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING)

        messages = self.sms_storage.sms_list_drafts()
        self.__draft_messages_count = 0
        if messages and len(messages) > 0:
            messages.sort(reverse=True, key=operator.itemgetter(3))
            for msg_id, readed, number, date in messages:
                self.__draft_messages_count = self.__draft_messages_count + 1

                number_aux = self._addr_manager.normalize_number(number)
                name = self._addr_manager.get_name_from_number(number_aux)
                name = number if name is None else '<' + name + '>'
                date_string = self.__get_date_string(date)

                a, b, c, d, text = self.sms_storage.sms_get_draft(msg_id)
                text = self.__lstrip_notification_prefix(text)

                text = escape_markup(text.replace('\n', ' '))
                name = escape_markup(name)
                model.append([msg_id,
                            name,
                            text,
                            date_string,
                            date])

        self.draft_list_treeview.set_model(model)

        if self.__draft_messages_count > 0:
            self.draft_tab_label.set_text(_("Draft")+" (%d)" % self.__draft_messages_count)
        else:
            self.draft_tab_label.set_text(_("Draft"))

    def __build_conversations_contacts_treeview(self):
        base_id = 0
        for field in [_("Name"),_("Telephone")]:
            col = gtk.TreeViewColumn(field)
            self.conversations_contacts_treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            if field == _("Name"):
                col.set_visible(True)
            else:
                col.set_visible(False)
            base_id = base_id + 1

        selection = self.conversations_contacts_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.__on_conversations_contacts_treeview_selection_changed)

    def __build_conversations_messages_treeview(self):
        base_id = 0
        for field in ["id", _("Message"), "spool", "number", "text"]:
            if field != _("Message"):
                col = gtk.TreeViewColumn(field)
                self.conversations_messages_treeview.append_column(col)
                cell = gtk.CellRendererText()
                cell.set_property("ellipsize", pango.ELLIPSIZE_END)
                # -- Add the cell renderer to the column before adding the attribute
                col.pack_start(cell, True)
                col.add_attribute(cell, 'text', base_id)
                col.set_visible(False)
            else:
                cell = self.__appendAutowrapColumn(self.conversations_messages_treeview, 50, "Notes", markup=1, foreground=5, background=6)
            base_id = base_id + 1

        gtk.rc_parse_string("""style "tree-style" {
            GtkTreeView::vertical-separator = 8
            }
            widget "*conversations_messages_treeview*" style "tree-style" """)
        self.conversations_messages_treeview.set_name("conversations_messages_treeview")

        selection = self.conversations_messages_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.__on_conversations_messages_treeview_selection_changed)

    def __appendAutowrapColumn(self, treeview, defwidth, name, **kvargs):
        cell = gtk.CellRendererText()
        cell.props.wrap_mode = pango.WRAP_WORD
        cell.props.wrap_width = defwidth
        column = gtk.TreeViewColumn(name, cell, **kvargs)
        treeview.append_column(column)

        def callback(treeview, allocation, column, cell):
            otherColumns = (c for c in treeview.get_columns() if c != column)
            newWidth = allocation.width - sum(c.get_width() for c in otherColumns)
            newWidth -= treeview.style_get_property("horizontal-separator") * 2
            if cell.props.wrap_width == newWidth or newWidth <= 0:
                return
            cell.props.wrap_width = newWidth
            store = treeview.get_model()
            if store is None:
                return
            store_iter = store.get_iter_first()
            while store_iter and store.iter_is_valid(store_iter):
                store.row_changed(store.get_path(store_iter), store_iter)
                store_iter = store.iter_next(store_iter)
            treeview.set_size_request(0,-1)
        treeview.connect_after("size-allocate", callback, column, cell)

        return cell

    def __fill_conversations_contacts_treeview(self):
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        numbers = []
        numbers_to_show = []
        numbers_messages = {}
        for msg_id, readed, number, date, error in self.sms_storage.sms_list_sent():
            if error is True:
                continue

            number_norm = self._addr_manager.normalize_number(number)
            if number_norm in numbers:
                if numbers_messages.has_key(number_norm):
                    numbers_messages[number_norm] = [numbers_messages[number_norm][0]+1, numbers_messages[number_norm][1]]
                else:
                    numbers_messages[number_norm] = [1, 0]
            else:
                numbers.append(number_norm)
                numbers_to_show.append(number)
                numbers_messages[number_norm] = [1, 0]

        for msg_id, readed, number, date in self.sms_storage.sms_list_received():
            number_norm = self._addr_manager.normalize_number(number)
            if number_norm in numbers:
                if numbers_messages.has_key(number_norm):
                    numbers_messages[number_norm] = [numbers_messages[number_norm][0], numbers_messages[number_norm][1]+1]
                else:
                    numbers_messages[number_norm] = [0, 1]
            else:
                numbers.append(number_norm)
                numbers_to_show.append(number)
                numbers_messages[number_norm] = [0, 1]

        numbers = list(set(numbers))

        show_received = self._get_conf_key_value("conversations_show_received")
        show_sended = self._get_conf_key_value("conversations_show_sended")
        for number in numbers:
            name = self._addr_manager.get_name_from_number(number)
            if name == None:
                for i in numbers_to_show:
                    if self._addr_manager.normalize_number(i) == number:
                        name = i

            messages = 0
            if show_sended:
                messages = messages + numbers_messages[number][0]
            if show_received:
                messages = messages + numbers_messages[number][1]

            model.append(["%s (%d)" % (name, messages), number])

        self.conversations_contacts_treeview.set_model(model)

    def __set_newmessage_summary_label(self, text):
        notify_active = self.newmessage_receipt_checkbutton.get_active()
        if notify_active:
            is_gsm7 = is_valid_gsm_text(text)
            if is_gsm7:
                method = "notifications_gsm7_method"
                prefix = "notifications_gsm7_prefix"
            else:
                method = "notifications_ucs2_method"
                prefix = "notifications_ucs2_prefix"

            if self._get_conf_key_value(method) == 'prefix':
                text = self._get_conf_key_value(prefix) + text

        messages, remains = self.__calculate_concatenation(text)
        self.__new_messages_count = messages
        chars_label = _("character left") if remains == 1 else _("characters left")
        msg_label = _("messages")  if messages > 1 else _("message")

        markup_text = '<b>%d %s / %d %s</b>' % (remains, chars_label, messages, msg_label)
        if messages > self.MAX_CONCATENATED_SMS:
            markup_text = '<span foreground="red">%s</span>' % markup_text
        self.newmessage_summary_label.set_markup(markup_text)

    def __on_newmessage_searchcontacts_entry_changed(self, widget):
        if self.newmessage_contacts_treeview.get_model() is not None:
            self.newmessage_contacts_treeview.get_model().get_model().refilter()

    def __on_newmessage_searchcontacts_entry_focus_in(self, widget, event, data=None):
        if self.newmessage_searchcontacts_entry.get_text() == self.newmessage_searchcontacts_entry_init_text:
            self.newmessage_searchcontacts_entry.set_text("")

    def __on_newmessage_searchcontacts_entry_focus_out(self, widget, event, data=None):
        if self.newmessage_searchcontacts_entry.get_text() == "":
            self.newmessage_searchcontacts_entry.set_text(self.newmessage_searchcontacts_entry_init_text)

    def __newmessage_searchcontacts_entry_icon_press(self, widget, icon_pos, event):
        self.newmessage_searchcontacts_entry.set_text("")
        self.newmessage_searchcontacts_entry.grab_focus()

    def __on_newmessage_message_textview_changed(self, text_buffer):
        startiter = text_buffer.get_start_iter()
        enditer = text_buffer.get_end_iter()
        text = startiter.get_text(enditer)

        self.__set_newmessage_summary_label(text)
        self.__refresh_newmessage_buttons_state()

    def __on_sendto_helper_changed(self, sender, is_valid):
        self.__refresh_newmessage_buttons_state(is_valid)
        return False

    @staticmethod
    def __get_textview_text(textview):
        text_buffer = textview.get_buffer()
        startiter = text_buffer.get_start_iter()
        enditer = text_buffer.get_end_iter()
        return startiter.get_text(enditer)

    def __refresh_newmessage_buttons_state(self, is_sendto_ok=None):
        if is_sendto_ok is None:
            is_sendto_ok = self.sendto_helper.validate(do_check_all=True)
        sendto_empty = self.sendto_helper.is_empty()
        message = self.__get_textview_text(self.newmessage_message_textview)

        can_save = False
        can_delete = False
        can_send = False

        if (not sendto_empty) or (len(message) > 0):
            can_delete = True
            can_save = True

        if is_sendto_ok and (len(message) > 0) and \
                (self.__new_messages_count <= self.MAX_CONCATENATED_SMS):
            can_send = True

        self.newmessage_send_button.set_sensitive(can_send)
        self.newmessage_reset_button.set_sensitive(can_delete)
        self.newmessage_save_button.set_sensitive(can_save)

    def __on_newmessage_reset_button_clicked(self, widget):
        sendto_empty = self.sendto_helper.is_empty()
        message = self.__get_textview_text(self.newmessage_message_textview)

        if (not sendto_empty) or (len(message) > 0):
            message = _("The text and the message recipients that you are writing will be deleted. Are you sure?")
            resp = question_dialog(message, parent=self.main_window)
            if resp == gtk.RESPONSE_YES:
                self.__fill_newmessage_tab('', '', False)
        else:
            self.__set_newmessage_mode(False)

    def __on_newmessage_save_button_clicked(self, widget):
        if self.__editing_draft != False:
            message = _("The draft is going to be updated. Do you want to continue?")
        else:
            message = _("The draft copy is going to be saved. Do you want to continue?")

        resp = question_dialog(message, parent=self.main_window)
        if resp == gtk.RESPONSE_YES:
            self.__newmessage_save_draft()
            self.__fill_newmessage_tab('', '', False)

    def __newmessage_save_draft(self):
        is_sendto_ok = self.sendto_helper.validate(do_check_all=True)
        sendto_raw = self.sendto_helper.get_raw_contents()
        message_text = self.__get_textview_text(self.newmessage_message_textview)

        if (not is_sendto_ok) and (len(message_text) == 0):
            return

        # -- Save an unique draft for all the recipients
        self.sms_storage.sms_set_draft(sendto_raw, message_text)

        if self.__editing_draft != False:
            self.sms_storage.sms_delete_draft(self.__editing_draft)

    def __on_newmessage_message_send_button_clicked(self, widget):
        valid_numbers = self.sendto_helper.get_phones()
        text = self.__get_textview_text(self.newmessage_message_textview)
        concatenated_messages = self.__calculate_concatenation(text)[0]
        if concatenated_messages > self.MAX_CONCATENATED_SMS:
            self.__show_notification_dialog(SENDING_MAX_CONCATENATED_ERROR % self.MAX_CONCATENATED_SMS)
            return

        if tgcm.country_support != "uk":
            message = _("Your sms will be sent. Do you want to continue?")
            dialog = tgcm.ui.windows.CheckboxDialog('send-sms-confirmation', \
                    default_response=gtk.RESPONSE_YES, \
                    icon=self.window_icon_path, title=_('Send SMS'), \
                    parent=self.main_window, message_format=message, \
                    type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
            response = dialog.run()
            dialog.destroy()

            if response != gtk.RESPONSE_YES:
                return

        rs = False
        if self.newmessage_receipt_checkbutton.get_active():
            is_gsm7 = is_valid_gsm_text(text)
            if is_gsm7:
                method = self._get_conf_key_value("notifications_gsm7_method")
                if method == 'prefix':
                    notifications_prefix = self._get_conf_key_value("notifications_gsm7_prefix")
                    text = notifications_prefix+text
                elif method == 'status-report':
                    rs = True
            else:
                method = self._get_conf_key_value("notifications_ucs2_method")
                if method == 'prefix':
                    notifications_prefix = self._get_conf_key_value("notifications_ucs2_prefix")
                    text = notifications_prefix+text
                elif method == 'status-report':
                    rs = True

        if valid_numbers:
            dev = self.device_manager.get_main_device()
            if (dev is None) or (dev.get_card_status() != CARD_STATUS_READY):
                message = SENDING_NO_MODEM_INFO
                warning_dialog(message, parent=self.main_window, \
                        title=_("There was an error sending the message"))
                for number in valid_numbers:
                    self.sms_storage.sms_send_offline(number, text)
                self.__clear_newmessage_dialog()
            else:
                message = self._MessageToSend(valid_numbers, text, self.__get_conf_smsc(), notify=rs)
                thread.start_new_thread(self.__send_messages, (message, ))

            self.__set_newmessage_mode(False)
        else:
            self.__sms_send_error_cb(None)

    SENDING_RESULT_NONE  = 0
    SENDING_RESULT_OK    = 1
    SENDING_RESULT_ERROR = 2
    SENDING_RESULT_ABORT = 3
    SENDING_DIALOG_DONE  = gtk.RESPONSE_CLOSE

    SENDING_RETRIES      = 2
    MAX_TIMEOUT_PER_SMS  = 20

    class _MessageToSend():
        def __init__(self, numbers, text, smsc, notify=False):
            self.numbers = numbers if hasattr(numbers, '__iter__') else [ numbers ]
            self.text = text
            self.notify = notify
            self.smsc = smsc

    def __send_messages(self, messages):
        messages = messages if hasattr(messages, '__iter__') else [ messages ]
        for message in messages:
            self.__send_message(message.numbers, message.text, message.smsc, message.notify)

    def __send_message(self, numbers, text, smsc, request_status):

        # -- If there is no modem at this point we have a bug!
        device  = self.device_manager.get_main_device()
        if device is None:
            raise IndexError, "Coulnd't send SMS as no main modem available"

        imsi = device.get_imsi()
        roaming = device.is_roaming()
        messages, chars = self.__calculate_concatenation(text)
        show_error = False

        device.stop_checker()

        if self.__main_window_running:
            parent = self.main_window
            msg = _("Preparing messages to send")
        else:
            parent = self.themed_dock.get_main_window()
            msg = _("Preparing pending messages to be sent")

        dialog = wait_dialog(msg, parent=parent, threaded=True)
        gobject.idle_add(self.__send_messages_pre, dialog)
        # -- Wait some time, so the user receives our notification
        time.sleep(1)

        self.__sending_result = self.SENDING_RESULT_NONE

        for count in range(0, len(numbers)):
            number = numbers[count]
            name = self._addr_manager.get_name_from_number(number)
            receiver = number if (name is None) else name

            for retries in range(1, self.SENDING_RETRIES + 1):
                self.__sending_event.clear()
                self.__sending_result = self.SENDING_RESULT_NONE

                if retries == 1:
                    txt = _("Sending message to '%s'") % receiver
                else:
                    txt = _("Retrying sending message to '%s'") % receiver

                gobject.idle_add(dialog.set_markup, txt)

                # -- Trigger the SMS transfer, but without blocking this loop
                gobject.idle_add(device.sms_send, number, smsc, text, self.__sms_send_ok_cb, self.__sms_send_error_cb, request_status, False)

                # -- Now wait for an event from any callback
                self.__sending_event.wait(self.MAX_TIMEOUT_PER_SMS * messages)

                # -- Check if we have received a response
                if self.__sending_result == self.SENDING_RESULT_OK:
                    # -- Update in GConfig the number of sent messages
                    self.conf.set_sms_sent(self.conf.get_sms_sent(roaming, imsi) + messages, roaming, imsi)
                    break
                if self.__sending_result == self.SENDING_RESULT_ABORT:
                    count = len(numbers)
                    break

            # -- By errors store the message with the error flag
            error_flag = True if (self.__sending_result != self.SENDING_RESULT_OK) else False
            self.sms_storage.save_sent_sms(number, text, error=error_flag)
            if error_flag is True:
                show_error = True

        gobject.idle_add(self.__send_messages_post, device, dialog, show_error)

    def __send_messages_pre(self, dialog):
        while True:
            resp = dialog.run()
            if resp == self.SENDING_DIALOG_DONE:
                break

        dialog.destroy()

    def __send_messages_post(self, device, dialog, show_error):
        # -- Check if need to remove the message from the drafts
        if self.__editing_draft != False:
            self.sms_storage.sms_delete_draft(self.__editing_draft)

        # -- Clear the new message fields if the messages were sent without problems
        self.__clear_newmessage_dialog()

        # -- Send a signal for closing the dialog
        dialog.response(self.SENDING_DIALOG_DONE)

        if show_error is True:
            self.__show_send_message_error()

        # -- IMPORTANT: During the transfer is possible that the main modem was removed
        new_main = self.device_manager.get_main_device()
        if (new_main is not None) and (device == new_main):
            device.start_checker()

    def __show_send_message_error(self):
        message = SENDING_ERROR_POSTPAID
        url_show = None
        device = self.device_manager.get_main_device();
        if device is not None:
            if tgcm.country_support == 'es':
                if not device.is_postpaid():
                    url_recharge = 'https://www.canalcliente.movistar.es/fwk/cda/controller/CCLI_CW_publico/pub/0,4093,259_43408951_43408937_0_0,00.html'
                    url_txt  = SENDING_ERROR_PREPAID_URL_TXT
                    url_show = [url_recharge,url_txt]
                    message  = SENDING_ERROR_PREPAID

            if not self.conf.get_ui_general_key_value("not_show_sms_error_dialog"):
                if self.__show_notification_dialog(message=message, url=url_show, ask_again_check_box=True):
                    self.conf.set_ui_general_key_value("not_show_sms_error_dialog",True)

    def __sms_send_ok_cb(self, r):
        if (r is None) or (len(r) == 0):
            self.__sending_result = self.SENDING_RESULT_ERROR
        else:
            self.__sending_result = self.SENDING_RESULT_OK
        self.__sending_event.set()

    def __sms_send_error_cb(self, e):
        self.__sending_result = self.SENDING_RESULT_ERROR
        self.__sending_event.set()

    def __send_offline_messages(self):
        pending_messages = self.sms_storage.sms_list_to_send()
        if pending_messages:
            dev = self.device_manager.get_main_device()
            if (dev is not None) and (dev.get_card_status() == CARD_STATUS_READY):
                messages = [ ]
                for index, read, number, date in pending_messages:
                    index, read, number, date, text = self.sms_storage.sms_get_to_send(index)

                    messages.append(self._MessageToSend(number, text, self.__get_conf_smsc()))
                    self.sms_storage.sms_delete_to_send(index) #We remove the SMS even if there is an error

                thread.start_new_thread(self.__send_messages, (messages, ))

    def __clear_newmessage_dialog(self):
        self.newmessage_sendto_textview.get_buffer().set_text("")
        self.newmessage_message_textview.get_buffer().set_text("")
        self.__set_newmessage_summary_label("")
        self.__refresh_newmessage_buttons_state()

    def __received_list_update_sensitive_widgets(self, answer, forward, delete):
        self.received_answer_button.set_sensitive(answer)
        self.received_forward_button.set_sensitive(forward)
        self.received_deleteselected_button.set_sensitive(delete)

    def __sent_list_update_sensitive_widgets(self, edit, forward, delete):
        self.sended_edit_button.set_sensitive(edit)
        self.sended_forward_button.set_sensitive(forward)
        self.sended_deleteselected_button.set_sensitive(delete)

    def __conversation_list_update_sensitive_widgets(self, answer, forward, delete):
        self.conversations_answer_button.set_sensitive(answer)
        self.conversations_forward_button.set_sensitive(forward)
        self.conversations_deleteselected_button.set_sensitive(delete)

    def __on_received_list_treeview_selection_changed(self, selection):
        model, paths = selection.get_selected_rows()
        if paths:
            if len(paths) > 1:
                self.__received_list_update_sensitive_widgets(False, False, True)
                self.received_from_label.set_text("")
                self.received_date_label.set_text("")
                self.received_message_textview.get_buffer().set_text("")
            else:
                self.__received_list_update_sensitive_widgets(True, True, True)
                index = model.get_value(model.get_iter(paths[0]), 0)

                msg_id, readed, number, date, text = self.sms_storage.sms_get_received(index)
                text = self.__lstrip_notification_prefix(text)
                norm_number = self._addr_manager.normalize_number(number)
                name = self._addr_manager.get_name_from_number(norm_number)
                if name == None:
                    name = number

                date_object = datetime.datetime.strptime(date, '%y/%m/%d %H:%M:%S')
                date_now = datetime.datetime.now()
                if date_object.date() == date_now.date():
                    date_string = date_object.strftime("%H:%M")
                    self.received_date_label.set_text(_("Today at %s") % date_string)
                else:
                    date_string = date_object.strftime("%d/%m/%Y")
                    self.received_date_label.set_text(date_object.strftime("%d/%m/%Y %H:%M:%S"))
                self.received_from_label.set_text(name)

                self.received_message_textview.get_buffer().set_text("")
                self.__add_link_textbuffer(self.received_message_textview.get_buffer(),text)

                model.set_value(model.get_iter(paths[0]), 1, name)
                model.set_value(model.get_iter(paths[0]), 2, escape_markup(text.replace('\n', ' ')))
                model.set_value(model.get_iter(paths[0]), 3, date_string)

                if readed == 0:
                    self.sms_storage.sms_mark_received_as_read(index)
        else:
            self.__received_list_update_sensitive_widgets(False, False, False)
            self.received_from_label.set_text("")
            self.received_date_label.set_text("")
            self.received_message_textview.get_buffer().set_text("")

    def __on_sended_list_treeview_selection_changed(self, selection):
        model, paths = selection.get_selected_rows()
        if paths:
            if len(paths) > 1:
                self.__sent_list_update_sensitive_widgets(False, False, True)
                self.sended_for_label.set_text("")
                self.sended_date_label.set_text("")
                self.sended_message_textview.get_buffer().set_text("")
            else:
                self.__sent_list_update_sensitive_widgets(True, True, True)
                index = model.get_value(model.get_iter(paths[0]), 0)
                date = model.get_value(model.get_iter(paths[0]), 4)
                if date == "pending":
                    msg_id, readed, number, ignore_date, text = self.sms_storage.sms_get_to_send(index)
                    error = False
                else:
                    msg_id, readed, number, date, text, error = self.sms_storage.sms_get_sent(index)

                text = self.__lstrip_notification_prefix(text)
                norm_number = self._addr_manager.normalize_number(number)
                name = self._addr_manager.get_name_from_number(norm_number)
                if name == None:
                    name = number

                if error is True:
                    date_string = self.SENT_ERROR_TEXT
                    self.sended_date_label.set_text(date_string)
                elif date == "pending":
                    date_string = _("Pending")
                    self.sended_date_label.set_text(_("Pending"))
                else:
                    date_object = datetime.datetime.strptime(date, '%y/%m/%d %H:%M:%S')
                    date_now = datetime.datetime.now()
                    if date_object.date() == date_now.date():
                        date_string = date_object.strftime("%H:%M")
                        self.sended_date_label.set_text(_("Today at %s") % date_string)
                    else:
                        date_string = date_object.strftime("%d/%m/%Y")
                        self.sended_date_label.set_text(date_object.strftime("%d/%m/%Y %H:%M:%S"))

                self.sended_for_label.set_text(name)

                self.sended_message_textview.get_buffer().set_text("")
                self.__add_link_textbuffer(self.sended_message_textview.get_buffer(),text)

        else:
            self.__sent_list_update_sensitive_widgets(False, False, False)
            self.sended_for_label.set_text("")
            self.sended_date_label.set_text("")
            self.sended_message_textview.get_buffer().set_text("")

    def __on_draft_list_treeview_selection_changed(self, selection):
        model, paths = selection.get_selected_rows()
        if paths:
            if len(paths) > 1:
                self.draft_edit_button.set_sensitive(False)
                self.draft_deleteselected_button.set_sensitive(True)
                self.draft_for_label.set_text("")
                self.draft_date_label.set_text("")
                self.draft_message_textview.get_buffer().set_text("")
            else:
                self.draft_edit_button.set_sensitive(True)

                self.draft_deleteselected_button.set_sensitive(True)
                index = model.get_value(model.get_iter(paths[0]), 0)
                msg_id, readed, number, date, text = self.sms_storage.sms_get_draft(index)
                text = self.__lstrip_notification_prefix(text)
                number = self._addr_manager.normalize_number(number)
                name = self._addr_manager.get_name_from_number(number)
                name = number if name is None else '<' + name + '>'

                date_object = datetime.datetime.strptime(date, '%y/%m/%d %H:%M:%S')
                date_now = datetime.datetime.now()
                if date_object.date() == date_now.date():
                    date_string = date_object.strftime("%H:%M")
                    self.draft_date_label.set_text(_("Today at %s") % date_string)
                else:
                    date_string = date_object.strftime("%d/%m/%Y")
                    self.draft_date_label.set_text(date_object.strftime("%d/%m/%Y %H:%M:%S"))
                self.draft_for_label.set_text(name)

                self.draft_message_textview.get_buffer().set_text("")
                self.__add_link_textbuffer(self.draft_message_textview.get_buffer(), text)
        else:
            self.draft_edit_button.set_sensitive(False)
            self.draft_deleteselected_button.set_sensitive(False)
            self.draft_for_label.set_text("")
            self.draft_date_label.set_text("")
            self.draft_message_textview.get_buffer().set_text("")

    @_TreeViewSelection('received_list_treeview')
    def __on_received_deleteselected_button_clicked(self, widget, **kwargs):
        resp = question_dialog(_("The selected messages will be deleted permanently. Do you want to continue?"), \
                parent=self.main_window)
        if resp == gtk.RESPONSE_YES:
            model, paths = kwargs['received_list_treeview']
            for path in paths:
                msg_id = model.get_value(model.get_iter(path), 0)
                self.sms_storage.sms_delete_received(msg_id)

    def __fill_newmessage_tab(self, sendto_raw, message, mode, index=0):
        # -- Set the phone number(s)
        self.sendto_helper.set_raw_content(sendto_raw)

        # -- Set the message text
        message = self.__lstrip_notification_prefix(message)
        self.newmessage_message_textview.get_buffer().set_text(message)
        self.__set_newmessage_summary_label(message)

        # -- Change to the New Message tab and grab the focus
        # depending on the missing text
        self.main_notebook.set_current_page(0)
        if len(sendto_raw) == 0:
            self.newmessage_sendto_textview.grab_focus()
        else:
            self.newmessage_message_textview.grab_focus()
        self.__set_newmessage_mode(mode, index)

    @_TreeViewSelection('received_list_treeview')
    def __on_received_reply_button_clicked(self, widget, **kwargs):
        model, paths = kwargs['received_list_treeview']
        if paths and len(paths) == 1:
            index = model.get_value(model.get_iter(paths[0]), 0)
            number = self.sms_storage.sms_get_received(index)[2]
            name = self._addr_manager.get_name_from_number(number)
            contact = self.sendto_helper.get_contact(name, number)
            self.__refresh_newmessage_tab_with_contact(contact, '', False)

    @_TreeViewSelection('received_list_treeview')
    def __on_received_forward_button_clicked(self, widget, **kwargs):
        model, paths = kwargs['received_list_treeview']
        if paths and len(paths) == 1:
            index = model.get_value(model.get_iter(paths[0]), 0)
            text = self.sms_storage.sms_get_received(index)[4]
            self.__refresh_newmessage_tab("", text, False)

    def __on_received_list_button_pressed(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            gobject.idle_add(self.__on_received_reply_button_clicked, widget)

    def __on_received_list_key_pressed(self, widget, event):
        if (event.keyval == gtk.gdk.keyval_from_name('Delete')):
            self.__on_received_deleteselected_button_clicked(widget)
        return False

    def __on_sended_deleteselected_button_clicked(self, widget):
        resp = question_dialog(_("The selected messages will be deleted permanently. Do you want to continue?"), \
                parent=self.main_window)
        if resp == gtk.RESPONSE_YES:
            selection = self.sended_list_treeview.get_selection()
            model, paths = selection.get_selected_rows()
            if paths:
                for path in paths:
                    msg_id = model.get_value(model.get_iter(path), 0)
                    date = model.get_value(model.get_iter(path), 4)

                    if date != self.SEND_PENDING_MARK:
                        self.sms_storage.sms_delete_sent(msg_id)
                    else:
                        self.sms_storage.sms_delete_to_send(msg_id)

    @_TreeViewSelection('sended_list_treeview')
    def __on_sended_edit_button_clicked(self, widget, **kwargs):
        model, paths = kwargs['sended_list_treeview']
        if paths and len(paths) == 1:
            index = model.get_value(model.get_iter(paths[0]), 0)
            msg_id, readed, number, date, text, error = self.sms_storage.sms_get_sent(index)
            name = self._addr_manager.get_name_from_number(number)
            contact = self.sendto_helper.get_contact(name, number)
            self.__refresh_newmessage_tab_with_contact(contact, text, False)

    @_TreeViewSelection('sended_list_treeview')
    def __on_sended_forward_button_clicked(self, widget, **kwargs):
        model, paths = kwargs['sended_list_treeview']
        if paths and len(paths) == 1:
            index = model.get_value(model.get_iter(paths[0]), 0)
            text = self.sms_storage.sms_get_sent(index)[4]
            self.__refresh_newmessage_tab('', text, False)

    def __on_sended_list_button_pressed(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.__on_sended_edit_button_clicked(widget)

    def __on_sended_list_key_pressed(self, widget, event):
        if (event.keyval == gtk.gdk.keyval_from_name('Delete')):
            self.__on_sended_deleteselected_button_clicked(widget)
        return False

    def __on_conversations_received_checkbutton_toggled(self, widget):
        self._set_conf_key_value("conversations_show_received", self.conversations_received_checkbutton.get_active())
        selection = self.conversations_contacts_treeview.get_selection()
        model, paths = selection.get_selected_rows()
        self.__fill_conversations_contacts_treeview()
        conversations_contacts_selection_aux = self.conversations_contacts_treeview.get_selection()
        for path in paths:
            conversations_contacts_selection_aux.select_path(path)
        self.__on_conversations_contacts_treeview_selection_changed(selection)

    def __on_conversations_sended_checkbutton_toggled(self, widget):
        self._set_conf_key_value("conversations_show_sended", self.conversations_sended_checkbutton.get_active())
        selection = self.conversations_contacts_treeview.get_selection()
        model, paths = selection.get_selected_rows()
        self.__fill_conversations_contacts_treeview()
        conversations_contacts_selection_aux = self.conversations_contacts_treeview.get_selection()
        for path in paths:
            conversations_contacts_selection_aux.select_path(path)
        self.__on_conversations_contacts_treeview_selection_changed(selection)

    def __read_selected_treeview_values(self, treeview, column):
        selection = treeview.get_selection()
        model, paths = selection.get_selected_rows()
        retval = [ ]
        for path in paths:
            retval.append(model.get_value(model.get_iter(path), column))
        return (retval, paths)

    def __on_conversations_deleteselected_button_clicked(self, widget):
        numbers, selected_paths = self.__read_selected_treeview_values(self.conversations_contacts_treeview, 1)
        resp = question_dialog(_("The selected messages will be deleted permanently. Do you want to continue?"), \
                parent=self.main_window)
        if resp == gtk.RESPONSE_YES:
            selection = self.conversations_messages_treeview.get_selection()
            model, paths = selection.get_selected_rows()
            for path in paths:
                spool = model.get_value(model.get_iter(path), 2)
                msg_id = model.get_value(model.get_iter(path), 0)
                if spool == 'received':
                    self.sms_storage.sms_delete_received(msg_id)
                if spool == 'sended':
                    self.sms_storage.sms_delete_sent(msg_id)

            self.__connect_to_device()

            # -- Now re-select the contacts before the delete operation. The selection will reload
            # -- the corresponding conversation messages
            try:
                selection = self.conversations_contacts_treeview.get_selection()
                for path in selected_paths: selection.select_path(path)
            except Exception, err:
                print "@FIXME: Selection error in conversations, %s" % err

    def __on_conversations_contacts_treeview_selection_changed(self, selection):
        model, paths = selection.get_selected_rows()
        numbers = []
        for path in paths:
            numbers.append(model.get_value(model.get_iter(path), 1))

        # -- Reload the conversations treeview even no number is selected, just for displaying an empty list
        self.__conversations_messages_load(numbers)

    def __conversations_messages_load(self, numbers):
        show_received = self._get_conf_key_value("conversations_show_received")
        show_sended = self._get_conf_key_value("conversations_show_sended")

        model = gtk.ListStore(gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING,
                              gobject.TYPE_STRING)

        all_messages = []

        if show_received:
            messages = self.sms_storage.sms_list_received()
            if messages and len(messages) > 0:
                for msg_id, readed, number, date in messages:
                    number_aux = self._addr_manager.normalize_number(number)
                    if number_aux in numbers:
                        all_messages.append(('received', msg_id, readed, number, date))

        if show_sended:
            messages = self.sms_storage.sms_list_sent()
            if messages and len(messages) > 0:
                for msg_id, readed, number, date, error in messages:
                    number_aux = self._addr_manager.normalize_number(number)
                    if number_aux in numbers:
                        all_messages.append(('sended', msg_id, readed, number, date))

        all_messages.sort(reverse=True, key=operator.itemgetter(4))
        numbers = {}
        for spool, msg_id, readed, number, date in all_messages:
            number_norm = self._addr_manager.normalize_number(number)
            date_object = datetime.datetime.strptime(date, '%y/%m/%d %H:%M:%S')
            date_now = datetime.datetime.now()
            if date_object.date() == date_now.date():
                date_string = _("Today at %s") % date_object.strftime("%H:%M")
            else:
                date_string = date_object.strftime("%d/%m/%Y %H:%M:%S")

            if not number_norm in numbers.keys():
                numbers[number_norm] = self.__generate_colors(len(numbers))

            name = self._addr_manager.get_name_from_number(number)
            if name == None:
                name = number

            if spool == 'received':
                a, b, c, d, text = self.sms_storage.sms_get_received(msg_id)
                text = self.__lstrip_notification_prefix(text)
                text = escape_markup(text)
                model_string = _("From: %s\t\t\tReceived: %s\n%s") % (name, date_string, text)
                front_color = "#000000"
                bg_color = numbers [number_norm][0]
            if spool == 'sended':
                a, b, c, d, text, error = self.sms_storage.sms_get_sent(msg_id)
                # -- If the message is marked as failed don't include it in the conversation
                if error is True:
                    continue

                text = self.__lstrip_notification_prefix(text)
                text = escape_markup(text)
                model_string = _(u'To: %s\t\t\t\tSent: %s\n%s') % (name, date_string, text)
                front_color = "#ffffff"
                bg_color = numbers [number_norm][1]

            model.append([msg_id, model_string, spool, number, text, front_color, bg_color])

        self.conversations_messages_treeview.set_model(model)

    def __generate_colors(self, order):
        if 0.3 * order > 1:
            hue = 0.3 * order % 1 + 0.05
        else:
            hue = 0.3 * order

        dark_saturation = 1
        dark_value = 0.3
        light_saturation = 0.2
        light_value = 1

        dark_red, dark_green, dark_blue = colorsys.hsv_to_rgb(hue, dark_saturation, dark_value)
        light_red, light_green, light_blue = colorsys.hsv_to_rgb(hue, light_saturation, light_value)

        dark_red = round(dark_red * 255)
        dark_green = round(dark_green * 255)
        dark_blue = round(dark_blue * 255)
        light_red = round(light_red * 255)
        light_green = round(light_green * 255)
        light_blue = round(light_blue * 255)

        dark_rgb = "#%02x%02x%02x" % (dark_red, dark_green, dark_blue)
        light_rgb = "#%02x%02x%02x" % (light_red, light_green, light_blue)

        return [light_rgb, dark_rgb]

    def __on_conversations_messages_treeview_selection_changed(self, selection):
        model, paths = selection.get_selected_rows()
        if paths:
            if len(paths) > 1:
                self.__conversation_list_update_sensitive_widgets(False, False, True)
            else:
                self.__conversation_list_update_sensitive_widgets(True, True, True)
        else:
            self.__conversation_list_update_sensitive_widgets(False, False, False)

    @_TreeViewSelection('conversations_messages_treeview')
    def __on_conversations_answer_button_clicked(self, widget, **kwargs):
        model, paths = kwargs['conversations_messages_treeview']
        if paths and len(paths) == 1:
            number = model.get_value(model.get_iter(paths[0]), 3)
            name = self._addr_manager.get_name_from_number(number)
            contact = self.sendto_helper.get_contact(name, number)
            self.__refresh_newmessage_tab_with_contact(contact, "", False)

    @_TreeViewSelection('conversations_messages_treeview')
    def __on_conversations_forward_button_clicked(self, widget, **kwargs):
        model, paths = kwargs['conversations_messages_treeview']
        if paths and len(paths) == 1:
            text = model.get_value(model.get_iter(paths[0]), 4)
            self.__refresh_newmessage_tab("", text, False)

    def __on_conversations_messages_treeview_button_pressed(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.__on_conversations_answer_button_clicked(widget)

    def __on_conversations_messages_treeview_key_pressed(self, widget, event):
        if (event.keyval == gtk.gdk.keyval_from_name('Delete')):
            self.__on_conversations_deleteselected_button_clicked(widget)
        return False

    def __on_draft_list_button_pressed(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.__on_draft_edit_button_clicked(widget)

    def __on_draft_list_key_pressed(self, widget, event):
        if (event.keyval == gtk.gdk.keyval_from_name('Delete')):
            self.__on_draft_deleteselected_button_clicked(widget)
        return False

    def __on_draft_deleteselected_button_clicked(self, widget):
        resp = question_dialog(_("The selected messages will be deleted permanently. Do you want to continue?"), \
                parent=self.main_window)
        if resp == gtk.RESPONSE_YES:
            selection = self.draft_list_treeview.get_selection()
            model, paths = selection.get_selected_rows()
            for path in paths:
                id = model.get_value(model.get_iter(path), 0)
                self.sms_storage.sms_delete_draft(id)

    @_TreeViewSelection('draft_list_treeview')
    def __on_draft_edit_button_clicked(self, widget, **kwargs):
        model, paths = kwargs['draft_list_treeview']
        if paths and len(paths) == 1:
            index = model.get_value(model.get_iter(paths[0]), 0)
            msg_id, readed, number, date, text = self.sms_storage.sms_get_draft(index)
            self.__refresh_newmessage_tab(number, text, True, index)

    def __set_newmessage_mode(self, edit_draft, index=0):
        if edit_draft:
            self.newmessage_save_button.set_label(_("Update drafts"))
            self.__editing_draft = index
        else:
            self.newmessage_save_button.set_label(_("Save"))
            self.__editing_draft = False

    def __close_window_cb(self, widget, event):
        self.main_window.hide()
        self.__main_window_running = False
        return True

    def __on_activate_notifications_radiobutton_toggled(self, widget):
        active = self.activate_notifications_radiobutton.get_active()
        self._set_conf_key_value("sending_notifications", active)
        self.__newmessage_set_activate_notifications(active)

    def __on_newmessage_receipt_checkbutton_toggled(self, widget):
        active = self.newmessage_receipt_checkbutton.get_active()
        self._set_conf_key_value("last_notifications_state", active)

        text_buffer = self.newmessage_message_textview.get_buffer()
        self.__on_newmessage_message_textview_changed(text_buffer)

    def __newmessage_set_activate_notifications(self, active):
        if active:
            self.newmessage_receipt_checkbutton.set_sensitive(False)
            self.newmessage_receipt_checkbutton.set_active(True)
        else:
            self.newmessage_receipt_checkbutton.set_sensitive(True)
            self.newmessage_receipt_checkbutton.set_active(bool(self._get_conf_key_value("last_notifications_state")))

    def __on_change_smsc_checkbutton_toggled(self, widget):
        if self.change_smsc_checkbutton.get_active():
            self.smsc_entry.set_sensitive(True)
            self.smsc_entry.grab_focus()
        else:
            self.smsc_entry.set_sensitive(False)
            self._set_conf_key_value("use_custom_smsc", False)
        self.smsc_entry.set_text("")

    def __on_settings_closing(self, settings):
        try:
            if self.change_smsc_checkbutton.get_active():
                number = tgcm.ui.MSD.MSDUtils.Validate.phone(self.smsc_entry.get_text())
                self._set_conf_key_value("use_custom_smsc", True)
                self._set_conf_key_value("custom_smsc", number)
            error = False
        except tgcm.ui.MSD.MSDUtils.ValidationError, err:
            markup = _('Services - SMS')
            error_dialog(str(err), markup=markup, parent=self.main_window)
            error = True

        return error

    def __show_new_message_notification(self):
        last_received = self.sms_storage.sms_last_received()
        if last_received is None:
            return

        # -- This is an old code, so dont touch it for now and only convert to the process data
        msg_id, readed, number, date, text = last_received
        number = self._addr_manager.normalize_number(number)
        name = self._addr_manager.get_name_from_number(number)
        sender = number if (name is None) else name

        show_notif=True;

        if self._get_conf_key_value("popup_sms_available") == True:
            numbers = self._get_conf_key_value("popup_sms_numbers")
            for popup_number in numbers:
                popup_number = self._addr_manager.normalize_number(popup_number)
                if popup_number == number:
                    self.__show_popup_sms(sender, text, flash_sms=True)
                    show_notif=False;
                    break

        if show_notif:
            self._notify.send(_("SMS received"), sender, self.__new_message_icon)

    def __show_popup_sms(self, number, text, flash_sms=False):
        if flash_sms == False:
            title = _("%s Information") % self.conf.get_company_name()
        else:
            title = _("SMS from %s :") % number

        dialog = gtk.Dialog(title=title, buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        box = dialog.get_content_area()

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        scrolled_window.set_border_width(6)
        box.add(scrolled_window)

        textbuffer = gtk.TextBuffer()
        self.__add_link_textbuffer(textbuffer, text)

        textview = gtk.TextView()
        textview.set_cursor_visible(False)
        textview.set_editable(False)
        textview.set_wrap_mode(gtk.WRAP_WORD)
        textview.set_buffer(textbuffer)
        scrolled_window.add(textview)
        textview.connect("button-press-event", self.__textview_button_press_event)
        textview.connect("motion-notify-event", self.__textview_motion_notify_event)
        textview.connect("visibility-notify-event", self.__textview_visibility_notify_event)

        dialog.show_all()
        dialog.resize(300, 200)

        # -- This dialog should not block the GUI
        gobject.idle_add(self.__show_popup_sms_run, dialog)

    def __show_popup_sms_run(self, dialog):
        self.sms_popup_dialog = dialog
        dialog.run()
        dialog.destroy()
        self.sms_popup_dialog = None

    # -- Testcases
    # self.__show_popup_sms("1234", "Der Himmel ist blau und das All ist schwarz: www.prolinux.de Aber echt frech!")
    # self.__show_popup_sms("1234", "Guck mal:\n\nhttp://www.prolinux.de\n\nOK?", flash_sms=True)
    # self.__show_popup_sms("1234", "www.1234.com - www.5678.com", flash_sms=True)
    # self.__show_popup_sms("1234", "--> http://doof.com:8080 <---\n\n>> ftp://123.com:1234 <<\n\nOK", flash_sms=True)
    def __add_link_textbuffer(self, textbuffer, text, url_name = None):
        # -- Allowed chars according RF1738: [0-9a-zA-Z] and "$-_.+!*'(),"  ()
        # URL extraction regex kindly donated by the TGCM/Win folks, all
        # kudos goes to them ;-)
        url_regex = """
# Capture entire matched URL
(

    # Optional: only allow some network protocols
    (?:
        (?:
            http|https|ftp|HTTP|HTTPS|FTP    # URL protocol
        ):\\/\\/                             # colon followed by 2 slashes
    )?

    # Check if it is the beginning of a word
    (?<=\\b)

    # The URL must not start with the character '@'
    (?<!\\@)

    # The domain name must begin with a valid character
    (?:[\w\d]

        # Other characters allowed in the domain
        (?:[\w\dñÑ()+,-.:=;$_!*'%?#])*
    )

    # It is required to have a recognized domain
    \\.
    (?:
        aero|arpa|asia|biz|cat|com|COM|coop|edu|gov|inet|info|int|jobs|mil|
        mobi|museum|name|net|org|ORG|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|
        al|am|an|ao|aq|ar|as|at|au|aw|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|
        bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cu|
        cv|cx|cy|cz|de|dj|dk|dm|do|dz|ec|ee|eg|er|es|et|eu|fi|fj|fk|fm|fo|
        fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|
        hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|
        km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|
        mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|
        ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|
        py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|sk|sl|sm|sn|so|sr|
        st|su|sv|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|
        ua|ug|uk|UK|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|za|zm|zw
    )

    # Port number
    (?::[0-9]+)?

    # Characters allowed in a URL according to RF1738
    (?:
        \\/[\w\d()+,-.:=@;$_!*'%?#&|\\\\]*
    )*

    # Check if we have consumed all characters allowed in a URL
    (?![a-z0-9()+,-./:=@;$_!*'%?#&|\\\\])
)
"""
        url_pattern = re.compile(url_regex, re.IGNORECASE | re.VERBOSE)

        email_regex = '[\w\d._%+-]+@[\w\d.-]+\\.[\w]{2,6}$'
        email_pattern = re.compile(email_regex, re.IGNORECASE)

        phone_pattern = re.compile('\+?\d{3,}$')

        patterns = (('url', url_pattern), \
                ('email', email_pattern), \
                ('phone', phone_pattern))

        founds = []
        for word in text.split():
            word = word.strip(';,.-()[]{}<>«»¿?/\"\'')
            for wtype, pattern in patterns:
                match = pattern.match(word)
                if match is not None:
                    founds.append((wtype, word))
                    break

        # -- No URLs found? Return at this point
        if len(founds) == 0:
            textbuffer.set_text(text)
            return

        # Default link color if not defined in GTK theme
        link_color="blue"

        # Search for the 'link_color' property in GTK theme
        def_settings = gtk.settings_get_default()
        color_scheme = def_settings.get_property("gtk-color-scheme").strip()
        color_scheme = color_scheme.split("\n")
        for p in color_scheme:
            p = p.split(": ")
            if (p[0]=="link_color"):
                link_color=p[1]
                break

        # -- Need an unique text_iter as the default signal revalidates it to point to the end of the buffer
        pos = 0
        text_iter  = textbuffer.get_iter_at_offset(pos)
        for wtype, found in founds[:]:
            start = text.find(found, pos)
            end = start + len(found)
            tagged = text[start:end] if (url_name is None) else url_name

            # -- Create a separated tag for each text_iter as we use it for getting the page URL
            tag = textbuffer.create_tag(None, foreground=link_color, underline=pango.UNDERLINE_SINGLE)
            tag.set_data("type", wtype)
            tag.set_data("page", text[start:end])
            # -- Write the token without and with tag
            textbuffer.insert(text_iter, text[pos:start])
            textbuffer.insert_with_tags(text_iter, tagged, tag)

            pos = end

        # -- Put the last remaining token as normal text
        textbuffer.insert(text_iter, text[pos:])

    def __get_date_string(self, date):
        date_object = datetime.datetime.strptime(date, '%y/%m/%d %H:%M:%S')
        date_now = datetime.datetime.now()
        if date_object.date() == date_now.date():
            date_string = date_object.strftime("%H:%M")
        else:
            date_string = date_object.strftime("%d/%m/%Y")

        return date_string

    def __refresh_newmessage_tab_with_contact(self, sendto_raw, message, mode):
        self.__refresh_newmessage_tab(sendto_raw, message, mode)

    def __refresh_newmessage_tab(self, sendto_raw, message, mode, index=0):
        # Refresh the fields of the New Message tab if required (in some
        # cases it doesn't as the contents are already there)

        # Switch to "new" tab
        self.main_notebook.set_current_page(0)

        sendto_orig = self.sendto_helper.get_raw_contents()
        message_orig = self.__get_textview_text(self.newmessage_message_textview)

        is_empty = self.sendto_helper.is_empty() and (len(message_orig) == 0)
        is_same = (sendto_orig == sendto_raw) and (message_orig == message)
        is_writable = True

        # If the SMS editor is not empty or its contents are different from
        # the new ones, ask the user for confirmation
        if (not is_empty) and (not is_same):
            resp = question_dialog(_("A new message is being edited, do you want to continue and overwrite it?"), \
                    parent=self.main_window)
            if resp != gtk.RESPONSE_YES:
                is_writable = False

        if is_writable:
            self.__fill_newmessage_tab(sendto_raw, message, mode, index)

    def new_message_from_addresses(self, contacts):
        contacts = [self.sendto_helper.get_contact(name, phone) for name, phone in contacts]
        sendto_raw = ', '.join(contacts)
        self.__fill_newmessage_tab(sendto_raw, '', False)

    def __show_notification_dialog(self, message=None, title=None, type=gtk.MESSAGE_ERROR, url=None,ask_again_check_box=False):
        dialog = gtk.MessageDialog(type=type, buttons=gtk.BUTTONS_OK, message_format=message, parent=self.main_window)
        if title == None:
            dialog.set_title(_("Error on sending"))
        else:
            dialog.set_title(title)
        check_ask_again = gtk.CheckButton(_("Don't show again"))

        box = dialog.get_content_area()
        vbox = gtk.VBox(False, 0)
        if (url!=None):
            url_label = gtk.LinkButton(url[0],url[1])
            vbox.pack_start(url_label, False, True, 0)

        if (ask_again_check_box):
            vbox.pack_start(check_ask_again, False, True, 0)

        box.add(vbox)
        dialog.show_all()
        dialog.set_icon_from_file(self.window_icon_path)
        dialog.run()
        dialog.destroy()
        return check_ask_again.get_active();

    def remove_actions(self):
        self.main_window.hide()
        self._messaging_manager.is_messaging_available(False)

    def install_actions(self):
        self._messaging_manager.is_messaging_available(False)

    def show_all(self):
        tgcm.ui.MSD.MSDAction.show_all(self)
        self.connection_vbox.hide()

    def launch_action(self, params=None, parent=None, force_new_message=False):
        self.__connect_to_device()

        messages = self.sms_storage.sms_list_received()
        unread_messages = 0
        for id, readed, number, date in messages:
            if not readed:
                unread_messages += 1
        if not force_new_message and unread_messages > 0:
            self.main_notebook.set_current_page(1)
        else:
            self.main_notebook.set_current_page(0)

        self.__main_window_running = True
        self.main_window.show_all()
        self.main_window.deiconify()

    def close_action(self, params=None):
        self.main_window.hide()

    def __lstrip_notification_prefix(self, text):
        is_gsm7 = is_valid_gsm_text(text)
        if is_gsm7:
            notifications_prefix = self._get_conf_key_value("notifications_gsm7_prefix")
        else:
            notifications_prefix = self._get_conf_key_value("notifications_ucs2_prefix")

        text = text.rstrip('\n')
        if text.startswith(notifications_prefix):
            text = text.lstrip(notifications_prefix)
        return text

    def __calculate_concatenation(self, text):
        is_gsm7 = is_valid_gsm_text(text)
        count = len(text)

        if is_gsm7:
            if count <= 160:
                messages = 1
                remains = 160 - count
            else:
                messages = math.ceil(float(count) / 153)
                remains = messages * 153 - count
        else:
            if count <= 70:
                messages = 1
                remains = 70 - count
            else:
                messages = math.ceil(float(count) / 67)
                remains = messages * 67 - count

        return messages, remains

    def __get_conf_smsc(self):
        return (self._get_conf_key_value("custom_smsc")) if (self._get_conf_key_value("use_custom_smsc")) else (self._get_conf_key_value("smsc_any"))

    def __call_mail_user_agent(self, destination):
        command = ['xdg-open', 'mailto:%s' % destination]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE)
        process.communicate()


class SendToTextViewerHelper(gobject.GObject):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
    }

    def __init__(self, parent, textview, addr_manager):
        gobject.GObject.__init__(self)

        self.parent = parent
        self.textview = textview
        self.textview.set_accepts_tab(False)
        self.textbuffer = textview.get_buffer()
        self.config = tgcm.core.Config.Config()
        self.addr_manager = addr_manager
        self.popup = None

        self.phone_patterns = (
            re.compile('\+?\d{3,}$'),
        )

        tag = self.textbuffer.create_tag('contact')
        tag.set_property('foreground', 'blue')
        tag = self.textbuffer.create_tag('error')
        tag.set_property('foreground', 'red')

        self.suggestion_model = {}
        self.__update_suggestion_model()
        self.addr_manager.connect('addressbook-model-updated', self.__on_addr_model_updated_cb)

        self.textview.connect('key-press-event', self.__on_key_press_cb)
        self.textview.connect('move-cursor', self.__on_move_cursor_cb)
        self.textview.connect('button-release-event', self.__on_button_release_cb)
        self.textview.connect('focus-out-event', self.__on_focus_out_event_cb)
        self.textview.connect('visibility-notify-event', self.__on_visibility_notify_event_cb)
        self.textbuffer.connect('changed', self.__on_textbuffer_modified_cb)

    ## Public members

    def add_contact(self, contact):
        start_iter = self.textbuffer.get_start_iter()
        end_iter = self.textbuffer.get_end_iter()
        sendto_contents = self.textbuffer.get_text(start_iter, end_iter)
        destinations = sendto_contents.split(',')
        destinations.append(contact)
        destinations = [x.strip() for x in destinations if len(x.strip()) > 0]
        sendto_text = ', '.join(destinations) + ', '
        self.textbuffer.set_text(sendto_text)

        is_valid = self.validate(do_check_all=True)
        self.emit('changed', is_valid)

    def clear(self):
        start_iter = self.textbuffer.get_start_iter()
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.delete(start_iter, end_iter)
        self.emit('changed', False)

    def get_contact(self, name, phone):
        if name is not None:
            contact = '%s <%s>' % (name, phone)
            if not self.__is_valid_agenda_contact(contact):
                # attempt to get a valid agenda contact
                norm_phone = self.addr_manager.normalize_number(phone)
                contact = contact = '%s <%s>' % (name, norm_phone)

                if not self.__is_valid_agenda_contact(contact):
                    # desist on finding a valid agenda contact, just
                    # return the phone number
                    contact = phone

            return contact
        else:
            return phone

    def get_phones(self):
        textview_marks = self.__get_textview_segment_marks()

        # Attempt to extract phones from TextView segments
        phones = []
        for start_mark, end_mark in textview_marks:
            start_iter = self.textbuffer.get_iter_at_mark(start_mark)
            end_iter = self.textbuffer.get_iter_at_mark(end_mark)
            text = self.textbuffer.get_text(start_iter, end_iter)
            text = text.strip()

            # It is a valid contact name?
            if self.__is_valid_agenda_contact(text):
                phone = self.suggestion_model[text][1]
                phones.append(phone)
            # It is a valid phonenumber?
            elif self.__is_valid_phonenumber(text):
                phones.append(text)
            # Unrecognized segment, it must not be processed
            else:
                pass

        # Remove duplicates
        phones = list(set(phones))
        return phones

    def get_raw_contents(self):
        start_iter = self.textbuffer.get_start_iter()
        end_iter = self.textbuffer.get_end_iter()
        return self.textbuffer.get_text(start_iter, end_iter)

    def set_raw_content(self, text):
        self.textbuffer.set_text(text)
        is_valid = self.validate(do_check_all=True)
        self.emit('changed', is_valid)

    def is_duplicated(self, phone):
        phones = self.get_phones()
        return phone in phones

    def is_empty(self):
        start_iter = self.textbuffer.get_start_iter()
        end_iter = self.textbuffer.get_end_iter()
        text = self.textbuffer.get_text(start_iter, end_iter)
        return len(text) == 0

    def validate(self, do_check_all=False):
        textview_marks = self.__get_textview_segment_marks()

        # Editor insert/input mark
        insert_mark = self.textbuffer.get_insert()

        # It is necessary at least a valid contact
        num_valid_contacts = 0

        # Iterate through TextView contents checking them if necessary
        is_correct = True
        for start_mark, end_mark in textview_marks:
            insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
            start_iter = self.textbuffer.get_iter_at_mark(start_mark)
            end_iter = self.textbuffer.get_iter_at_mark(end_mark)

            # Always remove tags for the segment were the cursor is located
            is_cursor_in_segment = (insert_iter.compare(end_iter) == 0) or \
                    insert_iter.in_range(start_iter, end_iter)
            if is_cursor_in_segment:
                self.textbuffer.remove_all_tags(start_iter, end_iter)

            text = self.textbuffer.get_text(start_iter, end_iter)
            text = text.strip()

            # Ignore empty words
            if len(text) > 0:
                if len(start_iter.get_tags()) == 0:
                    # The text doesn't have any tag, so check it and decide
                    # what tag to apply

                    # Check if it is an agenda contact or valid phonenumber
                    if self.__is_valid_agenda_contact(text) or \
                            self.__is_valid_phonenumber(text):
                        num_valid_contacts += 1
                        tag_name = 'contact'
                    else:
                        is_correct = False
                        tag_name = 'error'

                    # Only apply a tag if the cursor is not in that segment,
                    # or the user has asked for it explicitely
                    if do_check_all or (not is_cursor_in_segment):
                        self.textbuffer.apply_tag_by_name( \
                                tag_name, start_iter, end_iter)

                else:
                    # Check existing tags in the text
                    tag = start_iter.get_tags()[0]
                    tag_name = tag.get_property('name')
                    if tag_name == 'error':
                        is_correct = False
                    elif tag_name == 'contact':
                        num_valid_contacts += 1

        # The sendto filed could not be correct if there is no valid contact
        if num_valid_contacts == 0:
            is_correct = False

        return is_correct

    ## Callback functions

    def __on_addr_model_updated_cb(self, sender):
        self.__update_suggestion_model()

    def __on_key_press_cb(self, textview, event):
        if self.popup != None:
            if event.keyval == gtk.gdk.keyval_from_name('Up'):
                self.popup.prev()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name('Down'):
                self.popup.next()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name('Return'):
                self._confirm_popup()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name('Escape'):
                self.__hide_popup()
                return True
        return False

    def __on_move_cursor_cb(self, textview, step_size, count, extend_selection):
        self.validate()

    def __on_button_release_cb(self, textview, event):
        self.__hide_popup()
        self.validate()

    def __on_focus_out_event_cb(self, textview, event):
        self.__hide_popup()
        is_valid = self.validate(do_check_all=True)
        self.emit('changed', is_valid)

    def __on_visibility_notify_event_cb(self, textview, event):
        self.__hide_popup()
        is_valid = self.validate(do_check_all=True)
        self.emit('changed', is_valid)

    def __on_textbuffer_modified_cb(self, textbuffer):
        # Get currently word under the cursor
        word = self.__get_word_at_input()[0]
        word = word.lstrip()

        # Check if the word is part of an existing contact
        is_popup_needed = self.__get_is_popup_needed(word)

        if self.popup != None:
            # Suggestions popup IS being shown

            if is_popup_needed:
                # Just filter what appears on the popup
                self.popup.filter_contacts(word)
            else:
                # Destroy suggestions popup!
                self.popup.destroy()
                self.popup = None

        else:
            # Suggestions popup is NOT being shown
            if is_popup_needed:
                # Create a new suggestions popup as it is needed
                self.__show_popup(self.textbuffer)
                self.popup.filter_contacts(word)
            else:
                pass

        is_valid = self.validate()
        self.emit('changed', is_valid)

        return False

    ## Helper functions

    def __update_suggestion_model(self):
        self.suggestion_model.clear()

        contacts = self.addr_manager.get_all_contacts()
        for contact in contacts:
            suggestion_text = '%s <%s>' % (contact.name, contact.phone)
            suggestion_item = (contact.name, contact.phone)
            self.suggestion_model[suggestion_text] = suggestion_item

    def __get_textview_segment_marks(self):
        # Split TextView contents by commas
        start = self.textbuffer.get_start_iter()
        current = start.copy()

        elements = []
        condition = True
        while condition:
            if (current.get_char() == ',') or current.is_end():
                end = current.copy()

                start_mark = self.textbuffer.create_mark(None, start)
                end_mark = self.textbuffer.create_mark(None, end)
                elements.append((start_mark, end_mark))

                start = current.copy()
                start.forward_char()

            if current.is_end():
                condition = False
            current.forward_char()

        return elements

    def __show_popup(self, textbuffer):
        if self.addr_manager is not None:
            position = self.parent.window.get_root_origin()
            completion = self.suggestion_model.keys()
            self.popup = self.CompleterPopup(self, position, completion)
            return True
        return False

    def _confirm_popup(self):
        # Replace the word being edited with the selected in
        # the suggestions popup
        contact_name = self.popup.confirm()
        start_iter, end_iter = self.__get_word_at_input()[1:3]
        self.textbuffer.delete(start_iter, end_iter)
        if start_iter.is_start():
            text_mask = '%s, '
        else:
            text_mask = ' %s, '
        self.textbuffer.insert(start_iter, text_mask % contact_name)
        self.popup = None

        # Check and decorate TextBuffer contents
        is_valid = self.validate()
        self.emit('changed', is_valid)

    def __hide_popup(self):
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None

    def __get_word_at_input(self):
        insert_textmark = self.textbuffer.get_insert()
        current = self.textbuffer.get_iter_at_mark(insert_textmark)

        while (not current.is_start()) and (current.get_char() != ','):
            current.backward_char()
        if current.get_char() == ',':
            current.forward_char()
        start = current.copy()

        while (not current.is_end()) and (current.get_char() != ','):
            current.forward_char()
        end = current.copy()

        word = self.textbuffer.get_text(start, end)
        word = word.lstrip()
        return word, start, end

    def __get_is_popup_needed(self, word):
        if len(word) == 0:
            return False

        if word in self.suggestion_model.keys():
            return False

        for contact in self.suggestion_model.keys():
            if word.lower() in contact.lower():
                return True

        return False

    def __is_valid_agenda_contact(self, text):
        return text in self.suggestion_model.keys()

    def __is_valid_phonenumber(self, text):
        for pattern in self.phone_patterns:
            match = pattern.match(text)
            if match is not None:
                return True
        return False


    class CompleterPopup(object):

        def __init__(self, sendto_helper, position, completion, size=POPUP_SIZE):
            object.__init__(self)
            self.sendto_helper = sendto_helper
            self.textview = self.sendto_helper.textview
            self.completion = completion
            self.position = position

            self.popup = gtk.Window(gtk.WINDOW_POPUP)
            parent = self.sendto_helper.textview.get_toplevel()
            self.popup.set_transient_for(parent)
            self.popup.set_destroy_with_parent(True)
            self.filter_text = None

            frame = gtk.Frame()
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

            model = gtk.ListStore(gobject.TYPE_STRING)
            for item in self.completion:
                ite = model.append()
                model.set(ite, 0, item)

            model = model.filter_new()
            model.set_visible_func(self.__filter_contacts_func)
            self.model = gtk.TreeModelSort(model)

            self.list_view = gtk.TreeView(self.model)
            self.list_view.set_property('headers-visible', False)

            self.selection = self.list_view.get_selection()
            self.selection.select_path((0,))

            column = gtk.TreeViewColumn('', gtk.CellRendererText(), text=0)
            self.list_view.append_column(column)

            sw.add(self.list_view)
            frame.add(sw)

            self.list_view.connect('row-activated', self.__on_row_activated_cb)

            self.popup.add(frame)
            self.popup.set_size_request(size[0], size[1])
            self.__show_popup()

        def __filter_contacts_func(self, model, text_iter, user_data=None):
            value = model.get_value(text_iter, 0)
            if (value is not None) and (self.filter_text is not None):
                if self.filter_text.lower() not in value.lower():
                    return False
            return True

        def __show_popup(self):
            tbuffer = self.textview.get_buffer()
            ite = tbuffer.get_iter_at_mark(tbuffer.get_insert())
            rectangle = self.textview.get_iter_location(ite)
            absX, absY = self.textview.buffer_to_window_coords(gtk.TEXT_WINDOW_TEXT,
                    rectangle.x + rectangle.width + 325,
                    rectangle.y + rectangle.height + 165)
            self.popup.move(self.position[0] + absX, self.position[1] + absY)
            self.popup.show_all()

        ## Public members

        def filter_contacts(self, text):
            self.filter_text = text
            self.model.get_model().refilter()

            # Check if it is a selected item
            ite = self.selection.get_selected()[1]
            if ite is None:
                self.selection.select_path((0,))

        def hide_popup(self, *args, **kwargs):
            self.popup.hide()

        def prev(self):
            model, ite = self.selection.get_selected()
            mite = model.get_path(ite)
            if mite != None and mite[0] > 0:
                path = (mite[0] - 1,)
                self.list_view.set_cursor(path)

        def next(self):
            model, ite = self.selection.get_selected()
            mite = model.iter_next(ite)
            if mite != None:
                path = model.get_path(mite)
                self.list_view.set_cursor(path)

        def confirm(self):
            model, ite = self.selection.get_selected()
            contact_name = model.get_value(ite, 0)
            self.destroy()
            return contact_name

        def destroy(self):
            self.popup.hide()
            self.popup.destroy()

        ## Callbacks

        def __on_row_activated_cb(self, treeview, path, column):
            self.sendto_helper._confirm_popup()

gobject.type_register(SendToTextViewerHelper)
