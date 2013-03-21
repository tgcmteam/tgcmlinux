#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
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

#Datos para el uso de DBUS
PPP_MANAGER_OBJECT_PATH ="/es/tid/em/PPPManager"
PPP_MANAGER_SERVICE_NAME="es.tid.em.PPPManager"
PPP_MANAGER_INTERFACE_NAME ="es.tid.em.IPPPManager"

PPP_CONNECT_SIGNAL ="connected_signal"
PPP_DISCONNECT_SINGAL ="disconnected_signal"
PPP_CONNECTING_SIGNAL ="connecting_signal"
PPP_DISCONNECTING_SIGNAL ="disconnecting_signal"


#Estado del PPPD
PPP_STATUS_DISCONNECTED = 0
PPP_STATUS_CONNECTED = 1 
PPP_STATUS_CONNECTING = 2
PPP_STATUS_DISCONNECTING = 3

#Keys par el diccionario que continen los parametros de conexion

#(String)  El login para usar en la conexion 
PPP_PARAM_DEVICE_PORT_KEY ="DEVICE_PORT"

#(Numerico) VELOCIDAD para usar en la conexion
PPP_PARAM_DEVICE_SPEED_KEY ="DEVICE_SPEED"  

#(String) El login para usar en la conexion
PPP_PARAM_LOGIN_KEY ="LOGIN"

#(String) El password para usar en la conexion
PPP_PARAM_PASSWORD_KEY ="PASWORD"

# (String) el apn para conectars
PPP_PARAM_APN_KEY ="APN" 

PPP_PARAM_USE_PROXY_KEY = "USE_PROXY" # (boolean) si vamos ha usar proxy
PPP_PARAM_PROXY_ADDRESS_KEY = "PROXY_ADDRESS" # (String) La direcion de proxy
PPP_PARAM_PROXY_PORT_KEY ="PROXY_PORT" # (int) el puerto del proxy

PPP_PARAM_AUTO_DNS_KEY ="AUTO_DNS" # bool
PPP_PARAM_PRIMARY_DNS_KEY ="PRIMARY_DNS" # (string)el puerto primario
PPP_PARAM_SECUNDARY_DNS_KEY ="SECUNDARY_DNS" # (string) el puerto secundario

PPP_PARAM_DNS_SUFFIX_KEY = "DNS_SUFFIX" # (string) sufijos de busqueda


PPP_PARAM_COMPRESSION_KEY = "COMPRESION" # (boolean) compresion en la conexion
PPP_PARAM_FLOW_CONTROL_KEY = "FLOW_CONTROL" #(boolean) control de flujo
PPP_PARAM_ERROR_CONTROL_KEY = "ERROR_CONTROL" #(boolean) control de errorres

PPP_PARAM_CYPHER_PASSWORD_KEY = "CYPHER_PASSWORD" #(boolean) cifrar paswwod
