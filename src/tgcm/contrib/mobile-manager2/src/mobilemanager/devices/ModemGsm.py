#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
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

MODE_UNKNOWN      = 0x00000000
MODE_ANY          = 0x00000001
MODE_GPRS         = 0x00000002
MODE_EDGE         = 0x00000004
MODE_UMTS         = 0x00000008
MODE_HSDPA        = 0x00000010
MODE_2G_PREFERRED = 0x00000020
MODE_3G_PREFERRED = 0x00000040
MODE_2G_ONLY      = 0x00000080
MODE_3G_ONLY      = 0x00000100
MODE_HSUPA        = 0x00000200
MODE_HSPA         = 0x00000400
MODE_GSM          = 0x00000800
MODE_GSM_COMPACT  = 0x00001000

ALLOWED_MODE_ANY          = 0
ALLOWED_MODE_2G_PREFERRED = 1
ALLOWED_MODE_3G_PREFERRED = 2
ALLOWED_MODE_2G_ONLY      = 3
ALLOWED_MODE_3G_ONLY      = 4
ALLOWED_MODE_LAST = ALLOWED_MODE_3G_ONLY

DOMAIN_CS = 0
DOMAIN_PS = 1
DOMAIN_CS_PS = 2
DOMAIN_ANY = 3 

ACCESS_TECH_UNKNOWN     = 0
ACCESS_TECH_GSM         = 1
ACCESS_TECH_GSM_COMPACT = 2
ACCESS_TECH_GPRS        = 3
ACCESS_TECH_EDGE        = 4  # GSM w/EGPRS 
ACCESS_TECH_UMTS        = 5  # UTRAN 
ACCESS_TECH_HSDPA       = 6  # UTRAN w/HSDPA 
ACCESS_TECH_HSUPA       = 7  # UTRAN w/HSUPA 
ACCESS_TECH_HSPA        = 8  # UTRAN w/HSDPA and HSUPA 
ACCESS_TECH_HSPA_PLUS   = 9

ACCESS_TECH_LAST = ACCESS_TECH_HSPA


BAND_UNKNOWN      = 0x00000000
BAND_ANY          = 0x00000001
BAND_EGSM         = 0x00000002 #  900 MHz 
BAND_DCS          = 0x00000004 # 1800 MHz 
BAND_PCS          = 0x00000008 # 1900 MHz 
BAND_G850         = 0x00000010 #  850 MHz 
BAND_U2100        = 0x00000020 # WCDMA 3GPP UMTS 2100 MHz     (Class I) 
BAND_U1800        = 0x00000040 # WCDMA 3GPP UMTS 1800 MHz     (Class III) 
BAND_U17IV        = 0x00000080 # WCDMA 3GPP AWS 1700/2100 MHz (Class IV) 
BAND_U800         = 0x00000100 # WCDMA 3GPP UMTS 800 MHz      (Class VI) 
BAND_U850         = 0x00000200 # WCDMA 3GPP UMTS 850 MHz      (Class V) 
BAND_U900         = 0x00000400 # WCDMA 3GPP UMTS 900 MHz      (Class VIII) 
BAND_U17IX        = 0x00000800 # WCDMA 3GPP UMTS 1700 MHz     (Class IX) 
BAND_U1900        = 0x00001000 # WCDMA 3GPP UMTS 1900 MHz     (Class II) 

BAND_LAST = BAND_U1900

NETWORK_REG_STATUS_IDLE = 0
NETWORK_REG_STATUS_HOME = 1
NETWORK_REG_STATUS_SEARCHING = 2
NETWORK_REG_STATUS_DENIED = 3
NETWORK_REG_STATUS_UNKNOWN = 4
NETWORK_REG_STATUS_ROAMING = 5
