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

import re
import gtk
import gobject

TEXVIEWCOMPLETER_SIZE = (350,100)

AGENDA = ("David Castellanos Serrano", \
        "Carlos Castellanos Serrano", \
        "María Juana Serrano Flores", \
        "Perico de los Palotes")


class TextViewExample():
    def __init__(self):
        self.window = gtk.Window()
        self.window.resize(400, 350)
        self.window.connect('destroy', self.__on_window_destroy)

        self.textview = gtk.TextView()
        self.window.add(self.textview)

        ContactsTextViewerCompleter(self.window, self.textview, AGENDA)

        self.window.show_all()

    def run(self):
        gtk.main()

    def __on_window_destroy(self, widget, data=None):
        gtk.main_quit()


class ContactsTextViewerCompleter(object):

    def __init__(self, parent, textview, completion):
        self.parent = parent
        self.textview = textview
        self.textbuffer = textview.get_buffer()
        self.completion = completion
        self.popup = None

        self.number_pattern = re.compile('\d+')

        tag = self.textbuffer.create_tag('contact')
        tag.set_property('foreground', 'blue')
        tag = self.textbuffer.create_tag('error')
        tag.set_property('foreground', 'red')

        self.textview.connect('key-press-event', self.__on_key_press_cb)
        self.textview.connect('move-cursor', self.__on_move_cursor_cb)
        self.textview.connect('button-release-event', self.__on_button_release_cb)
        self.textview.connect('focus-out-event', self.__on_focus_out_event_cb)
        self.textview.connect('visibility-notify-event', self.__on_visibility_notify_event_cb)
        self.textbuffer.connect('changed', self.__on_textbuffer_modified_cb)

    ## Callback functions

    def __on_key_press_cb(self, textview, event):
        if self.popup != None:
            if event.keyval == gtk.gdk.keyval_from_name('Up'):
                self.popup.prev()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name('Down'):
                self.popup.next()
                return True
            elif event.keyval == gtk.gdk.keyval_from_name('Return'):
                contact_name = self.popup.confirm()

                # Replace the word being edited with the selected in
                # the suggestions popup
                start_iter, end_iter = self.__get_word_at_input()[1:3]
                self.textbuffer.delete(start_iter, end_iter)
                self.textbuffer.insert(start_iter, contact_name + ', ')
                self.popup = None

                # Check and decorate TextBuffer contents
                self.__validate_input()

                return True
            elif event.keyval == gtk.gdk.keyval_from_name('Escape'):
                self.__hide_popup()
                return True
        return False

    def __on_move_cursor_cb(self, textview, step_size, count, extend_selection):
        self.__validate_input()

    def __on_button_release_cb(self, textview, event):
        self.__hide_popup()
        self.__validate_input()

    def __on_focus_out_event_cb(self, textview, event):
        self.__hide_popup()
        self.__validate_input(do_check_all=True)

    def __on_visibility_notify_event_cb(self, textview, event):
        self.__hide_popup()
        self.__validate_input(do_check_all=True)

    def __on_textbuffer_modified_cb(self, textbuffer):
        # Get currently word under the cursor
        word = self.__get_word_at_input()[0]
        word = word.lstrip()
#
        # Check if the word is part of an existing contact
        is_show_contacts = self.__is_word_in_contacts(word)

        if self.popup != None:
            # Suggestions popup IS being shown

            if is_show_contacts:
                # Just filter what appears on the popup
                self.popup.filter_contacts(word)
            else:
                # Destroy suggestions popup!
                self.popup.destroy()
                self.popup = None

                self.__validate_input()

        else:
            # Suggestions popup is NOT being shown
            if is_show_contacts:
                # Create a new suggestions popup as it is needed
                self.__show_popup(self.textbuffer)
                self.popup.filter_contacts(word)
            else:
                # Just check TextView contents
                self.__validate_input()

        return False

    ## Helper functions

    def __show_popup(self, textbuffer):
        if AGENDA:
            position = self.parent.window.get_root_origin()
            self.popup = self.CompleterPopup(self.textview, position, AGENDA)
            return True
        return False

    def __hide_popup(self):
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None

    def __validate_input(self, do_check_all=False):
        # Split TextView contents by commas
        start = self.textbuffer.get_start_iter()
        current = start.copy()
        elements = []

        condition = True
        while condition:
            if (current.get_char() == ',') or (current.is_end()):
                end = current.copy()

                start_mark = self.textbuffer.create_mark(None, start)
                start_mark.set_visible(True)
                end_mark = self.textbuffer.create_mark(None, end)
                end_mark.set_visible(True)
                elements.append((start_mark, end_mark))

                start = current.copy()
                start.forward_char()

            if current.is_end():
                condition = False
            current.forward_char()

        insert_mark = self.textbuffer.get_insert()

        for start_mark, end_mark in elements:
            insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
            start_iter = self.textbuffer.get_iter_at_mark(start_mark)
            end_iter = self.textbuffer.get_iter_at_mark(end_mark)

            # Do inspect the segment if the user has asked for it explicitly
            # or the cursor is not located in it
            is_cursor_in_segment = (insert_iter.compare(end_iter) == 0) or \
                    insert_iter.in_range(start_iter, end_iter)
            if do_check_all or not is_cursor_in_segment:
                if len(start_iter.get_tags()) == 0:
                    text = self.textbuffer.get_text(start_iter, end_iter)
                    text = text.lstrip()

                    if self.__is_valid_agenda_contact(text):
                        self.textbuffer.apply_tag_by_name('contact', start_iter, end_iter)

                    elif self.__is_valid_phonenumber(text):
                        self.textbuffer.apply_tag_by_name('contact', start_iter, end_iter)

                    else:
                        self.textbuffer.apply_tag_by_name('error', start_iter, end_iter)

            else:
                self.textbuffer.remove_all_tags(start_iter, end_iter)

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

    def __is_word_in_contacts(self, word):
        if len(word) > 0:
            for contact in AGENDA:
                if word.lower() in contact.lower():
                    return True
        return False

    def __is_valid_agenda_contact(self, text):
        return text in AGENDA

    def __is_valid_phonenumber(self, text):
        return self.number_pattern.match(text) is not None


    class CompleterPopup(object):

        def __init__(self, textview, position, completion, size=TEXVIEWCOMPLETER_SIZE):
            object.__init__(self)
            self.textview = textview
            self.textbuffer = textview.get_buffer()
            self.completion = completion
            self.position = position

            self.popup = gtk.Window(gtk.WINDOW_POPUP)
            parent = textview.get_toplevel()
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
                    rectangle.x + rectangle.width + 0,
                    rectangle.y + rectangle.height + 25)# + 70)
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


if __name__ == '__main__':
    example = TextViewExample()
    example.run()
