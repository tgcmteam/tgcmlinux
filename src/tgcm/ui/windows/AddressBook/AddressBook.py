#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#           Cesar Garcia <cesar.garcia@openshine.com>
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
import pango
import gtk
import gtk.gdk
import gobject
import subprocess
import threading
import thread

import tgcm
import tgcm.core.Addressbook
import tgcm.core.Singleton
import tgcm.ui.MSD
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import question_dialog, wait_dialog, \
        error_dialog, gtk_sleep, Validate, ValidationError, gtk_builder_magic

MIN_SEARCH_LEN = 0


class AddressBook:
    __metaclass__ = tgcm.core.Singleton.Singleton

    def __init__(self):
        self.conf = tgcm.core.Config.Config()
        self._addr_manager = tgcm.core.Addressbook.AddressbookManager()
        self._actions_manager = tgcm.core.Actions.ActionManager ()
        self._actions_manager.connect ('action-install-status-changed', self.__on_action_install_status_changed)
        self._theme_manager = tgcm.core.Theme.ThemeManager()
        self.XMLTheme = tgcm.core.XMLTheme.XMLTheme()
        self.settings = tgcm.ui.windows.Settings()

        self.__sms_action = self._actions_manager.get_action('sms')

        self.dialog = tgcm.ui.windows.ServiceWindow('banner.addrbook', _("Contacts"))
        self.dialog.resize(750, 500)

        self.icon_file = self._theme_manager.get_icon ('icons', 'addressbook_taskbar.png')
        self.dialog.set_icon_from_file(self.icon_file)

        self._last_search_text =""
        self._clip_board = None

        self.SMS_action_installed = self.__sms_action.is_installed()

        # Main window
        self.windows_dir = os.path.join(tgcm.windows_dir , self.__class__.__name__)
        gtk_builder_magic(self, \
                filename=os.path.join(self.windows_dir, 'AddressBook_main.ui'), \
                prefix='addr')
        self.dialog.add (self.main_vbox)

        if tgcm.country_support != 'uk':
            self.search_label.destroy()

        self._search_entry_init_text = _("Text to find")
        self.search_entry.set_text(self._search_entry_init_text)
        self.statusbar.hide()

        # Contacts treeview
        model = self._addr_manager.get_treeview_model()
        model = model.filter_new()
        model.set_visible_func(self.__search_filter_func, self.search_entry)
        model = gtk.TreeModelSort(model)
        self.contact_treeview.set_model(model)

        self._contact_editor = ContactEditor(self.dialog)
        self.__build_treeview(self.contact_treeview)

        # Toolbar buttons
        button_list = ((self.add_contact_button, 'new_contact.png'), \
                (self.remove_contact_button, 'delete_contact.png'), \
                (self.synchronize_contacts_button, 'import.png'), \
                (self.edit_contact_button, 'edit_contact.png'), \
                (self.sms_button, 'sms.png'), \
                (self.mail_button, 'mail.png'))

        for button, icon_name in button_list:
            icon = gtk.image_new_from_file(self._theme_manager.get_icon('addressbook', icon_name))
            button.set_icon_widget(icon)
            icon.show()

#        # Contextual menu
        self.contextual_menu = gtk.Menu()
        menu_items = (('sms', _('Send message'), 'sms.png', self.on_send_sms_button_clicked), \
                ('mail', _('Send mail'), 'mail.png', self.on_send_mail_button_clicked), \
                ('new', _('New contact'), 'new_contact.png', self.on_add_button_clicked), \
                ('modify', _('Modify contact'), 'edit_contact.png', self.on_edit_button_clicked), \
                ('delete', _('Delete contact'), 'delete_contact.png', self.on_remove_button_clicked))

        self.contextual_menu_items = {}
        for item_key, item_str, item_icon, item_callback in menu_items:
            menu_item = gtk.ImageMenuItem(item_str)
            icon = gtk.image_new_from_file(self._theme_manager.get_icon('addressbook', item_icon))
            menu_item.set_image(icon)
            menu_item.connect('activate', item_callback)
            menu_item.show_all()

            self.contextual_menu.append(menu_item)
            self.contextual_menu_items[item_key] = menu_item

        # Signals
        self.dialog.connect('delete-event', self.on_close_button_clicked)
        self.dialog.close_button.connect('clicked', self.on_close_button_clicked)
        self.add_contact_button.connect("clicked",self.on_add_button_clicked)
        self.remove_contact_button.connect("clicked",self.on_remove_button_clicked)
        self.edit_contact_button.connect("clicked",self.on_edit_button_clicked)
        self.synchronize_contacts_button.connect("clicked",self.on_synchronize_button_clicked)
        self.sms_button.connect("clicked",self.on_send_sms_button_clicked)
        self.mail_button.connect("clicked",self.on_send_mail_button_clicked)
        self.search_entry.connect("changed",self.on_search_entry_changed);
        self.search_entry.connect ("focus-in-event", self.on_search_entry_focus_in)
        self.search_entry.connect ("focus-out-event", self.on__search_entry_focus_out)
        self.clear_search_entry_button.connect("clicked", self.on_clear_search_entry_button_clicked)

        self.contact_treeview.connect("button_press_event",self.__contact_treeview_button_event_cb)
        self.contact_treeview.connect("key_press_event",self.__contact_treeview_key_event_cb)
        self.contact_treeview.connect("cursor-changed",self.__contact_treeview_cursor_changed_cb,None)
        treeselection = self.contact_treeview.get_selection()
        treeselection.set_mode (gtk.SELECTION_MULTIPLE)
        self.__contact_treeview_cursor_changed_cb_h = treeselection.connect ("changed", self.__contact_treeview_cursor_changed_cb, None)

    def run (self):
        self.__check_button_sensitivity()
        self.dialog.show()

    def on_close_button_clicked(self, *args):
        self.dialog.hide()
        return True

    def __contacts_treeview_sort(self, column, treeview, number):
        if column.get_sort_order() == gtk.SORT_ASCENDING:
            column.set_sort_order(gtk.SORT_DESCENDING)
        else:
            column.set_sort_order(gtk.SORT_ASCENDING)

        for col in treeview.get_columns():
            col.set_sort_indicator(False)

        column.set_sort_indicator(True)
        ls = treeview.get_model()
        ls.set_sort_column_id(number, column.get_sort_order())

    def __build_treeview(self, tree_view):
        db_fields =   ["name","phone","email" ]

        base_id = 1
        self._columns = []

        if tgcm.country_support != 'uk':
            fields = [_("Name"),_("Telephone"),_("E-mail")]
        else:
            fields = [_("Name"),_("Phone number"),_("E-mail")]

        for field in fields:
            col = gtk.TreeViewColumn(field)
            tree_view.append_column(col)
            cell = gtk.CellRendererText()
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            col.set_cell_data_func(cell,self.__cell_render_func, self.search_entry)
            col.set_resizable(True)
            col.set_reorderable(True)
            col.set_clickable(True)
            col.connect('clicked', self.__contacts_treeview_sort, tree_view, base_id)

            if field == _('Name'):
                col.set_min_width(200)
            elif field == _('E-mail'):
                col.set_expand(True)
            else:
                col.set_min_width(120)

            cell.set_property("editable", True)
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            cell.connect("edited", self.__cell_edited_cb, (base_id, db_fields[base_id - 1]))

            self._columns.append(col)
            base_id = base_id + 1

        # -- Add at the end a column for the tooltip
        col = gtk.TreeViewColumn('Tooltip', gtk.CellRendererText())
        col.set_visible(False)
        tree_view.append_column(col)
        self._columns.append(col)

        # -- Set the tooltip column
        colnr = self._addr_manager.get_column_number_tooltip()
        self.contact_treeview.set_tooltip_column(colnr)

        self.contact_treeview.set_cursor(0)

    def __cell_edited_cb(self, cell, row, new_text, field_index_db_field_tuple=None):
        field_index, db_field = field_index_db_field_tuple

        new_value = new_text.strip()
        model     = self.contact_treeview.get_model()
        obj_id    = model[row][0]
        old_value = model[row][field_index]

        # -- Check if we have something to do as this callback is called when no modification was applied too
        if old_value == new_value:
            return

        # -- Make a sanity check for the modified cell value (name, phone number, etc.)
        try:
            column = field_index
            if column == self._addr_manager.get_column_number_name():
                self._contact_editor.validate_contact_name(new_value, self.dialog)
            elif column == self._addr_manager.get_column_number_phone():
                self._contact_editor.validate_contact_phone(new_value, self.dialog)
            elif column == self._addr_manager.get_column_number_email():
                self._contact_editor.validate_contact_email(new_value, self.dialog)
            else:
                raise IndexError, "Invalid column number %i" % column
        except _ContactError:
            return
        except Exception, err:
            print "@FIXME: AddressBook, error cell edit cb, %s" % err
            return

        # -- Good, the contact seems to be safe
        contact = self._addr_manager.get_contact(obj_id)
        exec ("contact.%s = '%s'" % (db_field, new_value))
        contact.save()

    def __cell_render_func(self,column, cell_renderer, model, iter, search_entry):
        entry_text = search_entry.get_text()
        if entry_text == None:
            return
        search_text = entry_text.strip().lower()
        if len(search_text) <= MIN_SEARCH_LEN :
            return

        idx =  self.contact_treeview.get_columns().index(column) + 1

        value = model.get_value(iter, idx)
        if value == None:
            return

        value_low = value.lower()
        idx = value_low.find(search_text)
        if idx >=0:
            prefix = value[:idx]
            body   = value[idx : idx +len(search_text)]
            suffix = value[idx + len(search_text):]
            cell_renderer.set_property('markup','%s<span background="blue" foreground="white">%s</span>%s' % (prefix, body, suffix))

    def __search_filter_func(self,model,iter,search_entry):
        search_text = search_entry.get_text()
        if search_text == self._search_entry_init_text:
            search_text = ""

        if search_text != None and len(search_text) <= MIN_SEARCH_LEN:
            return True

        num_col = model.get_n_columns()
        for i in range(num_col -1):
            value = model.get_value(iter, i+1)
            if value == None:
                continue
            value = value.strip().lower()
            if  search_text.lower() in value:
                return True

        return False

    def __on_action_install_status_changed (self, action_manager, action_obj, installed, data=None):
        if action_obj.codename == "MSDASendSMS":
            self.SMS_action_installed = action_obj.is_installed()
        self.__check_button_sensitivity()

    def __contact_treeview_selection_foreach_cb (self, model, path, iter, selected_ids):
        selected_ids.append (model.get_value (iter, 0))

    def __contacts_base_model_foreach_cb (self, model, path, iter, selected_ids):
        selection = self.contact_treeview.get_selection()
        id = model.get_value (iter, 0)
        if id in selected_ids:
            iter_aux = self.contact_treeview.get_model().get_model().convert_child_iter_to_iter(iter)
            iter_aux2 = self.contact_treeview.get_model().convert_child_iter_to_iter(None, iter_aux)
            selection.select_iter (iter_aux2)

    def __selected_contacts(self):
        contacts = []
        selection = self.contact_treeview.get_selection()
        selection.selected_foreach (self.__contact_selection_foreach_cb, contacts)
        return contacts

    def __contact_selection_foreach_cb (self, model, path, iter, contacts):
        model = self.contact_treeview.get_model()
        iter = model.get_iter (path)
        if iter != None:
            contact_id = model.get_value(iter, 0)
            target_contact  = self._addr_manager.get_contact (contact_id)
            contacts.append (target_contact)

    def __contact_treeview_button_event_cb(self,widget,event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.on_edit_button_clicked(widget)

        if event.button == 3:
            time = event.time

            path = self.contact_treeview.get_path_at_pos(int(event.x),int(event.y))
            selection = self.contact_treeview.get_selection()
            rows = selection.get_selected_rows()

            if path[0] not in rows[1]:
                selection.unselect_all()
            selection.select_path(path[0])

            self.contextual_menu.popup (None, None, None, event.button, time)

            return True

    def __contact_treeview_key_event_cb (self, widget, event):
        if (event.keyval == gtk.gdk.keyval_from_name ('Delete')):
            self.on_remove_button_clicked(self, widget)
        return False

    def __contact_treeview_cursor_changed_cb(self,widget,event):
        self.__check_button_sensitivity()

    def __check_button_sensitivity(self):
        selected_rows = self.contact_treeview.get_selection().count_selected_rows()
        buttons = (self.edit_contact_button, self.remove_contact_button, self.sms_button, self.mail_button)
        new_state = selected_rows > 0
        for button in buttons:
            button.set_sensitive(new_state)

        check_sms = True
        if not self.SMS_action_installed:
            self.sms_button.set_sensitive (False)
            self.contextual_menu_items['sms'].set_sensitive (False)
            check_sms = False

        if selected_rows > 0:
            active_sms = False
            active_emails = False
            contacts = self.__selected_contacts()
            for contact in contacts:
                if contact.phone != None and len (contact.phone) > 0:
                    active_sms = True
                if contact.email != None and len (contact.email) > 0:
                    active_emails = True
                if active_sms or active_emails:
                    break

            if check_sms:
                self.sms_button.set_sensitive (active_sms)
                self.contextual_menu_items['sms'].set_sensitive (active_sms)

            self.mail_button.set_sensitive (active_emails)
            self.contextual_menu_items['mail'].set_sensitive (active_emails)

        # Check edit button sensitivity
        if selected_rows == 0 or selected_rows > 1:
            self.edit_contact_button.set_sensitive (False)
            self.contextual_menu_items['modify'].set_sensitive (False)
        else:
            self.edit_contact_button.set_sensitive (True)
            self.contextual_menu_items['modify'].set_sensitive (True)

    def __on_export_clicked(self,widget,event=None):
        dialog = gtk.FileChooserDialog (_("Select destination file to export"), \
            self.dialog, gtk.FILE_CHOOSER_ACTION_SAVE, \
            buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_icon_from_file(self.icon_file)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            outputstream = ""
            for contact in  self._addressbook.get_all_contacts():
                outputstream = "%s%s,%s,%s,%s\n" % (outputstream,
                                                       contact.name,
                                                       contact.phone,
                                                       contact.email)
            fout = open ("%s.csv" % dialog.get_filename(), "w")
            fout.write (outputstream)
            fout.close()
        dialog.destroy()

    def __on_import_clicked (self, widget, event= None):
        dialog = gtk.FileChooserDialog (_("Select file to import"), \
            self.dialog, gtk.FILE_CHOOSER_ACTION_OPEN, \
            buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_icon_from_file(self.icon_file)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self._addr_manager.import_from_csv (dialog.get_filename())
            self.__check_button_sensitivity()

        dialog.destroy()

    def __on_copy_clicked (self, widget, event=None):
        selection = self.contact_treeview.get_selection()
        if selection.count_selected_rows() != 1:
            return

        model, itera  = selection.get_selected()
        contact_id = model.get_value(itera,0)
        target_contact  = self._addr_manager.get_contact(contact_id)
        self._clip_board.name = target_contact.name
        self._clip_board.phone = target_contact.phone
        self._clip_board.email = target_contact.email

    def __on_cut_clicked (self, widget, event=None):
        selection = self.contact_treeview.get_selection()
        if selection.count_selected_rows() != 1:
            return

        model ,itera  = selection.get_selected()
        contact_id = model.get_value(itera,0)
        target_contact  = self._addr_manager.get_contact(contact_id)
        self._clip_board.name = target_contact.name
        self._clip_board.phone = target_contact.phone
        self._clip_board.email = target_contact.email
        target_contact.destroySelf()

        self.contact_treeview.set_cursor(0)
        self.__check_button_sensitivity()

    def __on_paste_clicked (self, widget, event=None):
        if self._clip_board == None:
            return

        name = self._clip_board.name
        phone = self._clip_board.phone
        email = self._clip_board.email
        self._addr_manager.get_new_contact (name, phone, email)

        self.__check_button_sensitivity()

    def on_search_entry_changed(self,widget,event=None):
        new_search_text = widget.get_text()
        old_search_text =  self._last_search_text
        self._last_search_text = new_search_text

        if len(new_search_text) > MIN_SEARCH_LEN or len(old_search_text) >= MIN_SEARCH_LEN :
            self.contact_treeview.get_model().get_model().refilter()

    def on_search_entry_focus_in (self, widget, event, data=None):
        if self.search_entry.get_text() == self._search_entry_init_text:
            self.search_entry.set_text("")

    def on__search_entry_focus_out (self, widget, event, data=None):
        if self.search_entry.get_text() == "":
            self.search_entry.set_text(self._search_entry_init_text)

    def on_clear_search_entry_button_clicked(self, widget, event=None):
        self.search_entry.set_property("has-focus", True)
        self.search_entry.set_text ("")

    def on_send_sms_button_clicked (self, widget, data=None):
        selected_contacts = self.__selected_contacts()
        if selected_contacts is not None:
            contacts = []
            for contact in selected_contacts:
                contacts.append((contact.name, contact.phone))
            self.__sms_action.launch_action(parent=self.dialog, force_new_message=True)
            self.__sms_action.new_message_from_addresses(contacts)

    def on_send_mail_button_clicked(self,widget,data=None):
        contacts = self.__selected_contacts()
        if contacts is not None:
            receivers = [ ]
            for contact in contacts:
                if contact.email != None and len(contact.email) > 0:
                    receivers.append(contact.email)

            if len(receivers) > 0:
                widget.set_sensitive(False)
                proc = subprocess.Popen([ 'xdg-email' ] + receivers)
                gobject.idle_add(self.__send_email_button_wait_proc, proc, widget)

    def __send_email_button_wait_proc(self, proc, widget):
        proc.wait()
        if proc.returncode != 0:
            msg  = _('A client application for sending email can not be found.')
            mark = _('Error starting email client')
            error_dialog(msg, markup = mark, parent = self.dialog)
        else:
            # -- Give the application some time before enabling the button
            gtk_sleep(1.0)

        widget.set_sensitive(True)

    def on_add_button_clicked(self,widget,event=None):
        response = self._contact_editor.run()

        if response != gtk.RESPONSE_OK:
            return

        # Creo uno nuevo
        d = self._contact_editor.get_dict()
        self._addr_manager.get_new_contact (d['name'], d['phone'], d['email'])

        self.__check_button_sensitivity()

    def __remove_contacts(self, contacts, dlg):

        ARBITRARY_WAIT = 0.5

        # -- Give the dialog some time otherwise it remains blocked
        gtk_sleep(ARBITRARY_WAIT)

        for contact in contacts:
            contact.destroySelf(notify=False)

        selection = self.contact_treeview.get_selection()
        selection.handler_block(self.__contact_treeview_cursor_changed_cb_h)

        self._addr_manager.update_model()

        selection.handler_unblock(self.__contact_treeview_cursor_changed_cb_h)

        self.contact_treeview.set_cursor(0)
        self.__check_button_sensitivity()

        gtk_sleep(ARBITRARY_WAIT)
        dlg.destroy()

    def on_remove_button_clicked(self, widget, event=None):
        contacts = self.__selected_contacts()
        length = len (contacts)
        if length == 0:
            return
        elif length == 1:
            message = _(u'Do you want to delete the contact "%s"?') % (contacts[0].name)
            wait_msg = _('Please wait until the contact is deleted.')
        else:
            message = _(u'Do you want to delete the %d selected contacts?') % length
            wait_msg = _('Please wait until the contacts are deleted.')

        response = question_dialog(message, parent = self.dialog, icon = 'addressbook_taskbar.png')
        if response != gtk.RESPONSE_YES:
            return

        dlg = wait_dialog(wait_msg, parent = self.dialog, threaded = True)
        gobject.idle_add(self.__remove_contacts, contacts, dlg)
        dlg.run()

    def on_edit_button_clicked(self,widget,event=None):
        selection = self.contact_treeview.get_selection()

        if selection.count_selected_rows()!= 1:
            return

        contacts = self.__selected_contacts()
        if len(contacts) == 1:
            contact  =contacts[0]
            response = self._contact_editor.run(contact)
            if response != gtk.RESPONSE_OK:
                return

            d = self._contact_editor.get_dict()
            contact.name = d['name']
            contact.phone = d['phone']
            contact.email = d['email']
            contact.save()

            self.__check_button_sensitivity()

    def on_synchronize_button_clicked(self, widget, event=None):
        dlg = ImportDialog(self.dialog, self.contact_treeview)

        # -- @XXX: Before importing save the selected items for restoring the selection after the import
        # -- but here need the numbers not only the paths
        selection = self.contact_treeview.get_selection()
        #model, rows = selection.get_selected_rows()
        selection.unselect_all()
        dlg.run()
        #for row in rows:
        if len(self.contact_treeview.get_model()) > 0:
            selection.select_path((0,))

        self.contact_treeview.grab_focus()

    def __on_show_help_clicked (self, widget, event=None):
        dir_name = os.path.dirname(tgcm.help_uri)
        help_file = os.path.join(dir_name, "em_61.htm")
        ret = os.popen("gconftool-2 -g /desktop/gnome/applications/browser/exec")
        url_cmd = ret.readline().split()
        if len(url_cmd) > 0 :
            os.system("%s 'file://%s' &" % (url_cmd[0], help_file))


class ImportDialog():

    TAB_SELECTING = 0
    TAB_IMPORTING = 1
    TAB_FINISHED  = 2

    DEVICE_AGENDA = 0
    DEVICE_SIM    = 1

    ERROR_MESSAGE_SIM = _("It is not possible to import contacts from the SIM card because the Mobile Internet Device is busy or not ready.\nPlease insert it or turn it on if it is switched off, and try again in a few moments.")

    STATE_IDLE     = 0
    STATE_RUNNING  = 1
    STATE_CANCELED = 2
    STATE_FINISHED = 3

    # -- Maximal time for finishing the contacts import
    IMPORT_CONTACTS_MAX_TIMEOUT = 180

    def __init__(self, parent, contact_treeview):
        self._parent = parent
        self.contact_treeview = contact_treeview

        self.conf = tgcm.core.Config.Config()
        self._addr_manager = tgcm.core.Addressbook.AddressbookManager ()
        self._theme_manager = tgcm.core.Theme.ThemeManager()
        self.icon_file = self._theme_manager.get_icon('icons', 'addressbook_taskbar.png')

        gtk_builder_magic(self, \
                filename=os.path.join(tgcm.windows_dir, 'AddressBook', 'AddressBook_import.ui'), \
                prefix='ipd')

        self.notebook.set_show_tabs(False)
        self.back_button.set_sensitive(False)
        self.next_button.set_sensitive(False)
        self.result_textview.set_wrap_mode (gtk.WRAP_WORD_CHAR)

        self.__set_origin_model()

        self._canceling = False

        self.cancel_button.connect("clicked" , self.on_cancel_button_clicked)
        self.back_button.connect("clicked" , self.on_back_button_clicked)
        self.next_button.connect("clicked" , self.on_next_button_clicked)

        file_icon = self._theme_manager.get_icon('addressbook', 'import.png')
        self.import_contacts_window.set_icon_from_file(file_icon)
        self.import_contacts_window.set_deletable(False)
        self.import_contacts_window.set_modal(True)
        self.import_contacts_window.set_transient_for(parent)
        self.import_contacts_window.set_skip_taskbar_hint(False)
        self.import_contacts_window.connect('delete_event', self.__on_delete_event)

        self.__loop = None
        self.__import_event = threading.Event()
        self.__import_state = self.STATE_IDLE
        self.__import_pbar_id = None

    def __on_delete_event(self, dialog, widget=None, event=None):
        # Simulate a cancel event if the user closes the dialog
        self.on_cancel_button_clicked(None)

    def run(self):
        parent = self.import_contacts_window.get_transient_for()
        parent.set_sensitive(False)
        parent.set_deletable(False)
        self.import_contacts_window.show_all()
        self.__loop = gobject.MainLoop()
        self.__loop.run()
        self.import_contacts_window.destroy()
        parent.set_sensitive(True)
        parent.set_deletable(True)

    def __set_origin_model (self):
        base_id = 0
        for field in ["id", "origin"]:
            col = gtk.TreeViewColumn(field)
            self.origin_treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            if field == "origin":
                col.set_visible (True)
            else:
                col.set_visible (False)
            base_id = base_id + 1

        model = gtk.ListStore(gobject.TYPE_INT,
                              gobject.TYPE_STRING)
        model.append ([1, _("Device SIM")])

        self.origin_treeview.set_model(model)
        self.origin_treeview.set_headers_visible(False)

        selection = self.origin_treeview.get_selection()
        selection.connect ('changed', self.__on_origin_treeview_selection_changed)

    def __on_origin_treeview_selection_changed (self, selection):
        if selection.count_selected_rows() > 0:
            self.next_button.set_sensitive (True)
        else:
            self.next_button.set_sensitive (False)

    def __import_contacts_from_sim_caller(self, cancel):
        imported = self._addr_manager.import_from_device_SIM(cancel)
        if (not self.__import_event.is_set()) and (not cancel.is_set()):
            self.__import_state = self.STATE_FINISHED
            self.__import_count = imported
            self.__import_event.set()

    def __import_contacts_from_sim(self):
        # -- Before starting, check the state of the address book manager. If the
        progress, state, running = self._addr_manager.get_importing_state()
        if running:
            self.__import_contacts_post(self.ERROR_MESSAGE_SIM)
            self.__import_state = self.STATE_FINISHED
            return

        # -- OK, we can start to import from the SIM
        try:
            number_before = len(self.contact_treeview.get_model())
            cancel = threading.Event()
            self.__import_event.clear()
            self.__import_count = 0
            self.__import_state = self.STATE_RUNNING
            thread.start_new_thread(self.__import_contacts_from_sim_caller, (cancel, ))
        except Exception, err:
            print "@FIXME: Calling SIM contacts importer, %s" % err

        self.__import_event.wait(self.IMPORT_CONTACTS_MAX_TIMEOUT)
        if self.__import_state == self.STATE_CANCELED:
            cancel.set()
            gtk_sleep(0.5)
            number_after = len(self.contact_treeview.get_model())
            msg = _("Cancelled by user. %s contacts have been already imported from the selected source.") % (number_after - number_before)
        elif self.__import_state == self.STATE_RUNNING:
            cancel.set()
            msg = _("Unexpected timeout while importing contacts from the selected source.")
        elif self.__import_state == self.STATE_FINISHED:
            imported = self.__import_count
            if imported >= 0:
                msg = _("%s contacts in the address book have been imported from the selected source.") % imported
            else:
                msg = self.ERROR_MESSAGE_SIM

        gobject.idle_add(self.__import_contacts_post, msg)

    def on_cancel_button_clicked(self, widget, event=None):
        if self.__import_state == self.STATE_RUNNING:
            # -- OK, here we need to cancel the import
            self.__import_state = self.STATE_CANCELED
            self.__import_event.set()
        else:
            self.__loop.quit()

    def on_back_button_clicked (self, widget):
        active = self.notebook.get_current_page ()
        if active == 1:
            self.notebook.set_current_page (0)

            self.back_button.set_sensitive(False)
            self.next_button.set_sensitive(True)

    def on_next_button_clicked (self, widget):
        tab = self.notebook.get_current_page ()

        # -- Disable the next button at first
        self.next_button.set_sensitive(False)

        if tab == self.TAB_SELECTING:
            self.back_button.set_sensitive(False)
            self.cancel_button.set_sensitive(True)

            # -- Change to the import tab
            self.notebook.set_current_page(self.TAB_IMPORTING)

            # -- Get the source to import
            model, iter = self.origin_treeview.get_selection().get_selected()
            self.origin_label.set_text ("<b>%s</b>" % model.get_value(iter, 1))
            self.origin_label.set_use_markup(True)

            self.__import_pbar_id = gobject.timeout_add(250, self.__update_import_progressbar, self.progress_progressbar)

            origin = model.get_value (iter, 0)
            if origin == self.DEVICE_SIM:
                thread.start_new_thread(self.__import_contacts_from_sim, ( ))
                #gobject.idle_add(self.__import_contacts_from_sim)
            else:
                raise TypeError, "Invalid device source '%i' in AddressBook" % origin

        elif tab == self.TAB_FINISHED:
            # -- If we are in the finished tab, only close the dialog
            self.on_cancel_button_clicked (self, widget)

    # -- Call this after the imports is done
    def __import_contacts_post(self, msg):
        self.result_textview.get_buffer().set_text(msg)
        self.notebook.set_current_page(self.TAB_FINISHED)

        self.back_button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)
        self.next_button.set_sensitive(True)
        self.next_button.set_label(_("Close"))
        self.__import_event.set()
        self.__import_state = self.STATE_IDLE

        if self.__import_pbar_id is not None:
            gobject.source_remove(self.__import_pbar_id)
            self.__import_pbar_id = None

    def __update_import_progressbar(self, pbar):
        pbar.pulse()
        return True


class _ContactError(Exception):
    pass


class ContactEditor:

    def __init__(self, parent):
        self._theme_manager = tgcm.core.Theme.ThemeManager()

        gtk_builder_magic(self, \
                filename=os.path.join(tgcm.windows_dir, 'AddressBook', 'AddressBook_editor.ui'), \
                prefix='ced')

        self.contact_editor_dialog.set_transient_for(parent)
        self.icon_file = self._theme_manager.get_icon('icons', 'addressbook_taskbar.png')
        self.contact_editor_dialog.set_icon_from_file(self.icon_file)
        self.contact_editor_dialog.hide()
        self.ok_button.set_sensitive(False)

        if tgcm.country_support == 'uk':
            self.mobile_phone_label.set_markup("<b>%s</b>" % _("Phone number:"))

        self.contact_editor_dialog.connect("delete-event",self.on_dialog_delete)
        self.name_entry.connect("changed", self.__entry_changed, None)
        self.mobile_phone_entry.connect("changed", self.__entry_changed, None)
        self.email_entry.connect("changed", self.__entry_changed, None)

    def __is_min_entries_empty (self):
        result = False
        if self.name_entry.get_text() == "":
            result = True
        if self.mobile_phone_entry.get_text() == "":
            result = True

        return result

    def __entry_changed (self, widget, data):
        if self.__is_min_entries_empty():
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)

    def get_dict(self):
        d =  {}
        d["name"]  = self.name_entry.get_text().strip()
        d["phone"] = self.mobile_phone_entry.get_text().strip()
        d["email"] = self.email_entry.get_text().strip()
        d["copia_agenda_id"] = ""
        d["modification_stringdate"] = ""
        return d

    def __error_dialog(self, title, msg, parent, focus_widget=None):
        error_dialog(msg, parent=parent, title=title)
        if focus_widget is not None:
            focus_widget.set_can_focus(True)
            focus_widget.grab_focus()

    def run(self, contact=None, email=None, phone=None):
        if contact is None:
            self.contact_editor_dialog.set_title(_("New contact"))
            self.__clear_fields()
            if email is not None:
                self.email_entry.set_text(email)
            if phone is not None:
                self.mobile_phone_entry.set_text(phone)
        else:
            self.contact_editor_dialog.set_title(_("Modify contact"))
            self.__populate_fields(contact)

        # -- Set the focus for the name entry only once as the focus will be changed
        # -- depending on detected invalid entries
        self.name_entry.grab_focus()

        while True:
            response = self.contact_editor_dialog.run()
            if (response == gtk.RESPONSE_OK):
                try:
                    self.__validate_edited_contact()
                except _ContactError:
                    continue
                except Exception, err:
                    print "@FIXME: AddressBook, error validating contact, %s" % err

            break

        self.contact_editor_dialog.hide()
        return response

    def __validate_edited_contact(self):
        # -- Check for the name
        name = self.name_entry.get_text()
        self.validate_contact_name(name, self.contact_editor_dialog, focus_widget=self.name_entry)

        # -- Check for the phone number first
        phone = self.mobile_phone_entry.get_text()
        self.validate_contact_phone(phone, self.contact_editor_dialog, focus_widget=self.mobile_phone_entry)

        # -- Validate the email address
        email = self.email_entry.get_text()
        self.validate_contact_email(email, self.contact_editor_dialog, focus_widget=self.email_entry)

    def validate_contact_name(self, name, parent, focus_widget=None):
        name = name.strip()
        if len(name) == 0:
            self.__error_dialog(_("Invalid contact name"),
                                _("Invalid contact name. Please enter a valid name."),
                                parent,
                                focus_widget=focus_widget)
            raise _ContactError

    def validate_contact_phone(self, phone, parent, focus_widget=None):
        p = re.compile("^[0-9\+\#\*_]*$")
        phone = phone.strip()
        if (len(phone) == 0) or (p.match(phone) is None):
            self.__error_dialog(_("Invalid telephone number"),
                                _("Invalid telephone number. This field only allows numbers and characters +, # and *."),
                                parent,
                                focus_widget=focus_widget)
            raise _ContactError

    def validate_contact_email(self, email, parent, focus_widget=None):
        try:
            # -- Don't raise an exception by empty string as this is used for deleting the address
            if len(email.strip()) > 0:
                Validate.email(email)
        except ValidationError, err:
            self.__error_dialog(_("Invalid email address"),
                                _("Invalid email address. Please enter a valid address (e.g. test@test.com)."),
                                parent,
                                focus_widget=focus_widget)
            raise _ContactError

    def on_dialog_delete(self,widget,event=None):
        return True

    def __populate_fields(self,contact):
        self.name_entry.set_text(contact.name)

        if contact.phone == None:
            self.mobile_phone_entry.set_text("")
        else:
            self.mobile_phone_entry.set_text(contact.phone)

        if contact.email == None:
            self.email_entry.set_text("")
        else:
            self.email_entry.set_text(contact.email)

    def __clear_fields(self):
        self.name_entry.set_text("")
        self.mobile_phone_entry.set_text("")
        self.email_entry.set_text("")


class SearchContactDialog(gtk.Dialog):
    '''
    Shows a contact search dialog with filtering capabilities
    '''

    def __init__(self, parent=None, header_text=''):
        gtk.Dialog.__init__(self,
                title=_('Assign to contact'),
                parent=parent,
                flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        self._addr_manager = tgcm.core.Addressbook.AddressbookManager()
        self.resize(350, 400)
        self.set_border_width(4)

        filename = os.path.join(tgcm.windows_dir, \
                'AddressBook', 'AddressBook_search_contact.ui')
        gtk_builder_magic(self, \
                filename=filename, \
                prefix='addr')
        self.vbox.pack_start(self.search_contact_vbox, True, True, 0)

        # If there is no header text, hide its related label
        if len(header_text) > 0:
            self.info_label.set_text(header_text)
        else:
            self.info_label.hide()

        column = gtk.TreeViewColumn('name', gtk.CellRendererText(), text=1)
        column.set_expand(True)
        self.contact_treeview.append_column(column)

        # Support model filtering and ordering
        model = self._addr_manager.get_treeview_model()
        model = model.filter_new()
        model.set_visible_func(self.__search_contacts_filter_func)
        model = gtk.TreeModelSort(model)
        self.contact_treeview.set_model(model)

        # Connect some UI signals
        self.search_entry.connect('changed', self.__on_search_entry_changed_cb)
        self.search_entry.connect('icon-press', self.___search_entry_icon_press_cb)

        selection = self.contact_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect('changed', self.__on_selection_changed_cb)
        selection.select_path(0)

        self.contact_treeview.connect('row-activated', self.__on_row_activated_cb)

    def get_selected_contact(self):
        '''
        Returns the contact selected in the dialog
        '''
        contact_id = self.__get_selected_contact_id()
        return self._addr_manager.get_contact(contact_id)

    def __get_selected_contact_id(self, selection=None):
        if selection is None:
            selection = self.contact_treeview.get_selection()

        # Check if there is a selected row
        contact_id = None
        is_item_selected = selection.count_selected_rows() > 0
        if is_item_selected:
            (model, tree_iter) = selection.get_selected()
            contact_id = model.get_value(tree_iter, self._addr_manager.COLUMN_ID)

        return contact_id

    def __search_contacts_filter_func(self, model, text_iter, data=None):
        # This method returns True if the row must be showed, and False
        # otherwise
        name = model.get_value(text_iter, self._addr_manager.COLUMN_NAME)
        if (name is None) or (len(name) == 0):
            return False

        search_text = self.search_entry.get_text()
        if search_text.lower() in name.strip().lower():
            return True

        return False

    def __on_search_entry_changed_cb(self, widget, data=None):
        model = self.contact_treeview.get_model()
        if model is not None:
            model.get_model().refilter()

    def ___search_entry_icon_press_cb(self, widget, icon_pos, event):
        self.search_entry.set_text('')

    def __on_selection_changed_cb(self, selection, data=None):
        button = self.get_widget_for_response(gtk.RESPONSE_OK)
        contact_id = self.__get_selected_contact_id(selection)

        if contact_id is not None:
            button.set_sensitive(True)
        else:
            button.set_sensitive(False)

    def __on_row_activated_cb(self, treeview, path, column, data=None):
        contact_id = self.__get_selected_contact_id()
        if contact_id is not None:
            self.response(gtk.RESPONSE_OK)
