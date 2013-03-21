#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#
# Copyright (c) 2003-2008, Telefonica Móviles España S.A.U.
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
PIN_STATUS_WAITING_PIN = 1
PIN_STATUS_WAITING_PUK = 2
PIN_STATUS_READY = 3
PIN_STATUS_NO_SIM = 4
PIN_STATUS_SIM_FAILURE = 5
PIN_STATUS_WAITING_PH_NET_PIN = 6
PIN_STATUS_WAITING_PH_NET_PUK = 7

# Card status codes
CARD_STATUS_ERROR = -1
CARD_STATUS_NO_DETECTED = 0
CARD_STATUS_DETECTED = 10
CARD_STATUS_CONFIGURED = 20
CARD_STATUS_NO_SIM = 25
CARD_STATUS_PIN_REQUIRED = 30
CARD_STATUS_PUK_REQUIRED = 40
CARD_STATUS_OFF = 50
CARD_STATUS_ATTACHING = 60
CARD_STATUS_READY = 70
CARD_STATUS_PH_NET_PIN_REQUIRED = 80
CARD_STATUS_PH_NET_PUK_REQUIRED = 90

CARD_TECH_GSM = 0
CARD_TECH_GSM_COMPACT = 1
CARD_TECH_UMTS = 2
CARD_TECH_HSPA = 3
CARD_TECH_HSDPA = 4
CARD_TECH_HSUPA = 5

CARD_DOMAIN_CS = 0
CARD_DOMAIN_PS = 1
CARD_DOMAIN_CS_PS = 2
CARD_DOMAIN_ANY = 4

CARD_TECH_SELECTION_GPRS = 0
CARD_TECH_SELECTION_UMTS = 1
CARD_TECH_SELECTION_GRPS_PREFERED = 2
CARD_TECH_SELECTION_UMTS_PREFERED = 3
CARD_TECH_SELECTION_NO_CHANGE = 4
CARD_TECH_SELECTION_AUTO = 5

PPP_STATUS_DISCONNECTED = 0
PPP_STATUS_CONNECTED = 1
PPP_STATUS_CONNECTING = 2
PPP_STATUS_DISCONNECTING = 3
