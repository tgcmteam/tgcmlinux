#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
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
import time
import webbrowser

import tgcm
import tgcm.core.Config
import tgcm.core.Connections
import tgcm.core.ConnectionLogger
import tgcm.core.ConnectionSettingsManager
import tgcm.core.Messaging
import tgcm.core.FreeDesktop
import tgcm.core.MainModem
import tgcm.core.Singleton

import tgcm.ui
import tgcm.ui.MSD

from MSDMessages import *

from tgcm.ui.MSD.MSDUtils import gtk_builder_magic, gtk_sleep, error_dialog, warning_dialog

from MobileManager import CARD_STATUS_READY, PPP_STATUS_DISCONNECTED
from MobileManager.MobileManagerDbus import MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI
from freedesktopnet.networkmanager.networkmanager import NetworkManager

STATUS_MESSAGES = [_("Disconnected"),_("Connected"),_("Connecting"),_("Disconnecting")]
BUTTON_TITLES = [_("Connect"),_("Disconnect"),_("Connect"),_("Disconnect")]


class MSDConnectionsManager:
    __metaclass__ = tgcm.core.Singleton.Singleton

    def __init__(self):
        self._connection_manager = tgcm.core.Connections.ConnectionManager()
        self._connection_settings_manager = tgcm.core.ConnectionSettingsManager.ConnectionSettingsManager()
        self._conf = tgcm.core.Config.Config ()
        self._conn_logger = tgcm.core.ConnectionLogger.ConnectionLogger()
        self._messaging_manager = tgcm.core.Messaging.MessagingManager()
        self._action_manager = tgcm.core.Actions.ActionManager()
        self.security_manager = tgcm.ui.MSD.MSDSecurityManager()
        self.mcontroller = tgcm.core.FreeDesktop.DeviceManager()

        self.abort_now_flag = None
        self.cardmanager = None
        self.actual_connection = None

        self.waiting_connection = None
        self.starting_connection = None
        self.connection_successful = None
        self.url = None
        self.action = None
        self.bookmark_info = None
        self.smart_connector = False

        self.reconnect_on_disconnect = False
        self.is_in_first_reconnection_with_smart_connector=False

        #Ask pass dialog
        gtk_builder_magic(self, \
                filename=os.path.join(tgcm.msd_dir, 'MSDConnectionsManager_dialog.ui'),
                prefix='ask')

        self.pass_entry.connect("changed", self.__ask_pass_entry_cb, None)

        self.connect_to_bus()

    def connect_to_bus (self):
        success = self._connection_manager.connect_to_bus(self)
        if not success:
            tgcm.error("No se ha encontrado el ppp manager")
            error_dialog(markup=MSG_CONN_MANAGER_NO_PPP_MANAGER_TITLE, \
                    msg=MSG_CONN_MANAGER_NO_PPP_MANAGER)
            return False
        else:
            return True

    def __ask_pass_entry_cb (self, editable, data):
        if len (self.pass_entry.get_text()) > 0:
            self.pass_ok_button.set_sensitive(True)
        else:
            self.pass_ok_button.set_sensitive(False)
    """
    def get_connection_params(self, conn):
        if conn == None:
            conn_name = self._connection_manager.get_default_connection_name()
        else:
            conn_name = conn

        conn_info = self._connection_manager.get_connection_info(conn_name)

        password = None
        if conn_info["ask_password"] == True:
            password = self._ask_password (conn_name)
            password = tgcm.ui.MSD.MSDUtils.encode_password (password)

        return self._connection_manager.get_connection_params (conn_name, password)
    """
    def _ask_password (self, conn_name):
        self.pass_entry.set_text("")
        self.pass_ok_button.set_sensitive(False)
        self.pass_label.set_markup(MSG_CONN_MANAGER_ASK_PASSWORD % conn_name)

        ret = self.pass_dialog.run()
        if ret == gtk.RESPONSE_OK:
            password = self.pass_entry.get_text()
            self.pass_dialog.hide()

            return password
        else:
            self.pass_dialog.hide()
            return None

    def do_connect_with_smart_connector(self, bookmark_info = None, action = None, \
            url = None, skip_connection_index = None):
        self.skip_connection_index_on_reconnect=skip_connection_index
        self.connection_index=-1
        self.__connect_with_smart_connector(bookmark_info, action, url)

    def __connect_with_smart_connector(self, bookmark_info = None, action = None, url = None):
        try:

            if self._connection_manager.ppp_manager.nmConnectionState() == NetworkManager.State.DISCONNECTED:
                ret=-1
                while ret==-1:
                    conn_settings=self._get_next_connection()
                    if conn_settings==None:
                        self.error_on_connection()
                        ret=-2
                    else:
                        ret = self.connect_to_connection(connection_settings = conn_settings, \
                                smart_connector = True, bookmark_info = bookmark_info, \
                                action = action, url = url)

                    if ret==0:
                        self.__t_connection_name = conn_settings["name"]
        except:
            pass

    def _get_next_connection(self):
        self.connection_index=self.connection_index+1
        if self.connection_index==self.skip_connection_index_on_reconnect:
            self.connection_index=self.connection_index+1

        return self._connection_settings_manager.get_connection_by_index(self.connection_index)


    # Return :
    #   - 0 if everything is ok
    #   - -1 if the connection failed but we can try the next one
    #   - -2 if the connection failed and need to show a error dialog
    def connect_to_connection(self, connection_settings = None, force_connection = False, \
                action = None, bookmark_info = None, url = None, smart_connector = False):
        self.abort_now_flag = False
        self.smart_connector=smart_connector
        device_type=connection_settings["deviceType"]
        connection_name=connection_settings["name"]
        tgcm.info("Trying to connect to %s" % connection_name)
        if self.connect_to_bus() != True:
            return -1

        network_connection_status = self._connection_manager.ppp_manager.nmConnectionState()

        if (device_type==tgcm.core.FreeDesktop.DEVICE_WLAN or device_type==tgcm.core.FreeDesktop.DEVICE_WLAN_PROFILE):
            odev = self.mcontroller.get_wifi_device()
            if odev == None:
                return -1
            if self._connection_settings_manager.is_wifi_ap_available(connection_settings)==False:
                return -1

        if (device_type==tgcm.core.FreeDesktop.DEVICE_WIRED):
            odev = self.mcontroller.get_wired_device()
            if odev == None:
                return -1

        elif (device_type==tgcm.core.FreeDesktop.DEVICE_MODEM):

            if self._connection_manager.is_device_selected() == False:
                return -1

            odev = self.mcontroller.get_main_device()

            if odev.get_card_status() is not CARD_STATUS_READY:
                return -1

            if odev == None or odev.get_type() != tgcm.core.DeviceManager.DEVICE_MODEM:
                self.show_no_available_device_error()
                return -1

            if odev.is_roaming() and  bool(self._conf.check_policy('show-roaming-warning')):
                if tgcm.country_support == "es":
                    message = _("You are about to connect you in roaming and your customary data fares do not apply for the traffic that consummate abroad. Inform yourself of your roaming data fares in the 22119 (free call cost in the European Union; from other countries applicable price to calls with destination Spain according to roaming fare of the line). To control your bill you can define alerts in Escritorio Movistar and will receive notifications when reaching a certain amount of data spent.")
                else:
                    message = _("You're about to connect while abroad. Network operators have different charges for data usage and costs can soon mount up. To set up alerts so you know approximately how much data you have used go to Settings / Alerts.")
                title = _("Roaming alert")
                response = warning_dialog(msg=message, title=title)
                if response != gtk.RESPONSE_OK:
                    return -2

            if not odev.has_capability(MOBILE_MANAGER_DEVICE_STATE_INTERFACE_URI) :
                self.cardmanager = None
            else:
                self.cardmanager = odev
                if network_connection_status == PPP_STATUS_DISCONNECTED:
                    if self.cardmanager.get_card_status() != CARD_STATUS_READY:
                        if smart_connector == False:
                            error_dialog(markup=MSG_CONN_MANAGER_NO_CARDMANAGER_TITLE, \
                                    msg=MSG_CONN_MANAGER_NO_CARDMANAGER)
                        return -1

        if action != None:
            self.action = action

        if bookmark_info != None:
            self.bookmark_info = bookmark_info

        if url != None:
            self.url = url

        if network_connection_status == NetworkManager.State.CONNECTED :
            if self.actual_connection is not None and connection_settings["uuid"]==self.actual_connection["uuid"]:
                self.launch_service()
                return 0

            if force_connection == False:
                ret = self.__detect_active_connection_dialog(connection_name, action, bookmark_info)
            else:
                ret = 3

            if ret == 1 or ret < 0:
                return 0 #Cancelled by the user
            elif ret == 2 :
                self.launch_service()
                return 0
            elif ret == 3:
                self._connection_manager.ppp_manager.stop()
                gtk_sleep(0.1);
                self.waiting_connection = connection_settings


        self.reconnect_on_disconnect=None

        password=None
        if connection_settings["ask_password"] == True:
            password = self._ask_password (connection_name)
            if password is None:
                return 0 #Cancelled by the user


        #Reload connection info from gconf based on SIM characteristics
        try:
            if (connection_settings["origin"]!="networkmanager" or connection_settings["ask_password"]==True):
                connection_settings=self._connection_settings_manager.get_connection_info_dict_from_gconf(connection_settings['gconf_path'])
                self._connection_settings_manager.add_wwan_connection(connection_settings,write_gconf_if_required=False,update_if_possible=True,password=password)
                gtk_sleep(1.5);
                #time.sleep(1) #We must give some time to update the connection

        except (RuntimeError, TypeError, NameError):
            tgcm.error("Error in update")
            pass


        self._conf.set_proxy(connection_settings)

        ret=self._connection_manager.ppp_manager.start(connection_settings,odev)
        if ret!=0:
            self.action = None
            self.bookmark_info =None

        return ret



    def disconnect(self):
        self._connection_manager.disconnect()

    def disconnect_from_connection(self, conn_settings):
        self._connection_manager.disconnect_from_connection(conn_settings)

    # -- Returns True if the application should be closed
    def close_app(self):
        _close = True
        main_modem = tgcm.core.MainModem.MainModem()
        if main_modem.is_connected():
            app_name = self._conf.get_app_name()
            response = warning_dialog( \
                    msg=MSG_CONN_MANAGER_APP_CLOSE % (app_name, app_name), \
                    title=MSG_CONN_MANAGER_APP_CLOSE_TITLE, \
                    buttons=gtk.BUTTONS_OK_CANCEL)

            # -- If the user responds with OK we will close the application
            # -- even some failures are detected. This is the behavior under
            # -- windows too.
            if response == gtk.RESPONSE_OK:
                # -- Avoid the automatic reconnection as we are going to exit
                self.reconnect_on_disconnect = False

                # -- Get the reference to the NM object for disconnecting correctly
                nm_dev = main_modem.current_device().nm_dev
                nm_dev.Disconnect()

                # -- Wait until the modem is off but use a timeout for the worst case!
                time_start = time.time()
                timeout = 10  # -- Arbitrary timeout value
                time_end = (time_start + timeout)
                while (time_end > time.time()) and (main_modem.is_connected()):
                    while gtk.events_pending():
                        gtk.main_iteration()

                # -- If the modem is still connected we have a problem. In that
                # -- case show an error message but go ahead closing
                # -- the Tgcm so that the user disconnects the modem manually
                if main_modem.is_connected():
                    if tgcm.country_support == 'de':
                        msgInfo=_("Please try removing the Mobile Internet Device for assuring\nthat the WWAN connection is down.")
                    else:
                        msgInfo=_("Please try removing the Mobile Internet Device for assuring\nthat the 2G/3G/4G connection is down.")

                    error_dialog(markup=_("Unexpected disconnection failure"), \
                            msg=msgInfo)
                else:
                    main_modem.turn_off()

                _close = True
            else:
                _close = False
        else:
            main_modem.turn_off()
            _close = True

        return _close

    def show_no_available_device_error(self):
        error_dialog(markup=MSG_CONN_MANAGER_NO_CARDMANAGER_TITLE, \
                msg=MSG_CONN_MANAGER_NO_CARDMANAGER)

    def error_on_connection(self):
        self.reconnect_on_disconnect = False
        error_dialog(markup=MSG_CONN_MANAGER_CONNECTION_ERROR_TITLE, \
                msg=MSG_CONN_MANAGER_CONNECTION_ERROR)

    def launch_service(self):
        if self.url != None:
            webbrowser.open(self.url)
            self.url = None

        if self.action != None:
            self.action.launch_action()
            self.action = None

        if self.bookmark_info != None:
            if self.bookmark_info.url.startswith ("file:") or self.bookmark_info.url.startswith ("http:"):
                if self.bookmark_info.userdata == 1:
                    self.security_manager.launch_url(self.bookmark_info.url)
                else:
                    webbrowser.open(self.bookmark_info.url)
            else:
                webbrowser.open("http://%s " % self.bookmark_info.url)

            self.bookmark_info = None

    def abort_connection_now(self):
        self.__abort_connection_now()

    def __abort_connection_now(self):
        # Register cancel attempt
        self._conn_logger.register_cancel(self.actual_connection)

        self._connection_manager.ppp_manager.stop()
        self.abort_now_flag = True

    def __abort_connection_actions(self):
        self.action = None
        self.bookmark_info = None
        self.actual_connection = None
        self.starting_connection = None
        self.connection_successful = False
        self.waiting_connection = None
        #self.abort_now_flag = False

    def _connected_cb(self, dialer):
        if self.abort_now_flag == True:
            self.__abort_connection_actions()
            tgcm.debug("CONNECTED (Aborted)")
            return

        #self.actual_connection = self.starting_connection
        self.actual_connection = dialer.get_current_conn_settings()
        self.starting_connection = None
        self.launch_service()

        # Log connection attempt
        self._conn_logger.register_connection_attempt(self.actual_connection)

        tgcm.debug("CONNECTED ---> %s" % self.actual_connection["name"])
        self.connection_successful = True
        if self.reconnect_on_disconnect==None:
            self.reconnect_on_disconnect=self._conf.get_reconnect_on_disconnect()

    def _connecting_cb(self, dialer):
        if self.abort_now_flag == True:
            self.__abort_connection_actions()
            self.abort_now_flag == False
            self.connection_successful = False
            tgcm.debug("CONNECTING (Aborted)")
            return

        tgcm.debug("CONNECTING ---> %s" % self.starting_connection)
        self.connection_successful = False

    def _disconnecting_cb(self, dialer):
        self.reconnect_on_disconnect=False

    def _disconnected_cb(self, dialer):
        # Log disconnection attempt
        self._conn_logger.register_disconnection_attempt(self.actual_connection)

        if self.connection_successful == False:
            if self.abort_now_flag == True:
                self.__abort_connection_actions()
                self.abort_now_flag == False
                self.reconnect_on_disconnect=False
                tgcm.debug("DISCONNECTED (Aborted)")
                return

            self.actual_connection = None
            self.waiting_connection = None
            self.connection_successful = None

            if self.is_in_first_reconnection_with_smart_connector:
                self.is_in_first_reconnection_with_smart_connector=False
                self.do_connect_with_smart_connector(skip_connection_index=self.connection_index)
                return

            if self.smart_connector==False:
                self.error_on_connection()
            else:
                #self.connection_zone.do_connect_with_smart_connector()
                self.__connect_with_smart_connector()


        else:
            self.is_in_first_reconnection_with_smart_connector=False
            self.reconnect_on_disconnect=self.reconnect_on_disconnect and self._conf.get_reconnect_on_disconnect()
            if self.reconnect_on_disconnect:
                if self.smart_connector==True:
                    tgcm.info("Trying reconnect with smart_connector %s" % self.actual_connection['name'])
                    if (self.connect_to_connection(connection_settings=self.actual_connection,smart_connector=True)==0):
                        self.is_in_first_reconnection_with_smart_connector=True
                    else:
                        self.do_connect_with_smart_connector(skip_connection_index=self.connection_index)

                else:
                    tgcm.info("Reconnect to connection")
                    self.connect_to_connection(connection_settings=self.actual_connection,smart_connector=False)

            else:
                self.actual_connection = None
                if self.abort_now_flag == True:
                    self.__abort_connection_actions()
                    self.abort_now_flag == False
                    tgcm.debug("DISCONNECTED (Aborted)")
                    return

        tgcm.debug("DISCONNECTED ---")

    def __detect_active_connection_dialog(self, connection_name, action, bookmark_info):
        tgcm.info("detect-connection-dialog")
        if self._connection_manager.get_ask_before_change_connection() == False:
            return 3

        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO)
        dlg.set_markup (MSG_CONN_MANAGER_ACTIVE_CONN_DETECT_TITLE)
        vbox = dlg.vbox
        check_button = gtk.CheckButton(_("Do not show this dialogue again"))
        vbox.pack_end(check_button, expand=False)
        check_button.hide()

        if connection_name == None or connection_name == self._connection_manager.get_default_connection_name():
            if action != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_SERVICE_TITLE % action.get_visible_action_name())
                dlg.format_secondary_markup (MSG_CONN_MANAGER_OPEN_SERVICE_WITH_ACTIVE_CONN_DEFAULT % (self.actual_connection["name"], self._connection_manager.get_default_connection_name()))

            if bookmark_info != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_BOOKMARK_TITLE % bookmark_info.name)
                dlg.format_secondary_markup (MSG_CONN_MANAGER_OPEN_BOOKMARK_WITH_ACTIVE_CONN_DEFAULT  % (self.actual_connection["name"], self._connection_manager.get_default_connection_name()))

            if action == None and bookmark_info == None:
                dlg.set_markup(MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_TITLE)
                dlg.format_secondary_markup (MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_WITH_ACTIVE_CONN % (self.actual_connection["name"], self._connection_manager.get_default_connection_name()))
        else:
            if action != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_SERVICE_TITLE % action.get_visible_action_name())
                dlg.format_secondary_markup (MSG_CONN_MANAGER_OPEN_SERVICE_WITH_ACTIVE_CONN % (self.actual_connection["name"], connection_name))
            if bookmark_info != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_BOOKMARK_TITLE % bookmark_info.name)
                dlg.format_secondary_markup (MSG_CONN_MANAGER_OPEN_BOOKMARK_WITH_ACTIVE_CONN % (self.actual_connection["name"], connection_name))

        dlg.add_buttons(gtk.STOCK_CANCEL, 1, _("_Use established connection"), 2, gtk.STOCK_CONNECT, 3)
        ret = dlg.run()
        dlg.destroy()

        if ret > 1 :
            self._connection_manager.set_ask_before_change_connection(not check_button.get_active())

        return ret

    def __new_connection_active_dialog(self, connection_name, action, bookmark_info):
        tgcm.info("new-connection-dialog")
        if action == None and bookmark_info == None:
            if self._connection_manager.get_ask_before_connect() == False:
                return 2
        else:
            if self._connection_manager.get_ask_before_connect_to_action() == False:
                return 2

        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO)
        vbox = dlg.vbox
        check_button = gtk.CheckButton(_("Do not ask again"))
        vbox.pack_end(check_button, expand=False)
        check_button.set_property("has-focus", False)
        check_button.set_property("has-default", False)
        check_button.set_property("can-focus", False)
        check_button.set_property("can-default", False)
        check_button.show()

        if connection_name == None:
            if action != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_SERVICE_TITLE % action.get_visible_action_name())

            if bookmark_info != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_BOOKMARK_TITLE % bookmark_info.name)

            if action == None and bookmark_info == None:
                dlg.set_markup(MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_TITLE)

            message = self._connection_manager.get_default_connection_name()
            if message == "None":
                message = ""
            dlg.format_secondary_markup (MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_CONN % message)
        else:
            if action != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_SERVICE_TITLE  % action.get_visible_action_name())
                dlg.format_secondary_markup (MSG_CONN_MANAGER_OPEN_SERVICE  % connection_name)
            if bookmark_info != None:
                dlg.set_markup (MSG_CONN_MANAGER_OPEN_BOOKMARK_TITLE % bookmark_info.name)
                dlg.format_secondary_markup (MSG_CONN_MANAGER_OPEN_BOOKMARK % connection_name)
            if action == None and bookmark_info == None:
                dlg.set_markup(MSG_CONN_MANAGER_CONNECT_TO_CONN_TITLE)
                dlg.format_secondary_markup (MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_CONN % connection_name)

        dlg.add_buttons(gtk.STOCK_CANCEL, 1, gtk.STOCK_CONNECT, 2)
        dlg.set_default_response(2)
        ret = dlg.run()
        dlg.destroy()

        if action == None and bookmark_info == None:
            if ret > 1:
                self._connection_manager.set_ask_before_connect(not check_button.get_active())
        else:
            if ret > 1:
                self._connection_manager.set_ask_before_connect_to_action(not check_button.get_active())

        return ret
