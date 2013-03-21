#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2010-2011, Telefonica Móviles España S.A.U.
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
import time
import json

import tgcm

class SMSStorage:

    # -- Emitted when a new message has been received
    SPOOL_RECEIVED = 0
    SPOOL_SENT     = 1
    SPOOL_DRAFT    = 2
    # -- Emitted when an already received email has changed its state
    SPOOL_RECEIVED_READ    = 3
    SPOOL_RECEIVED_DELETED = 4

    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.json_file = os.path.join(tgcm.config_dir, "sms_storage.json")

        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as f:
                self.smsdb = json.load(f)
        else:
            self.smsdb = { "draft" : {}, "received" : {},  "sent" : {}, "to_send": {} }
            self.__save()

    #Delete sms methods (tgcm1.0)
    ##########################################
    def sms_delete_draft (self, index):
        ret = self.__delete("draft", index)
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_DRAFT)
        return ret

    def sms_delete_received (self, index):
        ret = self.__delete("received", index)
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_RECEIVED_DELETED)
        return ret

    def sms_delete_sent (self, index):
        ret = self.__delete("sent", index)
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_SENT)
        return ret

    def sms_delete_to_send (self, index):
        ret = self.__delete("to_send", index)
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_SENT)
        return ret


    #Get sms methods (tgcm1.0)
    ##########################################
    def sms_get_draft (self, index):
        sms = self.__get("draft", index)
        ret = [index,
               sms["read"],
               sms["number"],
               sms["date"],
               sms["text"]]

        return ret

    def sms_get_received (self, index):
        sms = self.__get("received", index)
        number = sms["number"]
        if sms.has_key("notification") and sms["notification"] == True:
            number = "FLASH:" + sms["number"]

        ret = [index,
               sms["read"],
               number,
               sms["date"],
               sms["text"]]

        return ret

    def sms_get_sent (self, index):
        sms = self.__get("sent", index)
        ret = [index,
               sms["read"],
               sms["number"],
               sms["date"],
               sms["text"],
               sms["error"]]

        return ret

    def sms_get_to_send (self, index):
        sms = self.__get("to_send", index)
        ret = [index,
               sms["read"],
               sms["number"],
               sms["date"],
               sms["text"]]

        return ret

    #List sms methods (tgcm1.0)
    ##########################################
    def sms_list_drafts (self):
        list = self.__list("draft")
        ret = []
        for i in list.keys():
            ret.append([i,
                        list[i]["read"],
                        str(list[i]["number"]),
                        str(list[i]["date"])])
        return ret

    def sms_list_received (self):
        list = self.__list("received")
        ret = []
        for i in list.keys():
            ret.append([i,
                        list[i]["read"],
                        str(list[i]["number"]),
                        str(list[i]["date"])])
        return ret

    def sms_last_received(self):
        try:
            received_all = self.sms_list_received()
            index = received_all[-1][0]
            return self.sms_get_received(index)
        except:
            return None

    def sms_list_sent (self):
        list = self.__list("sent")
        ret = []
        for i in list.keys():
            ret.append([i,
                        list[i]["read"],
                        str(list[i]["number"]),
                        str(list[i]["date"]),
                        list[i]["error"]])
        return ret

    def sms_list_to_send (self):
        list = self.__list("to_send")
        ret = []
        for i in list.keys():
            ret.append([i,
                        list[i]["read"],
                        str(list[i]["number"]),
                        str(list[i]["date"])])
        return ret

    #sms_mark_received_readed
    def sms_mark_received_as_read (self, index):
        ret = self.__mark_as_read("received", index)
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_RECEIVED_READ)
        return ret

    #sms_set_draft
    def sms_set_draft (self, number, text):
        ret = self.__set("draft",
                         {"text" : text,
                          "number" : number,
                          "date" : time.strftime("%y/%m/%d %H:%M:%S",
                                                 time.localtime()),
                          "read" : False
                          }
                         )
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_DRAFT)
        return ret

    def sms_send_offline (self, number, text):
        ret = self.__set("to_send",
                         {"text" : text,
                          "number" : number,
                          "date" : time.strftime("%y/%m/%d %H:%M:%S",
                                                 time.localtime()),
                          "read" : False
                          }
                         )
        # -- Emit the SENT signal as the list view with the pending messages needs an update
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_SENT)
        return ret

    def save_received_sms(self, sms):
        self.__set("received", sms)
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_RECEIVED)

    def save_sent_sms(self, number, text, error=False):
        ret = self.__set("sent",
                         {"text"   : text,
                          "number" : number,
                          "date"   : time.strftime("%y/%m/%d %H:%M:%S", time.localtime()),
                          "read"   : True,
                          "error"  : error
                          }
                         )
        self.device_manager.emit('active-dev-sms-spool-changed', self.SPOOL_SENT)
        return ret


    def __save(self):
        with open(self.json_file, "w") as f:
            json.dump(self.smsdb, f, indent=4)

    def __get(self, pool_id, index):
        if pool_id in ["draft", "received", "sent", "to_send"] :
            try:
                return self.smsdb[pool_id][str(index)]
            except:
                pass

        return {}

    def __set(self, pool_id, value):
        if pool_id in ["draft", "received", "sent", "to_send"] :
            try:
                index = "0"
                try :
                    num_list = []
                    for i in self.smsdb[pool_id].keys() :
                        num_list.append(int(i))
                    num_list.sort()

                    index = str(num_list[-1] + 1)
                except:
                    pass

                self.smsdb[pool_id][index] = value
                self.__save()
                return True
            except:
                return False

        return False

    def __update(self, pool_id, index, value):
        if pool_id in ["draft", "received", "sent", "to_send"] :
            try:
                self.smsdb[pool_id][str(index)] = value
                self.__save()
                return True
            except:
                return False

        return False

    def __delete(self, pool_id, index):
        if pool_id in ["draft", "received", "sent", "to_send"] :
            try:
                self.smsdb[pool_id].pop(str(index))
                self.__save()
                return True
            except:
                return False

        return False

    def __list(self, pool_id):
        if pool_id in ["draft", "received", "sent", "to_send"] :
            try:
                num_list = []
                for i in self.smsdb[pool_id] :
                    num_list.append(int(i))
                num_list.sort()
                ret = {}
                for i in num_list:
                    ret[i] = self.smsdb[pool_id][str(i)]

                return ret
            except:
                return {}

        return {}

    def __mark_as_unread(self, pool_id, index):
        if pool_id in ["draft", "received", "sent", "to_send"] :
            try:
                self.smsdb[pool_id][str(index)]["read"] = False
                self.__save()
                return True
            except:
                return False

        return False

    def __mark_as_read(self, pool_id, index):
        if pool_id in ["draft", "received", "sent", "to_send"] :
            try:
                self.smsdb[pool_id][str(index)]["read"] = True
                self.__save()
                return True
            except:
                return False

        return False

