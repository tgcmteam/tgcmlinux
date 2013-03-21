#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Luis Galdos     <luisgaldos@gmail.com>
#
# Copyright (c) 2010, 2011, Telefonica Móviles España S.A.U.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import os
import array

from mobilemanager.mmdbus.service import method, signal
from mobilemanager.mmdbus.properties import prop
from mobilemanager.Logging import debug, info, warning, error

MM_URI = 'org.freedesktop.ModemManager.Modem.Gsm.Contacts'

# -- This info encoding info comes from the Windows world
SIM_CONTACTS_ENCODING = 'utf-16-be'

def _convert_utf16_to_ucs2(value):
    # -- Convert the string to a bytes array
    bytes = array.array('B', value.encode(SIM_CONTACTS_ENCODING))

    # -- Create a bytes chain
    return ''.join(map(lambda a: "%02X" % a, bytes.tolist()))

def _convert_ucs2_to_utf16(value):
    # -- First create the index: [0:2], [2:4], [4:6], ...
    index = map(lambda x: [2*x, 2*x + 2], range(len(value) / 2))

    # -- Convert the hex values to characters
    ret = ''.join(map(lambda a : chr(int(value[a[0]:a[1]], 16)), index))

    # -- Return the decoded string
    return ret.decode(SIM_CONTACTS_ENCODING)

class CodepageError(Exception):
    pass

class PhonebookError(Exception):
    pass

class ModemGsmContacts(object):

    PHONEBOOK_SIM = "SM"

    def __change_phonebook(self, mode):
        retval = self.io.com.send_query({ "type" : "simple",
                                          "cmd"  : 'AT+CPBS="%s"' % mode })
        if retval is not True:
            raise PhonebookError, "Couldn't change the phonebook to SIM card"

    # -- Read the current codepage from the SIM card
    def __current_codepage(self):
        regex  = '\+CSCS:\ "(?P<current>.*)"'
        r_vals = [ 'current' ]
        retval = self.io.com.send_query({ 'type'     : 'regex',
                                          'cmd'      : 'AT+CSCS?',
                                          'regex'    : regex,
                                          'r_values' : r_vals })
        if retval is None:
            raise CodepageError, "Couldn't read current codepaging"

        return retval['current']

    # -- Change to the passed codepage and return the last codepage! You can use this for restoring
    # -- the codepaging
    def __change_codepage(self, coding):

        # -- First check if the coding is supported by this modem
        if not self.cache.has_key("sim_supported_codings"):
            # -- The return value of this command looks like: '+CSCS: ("IRA","GSM","UCS2")'
            regex  = "\+CSCS:\ \((?P<codings>.*)\)"
            r_vals = [ 'codings' ]
            retval = self.io.com.send_query({ 'type'     : 'regex',
                                              'cmd'      : 'AT+CSCS=?',
                                              'regex'    : regex,
                                              'r_values' : r_vals })

            if retval is None:
                raise CodepageError, "Couldn't get the list of supported codepages"

            self.cache['sim_supported_codings'] = retval['codings'].replace('"','').split(',')

        if not (coding in self.cache['sim_supported_codings']):
            raise CodepageError, "Coding '%s' is not supported by the SIM card" % coding

        current = self.__current_codepage()
        if current == coding:
            return current

        # -- Now try to change the coding
        cmd = 'AT+CSCS="%s"' % coding
        ret = self.io.com.send_query({ 'type' : 'simple',
                                       'cmd'  : cmd })
        if ret is False:
            raise CodepageError, "Couldn't change the codepage to '%s'" % coding

        return current

    @method(MM_URI,
            in_signature = 'ss', out_signature = 'u',
            method_name = "Add")
    def mgcontacts_add(self, name, number):
        def function(task):
            item_type = None
            if number.startswith("+") :
                item_type = 145
            else:
                item_type = 129

            # -- Select the SIM phonebook and change to the UCS2 codepaging
            self.__change_phonebook(self.PHONEBOOK_SIM)
            current_codepage = self.__change_codepage("UCS2")

            # -- @XXX: allow only ASCII strings for the phone number, or?
            try:
                number2 = str(number)
            except Exception, err:
                raise Exception, "Converting phone number to string, %s" % err

            # -- Even the application defines the parameter as 'dbus.UTF8String' we receive it as 'dbus.String'
            try:
                name2   = _convert_utf16_to_ucs2(name)
            except Exception, err:
                raise Exception, "Converting name to UCS2, %s" % err
                
            cmd = 'AT+CPBW=,"%s",%i,"%s"' % (number2, item_type, name2)
            res = self.io.com.send_query({ "type" : "simple",
                                           "cmd"  : cmd,
                                           "task" : task })

            # -- Restore the initial codepage
            self.__change_codepage(current_codepage)
            return res

        # -- Use the SIM phonebook
        self.io.task_pool.exec_task(function, task_msg='Add Contact', timeout=10, timeout_waiting=10)

        if self.cache.has_key("addressbook") :
            self.cache.pop("addressbook")

        # -- Get the index of the new created entry
        conts = self.mgcontacts_list()
        for cont in conts:
            if (name == cont[1]) and (number == cont[2]):
                return cont[0]

        return 0

    @method(MM_URI,
            in_signature = 'u', out_signature = '',
            method_name = "Delete")
    def mgcontacts_delete(self, index):
        def function(task):
            res = self.io.com.send_query({"type": "simple",
                                          "cmd" : 'AT+CPBW=%s' % index,
                                          "task" : task,})
            if res == True:
                try:
                    self.cache["addressbook"].pop(index)
                except:
                    pass

        return self.io.task_pool.exec_task(function, task_msg='Delete Contact')

    @method(MM_URI,
            in_signature = 'u', out_signature = 'uss',
            method_name = "Get")
    def mgcontacts_get(self, index):
        list = self.mgcontacts_list()
        for c in list :
            if c[0] == index :
                return c
        return [0,'','']

    @method(MM_URI,
            in_signature = '', out_signature = 'a(uss)',
            method_name = "List")
    def mgcontacts_list(self):
        def function(task):

            # -- Select the SIM and change the codepage
            self.__change_phonebook(self.PHONEBOOK_SIM)
            current_codepage = self.__change_codepage("UCS2")

            ab_size = 0

            if not self.cache.has_key("ab_size") :
                cmd = 'AT+CPBR=?'
                regex = "\+CPBR:.*\((?P<l>\d+)-(?P<r>\d+)\)"
                r_values = ["l", "r"]

                res = self.io.com.send_query({"type"     : "regex",
                                              "cmd"      : cmd,
                                              "task"     : task,
                                              "regex"    : regex,
                                              "r_values" : r_values,})
                if res == None :
                    self.__change_codepage(current_codepage)
                    return []

                self.cache["ab_size"] = int(res["r"])

            ab_size = self.cache["ab_size"]

            cmd = 'AT+CPBR=1,%s' % ab_size
            regex = "\+CPBR:\ *(?P<id>\d+),\"(?P<number>.+)\",(?P<i_type>\d+),\"(?P<name>.+)\""
            r_values = ["id", "number", "i_type", "name"]

            res = self.io.com.send_query({"type"     : "mregex",
                                          'raw'      : True,
                                          "cmd"      : cmd,
                                          "task"     : task,
                                          "regex"    : regex,
                                          "r_values" : r_values })
            contacts = {}

            if res is None :
                retval = None
            else:
                for contact in res :
                    new_c = { 'i_type' : contact["i_type"],
                              'name'   : _convert_ucs2_to_utf16(contact["name"]),
                              'number' : contact["number"] }

                    contacts[int(contact["id"])] = new_c

                self.cache["addressbook"] = contacts

                ab_ret = []
                for index in self.cache["addressbook"] :
                    ab_ret.append([index,
                                   self.cache["addressbook"][index]["name"],
                                   self.cache["addressbook"][index]["number"]])

                retval = ab_ret

            # -- Restore the initial codepage
            self.__change_codepage(current_codepage)
            return retval

        if self.cache.has_key("addressbook") :
            ab_ret = []
            for index in self.cache["addressbook"] :
                ab_ret.append([index,
                               self.cache["addressbook"][index]["name"],
                               self.cache["addressbook"][index]["number"]])
            return ab_ret

        return self.io.task_pool.exec_task(function, task_msg='List Contacts', timeout=20)

    @method(MM_URI,
            in_signature = 's', out_signature = 'a(uss)',
            method_name = "Find")
    def mgcontacts_find(self, pattern):
        list = self.mgcontacts_list()
        ret = []
        for c in list :
            if pattern in c[1] or pattern in c[2] :
                ret.append(c)

        return ret

    @method(MM_URI,
            in_signature = '', out_signature = 'u',
            method_name = "GetCount")
    def mgcontacts_get_count(self):
        try:
            return len(self.mgcontacts_list())
        except:
            return 0
