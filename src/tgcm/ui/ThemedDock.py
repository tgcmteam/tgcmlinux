#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <cesar.garcia.tapia@openshine.com>
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

import urlparse
import webbrowser

import gtk
import gobject

import tgcm
import tgcm.core.Advertising
import tgcm.core.ConnectionLogger
import tgcm.core.FreeDesktop
import tgcm.core.Notify
import tgcm.core.Singleton
import tgcm.core.TrafficManager
import tgcm.core.XMLConfig
import tgcm.core.XMLTheme
import tgcm.ui.MSD
import tgcm.ui.widgets.dock
import tgcm.ui.widgets.themedwidgets
import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import warning_dialog, format_to_maximun_unit, \
        format_to_maximun_unit_one_decimal, normalize_strength


class ThemedDock(gobject.GObject):

    __metaclass__ = tgcm.core.Singleton.Singleton
    __gsignals__ = {
        'app-closing': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.config = tgcm.core.Config.Config(tgcm.country_support)

        self.is_moving = False
        self.__is_maximized = False
        self.__unmaximized_width = 0
        self.__unmaximized_height = 0

        # Variables related to Wi-Fi Access Point status
        self._wifi_aap = False
        self._wifi_aap_listener_id = False

        self.XMLConf = tgcm.core.XMLConfig.XMLConfig()
        self.XMLConf.import_regional_info()

        self.XMLTheme = tgcm.core.XMLTheme.XMLTheme()
        self.XMLTheme.load_theme()
        self.dock_layout = self.XMLTheme.get_layout('dock.layout')

        # FIXME: Really ugly hack to set the correct size for a dock
        # with ads (e.g. Latam).
        # TGCM/Win uses a floating window to show the advertisements, but in
        # TGCM/Linux we need to have only one gtk.Window for the dock. The
        # size of our dock does not directly appear in themes.xml, so it is
        # needed to do some calculations to get it
        is_advertising = self.config.is_ads_available()
        if is_advertising:
            ad_layout = self.XMLTheme.get_layout('dock.advertising')

            orig_height = self.dock_layout['size']['height']
            ad_height = ad_layout['size']['height']
            self.dock_layout['size']['orig_height'] = orig_height
            self.dock_layout['size']['height'] = orig_height + ad_height

            orig_minY = self.dock_layout['border']['minY']
            self.dock_layout['border']['orig_minY'] = orig_minY
            self.dock_layout['border']['minY'] = orig_height + ad_height

        # Gnome 3 is an "application based" system, as opposed to "window based" (see
        # http://live.gnome.org/GnomeShell/ApplicationBased for more info). The interesting
        # thing with Gnome 3 is that it uses a different (and somewhat insane) algorithm to
        # look for the application name. That string is used e.g. in the title bar, alt+tab, etc.
        #
        # Currently, it seems that a .desktop file accessible world-wide (e.g. in
        # /usr/share/applications) is required, and the value of the X property "WM_CLASS" must
        # match with the name of that .desktop file. For example, if an application package
        # provides a file called 'xxxx.desktop', the WM_CLASS property of the application window
        # must be something like WM_CLASS(STRING) = "xxxx", "Xxxx".
        #
        # We have a problem with TGCM, because by default PyGTK uses the name of the main python
        # script to set the WM_CLASS value (in our case WM_CLASS(STRING) = "tgcm", "Tgcm"), so
        # Gnome 3 fails to find the appropriate .desktop file (eg. "tgcm-[es|ar|de|uy].desktop").
        # Instead of showing the correct application name, it shows "Tgcm".
        #
        # The following lines are intended to correctly establish the contents of the property
        # WM_CLASS to something like WM_CLASS(STRING) = "tgcm-es", "Tgcm-es". It unfortunately
        # fails but that is the documented way to do it.
        prg_name = 'tgcm-%s' % tgcm.country_support
        app_name = 'Tgcm-%s' % tgcm.country_support
        gobject.set_prgname(prg_name)
        gobject.set_application_name(app_name)

        gtk.window_set_default_icon(self.XMLTheme.get_window_icon())

        self.main_window = gtk.Window()
        self.main_window.set_name("tgcm_main_window")
        self.main_window.set_title(self.config.get_app_name())

        # WTF: Seems that PyGTK does not properly assign the property WM_CLASS with the
        # functions "gobject.set_prgname()". The following function indeed it does, but in
        # a very hostile and probably dangerous way. Keep it in mind!
        self.main_window.set_wmclass(prg_name, app_name)

        self.main_window.set_decorated(False)
        self.main_window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        self.main_window.connect("show", self.__on_show_window)
        self.main_window.connect("delete-event", self.__on_destroy_window)
        self.main_window.connect("check-resize", self.__on_check_resize)
        self.main_window.connect("configure-event", self.__on_configure_event)
        self.main_window.connect("motion-notify-event", self.__motion_notify_event)

        self.help_dialog = None

        self.__is_first_time = False
        if self.config.is_first_time():
            self.__is_first_time = True
            self.config.done_first_time()

        self.vbox = gtk.VBox()
        self.main_window.add(self.vbox)

        # Hidden menu, used for Ubuntu HUD and keyboard accelerators
        self.menubar = tgcm.ui.widgets.dock.Menubar.Menubar()
        self.vbox.pack_start(self.menubar.get_menubar(), False)

        self.main_box = gtk.Fixed()
        self.main_box.connect("size-allocate", self.__on_size_allocate)
        self.vbox.pack_start(self.main_box, True)

        self.vbox.show()
        self.menubar.get_menubar().hide()
        self.main_box.show()

        # Add a global URI hook to gtk.LinkButton widgets. This hook check if there is an
        # active connection before opening the URI, and if that is not the case it initiates
        # the SmartConnector logic
        gtk.link_button_set_uri_hook(self.__linkbutton_global_uri_hook)

    def load_all (self):
        self.__create_vars ()
        self.__create_functions ()

        self.device_dialer = tgcm.core.FreeDesktop.DeviceDialer()
        self.device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self._conn_manager = tgcm.core.ConnectionManager.ConnectionManager()
        self.doc_manager = tgcm.core.DocManager.DocManager()
        self.notify = tgcm.core.Notify.Notify()
        self.MSDConnManager = tgcm.ui.MSD.MSDConnectionsManager()
        self.MSDActManager = tgcm.ui.MSD.MSDActionsManager(self.MSDConnManager)
        self._conn_logger = tgcm.core.ConnectionLogger.ConnectionLogger()

        self.__layout_loader = tgcm.ui.widgets.themedwidgets.LayoutLoader(self.dock_layout)

        # Build and register accelerators in dock main window
        self.menubar.build_menus(self.__layout_loader.get_accelerators())
        self.main_window.add_accel_group(self.menubar.get_accelgroup())

        # Establish maximum and minimum dimensions for main window
        minX, minY = self.__layout_loader.get_min_size()
        maxX = gtk.gdk.screen_width()
        self.main_window.set_geometry_hints(None,
                min_height=minY,
                max_height=minY,
                min_width=minX,
                max_width=maxX)

        # FIXME: That is a really ugly hack to have the tooltips displayed in the dock.
        #
        # For an unknown reason, it seems that no tooltip is shown in the dock if it
        # is not continuously updating itself (e.g. if the user is disconnected from the
        # network it won't show any tooltip at all).
        #
        # I don't know the real reason, but it seems that calling the function
        # "gtk.tooltip_trigger_tooltip_query()" from time to time helps a little
        gobject.timeout_add(1000, self.__reenable_dock_tooltips)

        # Helper class used to detect and automatically close some NM windows,
        # e.g. PIN and PUK dialogs
        self.nm_dialog_close_helper = tgcm.ui.MSD.MSDNmPinDialogCloseHelper()

        self.connection_zone = tgcm.ui.widgets.dock.ConnectionZone(self.MSDConnManager)
        self.connection_zone.connect("connection_speed_changed", self.__on_speed_changed)
        #self.connection_zone.connect("network_tech_changed", self.__on_network_tech_changed)
        #self.connection_zone.connect("carrier_changed", self.__on_carrier_changed)
        self.connection_zone.connect("connected", self.__on_connection_connected)
        self.connection_zone.connect("disconnected", self.__on_connection_disconnected)
        self.connection_zone.connect("connecting", self.__on_connection_connecting)

        self.device_zone = tgcm.ui.widgets.dock.DeviceZone()
        self.device_zone.connect("active_device_changed", self.__on_active_device_changed)
        self.device_zone.connect("active_device_info_changed", self.__on_active_device_info_changed)
        self.device_zone.connect("active_device_signal_changed", self.__on_active_device_signal_changed)
        self.device_zone.connect("active_device_tech_changed", self.__on_active_device_tech_changed)
        self.device_zone.connect("roaming_state_changed", self.__on_roaming_state_changed)
        self.device_zone.connect("carrier_changed", self.__on_carrier_changed)
        self.device_zone.connect("supported_device_detected", self.__on_supported_device_detected)
        self.device_zone.connect("supported_device_ready", self.__on_supported_device_ready)
        self.device_zone.connect("supported_device_added", self.__on_supported_device_added)
        self.device_zone.connect("supported_device_removed", self.__on_supported_device_removed)

        self.traffic_zone = tgcm.ui.widgets.dock.TrafficZone()
        self.traffic_manager = tgcm.core.TrafficManager.TrafficManager()
        self.traffic_manager.connect('traffic-data-changed', self.__on_traffic_data_changed)

        self.main_modem = self.device_manager.main_modem
        self.main_modem.connect("main-modem-changed", self.__on_main_modem_changed)

        if self.config.is_ads_available():
            self.advertising = tgcm.core.Advertising.Advertising()

        self.__widgets = {}

        self.__load_main_window()
        self.__load_background()
        self.__load_caption()
        self.__load_widgets()
        self.__notify_widgets()

        self.services_toolbar, left, top = self.__layout_loader.get_services_toolbar( \
                self, self.MSDActManager, self.MSDConnManager)
        if self.services_toolbar:
            self.main_box.put(self.services_toolbar, left, top)
            self.services_toolbar.queue_resize()

        # Systray
        self.systray_manager = tgcm.ui.widgets.dock.Systray.SystrayManager( \
                self, self.MSDConnManager, self.connection_zone)
        self.MSDActManager.set_systray(self.systray_manager.get_systray())

        if self.config.get_ui_general_key_value("systray_showing_mw"):
            self.show_main_window()
        else:
            self.hide_main_window()

        self.device_policy = tgcm.ui.DevicePolicy()

        main_dev = self.device_manager.get_main_device();
        if main_dev is not None:
            dev_name = main_dev.get_prettyname()
            self.set_var("wwan.device", str(dev_name))
            self.set_var("wwan.device.on", True)

        self.device_dialer.updateConnectionStatus()
        self.traffic_manager.refresh_traffic_history()

        self.preferences_dialog = tgcm.ui.windows.Settings()
        if self.__is_first_time and (tgcm.country_support == 'uk'):
                self.preferences_dialog.run("General>1")

        # Some config-related callbacks
        self.config.connect('last-imsi-seen-changed', self.__on_last_imsi_seen_changed)

        self.news_dialog = tgcm.ui.windows.NewsServiceDialog()
        self.news_dialog.show_news_if_required()

    def __linkbutton_global_uri_hook(self, widget, url):
        '''
        Global URI hook to gtk.LinkButton widgets. This hook check if there is an
        active connection before opening the URI, and if that is not the case it
        displays an error dialog
        '''

        result = urlparse.urlparse(url)

        # Help URI: open the help manual
        if result.scheme == 'help':
            sections = [result.netloc]
            self.__openhelp(sections)

        # Dialog URI: open a specific configuration dialog
        elif result.scheme == 'dialog':
            dialog_id = result.netloc

            # Change billing day dialog
            if dialog_id == 'change_billing_day':
                self.traffic_zone.show_change_billing_day_dialog()

            # Unrecognized dialog, do nothing
            else:
                pass

        # URL URI: check if there is an active connection before opening the URI, and if
        # that is not the case it displays an error dialog
        else:
            is_connected = self._conn_manager.is_connected()
            if is_connected:
                webbrowser.open(url)
            else:
                title = _('Not connected')
                markup = _('The web page cannot be opened because you are not connected')
                message = _('Please connect and try again')

                toplevel = widget.get_toplevel()
                parent = toplevel if toplevel.is_toplevel() else None

                warning_dialog(message, markup=markup, title=title, parent=parent)

    def __reenable_dock_tooltips(self):
        gtk.tooltip_trigger_tooltip_query(gtk.gdk.display_get_default())
        return True

    def __on_speed_changed (self, sender, speed):
        self.set_var ("app.connection.speed", speed)

    def __on_network_tech_changed (self, sender, network_tech):
        self.set_var ("app.connection.tech.description", network_tech)

    def __on_connection_connected (self, sender, connection_name):
        self.set_var ("app.connecting", False)
        self.set_var ("app.connected", True)
        self.set_var ("str.connection", connection_name)
        self.set_var ("str.connect.status", _("Connected"))

        # Update signal status
        self.__update_signal_strength_status(True)

        # Update the connection type icon
        self.__update_connection_type_vars()

        # Remove previous Wi-Fi strength signals
        self.__remove_aap_strength_listener()

        # Listen to the changes in the properties of the active Access Point if necessary
        self.__create_aap_strength_listener()

    def __on_connection_disconnected (self, sender, connection_name):
        self.set_var ("app.connecting", False)
        self.set_var ("app.connected", False)
        self.set_var ("str.connection", "")
        self.set_var ("str.connect.status", _("Disconnected"))

        # Stop listening changes in the properties of the active Access Point if possible
        self.__remove_aap_strength_listener()

    def __on_connection_connecting (self, sender, connection_name):
        self.set_var ("app.connecting", True)
        self.set_var ("app.connected", False)
        self.set_var ("str.connection", connection_name)
        self.set_var ("str.connect.status", _("Connecting..."))

        gobject.timeout_add(200, self.__update_connection_progress)

        # Reset signal strength variables
        self.__update_signal_strength_status(False)

        # Update the connection type icon
        self.__update_connection_type_vars()

        # Remove previous Wi-Fi strength signals
        self.__remove_aap_strength_listener()

        # Listen to the changes in the properties of the active Access Point if necessary
        self.__create_aap_strength_listener()

    def __update_signal_strength_status(self, net_connected):
        connection_type = self.device_dialer.nmGetConnectionType()
        if connection_type == "ETHERNET":
            if net_connected:
                self.set_var("lan.signal", 1)
            else:
                self.set_var("lan.signal", 0)
        elif connection_type == "WIRELESS":
            try:
                wifi_aap = self.device_manager.get_wifi_device().get_active_access_point()
                strength = wifi_aap['Strength']

                norm_strength = normalize_strength(strength)
                self.set_var("app.connection.signal", norm_strength)

                nm_norm_strength = normalize_strength(strength, use_nm_levels = True)
                tooltip = self.__wifi_tooltips[nm_norm_strength]
                self.set_var('app.connection.signal.description', tooltip)
                self.set_var('wifi.signal.description', tooltip)
            except TypeError:
                # Seems that sometimes D-Bus throws some exceptions. There is very little
                # to do here, except to capture the exception and pray there is not anything
                # more broken.
                pass
        elif connection_type == "GSM":
            main_device=self.device_manager.get_main_device()
            if (main_device!=None):
                strength = main_device.get_SignalQuality()
                norm_strength = normalize_strength(strength)
                self.set_var("app.connection.signal", norm_strength)
                self.set_var("wwan.signal", norm_strength)

                nm_norm_strength = normalize_strength(strength, use_nm_levels = True)
                tooltip = self.__wwan_tooltips[nm_norm_strength]
                self.set_var('app.connection.signal.description', tooltip)
                self.set_var('wwan.signal.description', tooltip)

    def __update_connection_type_vars(self):
        connection_type = self.device_dialer.nmGetConnectionType()
        if connection_type == "ETHERNET":
            self.set_var("app.connection.lan", True)
            self.set_var("app.connection.wifi", False)
            self.set_var("app.connection.wwan", False)
        elif connection_type == "WIRELESS":
            self.set_var("app.connection.lan", False)
            self.set_var("app.connection.wifi", True)
            self.set_var("app.connection.wwan", False)
        elif connection_type == "GSM":
            self.set_var("app.connection.lan", False)
            self.set_var("app.connection.wifi", False)
            self.set_var("app.connection.wwan", True)

    def __create_aap_strength_listener(self):
        connection_type = self.device_dialer.nmGetConnectionType()
        if connection_type == "WIRELESS":
            wifi_device = self.device_manager.get_wifi_device()
            self._wifi_aap = wifi_device.get_active_access_point()
            self._wifi_aap_listener_id = self._wifi_aap.connect_to_signal('PropertiesChanged', self.__aap_strength_listener)

    def __remove_aap_strength_listener(self):
        if self._wifi_aap is not False:
            self._wifi_aap_listener_id.remove()
            self._wifi_aap = False
            self._wifi_aap_listener_id = False

    def __aap_strength_listener(self, properties):
        if self._wifi_aap is not False:
            try:
                norm_strength = normalize_strength(self._wifi_aap['Strength'])
                self.set_var('app.connection.signal', norm_strength)
            except Exception:
                pass

    def __update_connection_progress (self):
        if self.get_var ("app.connecting"):
            self.set_var ("app.connection.progress", (self.get_var ("app.connection.progress") + 1) % 11)
            return True
        else:
            return False

    def __on_active_device_changed (self, sender, device_active, device_name):
        if device_active:
            self.set_var ("wwan.device", device_name)
            self.set_var ("wwan.device.on", True)
            self.set_var ("wwan.device.status", '')
            self.set_var ("wwan.device.in", True)
        else:
            self.set_var ("wwan.device.init", False)
            self.set_var ("wwan.device", device_name)
            self.set_var ("wwan.device.on", False)
            self.set_var ("wwan.device.status", _('Device switched off'))
            self.set_var ("wwan.device.in", True)
            self.set_var ("wwan.operator", '')
            self.set_var ("wwan.signal",0)
            self.set_var ("wwan.rat",'')

    def __on_active_device_info_changed (self, sender, device_info):
        self.set_var ("wwan.device.description", device_info)

    def __on_active_device_signal_changed (self, sender, strength):
        norm_strength = normalize_strength(strength)
        self.set_var("wwan.signal", norm_strength)
        nm_norm_strength = normalize_strength(strength, use_nm_levels = True)
        tooltip = self.__wwan_tooltips[nm_norm_strength]
        self.set_var('wwan.signal.description', tooltip)

        connection_type = self.device_dialer.nmGetConnectionType()
        if connection_type == 'GSM':
            self.set_var('app.connection.signal', norm_strength)
            self.set_var('app.connection.signal.description', tooltip)

    def __on_active_device_tech_changed(self, sender, status):
        self.set_var("wwan.rat", status)

    def __on_roaming_state_changed (self, sender, roaming):
        self.set_var ("wwan.roaming", roaming)

    def __on_carrier_changed (self, sender, carrier):
        self.set_var ("wwan.operator", carrier)
        self.set_var ("wwan.device.init", False)

    def __on_supported_device_detected(self, sender):
        self.set_var ("wwan.device.in", True)
        self.set_var ("wwan.device.init", True)

    def __on_supported_device_ready(self, sender):
        self.set_var("wwan.device.in", True)
        self.set_var("wwan.device.init", False)

    def __on_supported_device_added (self, sender, dev_string):
        self.set_var ("wwan.device.init", False)

    def __on_main_modem_changed(self, main_modem, mcontroller, device):
        self.set_var ("wwan.device.init", True)

    def __on_supported_device_removed (self, sender, udi):
        self.set_var ("wwan.device.in", False)
        self.set_var ("wwan.device.on", False)
        self.set_var ("wwan.device.init", False)

    def __on_traffic_data_changed(self, traffic_manager, data_used, data_used_roaming, data_limit, billing_period):
        data_limit_string = format_to_maximun_unit_one_decimal(data_limit,"GB","MB","KB","Bytes")
        data_used_string = format_to_maximun_unit_one_decimal(data_used,"GB","MB","KB","Bytes")
        period_end_string = billing_period[1].strftime('%d/%m/%Y')
        period_start_string = billing_period[0].strftime('%d/%m/%Y')

        # -- Set the available data to zero if used higher than limit
        data_available = 0 if (data_used > data_limit) else (data_limit - data_used)
        data_available_string = format_to_maximun_unit_one_decimal(data_available,"GB","MB","KB","Bytes")

        try:
            fraction = int ((data_used * 10.0) / data_limit)
            if fraction > 10:
                fraction = 10
            elif fraction < 0:
                fraction = 0
        except:
            fraction = 0

        if tgcm.country_support == 'uk':
            description = _("Data purchased: %s\nYou've used: %s\nData available until %s: %s") % \
                (data_limit_string, data_used_string, period_end_string, data_available_string)
        elif tgcm.country_support == 'es':
            description = _("Consumed data since %s: %s") % \
                (period_start_string, data_used_string)
        else:
            description = _("Data purchased: %s\nConsumed data: %s\nAvailable data until %s: %s") % \
                (data_limit_string, data_used_string, period_end_string, data_available_string)

        self.set_var("str.user.data.available", "")
        self.set_var("str.user.data.available.data", "%s" % (data_available_string))
        self.set_var("str.user.data.used.data", "%s" % (data_used_string))

        self.set_var("user.data.used", fraction)
        self.set_var("user.data.description", description)
        self.set_var("str.user.data.limit.data", data_limit_string);

    def __load_main_window (self):
        self.orig_width, self.orig_height = self.__layout_loader.get_size()
        self.window_width = self.config.get_dock_width()

        self.orig_position = self.config.get_window_position()

        self.is_on_resize_cursor = False

        if self.window_width < self.orig_width:
            self.window_width = self.orig_width

        self.main_window.resize(self.window_width, self.orig_height)

    def __load_background (self):
        self.is_advertising = self.config.is_ads_available()
        background = self.__layout_loader.get_background( \
                self.XMLTheme.pixbufs, self.is_advertising)

        if background:
            self.background = background
            self.main_box.put(self.background, 0, 0)

    def __load_caption (self):
        caption_type, caption_top, caption_minimize, caption_maximize = self.__layout_loader.get_caption ()
        if caption_type:
            if caption_type == 'none':
                return
            elif caption_type == 'top':
                self.caption_top = caption_top
            elif caption_type == 'window':
                self.caption_top = 0

            self.background.connect ("button-press-event", self.__button_press_event)

    def __load_widgets (self):
        widgets = self.__layout_loader.get_widgets()
        for widget in widgets:
            self.main_box.put(widget, widget.left, widget.top)
            self.__widgets[widget.id] = widget

    def __notify_widgets (self):
        for widget_id in self.__widgets:
            widget = self.__widgets[widget_id]
            widget.check_vars ()

    def __on_configure_event(self, widget, event, params=None):
        # This method is called every time the dock allocates its sizes and width.
        # We will use it to store the current position of the dock
        window_position = self.main_window.get_position()

        # This operation is quite expensive, only save it if it is really necessary
        if self.orig_position != window_position:
            self.orig_position = window_position
            x, y = self.orig_position

            # Store current position of the dock
            self.config.set_window_position(x, y)

    def __on_check_resize(self, window):
        # Get current dock width
        new_width = self.main_window.get_size()[0]

        # Check if the dock has been really resized, or it is a spurious signal
        if self.window_width != new_width:
            self.window_width = new_width
            self.config.set_dock_width(new_width)

            # Seems that it is really needed to recalculate the services shown
            self.services_toolbar.resize()

    def __on_size_allocate (self, main_widget, allocation, params=None):
        window_width = allocation.width
        window_height = allocation.height

        main_widget.allocation = allocation

        self.background.size_allocate (gtk.gdk.Rectangle (0, 0, window_width, window_height))

        try:
            width_diff = abs(window_width - self.orig_width)
            height_diff = abs(window_height - self.orig_height)
        except:
            width_diff = 0
            height_diff = 0

        for widget_name in self.__widgets:
            widget = self.__widgets[widget_name]

            left = widget.left + width_diff*widget.anchor_tl[0]/100
            top = widget.top + height_diff*widget.anchor_tl[1]/100

            if widget.anchor_br[0] > 0:
                width = widget.width + width_diff*widget.anchor_br[0]/100 - width_diff*widget.anchor_tl[0]/100
            else:
                width = widget.width + width_diff*widget.anchor_br[0]/100
            if widget.anchor_br[1] > 0:
                height = widget.height + height_diff*widget.anchor_br[1]/100 - height_diff*widget.anchor_tl[1]/100
            else:
                height = widget.height + height_diff*widget.anchor_br[1]/100

            widget.size_allocate (gtk.gdk.Rectangle (left, top, width, height))

        return True

    def __create_vars (self):
        self.__wifi_tooltips = [
            _('Very low Wi-Fi coverage'),
            _('Low Wi-Fi coverage'),
            _('Good Wi-Fi coverage level'),
            _('Very good Wi-Fi coverage'),
            _('Excellent Wi-Fi coverage'),
        ]

        self.__wwan_tooltips = [
            _('Very low coverage level'),
            _('Low coverage level'),
            _('Good coverage level'),
            _('Very good coverage level'),
            _('Excellent coverage level'),
        ]

        self.vars = {}
        self.dyn_vars = {}

        self.vars ["wwan.homezone"] = False
        self.vars ["wwan.roaming"] = False
        self.vars ["wwan.device.status"] = _("Switched off")
        self.vars ["wwan.device.in"] = False
        self.vars ["wwan.device.on"] = False
        self.vars ["wwan.device.init"] = False
        self.vars ["wwan.signal"] = 0
        self.vars ["wifi.signal"] = 0
        self.vars ["lan.signal"] = 0
        self.vars ["lan.signal.description"] = _("LAN connectivity")
        self.vars ["available.signal"] = 0
        self.vars ["available.signal.description"] = ""
        self.vars ["available.signal.wwan"] = False
        self.vars ["available.signal.wifi"] = False
        self.vars ["available.signal.lan"] = False
        self.vars ["available.connection"] = ""
        self.vars ["available.connection.description"] = ""

        self.vars ["app.connected"] = False
        self.vars ["app.connecting"] = False
        self.vars ["app.connection.wwan"] = True
        self.vars ["app.connection.wifi"] = False
        self.vars ["app.connection.lan"] = False
        self.vars ["app.connection.seconds"] = ""
        self.vars ["app.connection.bytes"] = ""
        self.vars ["app.connection.speed"] = format_to_maximun_unit(0, "GBits","MBits","KBits","Bits") + "/s"
        self.vars ["app.connection.signal"] = 0
        self.vars ["app.connection.signal.description"] = ""
        self.vars ["app.connection.tech.description"] = ""
        self.vars ["str.connection"] = ""
        self.vars ["app.connection.progress"] = 0

        self.vars ["wwan.device"] = _("No device")
        self.vars ["wwan.device.description"] = _("Device: No device")
        self.vars ["wwan.operator"] = ""
        self.vars ["wwan.rat"] = ""

        # traffic
        self.vars ["traffic.available"] = self.config.is_traffic_available()
        #self.vars ["user.prepay"] = theApp.pay_type()==pay_t_pre
        self.vars ["str.user.data.available"] = ""
        self.vars ["str.user.data.available.data"] = ""

        if tgcm.country_support=='es':
            self.vars ["str.user.data.available.label"] = _("Data used")
        else:
            self.vars ["str.user.data.available.label"] = _("Available data")

        self.vars ["str.user.data.used"] = ""
        self.vars ["str.user.data.used.data"] = ""
        self.vars ["str.user.data.limit.data"] = ""
        self.vars ["str.user.data.used.label"] = _("You've used")
        self.vars ["user.data.used"] = 0
        self.vars ["user.data.description"] = ""

        # localizables
        self.vars ["str.mintotray"] = _("Minimize to system tray")
        self.vars ["str.minimize"] = _("Minimize")
        self.vars ["str.srvmore"] = _("More...")
        self.vars ["str.srvaddressbook"] = _("Contacts")
        self.vars ["str.srvwifi"] = self.config.get_wifi_service_name() #_("Wi-Fi areas")
        self.vars ["str.srvfavorites"] = _("Favourites")
        self.vars ["str.srvsms"] = _("SMS")
        self.vars ["str.srvprepay"] = _("Prepay")
        self.vars ["str.srvrecargasaldo"] = _("Top-up")
        self.vars ["str.close"] = _("Close %s") % self.config.get_app_name()
        self.vars ["str.exit"] = _("Close %s") % self.config.get_app_name()
        self.vars ["wwan.signal.description"] = ""
        self.vars ["wifi.signal.description"] = ""
        self.vars ["str.smartconnect"] = _("Smart Connection")
        self.vars ["str.smartconnect.description"] = _('Get connected launching Smart Connection')
        self.vars ["str.connect.status"] = _("Disconnected")
        self.vars ["str.connect.statustext"] = _("Status")
        if tgcm.country_support != "uk":
            self.vars ["str.getconnected"] = _("Get connected to the default connection")
        else:
            self.vars ["str.getconnected"] = ""
        self.vars ["str.disconnect"] = _("Disconnect")
        self.vars ["str.connect"] = _("Connect")
        self.vars ["str.cancel"] = _("Cancel")
        self.dyn_vars ["str.disconnect.description"] = self.__get_str_disconnect_description
        self.vars ["str.settings"] = _("Settings")
        self.vars ["str.settings.description"] = "IDS_MW_TTIP_BTNCFG"
        self.vars ["str.help"] = _("Help")
        self.vars ["str.help.description"] = "IDS_MW_TTIP_BTNAYU"
        self.vars ["str.prepaypage"] = "IDS_PREPAY_BTN"
        #self.vars ["str.prepaypage.description"] = theApp.m_iconfig.prepay_url()
        self.vars ["str.networks"] = _("Available networks")

        self.vars ["str.networkstooltip"] = _("Available mobile networks")
        self.vars ["str.traffic"] = _("Traffic")
        self.vars ["str.apptitle"] = self.config.get_app_name()

        # notifiers
        self.vars ["notifier.generic.text"] = ""
        self.vars ["notifier.traffic.text"] = ""
        self.vars ["notifier.error.text"] = ""
        self.vars ["notifier.error.title"] = "IDS_ERROR_NOTIFIER_TITLE"

    def __get_str_disconnect_description (self):
        return _("To cancel connection to %s, click here") % self.get_var ("str.connection")

    def __create_functions (self):
        self.functions = {}

        self.functions ["window.close"] = self.__close
        self.functions ["window.maximize"] = self.__maximize
        self.functions ["window.minimize"] = self.__minimize
        self.functions ["window.mintotray"] = self.__mintotray

        self.functions ["app.connect"] = self.__connect
        self.functions ["app.disconnect"] = self.__disconnect
        self.functions ["app.cancel_connect"] = self.__cancel_connect
        self.functions ["app.menudevice"] = self.__menudevice
        self.functions ["app.configure"] = self.__configure
        self.functions ["app.help"] = self.__help
        self.functions ["app.openhelp"] = self.__openhelp
        self.functions ["app.traffic"] = self.__traffic
        self.functions ["app.networks"] = self.__networks

        self.functions ["app.addressbook"] = self.__addressbook
        self.functions ["app.service"] = self.__service
        self.functions ["app.moreservices"] = self.__moreservices
        self.functions ["app.prepaypage"] = self.__prepaypage

        self.functions['app.open_ad'] = self.__open_advertising

        #LAYOUT-NOTIFICADOR-CONSUMO:
        #"wnd.click"
        #"wnd.close"

        #LAYOUT-NOTIFICADOR-SMS:
        #"wnd.click"
        #"wnd.close"

        #LAYOUT-NOTIFICADOR-VIDEOLLAMADA:
        #"wnd.click"
        #"wnd.pickup"
        #"wnd.hangup"
        #"wnd.silence"
        #"wnd.close"

        #LAYOUT-NOTIFICADOR-GENERICO:
        #"wnd.click"
        #"wnd.close"

    def set_var (self, varname, value):
        if varname in self.vars:
            self.vars [varname] = value
            self.__notify_widgets ()
            return True
        else:
            return False

    def get_var (self, varname):
        if varname in self.dyn_vars:
            return self.dyn_vars[varname]()

        if varname in self.vars:
            return self.vars[varname]

    def __close (self, event=None):
        try:
            self.close_app ()
        except Exception, err:
            print "@FIXME: Can't close app due unhandled error '%s'" % err

    def __minimize (self, event=None):
        self.__mintotray()

    def __mintotray (self, event=None):
        self.hide_main_window()

    def __connect (self, event=None):
        self.connection_zone.do_connect ()

    def __disconnect (self, event=None):
        self.connection_zone.do_disconnect ()

    def __cancel_connect (self, event=None):
        self.connection_zone.do_cancel_connect ()

    def __menudevice (self, event=None):
        self.device_zone.show_device_menu (event)

    def __configure (self, section=None, event=None):
        if (section is not None) and (len(section) > 0):
            section = section[0]
            if (section == 'recargasaldo') or (section == 'mydetails'):
                self.preferences_dialog.run('General>1')
            elif section == 'traffic':
                # If Alerts are enabled, show open Settings with that tab focused
                if self.config.is_alerts_available():
                    self.preferences_dialog.run('Alerts')

                # Spain doesn't have alerts enabled, but it was requested to open
                # instead 'My Details'
                elif tgcm.country_support == 'es':
                    self.preferences_dialog.run('General>1')

                # I don't know if that is possible, but in any case fallback to
                # the first tab of General section
                else:
                    self.preferences_dialog.run('General>0')
            elif section == 'addressbook':
                self.preferences_dialog.run('Addressbook')
            elif section:
                self.preferences_dialog.run("Services|%s" % section)
        else:
            self.preferences_dialog.run()


    def __help (self, event=None):
        if not self.help_dialog:
            self.help_dialog = tgcm.ui.windows.HelpDialog()
        self.help_dialog.show()

    def __openhelp (self, section=None, event=None):
        if section:
            section = section[0]
        else:
            return

        doc = ""
        if section == "traffic":
            doc = "tgcm_065.htm"
        elif section == "videocall":
            pass
        elif section == "introduction":
            doc = "Index.htm"
        elif section == "mobile_phone":
            doc = "tgcm_030.htm#mobile_phone"
        elif section == "addressbook":
            doc = "tgcm_050.htm#contacts"
        elif section == "wifi":
            doc = "tgcm_050.htm#wifi_areas"
        elif section == "favorites":
            doc = "tgcm_050.htm#favourites"
        elif section == "sms":
            doc = "tgcm_050.htm#sms"
        elif section == "intranet":
            doc = "tgcm_050.htm#intranet"
        elif section == "recargasaldo":
            doc = "tgcm_050.htm#topup"
        elif section == "bam":
            doc = "tgcm_100.htm#bam"
        elif section == "user_details":
            doc = "tgcm_060.htm#user_details"
        elif section == "help":
            doc = "tgcm_080.htm"
        elif section == "prepay":
            pass
        else:
            return

        if doc != "":
            parts = doc.split('#')
            path = self.doc_manager.get_doc_path (parts[0])
            if len(parts) > 1:
                webbrowser.open("file://%s#%s" % (path, parts[1]))
            else:
                webbrowser.open("file://%s" % path)

    def __traffic (self, event=None):
        self.traffic_zone.show_traffic_dialog ()

    def __networks (self, event=None):
        self.connection_zone.show_available_networks ()

    def __addressbook (self, event=None):
        print "ADDRESSBOOK"

    def __service (self, event=None):
        print "SERVICE"

    def __moreservices (self, event=None):
        print "MORE_SERVICES"

    def __prepaypage (self, event=None):
        print "PREPAYPAGE"

    def __open_advertising(self, param, event=None):
        url = None
        if param == 'main':
            url = self.advertising.get_dock_advertising()[1]
        elif param == 'service':
            url = self.advertising.get_service_advertising()[1]

        if url is not None:
            webbrowser.open(url)

    def __on_destroy_window (self, widget, event, data=None):
        self.close_app ()

    def on_systray_clicked (self):
        if self.config.get_ui_general_key_value ("systray_showing_mw"):
            self.hide_main_window ()
        else:
            self.show_main_window ()

    def hide_main_window (self):
        self.minimize_on = True
        self.main_window.hide()
        self.config.set_ui_general_key_value("systray_showing_mw", False)

    def show_main_window (self):
        self.minimize_on = False
        self.main_window.present()
        self.main_box.show()
        self.config.set_ui_general_key_value("systray_showing_mw", True)

    def __button_press_event (self, widget, event):
        if (event.type == gtk.gdk.BUTTON_PRESS) and (event.button == 1):
            if self.caption_top > 0:
                # Si no hemos pinchado en la parte superior de la cabecera indicada
                # por self.caption_top, no movemos la ventana
                y = self.main_window.get_position()[1]
                top = int (event.y_root) - y
                if top > self.caption_top:
                    return

            # Depending on the position of the cursor in the window it could be a
            # resize or a move operation
            cursor_position = self.__get_cursor_dock_position(event)
            if cursor_position == 0:
                # Move operation
                self.main_window.begin_move_drag(event.button, \
                    int(event.x_root), int(event.y_root), event.time)
                return True
            elif cursor_position == 1:
                # Left resize operation
                self.main_window.begin_resize_drag(gtk.gdk.WINDOW_EDGE_WEST, \
                    event.button, int(event.x_root), int(event.y_root), event.time)
                return True
            elif cursor_position == 2:
                # Right resize operation
                self.main_window.begin_resize_drag(gtk.gdk.WINDOW_EDGE_EAST, \
                    event.button, int(event.x_root), int(event.y_root), event.time)
            return True

    def __motion_notify_event(self, widget, event, params=None):
        # Depending on the position of the cursor in the window the cursor must be
        # set to normal or resize mode

        # That operation is quite expensive, so only update the cursor when it is
        # really necessary
        current_on_resize = self.__get_cursor_dock_position(event)
        if self.is_on_resize_cursor != self.__get_cursor_dock_position(event):
            self.is_on_resize_cursor = current_on_resize

            # Choose the appropiate cursor depending of its position in the dock
            cursor_position = self.__get_cursor_dock_position(event)
            if cursor_position == 0:
                # Normal cursor
                custom_cursor = None
            elif cursor_position == 1:
                # Left resize cursor
                custom_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE)
            elif cursor_position == 2:
                # Right resize cursor
                custom_cursor = gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)

            self.main_window.get_window().set_cursor(custom_cursor)

    def __get_cursor_dock_position(self, event):
        '''
        Returns the position of the cursor in the dock when a motion notify event
        arrives.

        @return: An integer indicating the position of the cursor in the dock.
            1 if the cursor is in the left resize grip, 2 in the right resize
            grip, 0 otherwise.
        '''
        resize_grip_size = 5
        coord_x = event.get_coords()[0]
        right_resize_grip = self.window_width - resize_grip_size

        if coord_x < resize_grip_size:
            return 1    # Left resize grip
        elif coord_x > right_resize_grip:
            return 2    # Right resize grip
        else:
            return 0    # Not resize area

    def __maximize (self, event=None):
        resizeX = self.dock_layout['border']['resizeX']
        resizeY = self.dock_layout['border']['resizeY']

        if self.__is_maximized:
            if resizeX and resizeY:
                self.main_window.unmaximize ()
            else:
                self.main_window.resize (self.__unmaximized_width, self.__unmaximized_height)
            self.__is_maximized = False
        else:
            if not resizeX and not resizeY:
                return
            elif resizeX and resizeY:
                self.main_window.maximize ()
            else:
                self.__unmaximized_width, self.__unmaximized_height = self.main_window.get_size ()
                if resizeX:
                    screen_width = gtk.gdk.screen_width()
                    self.main_window.resize (screen_width, self.__unmaximized_height)
                else:
                    screen_height = gtk.gdk.screen_height()
                    self.main_window.resize (self.__unmaximized_width, screen_height)
            self.__is_maximized = True

    def __on_show_window (self, widget, data=None):
        x, y = self.config.get_window_position ()

        if x == 0 and y == 0:
            width, height = self.main_window.get_size()
            screen_width = gtk.gdk.screen_width()
            self.main_window.move (screen_width/2 - width/2, 0)
        else:
            self.main_window.move (x, y)

    def __on_last_imsi_seen_changed(self, sender, imsi):
        if self.config.check_policy('mydetails-show-startup') and \
                self.config.is_last_imsi_seen_valid() and \
                self.config.is_first_time_imsi(imsi):
            self.config.set_is_first_time_imsi(imsi, False)
            self.__configure(['mydetails'])

    def close_app(self):
        self.config.update_last_execution_datetime()
        try:
            _close = self.MSDConnManager.close_app()
        except Exception, err:
            print "@FIXME: MSDConnManager.close_app() unexpected error, %s" % err
            return True

        # -- This is the point of non-return, so emit the closing signal
        if _close is True:
            self.emit('app-closing');
            self.main_window.hide()
            self._conn_logger.quit()
            gtk.main_quit()

        return (not _close)

    def get_main_window(self):
        return self.main_window

    def get_size(self):
        return self.main_window.get_size()

    def get_service_buttons_status(self):
        return self.services_toolbar.get_service_buttons_status()
