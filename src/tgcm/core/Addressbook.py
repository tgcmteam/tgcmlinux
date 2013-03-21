#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
#           Luis Galdos <luisgaldos@gmail.com>
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
import gobject
import gtk
import re
import sqlobject

import tgcm
import Config
import FreeDesktop
import Singleton

import MobileManager

from MobileManager.MobileManagerDbus import MOBILE_MANAGER_DEVICE_ADDRESSBOOK_INTERFACE_URI


class AddressbookManager(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    COLUMN_ID      = 0
    COLUMN_NAME    = 1
    COLUMN_PHONE   = 2
    COLUMN_EMAIL   = 3
    COLUMN_TOOLTIP = 4

    __gsignals__ = {
        'addressbook-model-updated' : ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( )) ,
    }

    class _Contact():
        def __init__(self, index, name, number):
            self.__index  = index
            self.__name   = name
            self.__number = number
            self.__number_normalized = None

        def index(self):
            return self.__index

        def name(self):
            return self.__name

        def number(self, normalized=False):
            if normalized is False:
                return self.__number
            else:
                if self.__number_normalized is None:
                    self.__number_normalized = AddressbookManager.normalize_number(self.__number)
                return self.__number_normalized

    def __init__ (self):
        gobject.GObject.__init__(self)

        self.importing = False
        self.conf      = Config.Config()
        self.addressbookmanager_sqlite = AddressbookManagerSQLite()
        self.__treeview_model = self.__create_model ()

        self.update_model()

    def get_treeview_model (self):
        return self.__treeview_model

    def get_column_number_name(self):
        return self.COLUMN_NAME

    def get_column_number_phone(self):
        return self.COLUMN_PHONE

    def get_column_number_email(self):
        return self.COLUMN_EMAIL

    def get_column_number_tooltip(self):
        return self.COLUMN_TOOLTIP

    def update_model (self):
        self.__treeview_model.clear()

        for contact in self.get_all_contacts():

            tooltip = "%s\n%s" % (contact.name, contact.phone)
            if contact.email is not None:
                tooltip += "\n%s" % (contact.email)
            self.__treeview_model.append([ contact.id,
                                           contact.name,
                                           contact.phone,
                                           contact.email,
                                           tooltip ])

        # -- Emit the signal for the listeners
        self.emit('addressbook-model-updated')

    def get_all_contacts (self):
        return self.addressbookmanager_sqlite.get_all_contacts()

    def get_contact (self, id):
        return self.addressbookmanager_sqlite.get_contact (id)

    def get_new_contact (self, name, phone, email, notify=True):
        contact = self.addressbookmanager_sqlite.get_new_contact(name, phone, email)
        if notify:
            self.update_model()
        return contact

    def get_number_from_name (self, name):
        return self.addressbookmanager_sqlite.get_number_from_name (name)

    def get_name_from_number (self, number):
        return self.addressbookmanager_sqlite.get_name_from_number (number)

    def import_from_csv (self, filename):
        fin = open (dialog.get_filename(), "rb")

        for line in fin:
            import_contact = line.split(',')
            d = {}
            d["name"] = import_contact[0]
            d["phone"] = import_contact[1]
            d["email"] = import_contact[2].replace('\n', '')
            new_mdcontact (self.conf, d)

        fin.close()

        self.update_model()

    def import_from_device_SIM (self, cancel):
        device_manager = FreeDesktop.DeviceManager()
        device_dialer = FreeDesktop.DeviceDialer()
        dev = device_manager.get_main_device()

        if dev != None:
            if dev.has_capability (MOBILE_MANAGER_DEVICE_ADDRESSBOOK_INTERFACE_URI):
                if device_dialer.status() == MobileManager.PPP_STATUS_DISCONNECTED or dev.is_multiport_device():
                    try:
                        _sim_contacts = dev.addressbook_list_contacts()
                        contacts = self.get_all_contacts()
                    except Exception, err:
                        # -- WTF: we can only return a negative value and not the error message
                        return -1

                    #remove duplicated phones from the SIM array
                    numbers = []
                    sim_contacts = [ ]
                    for contact in _sim_contacts:
                        numbers.append(contact[2])
                        sim_contacts.append(self._Contact(contact[0], contact[1], contact[2]))

                    contact_numbers = [ ]
                    for contact in contacts:
                        contact_numbers.append(self.normalize_number(contact.phone))

                    self.count_sim_contacts = len(sim_contacts)
                    self.count_progress = 0
                    imported = 0

                    for sim_contact in sim_contacts:
                        duplicated = False

                        if cancel.is_set():
                            break

                        for number in contact_numbers:
                            if self.__is_duplicated (sim_contact.number(normalized=True), (number, )):
                                duplicated = True
                                break

                        if not duplicated:
                            name  = sim_contact.name().encode('utf-8')
                            phone = sim_contact.number()
                            email = ""
                            self.get_new_contact(name, phone, email, notify=False)
                            imported += 1

                        self.count_progress += 1

                    gobject.idle_add(self.update_model)
                    return imported
                else:
                    return -1
            else:
                return -1
        else:
            return -1

    def get_importing_state (self):
        if self.importing == True:
            progress = self._sync.get_progress()
            state = self._sync.get_state()
            running = self._sync.running()

            state_string = ""

            if running:
                if state == self._sync.State_Connecting:
                    state_string = _("Connecting...")
                elif state == self._sync.State_InitSync:
                    state_string = _("Starting to import...")
                elif state == self._sync.State_Downloading:
                    state_string = _("Downloading...")
                elif state == self._sync.State_Acknowledge:
                    state_string = _("Confirming data...")
                elif state == self._sync.State_Cancelled:
                    state_string = _("Cancelling.")
                elif state == self._sync.State_Finished:
                    state_string = _("Import correct.")
                elif state == self._sync.State_FinishedWithError:
                    state_string = _("An error has occurred when importing.")
                elif state == self._sync.State_FinishedWithPartialDownload:
                    state_string = _("All the data has not been imported.")
            else:
                error = self._sync.get_error()
                if error == self._sync.Error_NoDB:
                    state_string = _("The address book can't be opened.")
                elif error == self._sync.Error_CouldNotConnect:
                    state_string = _("It can't connect.")
                elif error == self._sync.Error_InvalidReply:
                    state_string = _("An incorrect answer has been entered.")
                elif error == self._sync.Error_BadAuth:
                    state_string = _("The user/password is incorrect.")
                elif error == self._sync.Error_Unknown:
                    state_string = _("Unknown error.")

            return progress, state_string, running
        return None, None, None

    def cancel_import (self):
        if self._sync != None:
            self._sync.request_shutdown()

    # -- The numbers must be already normalized!
    def __is_duplicated (self, number, list):
        if len(list) == 0:
            return False

        for list_number in list:
            if number == list_number:
                return True

        return False

    def __create_model (self):
        model = gtk.ListStore( \
            gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        return model

    def normalize_number (number):
        if number is None or number == "":
            return ""

        conf = Config.Config ()

        match = conf.get_phone_match()
        format = conf.get_phone_format()

        regex_result = re.search (match, number)
        if regex_result != None:
            try:
                normalized_number = ''
                for i in format:
                    normalized_number = normalized_number + regex_result.group(i)

                return normalized_number
            except:
                return number
        else:
            return number
    normalize_number = staticmethod(normalize_number)


class AddressbookManagerSQLite (gobject.GObject):
    def __init__ (self):
        gobject.GObject.__init__(self)

        self.db_path = tgcm.sqlite_contacts_file
        conf_dir = os.path.dirname(self.db_path)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)

        connection_string = 'sqlite:' + self.db_path
        connection = sqlobject.connectionForURI(connection_string)
        sqlobject.sqlhub.processConnection = connection

        # creo tablas
        AddressbookContact_sqlite.createTable(ifNotExists=True)

    def get_all_contacts (self, with_mail=False):
        contacts = []

        if with_mail == True:
            result = AddressbookContact_sqlite.select(AddressbookContact_sqlite.q.email != "")
        else:
            result = AddressbookContact_sqlite.select()

        for contact in result:
            contacts.append (contact)
        return contacts

    def get_contact (self, id):
        return AddressbookContact_sqlite.get(id)

    def get_new_contact (self, name, phone, email):
        d = {}
        d["name"] = name
        d["phone"] = phone
        d["email"] = email
        d["copia_agenda_id"] = ""
        d["modification_stringdate"] = ""

        contact = AddressbookContact_sqlite (**d)

        return contact

    def get_number_from_name (self, name):
        name = str(name)
        selection = AddressbookContact_sqlite.select(AddressbookContact_sqlite.q.name == name)
        if selection and selection.count() > 0:
            return selection[0].phone
        else:
            return None

    def get_name_from_number (self, number):
        number = AddressbookManager.normalize_number (str(number))
        selection = AddressbookContact_sqlite.select()
        if selection and selection.count() > 0:
            for contact in selection:
                normalized_number = AddressbookManager.normalize_number (contact.phone)
                if normalized_number == number:
                    return contact.name

        return None

    def search_people(self):
        pass


class AddressbookContact_sqlite(sqlobject.SQLObject):
    class sqlmeta:
        table = "contacts"

    name  = sqlobject.StringCol()
    phone = sqlobject.StringCol()
    email = sqlobject.StringCol()
    copia_agenda_id = sqlobject.StringCol()
    modification_stringdate = sqlobject.StringCol()

    def save (self):
        _addressbook_manager = AddressbookManager()
        _addressbook_manager.update_model()

    def destroySelf (self, notify=True):
        sqlobject.SQLObject.destroySelf( self )

        if notify:
            _addressbook_manager = AddressbookManager()
            _addressbook_manager.update_model()
