#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
#           Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2010-2012, Telefonica Móviles España S.A.U.
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

import gobject
import time
import dbus.exceptions

import tgcm
import Config
import ConnectionLogger
import ConnectionManager
import ConnectionSettingsManager
import Signals
import NetworkManagerDbus
import SMSStorage
import Singleton
import MainModem
import MainWifi

from DeviceExceptions import *

import freedesktopnet
import freedesktopnet.networkmanager.accesspoint
from freedesktopnet import networkmanager
from freedesktopnet.networkmanager.networkmanager import NetworkManager

DEVICE_MODEM = 1
DEVICE_WIRED = 2
DEVICE_WLAN = 3
DEVICE_WLAN_PROFILE = 4

from MobileManager import CARD_DOMAIN_CS, CARD_DOMAIN_PS, CARD_DOMAIN_CS_PS, \
    CARD_DOMAIN_ANY, CARD_TECH_SELECTION_GPRS, CARD_TECH_SELECTION_UMTS, \
    CARD_TECH_SELECTION_GRPS_PREFERED, CARD_TECH_SELECTION_UMTS_PREFERED, \
    CARD_TECH_SELECTION_NO_CHANGE, CARD_TECH_SELECTION_AUTO, \
    CARD_STATUS_READY, CARD_STATUS_NO_SIM, CARD_STATUS_OFF, \
    CARD_STATUS_ATTACHING, CARD_STATUS_PIN_REQUIRED, \
    CARD_STATUS_PUK_REQUIRED, CARD_STATUS_ERROR, \
    CARD_STATUS_PH_NET_PIN_REQUIRED, CARD_STATUS_PH_NET_PUK_REQUIRED, \
    PPP_STATUS_CONNECTED, PPP_STATUS_CONNECTING, \
    PPP_STATUS_DISCONNECTED, PPP_STATUS_DISCONNECTING, \
    PIN_STATUS_READY, PIN_STATUS_WAITING_PIN, \
    PIN_STATUS_WAITING_PUK, PIN_STATUS_NO_SIM, \
    PIN_STATUS_WAITING_PH_NET_PIN, PIN_STATUS_WAITING_PH_NET_PUK

from mobilemanager.devices.ModemGsm import ALLOWED_MODE_ANY, \
    ALLOWED_MODE_2G_PREFERRED, ALLOWED_MODE_3G_PREFERRED, \
    ALLOWED_MODE_2G_ONLY, ALLOWED_MODE_3G_ONLY, ALLOWED_MODE_LAST, \
    DOMAIN_CS, DOMAIN_PS, DOMAIN_CS_PS, DOMAIN_ANY, \
    ACCESS_TECH_UNKNOWN, ACCESS_TECH_GSM, ACCESS_TECH_GSM_COMPACT, \
    ACCESS_TECH_GPRS, ACCESS_TECH_EDGE, ACCESS_TECH_UMTS, \
    ACCESS_TECH_HSDPA, ACCESS_TECH_HSUPA, ACCESS_TECH_HSPA, \
    ACCESS_TECH_HSPA_PLUS


class fallback_on_dbus_error(object):
    '''
    A decorator used to return a fallback value if a DBus call fails
    '''
    def __init__(self, fallback_value):
        self.fallback_value = fallback_value

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                value = func(*args, **kwargs)
            except:
                value = self.fallback_value
            return value
        return wrapper


class DeviceManager(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'active-dev-card-status-changed':    (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'active-dev-tech-status-changed':    (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'active-dev-domain-status-changed':  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'active-dev-mode-status-changed':    (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'active-dev-signal-status-changed':  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'active-dev-sms-spool-changed':      (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'active-dev-sms-flash-received':     (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING,)),
        'active-dev-sms-bam-received':       (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING,)),
        'active-dev-pin-act-status-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
        'active-dev-roaming-status-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
        'active-dev-carrier-changed':        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),

        #NEW Signals
        'device-added':   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'device-removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),

        # MobileModem signals
        'main-device-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'main-device-state-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (
            gobject.TYPE_PYOBJECT,   #Dev obj
            gobject.TYPE_PYOBJECT,   #state dict
        )),
        'main-device-fatal-error': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),

        # WiFi signals
        'wifi-device-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'wifi-device-state-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (
            gobject.TYPE_PYOBJECT,   #Dev obj
            gobject.TYPE_PYOBJECT,   #state dict
        )),

        # Common device signals
        'device-state-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (
            gobject.TYPE_PYOBJECT,   #Dev obj
            gobject.TYPE_PYOBJECT,   #state dict
        )),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.net_m = freedesktopnet.NetworkManager()
        self.sms_storage = SMSStorage.SMSStorage(self)
        self.connection_logger = ConnectionLogger.ConnectionLogger()

        self.devices = []

        self.main_device_object_path = None
        self.wifi_device_object_path = None
        self.wired_device_object_path = None
        self.main_modem = MainModem.MainModem(self)
        self.main_wifi = MainWifi.MainWifi(self)

        self.net_m.connect_to_signal("DeviceAdded", self.__DeviceAdded_cb)
        self.net_m.connect_to_signal("DeviceRemoved", self.__DeviceRemoved_cb)

        # -- Schedule this task for later as need the DeviceManager object ASAP
        gobject.idle_add(self.__check_available_devices)

    def get_main_device(self):
        "get main device (MobileModem)"

        return self.main_modem.current_device()

    def get_wifi_device(self):
        "get wifi device (WLan Device)"

        if self.wifi_device_object_path == None:
            return None

        for dev in self.devices:
            if str(dev.object_path) == str(self.wifi_device_object_path) :
                return dev

        return None

    def get_wired_device(self):
        "get wired device (Ethernet Device)"

        if self.wired_device_object_path == None:
            return None

        for dev in self.devices:
            if str(dev.object_path) == str(self.wired_device_object_path) :
                return dev

        return None

    def set_main_device(self, obj):
        "set main device (MobileModem)"

        if obj == None:
            for dev in self.devices:
                if dev.get_type() == DEVICE_MODEM:
                    dev._set_active(False)

            self.main_device_object_path = None
            self.emit('main-device-changed', None)
        else:
            if obj in self.devices and obj.get_type() == DEVICE_MODEM:
                for dev in self.devices:
                    if dev.get_type() == DEVICE_MODEM:
                        dev._set_active(False)
                self.main_device_object_path = str(obj.object_path)
                self.emit('main-device-changed', None)
                if (dev.status != CARD_STATUS_NO_SIM):
                    obj._set_active(True)
            else:
                if obj not in self.devices:
                    tgcm.error("This object not exists in device manager")
                elif obj.get_type() != DEVICE_MODEM:
                    tgcm.error("This object is not a Modem Device")

    def set_wifi_device(self, obj):
        "set main device (WiFi Device)"

        if obj == None:
            for dev in self.devices:
                if dev.get_type() == DEVICE_WLAN :
                    dev._set_active(False)

            self.wifi_device_object_path = None
            self.emit('wifi-device-changed' , None)
        else:
            if obj in self.devices and obj.get_type() == DEVICE_WLAN:
                for dev in self.devices:
                    if dev.get_type() == DEVICE_WLAN :
                        dev._set_active(False)
                self.wifi_device_object_path = str(obj.object_path)
                obj._set_active(True)
            else:
                if obj not in self.devices :
                    tgcm.error("This object not exists in device manager")
                elif obj.get_type() != DEVICE_WLAN:
                    tgcm.error("This object is not a WiFi Device")

    def set_wired_device(self, obj):
        "set Wired device (Ethernet Device)"

        if obj == None:
            for dev in self.devices:
                if dev.get_type() == DEVICE_WIRED :
                    dev._set_active(False)

            self.wired_device_object_path = None
            self.emit('wired-device-changed' , None)
        else:
            if obj in self.devices and obj.get_type() == DEVICE_WIRED:
                for dev in self.devices:
                    if dev.get_type() == DEVICE_WIRED :
                        dev._set_active(False)
                self.wired_device_object_path = str(obj.object_path)
                obj._set_active(True)
            else:
                if obj not in self.devices :
                    tgcm.error("This object not exists in device manager")
                elif obj.get_type() != DEVICE_WIRED:
                    tgcm.error("This object is not an Ethernet Device")

    def get_available_devices(self):
        ret = []
        for dev in self.devices:
            ret.append(dev)
        return ret

    def remove_device_on_fatal_error(self, device):
        self.__remove_device(device)
        self.emit('main-device-fatal-error')

    def __DeviceAdded_cb(self, device):
        for nm_dev in self.net_m.GetDevices():
            if str(nm_dev.object_path) == str(device):
                new_device = Device._create_device_from_nm_dev(nm_dev, self)
                if new_device != None:
                    self.devices.append(new_device)

                    tgcm.debug("Added : %s" % new_device)
                    if new_device.__class__ == DeviceModem:
                        if self.get_main_device() == None:
                            self.set_main_device(new_device)
                            tgcm.debug("Set Main device : %s" % new_device)
                        else:
                            # -- Emit this signal for the MainModem handler
                            self.emit('main-device-changed', new_device)

                    elif new_device.__class__ == DeviceWLan:
                        if self.get_wifi_device() == None:
                            self.set_wifi_device(new_device)
                            tgcm.debug("Set Wifi device : %s" % new_device)

                    self.emit("device-added", new_device)
                    return

    def __DeviceRemoved_cb(self, device):
        self.__remove_device(device)

    def __remove_device(self, device):
        objs_to_remove = filter(lambda x: str(x.object_path) == str(device), self.devices)
        for obj in objs_to_remove:
            self.devices.remove(obj)
            tgcm.debug("DeviceModem: Removed %s (%s)" % (obj.object_path, repr(obj)))
            self.emit("device-removed", obj.object_path)

            # -- Stop the device
            obj.stop()

    def __check_available_devices(self):
        for nm_dev in self.net_m.GetDevices():
            new_device = Device._create_device_from_nm_dev(nm_dev, self)
            if new_device == None:
                tgcm.debug("WARNING: Couldn't create device (%s). Probably ignored due RNDIS type?" % nm_dev.object_path)
            else:
                self.devices.append(new_device)

                if new_device.__class__ == DeviceModem:
                    if self.get_main_device() == None:
                        self.emit("device-added", new_device)
                        self.set_main_device(new_device)
                        # It is not a good idea to log the new WWAN device
                        # here because the GSM card might be blocked
                        tgcm.debug("Set Main device : %s" % new_device)
                elif new_device.__class__ == DeviceWLan:
                    if self.get_wifi_device() == None:
                        self.set_wifi_device(new_device)
                        self.connection_logger.register_new_device(new_device)
                        tgcm.debug("Set Wifi device : %s" % new_device)
                elif new_device.__class__ == DeviceWired:
                    if self.get_wired_device() == None:
                        self.set_wired_device(new_device)
                        self.connection_logger.register_new_device(new_device)
                        tgcm.debug("Set Ethernet device : %s" % new_device)

    @staticmethod
    def get_technology_string(tech=ACCESS_TECH_UNKNOWN):
        access_tech = {
            ACCESS_TECH_UNKNOWN:     "",
            ACCESS_TECH_GSM:         "GPRS",
            ACCESS_TECH_GSM_COMPACT: "GPRS",
            ACCESS_TECH_GPRS:        "GPRS",
            ACCESS_TECH_EDGE:        "EDGE",
            ACCESS_TECH_UMTS:        "3G",
            ACCESS_TECH_HSDPA:       "3.5G",
            ACCESS_TECH_HSUPA:       "3.5G+",
            ACCESS_TECH_HSPA:        "3.5G+",
            ACCESS_TECH_HSPA_PLUS:   "HSPA+"
        }

        tech_str = ''

        if (tech > ACCESS_TECH_UMTS) and (not MainModem.MainModem().is_connected()):
            tech = ACCESS_TECH_UMTS

        if tech in access_tech.keys():
            tech_str = access_tech[tech]

        return tech_str


class Device(gobject.GObject):
    type = None

    def __init__(self, nm_dev, device_manager):
        gobject.GObject.__init__(self)

        self.nm_dev = nm_dev
        self.object_path = nm_dev.object_path
        self.device_manager = device_manager
        self.is_active = False
        self.capabilities = []
        self.pretty_name = 'No pretty name'

    def emit(self, value):
        if self.get_type() == DEVICE_MODEM and self.is_active == True:
            self.device_manager.emit('main-device-state-changed', self, value)
        elif self.get_type() == DEVICE_WLAN and self.is_active == True:
            self.device_manager.emit('wifi-device-state-changed', self, value)

        self.device_manager.emit('device-state-changed', self, value)

    def get_nm_device(self):
        return self.nm_dev

    def get_type(self):
        return self.type

    def has_capability(self, value):
        if value in self.capabilities :
            return True
        else:
            return False

    def get_prettyname(self):
        return self.pretty_name

    @fallback_on_dbus_error(False)
    def is_connected(self):
        state = self.nm_dev.Get(NetworkManagerDbus.NM_DEVICE_IFACE, 'State')
        return state == NetworkManagerDbus.NM_DEVICE_STATE_ACTIVATED

    @fallback_on_dbus_error(True)
    def is_disconnected(self):
        state = self.nm_dev.Get(NetworkManagerDbus.NM_DEVICE_IFACE, 'State')
        return state == NetworkManagerDbus.NM_DEVICE_STATE_DISCONNECTED

    @fallback_on_dbus_error(False)
    def is_ready(self):
        state = self.nm_dev.Get(NetworkManagerDbus.NM_DEVICE_IFACE, 'State')
        unavailable_states = [
            NetworkManagerDbus.NM_DEVICE_STATE_UNKNOWN,
            NetworkManagerDbus.NM_DEVICE_STATE_UNMANAGED,
            NetworkManagerDbus.NM_DEVICE_STATE_UNAVAILABLE,
            NetworkManagerDbus.NM_DEVICE_STATE_FAILED
        ]
        return not state in unavailable_states

    def _set_active(self, value):
        if value == True:
            self.is_active = True
            if self.get_type() == DEVICE_MODEM:
                self.device_manager.emit('main-device-changed', self)
                self._reemit_signals()
            elif self.get_type() == DEVICE_WLAN:
                self.device_manager.emit('wifi-device-changed', self)
                self._reemit_signals()
        else:
            self.is_active = False

    def _reemit_signals(self):
        pass

    @staticmethod
    def _create_device_from_nm_dev(nm_dev, device_manager):
        if str(nm_dev["DeviceType"]) == "ETHERNET":
            # -- Ignore the RNDIS devices as we don't support it yet
            if Device.is_NDIS_device(nm_dev):
                return None

            return DeviceWired(nm_dev, device_manager)
        elif str(nm_dev["DeviceType"]) == "WIRELESS":
            return DeviceWLan(nm_dev, device_manager)
        elif str(nm_dev["DeviceType"]) == "GSM":
            modem_path = str(nm_dev["Udi"])
            modem_m = freedesktopnet.ModemManager()

            for mm_dev in modem_m.EnumerateDevices():
                if modem_path == str(mm_dev.object_path):
                    return DeviceModem(nm_dev, mm_dev, device_manager)

        return None

    @staticmethod
    def is_NDIS_device(nm_dev):
        if str(nm_dev["DeviceType"]) == "ETHERNET":
            if str(nm_dev["Driver"]) in ('cdc_ether', 'usbnet'):
                return True
        return False

    # -- For the case that the inheritance class doesn't have a stop method (this is the case for the Wlan devices)
    def stop(self):
        pass

class DeviceModem(Device):
    CARD_STATUS_CHECKER_INTERVAL = 500

    type = DEVICE_MODEM

    def __init__(self, nm_dev, mm_obj, device_manager):
        Device.__init__(self, nm_dev, device_manager)
        self.sms_stg = device_manager.sms_storage
        self.conf = Config.Config()
        self.modem          = mm_obj
        self.device_manager = device_manager
        self.main_modem     = device_manager.main_modem
        self.__main_device  = False

        self._cached_values = {}

        # -- These are the signals to be connected to DBUS
        signals = [
            ['mm-props', self.modem, "MmPropertiesChanged", self.__modem_manager_properties_changed_cb],
            ['signal', self.modem.iface["gsm.network"], "SignalQuality", self.__modem_gsm_network_signal_quality_cb],
            ['reginfo', self.modem.iface["gsm.network"], "RegistrationInfo", self.__modem_gsm_network_registration_info_cb],
            ['netmode', self.modem.iface["gsm.network"], "NetworkMode", self.__modem_gsm_network_network_mode_info_cb],
            ['complete', self.modem.iface["gsm.sms"], "Completed", self.__modem_gsm_sms_completed_cb],
            ['unlocked', self.modem.iface["gsm.card"], "DeviceUnlocked", self.__modem_gsm_card_unlocked_cb]
        ]
        self.__dbus_signals = Signals.DBusSignals(signals)

        signals = [
            ['main-modem', self.main_modem, "main-modem-changed", self.__main_modem_changed_cb],
            ['main-modem-disconnected', self.main_modem, "main-modem-disconnected", self.__main_modem_refresh_signals_cb],
            ['main-modem-connected', self.main_modem, "main-modem-connected", self.__main_modem_refresh_signals_cb]
        ]
        self.__gobj_signals = Signals.GobjectSignals(signals)

        self.device_dialer = DeviceDialer(self)
        self.__modem_status_checker_id=None
        self.start_checker()
        self.status = None
        self.has_domain_preferred=True

        self.__device_info = None
        self.__pretty_name = None
        self.__imei        = None

    # -- Disconnect all the signal of this object from the DBUS
    def dbus_disconnect(self):
        self.__dbus_signals.disconnect_all()

    def gobject_disconnect(self):
        self.__gobj_signals.disconnect_all()

    # -- Stop all the resources used by this object
    def stop(self):
        self.dbus_disconnect()
        self.gobject_disconnect()
        self.stop_checker()

    def start_checker(self):
        if self.__modem_status_checker_id is None:
            self.__modem_status_checker_id = gobject.timeout_add(self.CARD_STATUS_CHECKER_INTERVAL, self.__modem_status_checker)

    def stop_checker(self):
        if self.__modem_status_checker_id is not None:
            if gobject.source_remove(self.__modem_status_checker_id) is True:
                self.__modem_status_checker_id = None

    def __modem_status_checker(self):
        if self.status == None :
            self.status = self.get_card_status()
            self.emit({"card_status" : self.status})

        elif self.modem["Enabled"] == False and self.status != CARD_STATUS_OFF :
            self.status = CARD_STATUS_OFF
            self.emit({"card_status" : self.status})

        elif self.modem["Enabled"] == True and self.status != CARD_STATUS_READY :
            self.status = self.get_card_status()
            self.emit({"card_status" : self.status})

        else:
            status = self.get_card_status()
            if self.status != status:

                if status == CARD_STATUS_READY:
                    # -- By some modems, like the ZTE MF620, the Dbus method GetInfo() returns an error when
                    # -- card is awaiting for the PIN. For this reason we need to wait until the card
                    # -- is ready for reading the device info
                    self.__get_device_info()

                self.status = status
                self.emit({"card_status" : self.status})

        return True

    def __modem_manager_properties_changed_cb(self, iface, props):
        ret = {}

        if "UnlockRequired" in props:
            ret["card_status"] = self.get_card_status()
            self.status = ret["card_status"]

        if "Enable" in props:
            ret["card_status"] = self.get_card_status()
            self.status = ret["card_status"]

        tgcm.debug("Emit this %s" % ret)
        self.emit(ret)

    def __modem_gsm_network_signal_quality_cb(self, sq):
        value = {"signal_quality" : sq}
        self.emit(value)

    def __modem_gsm_network_registration_info_cb(self, state, carrier_code, carrier_name):
        tech = self.modem.iface["gsm.network"]["AccessTechnology"]
        value = {"carrier_name" : str(carrier_name),
                 "carrier_code" : str(carrier_code),
                 "roaming" : True if state == 5 else False,
                 "access_tech" : tech,
                 }

        self.emit(value)

    def __modem_gsm_network_network_mode_info_cb(self, mode):
        ret = None
        if mode == ALLOWED_MODE_2G_PREFERRED :
            ret = CARD_TECH_SELECTION_GRPS_PREFERED
        elif mode == ALLOWED_MODE_3G_PREFERRED :
            ret = CARD_TECH_SELECTION_UMTS_PREFERED
        elif mode == ALLOWED_MODE_2G_ONLY :
            ret = CARD_TECH_SELECTION_GPRS
        elif mode == ALLOWED_MODE_3G_ONLY :
            ret = CARD_TECH_SELECTION_UMTS
        else:
            ret = CARD_TECH_SELECTION_AUTO

        value = { "network_mode" : ret }
        self.emit(value)

    def __modem_gsm_sms_completed_cb(self, index, completed):
        sms_to_remove = []

        # Get the SMS from the GSM device
        sms = self.modem.iface["gsm.sms"].Get(index)

        # -- The below lines are only for debug purposes as the BAM query is failing under
        # -- some unknown conditions the returned value seems to be invalid
        try:
            doof = sms["concat_total"]
        except Exception, err:
            print "@FIXME: SMS completed callback received invalid message %s, %s " % (repr(sms), err)
            return

        if sms["concat_total"] == 0 :
            sms_to_remove.append(sms["index"])
        else:
            smss_list = self.modem.iface["gsm.sms"].List()
            concat_sms = {}
            for s in smss_list :
                if s["reference"] == sms["reference"]:
                    concat_sms[s["concat_number"]] = s

            # -- Check if we have the complete concatenated message otherwise need to wait
            if sms['concat_total'] != len(concat_sms):
                return

            # -- As we have the complete message delete it
            sms_text = ''
            for i in concat_sms.keys():
                sms_text = sms_text + concat_sms[i]["text"]
                sms_to_remove.append(concat_sms[i]["index"])

            sms["text"] = sms_text

        # Store the SMS only if it does not come from a reserved phone number
        number = sms['number']
        save_sms = True
        if (tgcm.country_support == 'es'):

            # -- Check for BAM responses
            if number in ( '223523', '0223523' ):
                phone_number = sms['text']
                imsi = self.get_imsi()

                self.conf.set_user_mobile_broadband_number(imsi, phone_number)
                save_sms = False

        # -- Check for the Flash SMS and BAM responses
        if (sms["notification"] is True) or (sms['notification'] == 1):
            # -- This is for the BAM (only available for Spain)
            if (tgcm.country_support == 'es') and (number == '222000'):
                self.device_manager.emit('active-dev-sms-bam-received', number, sms['text'])
            else:
                self.device_manager.emit('active-dev-sms-flash-received', number, sms['text'])

            save_sms = False

        if save_sms is True:
            sms["read"] = False
            self.sms_stg.save_received_sms(sms)

        for i in sms_to_remove :
            self.modem.iface["gsm.sms"].Delete(i)

    def __modem_gsm_card_unlocked_cb(self, opath):
        self.start_checker()

    def has_capability(self, value):
        if ".NoOptionsMenu" in value :
            return False
        return True

    def device_info(self):
        return self.__device_info

    def vendor(self):
        if self.__device_info is not None:
            return self.__device_info['manufacturer']

    def __get_device_info(self):
        invalid = _("Unknown")

        # -- Reduce serial port transfers by calling GetInfo() only if the info was not received yet
        if self.__device_info is None:
            # -- List of manufacturers we want to show
            manusLower = [ "alcatel", "huawei", "novatel", "sierra", "option" ]
            manusUpper = [ "ZTE", "ATI" ]

            # -- Format the manufacturer (replace spaces, convert to lower/upper case, etc.)
            manu = invalid
            try:
                manuAll, model, fw = self.modem.GetInfo()
                for _manu in manuAll.split(" "):
                    upper = _manu.upper()
                    lower = _manu.lower()
                    if upper in manusUpper:
                        manu = upper
                        break
                    elif lower in manusLower:
                        # -- Convert the first character to upper case
                        manu = lower.capitalize()
                        break
            except Exception, err:
                print "@FIXME: Got unexpected failure parsing manufacturer name, %s" % err

            # -- Store the internal device info only if we have a valid name
            self.__pretty_name = manu
            if manu != invalid:
                self.__device_info = { "manufacturer" : manu, "model" : model, "firmware" : fw }

    def get_prettyname(self):
        self.__get_device_info()
        return self.__pretty_name

    def _set_active(self, value):
        try:
            if self.is_on() == False:
                self.turn_on()
        except:
            pass
        Device._set_active(self, value)

    def emit(self, values):
        # -- If this device is not selected as main modem, then don't emit any signal
        if self.__main_device is False:
            return

        Device.emit(self, values)

        fields = (('signal_quality', 'active-dev-signal-status-changed'), \
                  ('carrier_name',   'active-dev-carrier-changed'), \
                  ('roaming',        'active-dev-roaming-status-changed'), \
                  ('card_status',    'active-dev-card-status-changed'), \
                  ('network_mode',   'active-dev-mode-status-changed'), \
                  ('domain_mode',    'active-dev-domain-status-changed'), \
                  ('access_tech',    'active-dev-tech-status-changed'), \
                  ('pin_active',     'active-dev-pin-act-status-changed'))

        for key, signal in fields:
            if self.__is_emission_needed(key, values):
                self.device_manager.emit(signal, values[key])

    def __is_emission_needed(self, key, values):
        is_emission_needed = False

        # Does the updated value contain a field with the key?
        if key in values:
            if key in self._cached_values:
                # If the key is found in the cache, it is only necessary
                # to emit it if the value is different
                is_emission_needed = values[key] != self._cached_values[key]
            else:
                # The key is not found in the cache, store its value and
                # emit its change
                is_emission_needed = True

        if is_emission_needed:
            self._cached_values[key] = values[key]

        return is_emission_needed

    def _reemit_signals(self):
        unlock_status = self.modem["UnlockRequired"]

        if self.is_on() and (len(unlock_status) == 0):
            sq = 0
            ri = '---'
            tech = None

            try:
                sq = self.modem.iface["gsm.network"].GetSignalQuality()
                ri = self.modem.iface["gsm.network"].GetRegistrationInfo()
                tech = self.modem.iface["gsm.network"]["AccessTechnology"]
            except:
                pass

            mode = self.get_technology()
            domain = self.get_domain()
            pa = self.is_pin_active()
            cs = self.get_card_status()

            value = {
                "signal_quality": sq,
                "carrier_name":   str(ri[2]),
                "carrier_code":   str(ri[1]),
                "roaming":        True if ri[0] == 5 else False,
                "card_status":    cs,
                "network_mode":   mode,
                "domain_mode":    domain,
                "pin_active":     pa,
                "access_tech":    tech,
            }
            self.emit(value)
        else:
            cs = self.get_card_status()
            value = {"card_status" : cs,}
            self.emit(value)

    @fallback_on_dbus_error(0)
    def get_SignalQuality(self):
        return self.modem.iface["gsm.network"].GetSignalQuality()

    #INFO INTERFACE
    def get_MSISDN(self):
        #TO DEPRECATE !!!!
        return self.modem.iface["gsm.card"].GetMSISDN()

    def get_IMEI(self):
        # -- The Dbus method returns a value of type 'dbus.String()', so need to convert to string
        if self.__imei is None:
            self.__imei = str(self.modem.iface['gsm.card'].GetImei())
        return self.__imei

    def get_ICCID(self):
        return self.modem.iface['gsm.card'].GetICCID()

    def is_multiport_device(self):
        #TO DEPRECATE !!!!
        return True

    # AUTH INTERFACE
    def is_pin_active(self):
        return self.modem.iface["gsm.card"].IsPinEnabled()

    def set_pin_active(self, pin, active):
        try:
            self.modem.iface["gsm.card"].EnablePin(pin, active)
        except:
            pa = self.is_pin_active()
            self.emit({"pin_active" : pa})
            return False

        pa = self.is_pin_active()
        self.emit({"pin_active" : pa})
        return True

    def pin_status(self):
        unlock_req = self.modem["UnlockRequired"]
        if unlock_req == '':
            return PIN_STATUS_READY
        elif unlock_req == 'sim-pin':
            return PIN_STATUS_WAITING_PIN
        elif unlock_req == 'sim-puk':
            return PIN_STATUS_WAITING_PUK
        elif unlock_req == 'ph-net-pin':
            return PIN_STATUS_WAITING_PH_NET_PIN
        elif unlock_req == 'ph-net-puk':
            return PIN_STATUS_WAITING_PH_NET_PUK

        #FIXME !!!
        return PIN_STATUS_NO_SIM

    def send_pin(self, pin):
        try:
            self.modem.iface["gsm.card"].SendPin(pin)
            if self.is_on() == False:
                self.turn_on()
        except:
            return False
        return True

    def set_pin(self, old_pin, new_pin):
        try:
            self.modem.iface["gsm.card"].SetPin(old_pin, new_pin)
        except:
            return False
        return True

    def send_puk(self, puk, pin):
        try:
            self.modem.iface["gsm.card"].SendPuk(puk, pin)
        except:
            return False
        return True

    # STATUS INTERFACE
    def get_card_info(self):
        manufacturer, model, revision = self.modem.GetInfo()
        ret = []
        ret.append("Manufacturer: %s" % manufacturer if manufacturer != '' else '-')
        ret.append("Model: %s" % model if model != '' else '-')
        ret.append("Revision: %s" % revision if revision != '' else '-')
        return ret

    def get_card_status(self):
        if self.modem["Enabled"] != True:
            return CARD_STATUS_OFF
        else:
            unlock_req = self.modem["UnlockRequired"]
            if unlock_req == '':
                if self.is_attached() == True:
                    return CARD_STATUS_READY
                else:
                    imsi=self.get_imsi()
                    if imsi is not None and imsi != '':
                        return CARD_STATUS_ATTACHING
                    else:
                        return CARD_STATUS_NO_SIM
            elif unlock_req == 'sim-pin':
                return CARD_STATUS_PIN_REQUIRED
            elif unlock_req == 'sim-puk':
                return CARD_STATUS_PUK_REQUIRED
            elif unlock_req == 'ph-net-pin':
                return CARD_STATUS_PH_NET_PIN_REQUIRED
            elif unlock_req == 'ph-net-puk':
                return CARD_STATUS_PH_NET_PUK_REQUIRED

        return CARD_STATUS_ERROR

    def get_imsi(self):
        # Look for the IMSI in the cache first
        if 'imsi' in self._cached_values:
            return self._cached_values['imsi']

        # IMSI could only be consulted if the modem is ready
        if self.modem["UnlockRequired"] != '':
            return

        # Ask mobile-manager2 for the value of the IMSI
        try:
            ret = self.modem.iface["gsm.card"].GetImsi()
            if ret is not None:
                self._cached_values['imsi'] = ret
                return self._cached_values['imsi']
        except:
            pass

        # If everything fails return a obviously erroneous value
        return None

    def get_imsi_safe (self):
        self.get_imsi()

    def turn_off(self):
        # Before turning off, disconnect the modem over the NM interface
        # otherwise the NM will remove the device!
        try:
            if self.device_dialer.is_modem():
                self.device_dialer.emit('disconnecting')

            keys_to_remove = ('carrier_name', 'carrier_code', 'roaming', \
                    'network_mode', 'domain_mode', 'access_tech', \
                    'signal_quality')
            for key in keys_to_remove:
                if key in self._cached_values:
                    del self._cached_values[key]

            self.nm_dev.Disconnect()
        except dbus.exceptions.DBusException, err:
            # -- This exception is caused when the modem is not connected but we send a disconnect request
            pass
        self.stop_checker()
        self.modem.Enable(False)

    def turn_on(self):
        self.modem.Enable(True)
        self.start_checker()
        self.__main_modem_refresh_signals_cb(None, None, None)

    def is_on(self):
        return self.modem["Enabled"] == True

    def is_card_ready(self):
        return self.get_card_status() == CARD_STATUS_READY

    def is_attached(self):
        try:
            reg = self.modem.iface["gsm.network"].GetRegistrationInfo()[0]
        except:
            return False

        if reg == 1 or reg == 5 :
            return True
        else:
            return False

    def set_carrier_auto_selection(self):
        ret = self.modem.iface["gsm.network"].AutoRegistration()
        op_name = self.modem.iface["gsm.network"].GetRegistrationInfo()[2]
        self.device_manager.emit('active-dev-carrier-changed', op_name)
        return ret

    def is_carrier_auto(self):
        return self.modem.iface["gsm.network"].IsAutoRegistrationMode()

    def is_postpaid(self):
        if tgcm.country_support == "es":
            imsi = self.get_imsi ()
            return not self.conf.is_imsi_based_prepaid(imsi)

        elif tgcm.country_support != "de":
            return True
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

    def get_cover_key(self, key, rfunc, efunc):
        self.modem.iface['gsm.ussd'].Initiate(key,
                                           reply_handler=rfunc,
                                           error_handler=efunc,
                                           timeout=2000000)

    def is_roaming(self):
    #    return False
        try:
            reg = self.modem.iface["gsm.network"].GetRegistrationInfo()[0]
            if reg == 5 :
                return True
            else:
                return False
        except:
            return False

    def get_technology(self):
        try:
            tech_mm = self.modem.iface["gsm.network"].GetAllowedMode()
        except:
            tech_mm = None

        if tech_mm == ALLOWED_MODE_ANY:
            tech = CARD_TECH_SELECTION_AUTO
        elif tech_mm == ALLOWED_MODE_2G_ONLY:
            tech = CARD_TECH_SELECTION_GPRS
        elif tech_mm == ALLOWED_MODE_2G_PREFERRED:
            tech = CARD_TECH_SELECTION_GRPS_PREFERED
        elif tech_mm == ALLOWED_MODE_3G_ONLY:
            tech = CARD_TECH_SELECTION_UMTS
        elif tech_mm == ALLOWED_MODE_3G_PREFERRED:
            tech = CARD_TECH_SELECTION_UMTS_PREFERED
        else:
            tech = CARD_TECH_SELECTION_AUTO

        return tech

    def set_technology(self, tech = CARD_TECH_SELECTION_NO_CHANGE):
        if  tech == CARD_TECH_SELECTION_AUTO:
            tech_mm = ALLOWED_MODE_ANY
            tech_string = 'AUTO'
        elif tech == CARD_TECH_SELECTION_GPRS:
            tech_mm = ALLOWED_MODE_2G_ONLY
            tech_string =  'GPRS'
        elif tech == CARD_TECH_SELECTION_UMTS:
            tech_mm = ALLOWED_MODE_3G_ONLY
            tech_string = 'UMTS'
        elif tech == CARD_TECH_SELECTION_GRPS_PREFERED:
            tech_mm = ALLOWED_MODE_2G_PREFERRED
            tech_string = 'GPRS_PREF'
        elif tech == CARD_TECH_SELECTION_UMTS_PREFERED:
            tech_mm = ALLOWED_MODE_3G_PREFERRED
            tech_string = 'UMTS_PREF'

        self.modem.iface['gsm.network'].SetAllowedMode(tech_mm)
        tgcm.info('Setting MODE: %s' % tech_string)
        self.emit({'network_mode' : tech})

        if (tech != CARD_TECH_SELECTION_NO_CHANGE) and \
                (tech != self.conf.get_last_device_mode()):
            self.conf.set_last_device_mode(tech)

    def get_domain(self):
        try:
            domain_mm = self.modem.iface["gsm.network"].GetDomain()
        except:
            domain_mm = None

        if domain_mm == DOMAIN_CS_PS:
            domain = CARD_DOMAIN_CS_PS
        elif domain_mm == DOMAIN_CS:
            domain = CARD_DOMAIN_CS
        elif domain_mm == DOMAIN_PS:
            domain = CARD_DOMAIN_PS
        elif domain_mm == DOMAIN_ANY:
            domain = CARD_DOMAIN_ANY
        else:
            # -- In the MM specs there is no error value so return any
            domain = CARD_DOMAIN_ANY

        return domain

    def set_domain(self, domain = CARD_DOMAIN_ANY):
        if domain == CARD_DOMAIN_CS_PS:
            domain_mm = DOMAIN_CS_PS
            domain_string = 'CS_PS'
        elif domain == CARD_DOMAIN_CS:
            domain_mm = DOMAIN_CS
            domain_string = 'CS'
        elif domain == CARD_DOMAIN_PS:
            domain_mm = DOMAIN_PS
            domain_string = 'PS'
        elif domain == CARD_DOMAIN_ANY:
            domain_mm = DOMAIN_ANY
            domain_string = 'ANY'
        else:
            raise ValueError, "@FIXME: set_domain() got invalid domain type '%s'" % domain

        self.modem.iface['gsm.network'].SetDomain(domain_mm)
        tgcm.info('Setting DOMAIN: %s' % domain_string)
        self.emit({'domain_mode' : domain})

        if domain != self.conf.get_last_domain():
            self.conf.set_last_device_domain(domain)

    def set_carrier(self, network_id, tech):
        self.modem.iface["gsm.network"].RegisterWithTech(network_id,tech)
        op_name = self.modem.iface["gsm.network"].GetRegistrationInfo()[2]
        self.device_manager.emit('active-dev-carrier-changed', op_name)
        return True

    def get_access_technology(self):
        return self.modem.iface["gsm.network"]["AccessTechnology"]

    # -- We need to restart the status checker before starting the callback of our caller
    def __get_carrier_list_reply_cb(self, carriers):
        self.start_checker()
        if self.__get_carrier_list_cbs["reply"] is not None:
            self.__get_carrier_list_cbs["reply"](carriers)

    def __get_carrier_list_error_cb(self, error):
        self.start_checker()
        if self.__get_carrier_list_cbs["error"] is not None:
            self.__get_carrier_list_cbs["error"](error)

    def get_carrier_list(self, reply_handler, error_handler):

        self.__get_carrier_list_cbs = { "reply" : reply_handler, "error" : error_handler }

        # -- Need to stop the device checker which triggers AT-commands in the MM, as the scan could take
        # -- a long time and during this time the requests from the Tgcm should not block the application
        self.stop_checker()
        self.modem.iface["gsm.network"].Scan(reply_handler=self.__get_carrier_list_reply_cb,
                                             error_handler=self.__get_carrier_list_error_cb,
                                             timeout=2000000)

    #SMS INTERFACE
    def sms_send (self, number, smsc, text, rfunc, efunc, request_status=False, store_message=True):
        self.modem.iface["gsm.sms"].Send({'number' : number, 'text' : text, 'status_request' : request_status,'smsc' : smsc}, reply_handler=rfunc, error_handler=efunc, timeout=2000000)
        if store_message:
            self.sms_stg.save_sent_sms(number, text)

    #Addressbook
    def addressbook_list_contacts(self):
        return self.modem.iface["gsm.contacts"].List()

    def __main_modem_changed_cb(self, main_modem, device_manager, device):
        if device == self:
            self.__main_device = True

    def __main_modem_refresh_signals_cb(self, main_modem, device_manager, device):
        try:
            ri = self.modem.iface["gsm.network"].GetRegistrationInfo()
            tech = self.modem.iface["gsm.network"]["AccessTechnology"]
            mode = self.get_technology()
            domain = self.get_domain()
            value = {
                "carrier_name": str(ri[2]),
                "carrier_code": str(ri[1]),
                "roaming": True if ri[0] == 5 else False,
                "network_mode": mode,
                "domain_mode": domain,
                "access_tech": int(tech),
            }
            self.emit(value)
        except:
            pass

    def is_operator_locked(self):
        return self.modem.IsOperatorLocked()

    def unlock_operator(self, unlock_code):
        try:
            return self.modem.UnlockOperator(unlock_code)
        except dbus.exceptions.DBusException, e:
            name = e.get_dbus_name()
            if name == 'org.freedesktop.ModemManager.Modem.Gsm.OperationNotAllowed':
                raise DeviceOperationNotAllowed()
            elif name == 'org.freedesktop.ModemManager.Modem.Gsm.IncorrectPassword':
                raise DeviceIncorrectPassword()
            else:
                raise e


class DeviceWLan(Device):
    type = DEVICE_WLAN

    def get_access_points(self):
        return self.nm_dev.GetAccessPoints()

    def get_active_access_point(self):
        aap = self.nm_dev["ActiveAccessPoint"]
        return freedesktopnet.networkmanager.accesspoint.AccessPoint(aap.object_path)

    def get_prettyname(self):
        return "WLan - %s" % self.nm_dev["Interface"]

    def mac(self):
        return self.nm_dev['HwAddress']

class DeviceWired(Device):
    type = DEVICE_WIRED

    def get_prettyname(self):
        return "Wired - %s" % self.nm_dev["Interface"]


class DeviceDialer(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'connecting'    : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE , ()) ,
        'connected'     : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE , ()) ,
        'disconnecting' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE , ()) ,
        'disconnected'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE , ()) ,
    }

    def __init__(self, device_manager):
        gobject.GObject.__init__(self)
        self._net_m = freedesktopnet.NetworkManager()
        self._conn_manager = ConnectionManager.ConnectionManager()
        self.device_manager = device_manager

        # -- Check if any interface is connected and call 'nmGetConnectionType()' for updating 'self.dev'
        self.dev = None
        self.nmGetConnectionType()
        self.updateConnectionStatus()

        self._disconnecting_dev = None
        self.connection_settings = None

        system_bus = dbus.SystemBus()
        system_bus.add_signal_receiver(self.print_state_changed, \
                "StateChanged", \
                "org.freedesktop.NetworkManager.Device", \
                path_keyword='path')

    def updateConnectionStatus(self):
        conn_state = self.nmConnectionState()
        if conn_state == NetworkManager.State.CONNECTED:
            tgcm.info ("Status connected")
            self._status = PPP_STATUS_CONNECTED;
            self.is_connected = True
            self.is_disconnected = False
            self.emit('connected')
        else:
            self._status = PPP_STATUS_DISCONNECTED
            self.is_connected = False
            self.is_disconnected = True

    def start(self, connection_settings, odev, disconnecting_device=None):
        self._disconnecting_dev = disconnecting_device
        self.dev = odev.nm_dev;
        self.connection_settings = connection_settings
        if (odev != None):
            try:
                if self.dev != self._disconnecting_dev:
                    self._connect()
                self.__change_status_emit_signal(PPP_STATUS_CONNECTING, 'connecting')
                return 0
            except:
                self.dev = None
                self.connection_settings = None
                return -1
        return -2

    def _connect(self):
        tgcm.debug("DeviceDialer start %s" % self.connection_settings["name"])
        self._status = PPP_STATUS_CONNECTING;
        self._net_m.ActivateConnection(self.connection_settings.get_nm_settings(), self.dev, "/")
        self._disconnecting_dev = None;

    def stop(self):
        devices_to_disconnect = []

        self.dev = None;
        self.connection_settings=None

        acs = self._net_m["ActiveConnections"]
        for connection in acs:
            devices_to_disconnect += connection["Devices"]

        self.__disconnect_devices(devices_to_disconnect)

    def stop_connection(self, conn_settings):
        active_connection = self._conn_manager.get_related_active_connection(conn_settings)
        devices_to_disconnect = []
        if active_connection is not None:
            for object_path in active_connection.Get(NetworkManagerDbus.NM_CONN_ACTIVE_IFACE, 'Devices'):
                device = freedesktopnet.networkmanager.device.Device(object_path)
                devices_to_disconnect.append(device)
            self.__disconnect_devices(devices_to_disconnect)

    def __disconnect_devices(self, devices):
        if(len(devices) == 0):
            return

        for device in devices:
            while device["state"] in range(networkmanager.device.Device.State.PREPARE,networkmanager.device.Device.State.ACTIVATED+1):
                device.Disconnect()
                time.sleep(0.1)

        self._status = PPP_STATUS_DISCONNECTED
        self.emit('disconnecting')
        self.is_connected = False
        self.is_disconnected = True
        tgcm.debug('DeviceDialer stop')

    def status(self):
        return self._status

    def nmConnectionState(self):
        state = self._net_m["State"]
        return state.value

    def get_current_conn_settings(self):
        if self.connection_settings is not None:
            return self.connection_settings

        try:
            selected_connection = None

            _cons = self._net_m["ActiveConnections"]
            for connection in _cons:
                selected_connection = connection
                if connection["Default"] == True:
                    break
            if selected_connection != None:
                connection_settings_nm = selected_connection["Connection"]
                _set = connection_settings_nm.GetSettings()
                uuid = str(_set["connection"]["uuid"])
                connection_settings_manager = ConnectionSettingsManager.ConnectionSettingsManager()
                self.connection_settings = connection_settings_manager.get_connection_by_uuid(uuid)
                if self.connection_settings == None:
                    print "@FIXME:  UUID not found at get_current_conn_settings , %s", uuid

            return self.connection_settings

        except IndexError:
            pass
        except Exception, err:
            print "@FIXME: Unexpected failure in get_current_conn_settings(), %s" % err

        return None

    def nmGetConnectionType(self):
        if self.dev is None:
            _acs = self._net_m["ActiveConnections"]
            for connection in _acs:
                if connection["Default"]==True:
                    self.dev = connection["Devices"][0]
                    break

        if self.dev is not None:
            return str(self.dev["DeviceType"])

        return None

    def is_modem(self):
        return (self.nmGetConnectionType() == "GSM")

    def is_wlan(self):
        return (self.nmGetConnectionType() == "WIRELESS")

    def ip_interface(self):
        if self.dev is None:
            raise IOError, 'No IP interface as no device connected yet'

        return self.dev['IpInterface']

    # -- IMPORTANT: First set the internal status and afterwards emit the signal!
    def __change_status_emit_signal(self, status, signal, *args):
        self.__status__ = status
        self.emit(signal, *args)

    # -- Parameters of this callback function from the NetworkManager specification:
    # -- StateChanged ( u: new_state, u: old_state, u: reason )
    def print_state_changed(self, *args,**kwargs):
        if (len(args) < 3):
            return

        new_state = int(args[0])
        old_state = int(args[1])
        reason = int(args[2])

        devpath = kwargs['path']
        if self.dev is not None:
            #We are monitoring a specific device
            if self.dev.object_path != devpath:
                #If the signal comes from a different device we ignore it
                return

#        if self.__is_NDIS_device(devpath):
#            return

        print "[%s] Device '%s' StateChanged() parameters: %s" % (time.strftime("%X"), devpath, ", ".join(map(str,args)))

        if (new_state == networkmanager.device.Device.State.ACTIVATED):
            self.__change_status_emit_signal(PPP_STATUS_CONNECTED, 'connected')

#        elif (old_state == 70) and (new_state == 120) and (reason == 5):
#            if self.is_modem():
#                tgcm.debug("Probably fatal error detected. Removing device %s" % devpath)
#                self.device_manager.remove_device_on_fatal_error(devpath)
#                self.dev = None
#                self.connection_settings = None
#            else:
#                self.__change_status_emit_signal(PPP_STATUS_DISCONNECTED, 'disconnected')
#
#        elif (old_state == 120) and (new_state == 30) and (reason == 0):
#            # Do nothing
#            pass

        elif (new_state in range(networkmanager.device.Device.State.PREPARE, networkmanager.device.Device.State.IP_CONFIG + 1)):
            if self.nmConnectionState() != NetworkManager.State.CONNECTED:
                # -- Emit the connecting signal only one time
                if (old_state not in range(networkmanager.device.Device.State.PREPARE, networkmanager.device.Device.State.IP_CONFIG)):
                    self.__change_status_emit_signal(PPP_STATUS_CONNECTING, 'connecting')

        elif ((new_state == networkmanager.device.Device.State.DISCONNECTED or
              new_state == networkmanager.device.Device.State.UNAVAILABLE) and
              not (old_state == networkmanager.device.Device.StateReason.CONFIG_EXPIRED and
                   reason != networkmanager.device.Device.StateReason.USER_REQUESTED)):

            if self.nmConnectionState() != NetworkManager.State.CONNECTED:

                if self._disconnecting_dev is not None and self.connection_settings is not None:
                    #The device needs 2 seconds to be up&ready
                    time.sleep(2)
                    self._connect()
                    return

                self.dev = None;
                self.connection_settings = None
                self.__change_status_emit_signal(PPP_STATUS_DISCONNECTED, 'disconnected')
            else:
                self.dev = None;
                self.connection_settings = None
                self.__change_status_emit_signal(PPP_STATUS_CONNECTED, 'connected')

        elif (new_state == networkmanager.device.Device.State.UNMANAGED and
             (reason == networkmanager.device.Device.StateReason.REMOVED or reason == networkmanager.device.Device.StateReason.SLEEPING)):
            self.dev = None;
            self.connection_settings = None
            if self.nmConnectionState() != NetworkManager.State.CONNECTED:
                self.__change_status_emit_signal(PPP_STATUS_DISCONNECTED, 'disconnected')
            else:
                self.__change_status_emit_signal(PPP_STATUS_CONNECTED, 'connected')



        else:
            print "@FIXME: Unhandled device state change (state = %i, reason = %i)" % (new_state, reason)

    def __is_NDIS_device(self,devpath):
        for nm_dev in self._net_m.GetDevices():
            if str(nm_dev.object_path) == str(devpath):
                return Device.is_NDIS_device(nm_dev)

        return False;

gobject.type_register(DeviceManager)
gobject.type_register(DeviceDialer)
