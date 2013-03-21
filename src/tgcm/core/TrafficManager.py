#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           Luis Galdos <luisgaldos@gmail.com>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2003-2011, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import os
import glib
import gobject
import gtk
import thread
import threading
import datetime
import time

import tgcm
import Config
import FreeDesktop
import Notify
import Singleton
import TrafficStorage
import TrafficUpdater

def _gtk_wait(time_lapse):
    time_start = time.time()
    time_end = (time_start + time_lapse)

    while time_end > time.time():
        while gtk.events_pending():
            gtk.main_iteration()


class TrafficManager(gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'update-instant-velocity' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)) ,
        'reset-instant-velocity'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( )) ,
        'update-session-time' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)) ,

        'update-session-data-transfered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)) ,
        'reset-session-data-transfered'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( )) ,

        'update-session-max-speed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)) ,
        'reset-session-max-speed'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( )) ,

        # data_used, data_used_roaming, data_limit, billing_period
        'traffic-data-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, \
            (gobject.TYPE_INT64, gobject.TYPE_INT64, gobject.TYPE_INT64, gobject.TYPE_PYOBJECT)),

        'billing-period-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ( )),

        'update-expenses-info' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)) ,
        'update-roaming-expenses-info' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)) ,
    }

    SESSION_TIME_INIT  = 0
    SESSION_TIME_START = 1
    SESSION_TIME_STOP  = 2
    SESSION_TIME_RESET = 3
    SESSION_TIME_EXIT  = 4

    MONITORING_IDLE = 0
    MONITORING_3G   = 1
    MONITORING_WIFI = 2

    def __init__(self) :
        gobject.GObject.__init__(self)
        self._device_manager = FreeDesktop.DeviceManager()
        self.conf = Config.Config(tgcm.country_support)
        self.notify = Notify.Notify()
        self.__updater    = TrafficUpdater.TrafficUpdater()
        self.__main_modem = FreeDesktop.MainModem.MainModem()
        self.__main_wifi  = FreeDesktop.MainWifi.MainWifi()

        # FIXME: Usually it is a bad idea to have a dependency to a UI element in the Core
        self.__dock       = tgcm.ui.ThemedDock()

        #TrafficHistoryGraphData
        db_file = os.path.join(tgcm.config_dir, "traffic-%s.db" % tgcm.country_support)
        self._storage = TrafficStorage.TrafficStorage(self.conf, db_file)

        self.is_roaming = None

        # Billing period related expenses
        self._cached_expenses = {}
        self._cached_monthly_limit = {}
        self._cached_billing_period = None

        # Session related expenses
        self.session_data_transfered = 0
        self.session_max_speed = 0

        # Various
        self.last_received_bytes = 0
        self.last_sent_bytes = 0
        self.__monitoring = self.MONITORING_IDLE

        ## Check if a billing period has expired between now and the latest execution ##
        # The only thing necessary that needs to be reset is the SMS counters, because
        # unlike the traffic accounting, it is saved in a incremental register in GConf.
        if self.conf.is_last_imsi_seen_valid():
            imsi = self.conf.get_last_imsi_seen()
            billing_period = self.conf.get_imsi_based_billing_period(imsi)

            # The billing period is a list of Date objects, and the last execution is a
            # Datetime object. In order to compare them, it is necessary to convert the
            # first date of the billing period from Date to Datetime
            last_execution = self.conf.get_last_execution_datetime()
            first_day_period = datetime.datetime.combine(billing_period[0], datetime.time())

            # If the date time of the last execution is older than the date of the first
            # day of current billing period, I assume that there have been a billing period
            # change and it is necessary to reset the SMS counters
            if last_execution < first_day_period:
                self.__reset_sms_counters(imsi)

        # Configure current traffic history
        self.__billing_period_change_event = None
        self.__start_traffic_history()

        # Create alert list for current recognized IMSI
        self.__create_current_alerts()

        # -- Signals from the MainModem for detecting the connected/disconnected signals
        self.__main_modem.connect('main-modem-connected'    , self.__main_modem_connected_cb)
        self.__main_modem.connect('main-modem-disconnected' , self.__main_modem_disconnected_cb)
        self.__main_wifi.connect('main-wifi-connected'      , self.__main_wifi_connected_cb)
        self.__main_wifi.connect('main-wifi-disconnected'   , self.__main_wifi_disconnected_cb)

        self.__updater.connect("traffic-updater-trigger", self.__traffic_updater_trigger_cb)

        self.conf.connect('last-imsi-seen-changed', self.__on_last_imsi_changed)
        self.conf.connect('billing-day-changed', self.__on_billing_day_changed)
        self.conf.connect('monthly-limit-changed', self.__on_monthly_limit_changed)
        self.conf.connect('alerts-info-changed', self.__on_alerts_changed)
        self.__dock.connect('app-closing',self.__on_app_close)

        # -- Start the thread that will update the session time
        self.__session_time_event = threading.Event()
        self.__session_time_state = self.SESSION_TIME_INIT
        thread.start_new_thread(self.__session_time_thread, ( ))
        glib.idle_add(self.__init)

    # -- We don't need to check for the main modem as it emits a delayed signal during the init
    def __init(self):
        if self.__main_wifi.is_connected():
            self.__main_wifi_connected_cb(self.__main_wifi, self.__main_wifi.current_device())

    def get_storage(self):
        return self._storage

    def get_current_traffic_data(self):
        '''
        Method to synchronously get the traffic data related to the current session
        '''
        traffic_data = {}
        traffic_data['data_used'] = self._cached_expenses[False]['total']         # NOT roaming
        traffic_data['data_used_roaming'] = self._cached_expenses[True]['total']  # roaming
        traffic_data['data_limit'] = self._cached_monthly_limit[False]            # NOT roaming
        traffic_data['billing_period'] = self._cached_billing_period
        return traffic_data

    def reset_history(self, imsi):
        for is_roaming in (True, False):
            self._storage.reset(imsi, is_roaming)
        self.refresh_traffic_history()
        self.__reset_sms_counters(imsi)


    #CALLBACKS
    #----------------------------------------------

    def __start_session_widgets(self, monitor):
        self.__start_session_time()
        self.__start_session_data_transfered()
        self.__monitoring = monitor

    def __stop_session_widgets(self):
        # -- Wait until the already emitted signals are done so we reset all the widget afterwards
        self.__updater.stop()
        self.__stop_session_time()
        _gtk_wait(1.5)

        self.last_received_bytes = 0
        self.last_sent_bytes = 0
        self.is_roaming = None
        self.__monitoring = self.MONITORING_IDLE

        self.__reset_instant_velocity()
        self.__reset_session_max_speed()
        self.__stop_session_time()
        self.__reset_session_data_transfered()

    def __main_modem_connected_cb(self, handler, main_modem, devpath):
        # -- If the Wif is monitored, need to reset all the session widgets
        if self.__monitoring == self.MONITORING_WIFI:
            self.__stop_session_widgets()
            self.__start_session_widgets(self.MONITORING_3G)
        else:
            self.__start_session_widgets(self.MONITORING_3G)

        #print "----> Starting monitor 3G"
        self.__start_traffic_history()
        self.__updater.start()

    def __main_modem_disconnected_cb(self, handler, main_modem, devpath):
        if self.__monitoring == self.MONITORING_3G:
            #print "----> Stopping monitor 3G"
            self.__stop_session_widgets()
            self.__end_traffic_history()

            # -- Check if a wifi is enabled, in that case need to monitor it
            if self.__main_wifi.is_connected():
                # -- Give the widgets some time to refresh
                _gtk_wait(1)
                self.__main_wifi_connected_cb(self.__main_wifi, self.__main_wifi.current_device())

    def __main_wifi_connected_cb(self, handler, main_wifi):
        # -- If there is a 3G connections skip the Wifi traphic monitoring
        if self.__monitoring != self.MONITORING_3G:
            #print "----> Starting to monitor wifi"
            self.__start_session_widgets(self.MONITORING_WIFI)
            self.__updater.start()

    def __main_wifi_disconnected_cb(self, handler, main_wifi):
        if self.__monitoring == self.MONITORING_WIFI:
            #print "----> Stopping to monitor wifi"
            self.__stop_session_widgets()

    def __traffic_updater_trigger_cb(self, updater, i_time):
        if self.__monitoring == self.MONITORING_3G:
            dev = self.__main_modem.current_device()
        else:
            dev = self.__main_wifi.current_device()

        try:
            name = dev.nm_dev['IpInterface']
            iface = updater.iface(name)
            r_bytes = iface.rx.last()
            s_bytes = iface.tx.last()
        except TrafficUpdater.TrafficUpdaterError:
            updater.stop()
            return

        self.__update_session_data_transfered(updater, r_bytes, s_bytes, i_time)
        self.__update_session_max_speed(updater, r_bytes, s_bytes, i_time)
        self.__update_instant_velocity(iface, r_bytes, s_bytes, i_time)

        if self.__monitoring == self.MONITORING_3G:
            self.__update_traffic_history(updater, r_bytes, s_bytes, i_time)
            self.__update_alerts()

        self.last_received_bytes = r_bytes
        self.last_sent_bytes     = s_bytes


    #UTILS
    #----------------------------------------------
    def _is_roaming(self):
        if self.is_roaming != None:
            return self.is_roaming

        dev = self._device_manager.get_main_device()
        if dev != None :
            self.is_roaming = dev.is_roaming()
            return self.is_roaming

        return False

    def __get_transfer_deltas(self, r_bytes, s_bytes):
        received_delta = r_bytes - self.last_received_bytes
        sent_delta = s_bytes - self.last_sent_bytes
        if received_delta < 0 :
            received_delta = 0
        if sent_delta < 0 :
            sent_delta = 0

        return received_delta, sent_delta

    def __seconds2HMS(self, seconds):
        seconds = int(seconds)
        hours = seconds / 3600
        seconds -= 3600 * hours
        minutes = seconds / 60
        seconds -= 60 * minutes
        return hours, minutes, seconds

    #Session Data Transfered methods
    #----------------------------------------------
    def __start_session_data_transfered(self):
        self.session_data_transfered = 0
        self.emit('update-session-data-transfered', self.session_data_transfered)

    def __reset_session_data_transfered(self):
        self.session_data_transfered = 0
        self.emit('update-session-data-transfered', self.session_data_transfered)
        self.emit('reset-session-data-transfered')

    def __update_session_data_transfered(self, updater, r_bytes, s_bytes, i_time):
        r_delta, s_delta = self.__get_transfer_deltas(r_bytes, s_bytes)
        self.session_data_transfered = self.session_data_transfered + r_delta + s_delta
        self.emit('update-session-data-transfered', self.session_data_transfered)

    def __update_session_max_speed(self, updater, r_bytes, s_bytes, i_time):
        r_delta, s_delta = self.__get_transfer_deltas(r_bytes, s_bytes)
        speed = float(r_delta) / i_time
        if speed > self.session_max_speed and self.last_received_bytes:
            self.session_max_speed = speed
        self.emit('update-session-max-speed', self.session_max_speed)

    def __reset_session_max_speed(self):
        self.session_max_speed = 0
        #self.emit("update-session-max-speed", 0)
        self.emit('reset-session-max-speed')

    # -- This thread emits the signal for the session time
    def __session_time_thread(self):
        _running = False
        gobject.idle_add(self.emit, 'update-session-time', 0, 0, 0)

        while True:
            # -- Wait for 250ms and send the new session time
            self.__session_time_event.wait(0.250)

            if self.__session_time_event.is_set():
                self.__session_time_event.clear()

                if self.__session_time_state == self.SESSION_TIME_START:
                    _running = True
                    _start_time = time.time()

                elif self.__session_time_state == self.SESSION_TIME_STOP:
                    _running = False
                    gobject.idle_add(self.emit, 'update-session-time', 0, 0, 0)

                elif self.__session_time_state == self.SESSION_TIME_RESET:
                    _running = True
                    gobject.idle_add(self.emit, 'update-session-time', 0, 0, 0)
                    continue

                elif self.__session_time_state == self.SESSION_TIME_EXIT:
                    return

            # -- Calculate the new session time if running
            if _running is True:
                _delta = time.time() - _start_time
                h, m, s = self.__seconds2HMS(_delta)
                gobject.idle_add(self.emit, 'update-session-time', h, m, s)

    #Session Time Data methods
    #----------------------------------------------
    def __start_session_time(self):
        self.__session_time_state = self.SESSION_TIME_START
        self.__session_time_event.set()

    def __stop_session_time(self):
        self.__session_time_state = self.SESSION_TIME_STOP
        self.__session_time_event.set()

    def __reset_session_time(self):
        self.__session_time_state = self.SESSION_TIME_RESET
        self.__session_time_event.set()

    #Velocity Data methods
    #----------------------------------------------
    def __update_instant_velocity(self, iface, r_bytes, s_bytes, i_time) :
        rx_rate = float(iface.rx.delta()) / i_time
        tx_rate = float(iface.tx.delta()) / i_time
        self.emit('update-instant-velocity', rx_rate, tx_rate)

    def __reset_instant_velocity(self):
        self.emit('reset-instant-velocity')

    #Traffic History Methods
    #----------------------------------------------

    def refresh_traffic_history(self):
        self.__start_traffic_history()
        self.__create_current_alerts()

    def __start_traffic_history(self):
        '''
        This method creates the necessary data structures to manage the expenses
        of current connection
        '''
        # Get some IMSI dependent data, like monthly limits, billing_period, etc.
        imsi = self.conf.get_last_imsi_seen()
        if not self.conf.is_last_imsi_seen_valid():
            self._cached_billing_period = self.conf.get_default_billing_period()
            for is_roaming in (True, False):
                monthly_limit = self.conf.get_default_selected_monthly_limit(is_roaming)
                self._cached_monthly_limit[is_roaming] = monthly_limit * 1024 * 1024    # calculate it in bytes
        else:
            self._cached_billing_period = self.conf.get_imsi_based_billing_period(imsi)
            for is_roaming in (True, False):
                monthly_limit = self.conf.get_imsi_based_selected_monthly_limit(imsi, is_roaming)
                if monthly_limit == -1:     # Is it a custom monthly limit?
                    monthly_limit = self.conf.get_imsi_based_other_monthly_limit(imsi, is_roaming)
                self._cached_monthly_limit[is_roaming] = monthly_limit * 1024 * 1024    # calculate it in bytes

        # Calculate the expenses for current billing period
        first_day = self._cached_billing_period[0]
        last_day = self._cached_billing_period[1]
        for is_roaming in (True, False):
            self._cached_expenses[is_roaming] = self._storage.get_accumulated(imsi, \
                    first_day, last_day, is_roaming)

        # Throw a signal 'traffic-data-changed'. That is a high-level signal used by some components
        # like the Traffic window and TrafficZone in the dock
        self.emit('traffic-data-changed',
                self._cached_expenses[False]['total'],  # data_used, NOT roaming
                self._cached_expenses[True]['total'],   # data_used_roaming
                self._cached_monthly_limit[False],      # limit_data NOT roaming
                self._cached_billing_period             # billing_period
        )

        # Throw an 'update-expenses-info' signal for both roaming and not roaming. That is a lower
        # level signal which talks about absolute expenses
        for is_roaming in (True, False):
            signal_id = 'update-expenses-info' if not is_roaming else 'update-roaming-expenses-info'
            expenses = self._cached_expenses[is_roaming]
            self.emit(signal_id, expenses['total'], expenses['received'], expenses['sent'])

        ## Live billing period change management

        # It is pretty unlikely, but it could be possible that TGCM is being executed during a
        # billing period change. To handle this situation, we will create a scheduled event to
        # recreate the traffic history

        # Cancel any existing scheduled event
        if self.__billing_period_change_event is not None:
            self.__billing_period_change_event.cancel()

        # Calculate the delta difference between now and the next billing period change, and
        # configure consequently the scheduled event
        delta_next_day = datetime.timedelta(days = 1)
        period_end = last_day + delta_next_day
        interval = int(time.mktime(period_end.timetuple()) - time.time())
        glib.timeout_add_seconds(interval, self.__on_billing_period_change)

    def __update_traffic_history(self, dialer, received_bytes, sent_bytes, interval_time):
        '''
        This method is called every second to update the expenses of the current connection
        if applicable. It is in charge of throwing the necessary signals to update some
        UI components
        '''
        # Get some session-related info, like expense changes, is_roaming, etc.
        imsi = self.conf.get_last_imsi_seen()
        is_roaming = self._is_roaming()
        recv_delta, sent_delta = self.__get_transfer_deltas(received_bytes, sent_bytes)

        # Update the expenses for the current billing period
        expenses = self._cached_expenses[is_roaming]
        expenses['received'] += recv_delta
        expenses['sent'] += sent_delta
        expenses['total'] = expenses['received'] + expenses['sent']

        self._storage.update(imsi, sent_delta, recv_delta, is_roaming, suggest_sync = False)

        # Build the data necessary for a signal 'traffic-data-changed' and throw it
        self.emit('traffic-data-changed',
                self._cached_expenses[False]['total'],  # data_used, NOT roaming
                self._cached_expenses[True]['total'],   # data_used_roaming
                self._cached_monthly_limit[False],      # limit_data NOT roaming
                self._cached_billing_period             # billing_period
        )

        # Throw an adequate 'update-expenses-info' signal for the current is_roaming() status
        signal_id = 'update-expenses-info' if not is_roaming else 'update-roaming-expenses-info'
        self.emit(signal_id, expenses['total'], expenses['received'], expenses['sent'])

    def __end_traffic_history(self):
        '''
        This method is called when a connection is closed or the application is being shutdown.
        It forces the traffic storage to write its changes.
        '''
        imsi = self.conf.get_last_imsi_seen()
        is_roaming = self._is_roaming()
        self._storage.do_sync(imsi, is_roaming)

    def __reset_sms_counters(self, imsi):
        self.conf.reset_sms_sent(imsi)


    # Alerts Methods
    #----------------------------------------------

    def __create_current_alerts(self):
        self._current_alerts = {}
        self._current_alerts[True] = []
        self._current_alerts[False] = []

        # Are alerts disabled?
        if not self.conf.is_alerts_available():
            return

        imsi = self.conf.get_last_imsi_seen()
        if not self.conf.is_last_imsi_seen_valid():
            return

        for is_roaming in (True, False):
            pending_alerts = self._current_alerts[is_roaming]

            accumulated_traffic = self._cached_expenses[is_roaming]['total']
            alerts = self.conf.get_alerts(is_roaming)
            enabled_alerts = self.conf.get_imsi_based_enabled_alerts(imsi, is_roaming)

            monthly_limit = self.conf.get_imsi_based_selected_monthly_limit(imsi, is_roaming)
            if monthly_limit == -1:
                monthly_limit = self.conf.get_imsi_based_other_monthly_limit(imsi, is_roaming)
            monthly_limit = monthly_limit * 1024 * 1024 # bytes

            for alert in sorted(alerts):
                is_enabled = alert in enabled_alerts
                alert_data = monthly_limit * alert / 100
                is_pending = alert_data > accumulated_traffic
                pending_alerts.append({ \
                    'percent' : alert, 'is_enabled' : is_enabled, \
                    'is_pending' : is_pending, 'data' : alert_data})

    def __update_alerts(self):
        is_roaming = self._is_roaming()
        accumulated_traffic = self._cached_expenses[is_roaming]['total']
        pending_alerts = self._current_alerts[is_roaming]

        alert_issued = False
        for i in range(0, len(pending_alerts)):
            if not alert_issued:
                alert = pending_alerts[i]
                alert_percent = alert['percent']
                is_enabled = alert['is_enabled']
                is_pending = alert['is_pending']
                alert_data = alert['data']

                if is_enabled and is_pending and (accumulated_traffic >= alert_data):
                    alert_issued = True
                    alert['is_pending'] = False
                    if tgcm.country_support == 'de':
                        conn_type_str='2G/3G/4G'
                    else:
                        conn_type_str='WWAN'

                    if alert_percent == 100:
                        self.notify.send(_("Traffic"), \
                            _("The set %s traffic limit has been reached") % conn_type_str)
                    else:
                        self.notify.send(_("Traffic"), \
                            _("The set %s traffic limit percentage has been reached (%s%%)") % \
                            (conn_type_str, alert_percent))


    # Billing period change related signal callback
    #-----------------------------------------------

    def __on_billing_period_change(self):
        imsi = self.conf.get_last_imsi_seen()
        self.__reset_sms_counters(imsi)
        self.refresh_traffic_history()
        self.emit('billing-period-changed')
        return False


    # Alert-related signal callbacks
    #-----------------------------------------------

    def __on_last_imsi_changed(self, sender, imsi):
        self.refresh_traffic_history()

    def __on_billing_day_changed(self, sender):
        imsi = self.conf.get_last_imsi_seen()
        self._storage.do_sync(imsi, self._is_roaming())
        self.refresh_traffic_history()

    def __on_monthly_limit_changed(self, sender):
        imsi = self.conf.get_last_imsi_seen()
        self._storage.do_sync(imsi, self._is_roaming())
        self.refresh_traffic_history()

    def __on_alerts_changed(self, sender):
        self.__create_current_alerts()

    def __on_app_close(self, sender):
        '''
        This method will be called when the application is about to close
        '''
        # Stop traffic history, it will sync the accounting data with the db file
        self.__end_traffic_history()

        self.__session_time_state = self.SESSION_TIME_EXIT
        self.__session_time_event.set()

        # Cancel any existing scheduled event
        if self.__billing_period_change_event is not None:
            self.__billing_period_change_event.cancel()

        # Explicitly de-reference the TrafficStorage object, so it will be destroyed
        # anytime soon
        self._storage = None

gobject.type_register(TrafficManager)
