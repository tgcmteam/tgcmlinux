#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#
# Copyright (c) 2003-2007, Telefonica Móviles España S.A.U.
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

MSG_ERROR_CARDMANAGER_NOT_AVAILABLE = _("Connection with the Mobile Internet Device cannot be established.")


#Card manager
MSG_STATUS_SEARCHING_CARD = ""
MSG_STATUS_INITIALIZING_CARD = _("Running device")
MSG_STATUS_CARD_OFF = _("Device off")
MSG_STATUS_WAINTING_PIN = _("Checking PIN code")
MSG_STATUS_WAINTING_PUK = _("Checking PUK code")
MSG_STATUS_CARD_ATTACHING = _("Searching network and registering")
MSG_STATUS_CARD_READY = _("Device ready")
MSG_STATUS_CARD_NOT_DETECTED = _("Device not detected")
MSG_STATUS_CARD_DETECTED = _("Device detected")

#dialog de Seguridad sim SIM

MSG_SIM_SEC_INSERT_PIN = _("Introduce the device PIN")
MSG_SIM_SEC_DEACTIVATE_PIN = _("The SIM device PIN code is activated.\nTo activate it enter its value in the box\nand click on Accept.")
MSG_SIM_SEC_ACTIVATE_PIN = _("The SIM device PIN code is deactivated.\nTo activate it enter its value in the box\nand click on Accept.")
MSG_SIM_SEC_WRONG_PIN = _("The PIN code entered is incorrect.")
MSG_SIM_SEC_WRONG_PIN_FORMAT = _("The PIN code entered must have between 4 and 8 figures.\nPlease, try again.")
MSG_SIM_SEC_PIN_VERIFICATION_FAILED = _("The PIN and the PIN check do not coincide.")
MSG_SIM_SEC_PUK_FAILED = _("The PUK code entered is incorrect.")
MSG_AT_COMMAND_FAILED = _("Connection with the Mobile Internet Device cannot be established.")

MSG_PUK_INSERTION_CANCELED = _("You have cancelled the process checking your PUK code and Mobile Internet Device will go off\n\nTo run the process again start it from the device menu through the option 'Activate device'.")
MSG_PUK_INSERTION_CANCELED_TITLE = _("Checking cancelled")

MSG_PIN_INSERTION_CANCELED = _("You have cancelled the process checking the PIN code and your Device Mobile Internet will go off.\n\nTo run the process again start it from the device menu through the option 'Activate device'.")


MSG_PIN_INSERTION_CANCELED_TITLE = _("Checking cancelled")

MSG_PIN_CHANGE_FAILED = _("The SIM device PIN code change procedure has been unsuccessful.\nThe Mobile Internet Device will now go off. The next time that it is turned on its PUK code will be requested.")
MSG_PIN_CHANGE_FAILED_TITLE = _("Error when changing the PIN")


#Estados del pin
MSG_SIM_PIN_ACTIVE = _("Activated")
MSG_SIM_PIN_NO_ACTIVE = _("Deactivated")

MSG_PIN_ACTIVE_INFO = _("The SIM device PIN code is activated.\nTo deactivate it enter its value in the box and click on the Accept button.")

MSG_PIN_INACTIVE_INFO = _("The SIM device PIN code is deactivated.\nTo activate it enter its value in the box and click on the Accept button.")

#buscar operadora
MSG_CARRIER_IS_LONG_OPERATION_TITLE = _("Select operator manual")
MSG_CARRIER_IS_LONG_OPERATION = _("A search for available operators will now be carried out. This operation could take a few minutes. To start the search click on Accept.")

MSG_PIN_MANAGE_FAILED = _("An error has occurred in the activate/deactivate process of the PIN code of the SIM device.\nThe Mobile Internet Device will now go off. The next time that it is turned on its PUK code will be requested.")

MSG_PIN_MANAGE_FAILED_TITLE = _("Error on activating/deactivating the PIN")

MSG_SEARCHING_CARRIERS = _("Please, wait while it searches for available operators.\nThis process could take a few minutes.")
MSG_SEARCHING_CARRIERS_TITLE = _("Searching for operators")

MSG_CARRIER_SEARCH_ERROR = _("An error has occurred while searching for available operators.")
MSG_CARRIER_ATTACH_ERROR = _("An error has occurred while the selected operator was being configured.")

MSG_ATTACHING_CARRIER = _("Please wait while the operator is being configured\nselected.")
MSG_ATTACHING_CARRIER_TITLE = _("Configuring operator")

MSG_RESET_CONSUM_WARNING = _("On restarting the information on the accumulated traffic will be deleted.")

#Bookmarks

MSG_DELETE_BOOKMARK_TITLE = _("<b>Delete favourite</b>")
MSG_DELETE_BOOKMARK = _("Do you want to delete the favourite '%s'?")

MSG_ADD_BOOKMARK_TITLE = _("New favourite")
MSG_EDIT_BOOKMARK_TITLE = _("Modify favourite")

MSG_INVALID_BOOKMARK_NAME_TITLE = _("<b>Favourite name is invalid</b>")
MSG_INVALID_BOOKMARK_NAME = _("The favourite name cannot have the character '/'.")

MSG_NO_BOOKMARK_NAME_TITLE = _("<b>Favourite name</b>")
MSG_NO_BOOKMARK_NAME = _("Enter a name for the favourite.")

MSG_BOOKMARK_NAME_EXISTS_TITLE = _("<b>A favourite with the name '%s' already exists</b>")
MSG_BOOKMARK_NAME_EXISTS = _("Please choose another name.")

MSG_BOOKMARK_NO_FILE_SELECTED_TITLE = _("<b>You have not chosen a file</b>")
MSG_BOOKMARK_NO_FILE_SELECTED = _("Please choose a file to create the favourite.")

MSG_BOOKMARK_NO_URL_SELECTED_TITLE = _("<b>You have not entered the URL</b>")
MSG_BOOKMARK_NO_URL_SELECTED = _("Please enter a URL to create the favourite.")

#Connections

MSG_DELETE_CONNECTION_TITLE = _("<b>Delete connection</b>")
MSG_DELETE_CONNECTION = _("Do you want to delete the connection '%s'?")

MSG_DELETE_DEFAULT_CONNECTION_TITLE = _("<b>Delete default connection</b>")
MSG_DELETE_DEFAULT_CONNECTION = _("The default connection can not be deleted.\nIf you are sure you want to delete this connection, select another one as default.")

MSG_ADD_CONNECTION_TITLE = _("New connection")
MSG_EDIT_CONNECTION_TITLE = _("Modify connection")

MSG_CONNECTION_NAME_EXISTS_TITLE = _("<b>A connection with the name '%s' already exists</b>")
MSG_CONNECTION_NAME_EXISTS = _("Please choose another name")

MSG_NO_CONNECTION_NAME_TITLE = _("<b>Connection name</b>")
MSG_NO_CONNECTION_NAME = _("Enter a name to connect.")

MSG_NO_CONNECTION_USER_TITLE = _("<b>Enter a user</b>")
MSG_NO_CONNECTION_USER = _("You have not entered the user name to connect.")

MSG_NO_CONNECTION_APN_TITLE = _("<b>Enter the APN</b>")
MSG_NO_CONNECTION_APN = _("You have not entered the APN.")

MSG_NO_CONNECTION_PASSWORD_TITLE = _("<b>Enter the password</b>")
MSG_NO_CONNECTION_PASSWORD = _("You have not entered the connection password.")

MSG_NO_CONNECTION_PROFILE_TITLE = _("<b>The personalised profile field is empty</b>")
MSG_NO_CONNECTION_PROFILE = _("Please, state the personalised profile that you want to use.")

MSG_NO_CONNECTION_DNS_TITLE = _("<b>The DNS information is incomplete</b>")
MSG_NO_CONNECTION_DNS = _("Please, fill in the corresponding fields correctly.")

MSG_NO_CONNECTION_PROXY_IP_TITLE = _("<b>The Proxy address is invalid</b>")
MSG_NO_CONNECTION_PROXY_IP = _("Enter a valid address.")

MSG_NO_CONNECTION_PROXY_PORT_TITLE = _("<b>he Proxy port is invalid</b>")
MSG_NO_CONNECTION_PROXY_PORT = _("Positive whole numbers are allowed.")

#Connections Manager

MSG_CONN_MANAGER_NO_PPP_MANAGER_TITLE = _("<b>Connection with the PPP Manager cannot be established</b>")
MSG_CONN_MANAGER_NO_PPP_MANAGER = _("Connection through the PPP Manager has failed. This means that at the moment it is impossible to establish connection with Internet with this application.")

MSG_CONN_MANAGER_ASK_PASSWORD = _("<b>Enter the user password to the connection '%s'</b>")

MSG_CONN_MANAGER_NO_CARDMANAGER_TITLE = _("<b>Connection is not possible</b>")
MSG_CONN_MANAGER_NO_CARDMANAGER = _("The Mobile Internet Device is not ready to be connected. Please Insert it or turn it on if it is off and wait until it is registered on the network.")

MSG_CONN_MANAGER_APP_CLOSE_TITLE = _("Close Escritorio Movistar")
MSG_CONN_MANAGER_APP_CLOSE = _("If you close the %s, the connection in progress will be disconnected. Do you want to continue closing %s?")

MSG_CONN_MANAGER_NO_DEVICE_TITLE = _("<b>No device has been selected</b>")
MSG_CONN_MANAGER_NO_DEVICE = _("The requested connection cannot be established as there is no device. Please choose a device in the Configuration window.")

MSG_CONN_MANAGER_CONNECTION_ERROR_TITLE = _("<b>Error in the connection</b>")
MSG_CONN_MANAGER_CONNECTION_ERROR = _("Connection cannot be established. Please, try again.")

MSG_CONN_MANAGER_ACTIVE_CONN_DETECT_TITLE = _("<b>Another active connection has been detected</b>")

MSG_CONN_MANAGER_OPEN_SERVICE_TITLE = _("<b>Open service '%s'</b>")
MSG_CONN_MANAGER_OPEN_SERVICE = _("Do you want to establish connection associated with the service? (%s)")
MSG_CONN_MANAGER_OPEN_SERVICE_WITH_ACTIVE_CONN = _("At the moment you are connected to '%s'. Do you want to open the service by changing your associated connection '%s' or would you prefer to use the current connection?\nIf you change the connection you could loose information in other services and Open favourites.")
MSG_CONN_MANAGER_OPEN_SERVICE_WITH_ACTIVE_CONN_DEFAULT = _("At the moment you are connected to '%s'. Do you want to open the service by changing to your default connection '%s' or do you prefer to use the connection current?\nIf you change the connection you could loose information in other services and Open favourites.")


MSG_CONN_MANAGER_OPEN_BOOKMARK_TITLE = _("<b>Open favourite '%s'</b>")
MSG_CONN_MANAGER_OPEN_BOOKMARK = _("Do you want to establish the connection associated with the favourite? (%s)")
MSG_CONN_MANAGER_OPEN_BOOKMARK_WITH_ACTIVE_CONN = _("At the moment you are connected to '%s'. Do you want to open the favourite? by changing your associated connection '%s' or would you prefer to use the current connection?\nIf you change the connection you could loose information in other services and Open favourites.")
MSG_CONN_MANAGER_OPEN_BOOKMARK_WITH_ACTIVE_CONN_DEFAULT = _("At the moment you are connected to '%s'. Do you want to open the favourite? by changing to your default connection '%s' or do you prefer to use the connection current?\nIf you change the connection you could loose information in other services and Open favourites.")

MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_TITLE = _("<b>Connect to the pre-set connection</b>")
MSG_CONN_MANAGER_CONNECT_TO_CONN_TITLE = _("<b>Connect to the selected connection</b>")
MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_WITH_ACTIVE_CONN = _("At the moment you are connected to '%s'. Do you want to open the connection '%s' or Do you prefer to use the current connection?\nIf you change the connection you could loose information in other services and Open favourites.")

MSG_CONN_MANAGER_CONNECT_TO_DEFAULT_CONN = _("Do you want to establish the preset connection (%s)?")
MSG_CONN_MANAGER_CONNECT_TO_CONN = _("Do you want to establish the connection (%s)?")

MSG_INVALID_PHONE_TITLE = _("<b>The telephone number is invalid</b>")
MSG_INVALID_PHONE =  _("Numerical characters are the values allowed.")
