#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2010, Telefonica Móviles España S.A.U.
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
import gobject
import re
import time

from mobilemanager.mmdbus.service import method, signal
from mobilemanager.sms.pdu import PDU, PDU_REFERENCE_NONE
from mobilemanager.Logging import debug, info, warning, error

from dbus.exceptions import DBusException

MM_URI='org.freedesktop.ModemManager.Modem.Gsm.SMS'

SMS_STATUS_UNREAD = 0
SMS_STATUS_READ   = 1
SMS_STATUS_ALL    = 4

PDU_TRANSFER_TIMEOUT = 15
PDU_TRANSFER_DELAY   = 10 # -- This is for the worst case as with five seconds the transfer of some messages fail

class ModemGsmSMS(object):
    @method(MM_URI, 
            in_signature = 'u', out_signature = '',
            method_name="Delete")
    def mgsms_delete(self, index):
        def function(task) :
            cmd = 'AT+CMGD=%s' % index
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : cmd, 
                                    "task" : task})

        task_msg = "Delete SMS (%s)" % (index)
        self.io.task_pool.exec_task(function, task_msg=task_msg)

    @method(MM_URI, 
            in_signature = 'u', out_signature = 'a{sv}',
            method_name="Get")
    def mgsms_get(self, index):
        msgs = self.mgsms_get_sms_with_status(SMS_STATUS_READ)
        for m in msgs:
            if m["index"] == index:
                return m
        
        return {}

#     @method(MM_URI, 
#             in_signature = '', out_signature = 'u',
#             method_name="GetFormat")
#     def mgsms_get_format(self):
#         pass

    @method(MM_URI, 
            in_signature = '', out_signature = 's',
            method_name="GetSmsc")
    def mgsms_get_smsc(self):
        return '' if not "smsc" in self.cache else self.cache["smsc"]

    @method(MM_URI, 
            in_signature = '', out_signature = 'aa{sv}',
            method_name="List")
    def mgsms_list(self):
        return self.mgsms_get_sms_with_status(SMS_STATUS_READ)

    @method(MM_URI,
            in_signature = 'a{sv}', out_signature = 'au',
            method_name="Send")
    def mgsms_send(self, properties):
        def function(task):
            enabled_continuity = False
            raise_error        = None

            # -- Try to set the continuity of SMS relay protocol link as we have concatenated messages
            if len(pdu_list) > 1:
                res = self.io.com.send_query({"type" : "simple", "cmd"  : 'AT+CMMS=2', "task" : task})
                if res is True:
                    enabled_continuity = True

            # -- Set PDU message mode
            cmd = 'AT+CMGF=0'
            self.io.com.send_query({ "type" : "simple", "cmd"  : cmd, "task" : task })

            response = [ ]
            for pdu in pdu_list:
                try:
                    r = self.mgsms_send_pdu(pdu, task, timeout=PDU_TRANSFER_TIMEOUT)
                except Exception, err:
                    raise_error = Exception(err)
                    break

                # -- By concatenated messages abort after the first failure
                if r is not None:
                    response.append(r)
                else:
                    raise_error = ValueError("PDU transfer failed, aborting message transfer")
                    break

                # -- Wait before sending the next PDU if the continuity mode was not enabled
                if (len(pdu_list) > 1) and (enabled_continuity is False):
                    time.sleep(PDU_TRANSFER_DELAY)

            # -- Reset to the factory default
            if (len(pdu_list) > 1) and (enabled_continuity is True):
                self.io.com.send_query({"type" : "simple", "cmd"  : 'AT+CMMS=0', "task" : task})

            if raise_error is not None:
                raise raise_error

            return response

        text = properties["text"]
        if len(text) > 10 :
            text = text[:10] + "..."

        # -- Calculate the complete timeout depending on the number of messages to send
        pdu_list = self.mgsms_get_pdus(properties)
        timeout  = len(pdu_list) * (PDU_TRANSFER_TIMEOUT)

        task_msg = "Send Sms to %s -> '%s' " % (properties["number"], text)
        return self.io.task_pool.exec_task(function, task_msg=task_msg, timeout = timeout)

    @method(MM_URI, 
            in_signature = 's', out_signature = '',
            method_name="SetSmsc")
    def mgsms_set_smsc(self, smsc):
        self.cache["smsc"] = smsc

    @signal(MM_URI, 
            signature = 'ub',
            signal_name = 'Completed')
    def mgsms_completed_signal(self, id, status):
        pass

    @signal(MM_URI, 
            signature = 'ub',
            signal_name = 'SmsReceived')
    def mgsms_sms_received_signal(self, id, status):
        pass
    
    def mgsms_get_pdus(self, properties):
        p = PDU()
        
        number = None if not properties.has_key("number") else properties["number"]
        text = None if not properties.has_key("text") else properties["text"]
        smsc = "" if not properties.has_key("smsc") else properties["smsc"]
        validity = "" if not properties.has_key("validity") else properties["validity"]
        sms_class = "" if not properties.has_key("class") else properties["class"]
        status_request = False if not properties.has_key("status_request") else properties["status_request"]

        if number == None or text == None :
            return []

        return p.encode_pdu(number, text, csca=smsc, request_status=status_request)

    def mgsms_send_pdu(self, sms, task, timeout=None):
        ''' Called from mgsmsm_send.task() '''

        cmd = 'AT+CMGS=%s' % sms[0]
        regex = '\+CMGS:\ +(?P<index>\d*)'
        r_values = ["index"]
        snd_part = sms[1] + chr(26)

        res = self.io.com.send_query({"type"         : "mregex",
                                      "cmd"          : cmd,
                                      "task"         : task,
                                      "regex"        : regex,
                                      "r_values"     : r_values,
                                      "snd_part"     : snd_part,
                                      'read_timeout' : timeout,
                                      'debug'        : False })

        # -- The return value of the 'mregex' is an empty list by ERROR
        retval = None
        if type(res) == type([ ]):
            try:
                retval = int(res[0]["index"])
            except:
                retval = None

        return retval

    def mgsms_get_sms_with_status(self, status):
        def function(task) :
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : "AT+CMGF=0",
                                    "task" : task})
            
            raw_res = self.io.com.send_query({"cmd" : 'AT+CMGL=%s' % status,
                                              "task" : task})

            response = []
            p = PDU()

            if raw_res[2] == "OK" :
                for i in range(0, len(raw_res[1]), 2) :
                    if raw_res[1][i].startswith("+CMGL:") :
                        pattern = re.compile("\+CMGL:\ +(?P<index>\d*),(?P<status>\d*),")
                        matched_res = pattern.match(raw_res[1][i])
                        try:
                            sender, datestr, msg , csca, ref, cnt, seq, fmt, flash_sms = p.decode_pdu(raw_res[1][i+1])
                            msg = { "number" : sender,
                                    "text" : msg,
                                    "smsc" : csca,
                                    "date" : datestr,
                                    "reference" : int(ref),
                                    "concat_total" : int(cnt),
                                    "concat_number" : int(seq),
                                    "index": int(matched_res.group("index")),
                                    "status" : int(matched_res.group("status")),
                                    "notification" : flash_sms
                                    }
                            
                            if 'application/vnd.wap.mms-message' in  msg["text"] :
                                continue

                            if msg["concat_total"] == 0:
                                msg["completed"] = True
                            else:
                                msg["completed"] = False

                            response.append(msg)
                        except:
                            pass

            #Check completed concatenated msgs
            refs = {}

            for m in response:
                if m["concat_total"] > 0:
                    if not refs.has_key(m["reference"]):
                        refs[m["reference"]] = []

                    refs[m["reference"]].append(m)

            for r in refs.keys():
                if len(refs[r]) == refs[r][0]["concat_total"] :
                    for m in response:
                        if m["reference"] == r :
                            m["completed"] = True

            return response

        if status == SMS_STATUS_UNREAD :
            task_msg = "Checking SMS with status UNREAD"
        elif status == SMS_STATUS_ALL :
            task_msg = "Checking SMS with status ALL"
        elif status == SMS_STATUS_READ :
            task_msg = "Checking SMS with status READ"
        else:
            task_msg = "Checking SMS with status UNKNOWN"

        timeout = 4
        return self.io.task_pool.exec_task(function, task_msg=task_msg, timeout=timeout)

    def __mgsms_check_new_sms(self):
        new_msg = self.mgsms_get_sms_with_status(SMS_STATUS_UNREAD)
        if len(new_msg) == 0:
            return

        # -- Cache the messages for avoding too much read operations
        if not self.cache.has_key("all_read_messages"):
            self.cache["all_read_messages"] = self.mgsms_get_sms_with_status(SMS_STATUS_ALL)
        else:
            self.cache["all_read_messages"] += new_msg

        # -- Only for debugging
        #for msg in self.cache['all_read_messages']:
        #    print "%3s - %3s - %3s" % (msg['index'], msg['concat_total'], msg['reference'])

        # -- Filter messages with a reference number (concatenated messages)
        concatenated = filter(lambda  msg: msg['reference'] != PDU_REFERENCE_NONE, self.cache["all_read_messages"])
        references   = set(map(lambda msg: msg['reference'], concatenated))
        for ref in references:
            # -- Get all the messages with the same reference number
            msgs = filter(lambda msg: msg['reference'] == ref, concatenated)
            msg  = msgs[0]
            if len(msgs) == msg['concat_total']:
                self.mgsms_completed_signal(msg["index"], True)
                for msg in msgs: self.cache["all_read_messages"].remove(msg)

        # -- Filter messages without reference number (simple messages)
        simples = filter(lambda  msg: msg['reference'] == PDU_REFERENCE_NONE, self.cache["all_read_messages"])
        for msg in simples:
            self.mgsms_completed_signal(msg["index"], True)
            self.cache["all_read_messages"].remove(msg)

    def mgsms_init_st_m_watchers(self):
        self.st_m.register_watcher(range(0,60,10), self.mgsms_init_sms)
        self.st_m.register_watcher(range(0,60,10), self.mgsms_check_for_new_smss_watcher)
        pass

    def mgsms_init_sms(self):
        if "sms_initializated" not in self.cache :
            self.cache["sms_initializated"] = False

        def function(task):
            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : 'AT+CNMI=0,0,0,0,0',
                                    "task" : task})

            self.io.com.send_query({"type" : "simple",
                                    "cmd"  : 'AT+CPMS="SM","SM","SM"',
                                    "task" : task })

        if self.mgc_get_unlock_status() == '' and self.cache["sms_initializated"] == False :
            task_msg = "Init SMS system"
            self.io.task_pool.exec_task(function, task_msg=task_msg)
            self.cache["sms_initializated"] = True

    def mgsms_check_for_new_smss_watcher(self):
        if self.mgc_get_unlock_status() == '':
            self.__mgsms_check_new_sms()
