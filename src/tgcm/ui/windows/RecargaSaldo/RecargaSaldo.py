#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : David Castellanos <dcastellanos@indra.es>
#           Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2011-2012, Telefonica Móviles España S.A.U.
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
import gobject
import thread
import threading
import time

import tgcm
import tgcm.core.Config
import tgcm.core.FreeDesktop
import tgcm.core.Singleton
import tgcm.core.Theme

import tgcm.ui.windows

from tgcm.ui.MSD.MSDUtils import error_dialog, gtk_builder_magic, Validate, ValidationError

class RecargaSaldo:
    __metaclass__ = tgcm.core.Singleton.Singleton

    def __init__(self):
        self.__phonequery_area = None
        self.__conf = tgcm.core.Config.Config()
        self.__device_manager = tgcm.core.FreeDesktop.DeviceManager()

        # Parent dialog
        self.__dialog = tgcm.ui.windows.ServiceWindow('banner.recargasaldo', \
                tgcm.dockables_info['recargasaldo'])

        theme_manager = tgcm.core.Theme.ThemeManager()
        icon_file = theme_manager.get_icon('icons', 'recarga_taskbar.png')
        self.__dialog.set_icon_from_file(icon_file)

        # Controls
        files_dir = os.path.join(tgcm.windows_dir, 'RecargaSaldo')

        gtk_builder_magic(self, \
            filename=os.path.join(files_dir, 'RecargaSaldo_main.ui'), \
            prefix='esp')
        self.__dialog.add(self.recargasaldo_main)

        # Load the BAM phone query area or Movistar (Spain)
        self.__phonequery_area = RecargaSaldoPhoneQuery(self.__dialog)
        self.phonenumber_parent.add(self.__phonequery_area.get_area())

        # RecargaSaldo links
        self.credit_card_link.set_uri(self.__conf.get_dockable_url('recargasaldo', 'url-1'))
        self.credit_card_link.set_tooltip_text('')
        self.topup_link.set_uri(self.__conf.get_dockable_url('recargasaldo', 'url-2'))
        self.topup_link.set_tooltip_text('')
        self.vouchers_link.set_uri(self.__conf.get_dockable_url('recargasaldo', 'url-3'))
        self.vouchers_link.set_tooltip_text('')

        self.__dialog.connect('delete_event', self.__on_dialog_close)
        self.__dialog.close_button.connect('clicked', self.__on_dialog_close)

    def run(self):
        self.__dialog.show()

    @staticmethod
    def is_visible():
        '''
        Returns a boolean depending if the 'Prepay Service' button should be available
        in the dock or not.

        @return: True if the 'Prepay Service' should be available, False otherwise.
        '''
        conf = tgcm.core.Config.Config()
        if not conf.is_last_imsi_seen_valid():
            is_prepay = conf.is_default_prepaid()
        else:
            imsi = conf.get_last_imsi_seen()
            is_prepay = conf.is_imsi_based_prepaid(imsi)
        return is_prepay

    def __on_dialog_close(self, *args):
        # Request the phone query area to validate its contents and save them
        try:
            self.__phonequery_area.do_save()

            # Only hide the dialog if the dialog fields are correct and have
            # been saved successfully
            self.__dialog.hide()

        # Seems there was a problem saving the BAM phone query area, warn the
        # user about the problem
        except RecargaSaldoSaveError, err:
            self.__phonequery_area.grab_focus()
            error_dialog(err.details, markup = err.msg, parent = self.__dialog)

        return True


class RecargaSaldoPhoneQuery():
    '''
    RecargaSaldoPhoneQuery provides an area for phone number determination in Movistar (Spain).
    The "Query" button is only enabled when a GSM device is detected, its card status is OK and
    the phone number for its card is unknown.

    @see: get_area()
    '''

    EVENT_IDLE                = 0
    EVENT_NUMBER_SMS_RECEIVED = 1
    EVENT_CLASS_ZERO_RECEIVED = 2
    EVENT_CANCEL              = 3
    EVENT_PROCESSING          = 4

    def __init__(self, parent=None):
        self.__conf = tgcm.core.Config.Config()
        self.__device_manager = tgcm.core.FreeDesktop.DeviceManager()
        self.__parent = parent

        files_dir = os.path.join(tgcm.windows_dir, 'RecargaSaldo')
        gtk_builder_magic(self, \
                filename=os.path.join(files_dir, 'RecargaSaldo_phonebox.ui'), \
                prefix='esp')

        # Some boolean variables necessary for the phone number determination algorithm
        self.__event_type  = self.EVENT_IDLE
        self.__query_event = threading.Event()

        # -- Update all the widgets
        self.__load_phone_number()
        self.__enable_widgets()

        # Some signals
        self.phonenumber_button.connect('clicked', self.__on_phonenumber_button_clicked)
        self.phonenumber_entry.connect('activate', self.__on_phonenumber_entry_activate)
        self.__conf.connect('last-imsi-seen-changed', self.__on_last_imsi_seen_changed)
        self.__conf.connect('user-mobile-broadband-number-changed', self.__on_phonenumber_changed)

        self.__device_manager.connect('active-dev-card-status-changed', self.__on_card_status_changed)
        main_modem = self.__device_manager.main_modem
        main_modem.connect('main-modem-changed', self.__main_modem_changed_cb)
        main_modem.connect('main-modem-removed', self.__main_modem_removed_cb)

    def do_save(self):
        '''
        Checks the phone number in the entry (if any) and if it is correct save it.

        @raise RecargaSaldoSaveError: If there was a problem while saving the phone number,
            e.g. the phone number is not valid.
        '''
        # If there have not been a valid IMSI in the system just return
        if not self.__conf.is_last_imsi_seen_valid():
            return

        phone_number = self.phonenumber_entry.get_text()

        # Check if the contents of the entry is a valid phone number
        try:
            if len(phone_number) != 0:
                phone_number = Validate.Spain.mobile_phone(phone_number)
            imsi = self.__conf.get_last_imsi_seen()
            self.__conf.set_user_mobile_broadband_number(imsi, phone_number)

        # If there was a problem with the validation throws an exception to let
        # someone manage the problem
        except ValidationError, err:
            msg = _('Invalid mobile broadband number')
            details = str(err)
            raise RecargaSaldoSaveError(msg, details)

    def grab_focus(self):
        self.phonenumber_entry.grab_focus()

    def set_description_label(self, text):
        self.phonenumber_label.set_markup(text)

    def __load_phone_number(self):
        if self.__conf.is_last_imsi_seen_valid():
            phone_number = self._get_phonenumber()
            self.phonenumber_entry.set_sensitive(True)
            self.phonenumber_entry.set_text(phone_number)
        else:
            self.phonenumber_entry.set_sensitive(False)

    def __enable_widgets(self):
        # Update accordingly the request button widget
        is_bam_available = self.__is_bam_available()
        self.phonenumber_button.set_sensitive(is_bam_available)

    def __is_bam_available(self):
        # If there isn't a WWAN device present in the system disable the query
        # button as the BAM query mechanism is not available
        main_modem = self.__device_manager.get_main_device()
        if main_modem is None:
            is_bam_available = False

        # The WWAN device seems to be turn off, so the BAM query mechanism is not
        # available too
        elif not main_modem.is_on():
            is_bam_available = False

        # The WWAN device seems to be not attached to the network, so the BAM
        # query mechanism is not available too
        elif not main_modem.is_card_ready():
            is_bam_available = False

        # The default behavior is to have the query button enabled and to
        # display the phone number of the last IMSI card present in the system
        else:
            is_bam_available = True

        return is_bam_available

    def processing(self):
        '''
        Returns True if the processing thread that executes the BAM query is active waiting for some operation
        '''
        return ((self.__event_type == self.EVENT_PROCESSING) or (self.__event_type == self.EVENT_CLASS_ZERO_RECEIVED))

    def get_area(self):
        '''
        Returns a widget for phone number determination in Movistar (Spain).

        @return: a GtkWidget.
        '''
        return self.phonenumber_hbox

    def _query_phone_number(self):
        '''
        Query mechanism for phone number determination in Movistar (Spain).

        The asynchronous BAM phone number query mechanism which in sending
        a special SMS message to a  phone number asking for the phone number of the current
        GSM card.
        '''
        thread.start_new_thread(self.__send_phone_number_request, ( ))

    def _get_phonenumber(self):
        '''
        Returns the phone number associated to the GSM card if it was previously known.

        @return: A string containing the phone number associated to the GSM card if known,
            an empty string otherwise.
        '''
        phone_number = ''
        if self.__conf.is_last_imsi_seen_valid():
            imsi = self.__conf.get_last_imsi_seen()
            phone_number = self.__conf.get_user_mobile_broadband_number(imsi)
        return phone_number

    # -- Handles the complete BAM query
    def __send_phone_number_request(self):

        # -- Arbitrary  maximal timeout for this operation
        QUERY_TIMEOUT_SECONDS = 20

        self.__query_event.clear()
        self.__event_type = self.EVENT_PROCESSING

        gobject.idle_add(self.__pre_send_phone_number_request)

        # -- We need to stop the main device checker as the BAM query would block the modem for some time
        main_device = self.__device_manager.get_main_device()
        main_device.stop_checker()
        time.sleep(2) # -- Arbitrary value long enough for the giving other threads the option to read from the modem

        # -- Get the custom SMSC
        use_custom_smsc = self.__conf.get_action_key_value('sms', 'use_custom_smsc')
        if use_custom_smsc:
            smsc = self.__conf.get_action_key_value('sms', 'custom_smsc')
        else:
            smsc = self.__conf.get_action_key_value('sms', 'smsc_any')

        # -- Connect locally to this signal for avoiding that other objects receive this signal too
        match = self.__device_manager.connect('active-dev-sms-bam-received' , self.__on_bam_sms_class_zero_received)

        # -- First send the request assuming a non-corporative SIM card
        for number in ('223523', '0223523'):

            # DeviceModem.sms_send() takes two function as parameters:
            # - OK handler is called when the SMS was properly sent.
            # - Error handler is called when the SMS could not be delivered.
            main_device.sms_send(number, smsc, 'NUMERO', self.__phonenumber_request_ok, \
                                 self.__phonenumber_request_error, store_message=False)

            # -- Now wait until some event is set
            self.__query_event.wait(timeout=QUERY_TIMEOUT_SECONDS)

            # -- Check if somebody has set the event
            if self.__query_event.is_set():

                self.__query_event.clear()

                # -- Good, the SMS has arrived, so we are done
                if self.__event_type == self.EVENT_NUMBER_SMS_RECEIVED:
                    break
                # -- If the class zero message has arrive continue with the next number
                elif self.__event_type == self.EVENT_CLASS_ZERO_RECEIVED:
                    continue
                # -- This event could appear when the modem was removed so check if the main modem is still available
                elif self.__event_type == self.EVENT_CANCEL:
                    break

            # -- Some modems don't support messages of class zero, so we need to send the request to the second number after
            # -- the first timeout
            elif self.__event_type == self.EVENT_PROCESSING:
                self.__event_type = self.EVENT_CLASS_ZERO_RECEIVED
                continue

            # -- That's ugly, we have a timeout and should not continue. Print the error message and stop further operations
            gobject.idle_add(self.__show_request_error, None)
            break

        # -- IMPORTANT: During the BAM query is possible that the main modem was removed!
        new_main = self.__device_manager.get_main_device()
        if (new_main is not None) and (main_device == new_main):
            main_device.start_checker()

        self.__device_manager.disconnect(match)
        self.__event_type = self.EVENT_IDLE
        gobject.idle_add(self.__post_send_phone_number_request)

    # -- Operations to be done before starting the BAM query
    def __pre_send_phone_number_request(self):

        def __update_progress_bar(pbar):
            pbar.pulse()
            return True

        # -- For avoiding any operation during the BAM query block the complete application with the help of a progress bar
        dlg = gtk.Dialog(parent = self.__parent,
                flags  = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        dlg.set_title(self.__conf.get_app_name())
        dlg.set_border_width(20)

        # -- Create the progress bar for the query operation
        pbar = gtk.ProgressBar()
        pbar.set_text(_("Waiting for operator response"))
        pbar.set_fraction(1.0)
        pbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)

        dlg.vbox.pack_start(pbar)
        pbar.show()

        pbar_id = gobject.timeout_add(200, __update_progress_bar, pbar)

        self.__dlg     = dlg
        self.__pbar_id = pbar_id

        # -- Be aware, this will block this thread
        dlg.set_resizable(False)
        while True:
            # -- Dont allow to close the progress dialog
            resp = dlg.run()
            if resp == gtk.RESPONSE_DELETE_EVENT:
                continue
            else:
                break

    # -- Operations to be done when the BAM query is done
    def __post_send_phone_number_request(self):
        gobject.source_remove(self.__pbar_id)
        self.__dlg.response(gtk.RESPONSE_CLOSE)
        self.__dlg.destroy()
        self.__dlg = None
        self.__enable_widgets()

    # -- Nice, the machine is rolling on
    def __phonenumber_request_ok(self, r):
        pass

    # -- Dont need to react to this callback as we will receive the SMS of class zero or the processing thread will
    # -- catch the timeout
    def __phonenumber_request_error(self, r):
        pass

    def __show_request_error(self, msg=None):
        '''
        DeviceModem.sms_send() Error handler: BAM SMS could not be delivered, the user must be
        informed about that.
        '''
        if msg is None:
            markup = _('Unexpected error')
            msg = _('We\'re sorry, but it was not possible to query your Broadband Mobile Number. Please try again later.')

        error_dialog(msg, markup = markup, parent = self.__parent)

    def __on_phonenumber_button_clicked(self, widget, data=None):
        # Disable "Query" button because only one concurrent petition is allowed
        self.phonenumber_button.set_sensitive(False)

        # Initiate the BAM query mechanism
        self._query_phone_number()

        # Clear the phone number area until end of BAM query mechanism
        self.phonenumber_entry.set_text('')

    def __on_phonenumber_entry_activate(self, widget, data=None):
        # Save if possible the phone number if the user presses Enter
        self.do_save()

    def __on_last_imsi_seen_changed(self, sender, imsi):
        self.__load_phone_number()
        self.__enable_widgets()

    def __on_phonenumber_changed(self, sender, phone_number):
        # Phone number has changed, so we assume that the response SMS message as arrived
        self.phonenumber_entry.set_text(phone_number)

        self.__event_type = self.EVENT_NUMBER_SMS_RECEIVED
        self.__query_event.set()

    def __on_bam_sms_class_zero_received(self, device_manager, number, text):
        self.__event_type = self.EVENT_CLASS_ZERO_RECEIVED
        self.__query_event.set()

    def __on_card_status_changed(self, device_manager, card_status):
        self.__enable_widgets()

    def __main_modem_changed_cb(self, main_modem, device_manager, device):
        self.__load_phone_number()
        self.__enable_widgets()

    def __main_modem_removed_cb(self, main_modem, objpath):
        '''
        Device removal callback. If a 3G/GSM device is removed, both the phone number field
        and the query button will be disabled.
        '''
        # -- Cancel the BAM query processing if it's active. The processing thrad will update the widgets
        if self.processing():
            self.__event_type = self.EVENT_CANCEL
            self.__query_event.set()
        else:
            self.__enable_widgets()

class RecargaSaldoSaveError(Exception):
    def __init__(self, msg, details):
        self.msg = msg
        self.details = details

    def __str__(self):
        return self.details
