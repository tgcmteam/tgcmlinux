#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#
# Copyright (c) 2003-2010, Telefonica Móviles España S.A.U.
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
import sys
import gobject
import time
import dbus
import dbus.glib
import gtk
import tgcm

import MobileManager

from MobileManager.MobileStatus import *
from MobileManager.MobileManagerDbus import MOBILE_MANAGER_CONTROLLER_PATH,MOBILE_MANAGER_CONTROLLER_URI,MOBILE_MANAGER_CONTROLLER_INTERFACE_URI,MOBILE_MANAGER_DEVICE_PATH,MOBILE_MANAGER_DEVICE_URI,MOBILE_MANAGER_DEVICE_ADDRESSBOOK_INTERFACE_URI,MOBILE_MANAGER_DEVICE_INFO_INTERFACE_URI,MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI,MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI,MOBILE_MANAGER_DEVICE_SMS_INTERFACE_URI,MOBILE_MANAGER_DEVICE_XZONE_INTERFACE_URI, MOBILE_MANAGER_DIALER_INTERFACE_URI

from DeviceManager import DeviceManager
from DeviceDialer import DeviceDialer

from DeviceExceptions import *
from DeviceDecorators import *

class Device(gobject.GObject) :
    def __init__ (self, opath) :
        gobject.GObject.__init__(self)
        self.path = opath
        self.mcontroller = DeviceManager()

        self.device_dialer = DeviceDialer()
        self.dbus = self.mcontroller.dbus

        self.conf = tgcm.core.Config.Config()
        self.domain = MobileManager.CARD_DOMAIN_CS_PS
        self.mode = MobileManager.CARD_TECH_SELECTION_AUTO

        domain = self.conf.get_last_domain()
        mode = self.conf.get_last_device_mode()

        if domain == "cs_ps" :
            self.domain = MobileManager.CARD_DOMAIN_CS_PS
        elif domain == "cs" :
            self.domain = MobileManager.CARD_DOMAIN_CS
        elif domain == "ps" :
            self.domain = MobileManager.CARD_DOMAIN_PS

        if mode == "auto" :
            self.mode = MobileManager.CARD_TECH_SELECTION_AUTO
        elif mode == "gsm" :
            self.mode = MobileManager.CARD_TECH_SELECTION_GPRS
        elif mode == "wcdma" :
            self.mode = MobileManager.CARD_TECH_SELECTION_UMTS
        elif mode == "gsm_first" :
            self.mode = MobileManager.CARD_TECH_SELECTION_GRPS_PREFERED
        elif mode == "wcdma_first" :
            self.mode = MobileManager.CARD_TECH_SELECTION_UMTS_PREFERED

        self.__addressbook = self.__get_device_addressbook_from_path(self.path)
        self.__info = self.__get_device_info_from_path(self.path)
        self.__auth = self.__get_device_auth_from_path(self.path)
        self.__state = self.__get_device_state_from_path(self.path)
        self.__sms = self.__get_device_sms_from_path(self.path)

        self.cache = {}

        self.mcontroller.connect("dev-roaming-status-changed", self.__DevRoamingActStatusChanged_cb)
        self.mcontroller.connect("dev-card-status-changed", self.__DevCardStatusChanged_cb)


    def __get_device_addressbook_from_path(self, dev_path):
        dev = self.dbus.get_object(MOBILE_MANAGER_DEVICE_URI,
                                   dev_path)
        dev_addressbook = dbus.Interface(dev, MOBILE_MANAGER_DEVICE_ADDRESSBOOK_INTERFACE_URI)
        return dev_addressbook

    def __get_device_info_from_path(self, dev_path):
        dev = self.dbus.get_object(MOBILE_MANAGER_DEVICE_URI,
                                   dev_path)
        dev_info = dbus.Interface(dev, MOBILE_MANAGER_DEVICE_INFO_INTERFACE_URI)
        return dev_info

    def __get_device_auth_from_path(self, dev_path):
        dev = self.dbus.get_object(MOBILE_MANAGER_DEVICE_URI,
                                   dev_path)
        dev_auth = dbus.Interface(dev, MOBILE_MANAGER_DEVICE_AUTH_INTERFACE_URI)
        return dev_auth

    def __get_device_state_from_path(self, dev_path):
        dev = self.dbus.get_object(MOBILE_MANAGER_DEVICE_URI,
                                   dev_path)
        dev_state = dbus.Interface(dev, MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI)
        return dev_state

    def __get_device_sms_from_path(self, dev_path):
        dev = self.dbus.get_object(MOBILE_MANAGER_DEVICE_URI,
                                   dev_path)
        dev_sms = dbus.Interface(dev, MOBILE_MANAGER_DEVICE_SMS_INTERFACE_URI)
        return dev_sms

    # ADDRESSBOOK INTERFACE

    @addressbook_interface_required
    @check_device
    @mobile_manager
    def addressbook_list_contacts(self):
        return self.__addressbook.ListContacts()

    # INFO INTERFACE
    @mobile_manager
    def get_capabilities(self):
        if self.cache.has_key("capabilities") :
            return self.cache["capabilities"]
        else:
            ret = self.__info.GetCapabilities()
            self.cache["capabilities"] = ret
            return ret

    @mobile_manager
    def has_capability(self, capability):
        if self.cache.has_key("capabilities") :
            if capability in self.cache["capabilities"]:
                return True
            else:
                return False
        else:
            ret = self.__info.GetCapabilities()
            self.cache["capabilities"] = ret

        return self.__info.HasCapability(capability)

    @mobile_manager
    def get_velocity(self):
        return self.__info.GetVelocity()

    @mobile_manager
    def set_velocity(self, value):
        self.__info.SetVelocity(value)

    @mobile_manager
    def get_prettyname(self):
        if self.cache.has_key("prettyname") :
            return self.cache["prettyname"]
        else:
            ret = self.__info.GetPrettyName()
            self.cache["prettyname"] = ret
            return ret

    @mobile_manager
    def get_MSISDN (self):
        if self.cache.has_key("MSDISDN") :
            return self.cache["MSDISDN"]
        else:
            ret = self.__info.GetMSISDN()
            if ret != "":
                self.cache["MSDISDN"] = ret
            return ret

    @mobile_manager
    def get_device_icon(self):
        if self.cache.has_key("icon") :
            return self.cache["icon"]
        else:
            ret = self.__info.GetDeviceIcon()
            self.cache["icon"] = ret
            return ret

    @mobile_manager
    def get_priority(self):
        if self.cache.has_key("priority") :
            return self.cache["priority"]
        else:
            ret = self.__info.GetPriority()
            self.cache["priority"] = ret
            return ret

    @mobile_manager
    def set_prority(self, priority):
        self.cache["priority"] = priority
        return self.__info.SetPriority(priority)

    @mobile_manager
    def is_multiport_device(self):
        if self.cache.has_key("is_multiport") :
            return self.cache["is_multiport"]
        else:
            ret = self.__info.IsMultiPortDevice()
            self.cache["is_multiport"] = ret
            return ret

    @mobile_manager
    def get_data_device_path(self):
        return self.__info.GetDataDevicePath()

    @mobile_manager
    def get_hardware_flow_control(self):
        return self.__info.GetHardwareFlowControl()

    @mobile_manager
    def get_hardware_error_control(self):
        return self.__info.GetHardwareErrorControl()

    @mobile_manager
    def get_hardware_compress(self):
        return self.__info.GetHardwareCompress()

    @mobile_manager
    def set_hardware_flow_control(self, value):
        self.__info.SetHardwareFlowControl(value)

    @mobile_manager
    def set_hardware_error_control(self, value):
        self.__info.SetHardwareErrorControl(value)

    @mobile_manager
    def set_hardware_compress(self, value):
        self.__info.SetHardwareCompress(value)

    # AUTH INTERFACE

    @auth_interface_required
    @device_ready_required
    @mobile_manager
    def is_pin_active(self):
        return self.__auth.IsPINActive()

    @auth_interface_required
    @device_ready_required
    @mobile_manager
    def set_pin_active(self, pin, active):
        return self.__auth.SetPINActive(pin, active)

    @auth_interface_required
    @mobile_manager
    def pin_status(self):
        return self.__auth.PINStatus()

    @auth_interface_required
    @mobile_manager
    def send_pin(self, pin):
        return self.__auth.SendPIN(pin)

    @auth_interface_required
    @device_ready_required
    @mobile_manager
    def set_pin(self, old_pin, new_pin):
        return self.__auth.SetPIN(old_pin, new_pin)

    @auth_interface_required
    @mobile_manager
    def send_puk(self, puk, pin):
        return self.__auth.SendPUK(puk, pin)

    # STATUS INTERFACE

    @state_interface_required
    @device_ready_required
    @mobile_manager
    def get_card_info(self):
        if self.cache.has_key("cardinfo") :
            return self.cache["cardinfo"]
        else:
            ret = self.__state.GetCardInfo()
            self.cache["cardinfo"] = ret
            return ret

    @state_interface_required
    @mobile_manager
    def get_card_status(self):
        if self.device_dialer.status() != PPP_STATUS_DISCONNECTED and not self.is_multiport_device() :
            return CARD_STATUS_READY
        return self.__state.GetCardStatus()

    @mobile_manager
    def get_imsi (self):
        if self.cache.has_key("imsi"):
            return self.cache["imsi"]
        else:
            ret = self.__state.GetImsi()
            self.cache["imsi"] = ret
            return ret


    def get_imsi_safe (self):
        if self.cache.has_key("imsi"):
            return self.cache["imsi"]

        if self.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI):
            if self.get_card_status() == CARD_STATUS_READY :
                if self.device_dialer.status() != PPP_STATUS_DISCONNECTED and not self.is_multiport_device():
                    return ""
                else:
                    ret = self.get_imsi()
                    if ret == None :
                        return ""
                    return ret
            else:
                return ""
        else:
            return ""

    @state_interface_required
    @mobile_manager
    def turn_off(self):
        return self.__state.TurnOff()

    @state_interface_required
    @mobile_manager
    def turn_on(self):
        return self.__state.TurnOn()

    @state_interface_required
    @mobile_manager
    def is_on(self):
        return self.__state.IsOn()

    @state_interface_required
    @mobile_manager
    def is_attached(self):
        return self.__state.IsAttached()

    @state_interface_required
    @mobile_manager
    def set_carrier_auto_selection(self):
        return self.__state.SetCarrierAutoSelection()

    @state_interface_required
    @mobile_manager
    def is_carrier_auto(self):
        return self.__state.IsCarrierAuto()

    @state_interface_required
    @device_ready_required
    @mobile_manager
    def is_postpaid(self):
        if tgcm.country_support != "de":
            return self.__state.IsPostpaid()
        else:
            imsi = self.get_imsi ()
            prepay_imsis = ["2620749",
                            "26207500",
                            "26207515",
                            "26207516",
                            "26207511"]

            for imsi_aux in prepay_imsis:
                if imsi.startswith (imsi_aux):
                    return False

            return True

    @state_interface_required
    @device_ready_required
    @mobile_manager
    def get_cover_key(self, key, rfunc, efunc):
        self.__state.GetUSSDCmd(key,
                                reply_handler=rfunc,
                                error_handler=efunc)

    @state_interface_required
    @device_ready_required
    @mobile_manager
    def is_roaming(self):
        if (os.path.exists(os.path.join(tgcm.config_dir, "roaming"))) :
            return True

        if self.cache.has_key("roaming") :
            return self.cache["roaming"]
        else:
            if self.device_dialer.status() != PPP_STATUS_DISCONNECTED and not self.is_multiport_device() :
                tgcm.debug("MMC : return not roaming, because MM don't know this info and can't ask it")
                return False

            if self.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) :
                ret = self.__state.IsRoaming()
                self.cache["roaming"] = ret
                return ret
            else:
                self.cache["roaming"] = False
                return False

    @state_interface_required
    @device_ready_required
    @mobile_manager
    def set_mode_domain(self, mode=None, domain=None):
        d = domain
        m = mode
        if d == None :
            d = self.domain
        if m == None :
            m = self.mode

        if d == MobileManager.CARD_DOMAIN_CS_PS :
            tgcm.info ("Setting  DOMAIN : CS_PS")
        elif d == MobileManager.CARD_DOMAIN_CS :
            tgcm.info ("Setting  DOMAIN : CS")
        elif d == MobileManager.CARD_DOMAIN_PS :
            tgcm.info ("Setting  DOMAIN : PS")


        if  m == MobileManager.CARD_TECH_SELECTION_AUTO :
            tgcm.info ("Setting  MODE : AUTO")
        elif m == MobileManager.CARD_TECH_SELECTION_GPRS :
            tgcm.info ("Setting  MODE : GPRS")
        elif m == MobileManager.CARD_TECH_SELECTION_UMTS :
            tgcm.info ("Setting  MODE : UMTS")
        elif m == MobileManager.CARD_TECH_SELECTION_GRPS_PREFERED :
            tgcm.info ("Setting  MODE : GPRS_PREF")
        elif m == MobileManager.CARD_TECH_SELECTION_UMTS_PREFERED :
            tgcm.info ("Setting  MODE : UMTS_PREF")

        if self.__state.SetModeDomain(m, d) :
            self.mode = m
            self.domain = d

        return


    @state_interface_required
    @device_ready_required
    @mobile_manager
    def get_mode_domain(self):
        return self.__state.GetModeDomain()

    @state_interface_required
    @device_ready_required
    @mobile_manager
    def set_carrier(self, value1, value2):
        return self.__state.SetCarrier(value1, value2)


    @state_interface_required
    @device_ready_required
    @mobile_manager
    def get_carrier_list(self, reply_handler, error_handler):
        return self.__state.GetCarrierList(reply_handler=reply_handler,
                                           error_handler=error_handler,
                                           timeout=2000000)

    # SMS INTERFACE

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_send (self, number, smsc, text, rfunc, efunc, request_status=False):
        if request_status == False :
            self.__sms.Send(number, smsc, text,
                            timeout=2000000,
                            reply_handler=rfunc,
                            error_handler=efunc)
        else:
            self.__sms.SendWithRequestStatus(number, smsc, text,
                                             timeout=2000000,
                                             reply_handler=rfunc,
                                             error_handler=efunc)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_get_draft (self, index):
        return self.__sms.GetDraft (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_set_draft (self, number, text):
        return self.__sms.SetDraft (number, text)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_edit_draft (self, index, number, text):
        return self.__sms.EditDraft (index, number, text)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_delete_draft (self, index):
        return self.__sms.DeleteDraft (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_list_drafts (self):
        return self.__sms.ListDrafts ()

    def __rewrite_received_item(self, i,r,sender,d,msg) :
        if "SR-OK" in sender :
            sender = _("Notification")
            recipient, scts, dt = msg.split("|")
            new_msg = _("The SMS for %s, sent on %s at %s, has been delivered on %s at %s.") % (recipient,
                                                                                              scts.split()[0],
                                                                                              scts.split()[1],
                                                                                              dt.split()[0],
                                                                                              dt.split()[1])
            return (i,r,sender,d,new_msg)
        elif "SR-UNKNOWN" in sender :
            sender = _("Notification")
            recipient, scts, dt = msg.split("|")
            new_msg = _("There has been an error while sending the SMS for %s, sent on %s at %s. ") % (recipient,
                                                                                                       scts.split()[0],
                                                                                                       scts.split()[1])
            return (i,r,sender,d,new_msg)
        elif "SR-STORED" in sender :
            sender = _("Notification")
            recipient, scts, dt = msg.split("|")
            new_msg = _("The SMS for %s, sent on %s at %s, has been stored in the short message service center.") % (recipient,
                                                                                                                   scts.split()[0],
                                                                                                                   scts.split()[1])
            return (i,r,sender,d,new_msg)
        else:
            return (i,r,sender,d,msg)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_get_received (self, index):
        i,r,sender,d,msg   = self.__sms.GetReceived (index)
        return self.__rewrite_received_item(i,r,sender,d,msg)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_delete_received (self, index):
        return self.__sms.DeleteReceived (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_list_received (self):
        ret = self.__sms.ListReceived ()
        received_list =  []
        for i,r,sender,d in ret :
            if sender.startswith("SR-") :
                sender = _("Notification")

            received_list.append((i,r,sender,d))

        return received_list

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_mark_received_readed (self, index):
        return self.__sms.MarkReceivedReaded (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_mark_received_unreaded (self, index):
        return self.__sms.MarkReceivedUnreaded (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_get_sended (self, index):
        return self.__sms.GetSended (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_delete_sended (self, index):
        return self.__sms.DeleteSended (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_list_sended (self):
        return self.__sms.ListSended ()

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_mark_sended_readed (self, index):
        return self.__sms.MarkSendedReaded (index)

    @sms_interface_required
    @device_ready_required
    @mobile_manager
    def sms_mark_sended_unreaded (self, index):
        return self.__sms.MarkSendedUnreaded (index)

    def __DevRoamingActStatusChanged_cb(self, mcontroller, device, status):
        if self.path == device :
            self.cache["roaming"] = status
            tgcm.debug("Caching roaming value (%s , %s, %s)" % (self, device, status))

    def __DevCardStatusChanged_cb(self, mcontroller, device, status):
        if self.path == device :
            if status == CARD_STATUS_READY :
                if not self.cache.has_key("imsi") :
                    self.get_imsi_safe()

                try:
                    self.get_card_info()
                except:
                    pass



gobject.type_register(Device)
