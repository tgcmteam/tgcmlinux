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
import tempfile
import webbrowser

import tgcm
import tgcm.core.Config
import tgcm.core.Singleton

import tgcm.ui.ThemedDock

from MSDMessages import *
from tgcm.ui.MSD.MSDUtils import gtk_builder_magic

TEMPLATE_DATA ="""<html>
<body>
<style type="text/css">
input.flat{
    color:#333;
      font-family:'trebuchet ms',helvetica,sans-serif;
      font-size:84%%;
      font-weight:bold;
      border:1px solid;
      border-top-color:#999;
      border-left-color:#999;
      border-right-color:#666;
      border-bottom-color:#666;
}
input.invisible{
  background-color:transparent;
  border:0px;
  display:none;
}


</style>

<p align="center">
<form id="frm" action="%(url)s" method="POST">
    <input type="hidden" name="TM_LOGIN" value="%(login)s">
    <input type="hidden" name="TM_PASSWORD"  value="%(password)s">
    <input type="hidden" name="TM_ACTION"  value="LOGIN">
    <input type="hidden" name="URL"  value="%(url)s">
    <input class="invisible" id="sub" type="submit" class="flat" value="">
</form>
</p>
<script language="JavaScript"><!--
    document.getElementById("sub").value="";
    document.getElementById("sub").className="invisible";
    document.getElementById("frm").submit();
//-->
</script>
</body>
</html>"""


class MSDSecurityManager(object):
    """
    Esta clase encapsula la gestion de los seervicios seguros
    """

    __metaclass__ = tgcm.core.Singleton.Singleton

    def __init__(self):
        self.doc_manager = tgcm.core.DocManager.DocManager()

        self.conf = tgcm.core.Config.Config()

        gtk_builder_magic(self, \
                filename=os.path.join(tgcm.msd_dir, 'MSDSecurityManager_dialog.ui'), \
                prefix='sec')

        self.help_button.connect("clicked",self.__help_button_cb)
        self.phone_entry.connect("changed", self.__security_dialog_entry_changed, None)
        self.password_entry.connect("changed", self.__security_dialog_entry_changed, None)


    def launch_url(self, url, parent=None):
        """
        lanza la url  de mananera compatible con la seguirdad unificada de TME.
        Si la seguridad NO  esta activada la url se lanza de la manera normal
        """
        if self.conf.get_auth_activate():
            self.launch_secure_url(url, parent)
        else:
            #tgcm.debug("lanzando URL NO segura")
            webbrowser.open(url)

    def launch_secure_url(self, url, parent=None):
        #tgcm.debug("LANZANDO URL SEGURA %s" % url)
        current_login, current_password = self.conf.get_celular_info()

        if  self.__should_ask_password() :
            response, current_login, current_password = self.__run_security_dialog(parent)
            if response != gtk.RESPONSE_OK:
                return

        template_dict = {"url" : url,
                         "login": current_login,
                         "password": current_password}
        file_name =self.__create_temporal_file(template_dict)
        if file_name is not None:
            webbrowser.open(file_name)
        else:
            tgcm.error("ERROR creando fichero temporal")

    def __help_button_cb(self,widget):
        doc = "tgcm_060.htm#user_details"
        parts = doc.split('#')
        path = self.doc_manager.get_doc_path(parts[0])
        if len(parts) > 1:
            webbrowser.open("file://%s#%s" % (path, parts[1]))
        else:
            webbrowser.open("file://%s" % path)

    def __create_temporal_file(self,template_dict):
        try:
            os.system("rm -rf /tmp/em-*")
            # creo el fichero temporal
            fd ,file_name = tempfile.mkstemp("","em-")
            f = os.fdopen(fd,"w")
            f.write(TEMPLATE_DATA % template_dict)
            f.close()
            return file_name
        except Exception ,msg:
            tgcm.error("error creando temporal file url %s " % msg)
            return None

    def __should_ask_password(self):
        if self.conf.get_ask_password_activate():
            return True

        login, password =  self.conf.get_celular_info()

        if login is None or password is None:
            return True

        if len(login) == 0 or len(password) == 0:
            return True

        return False

    def run_security_dialog(self, parent=None):
        return self.__run_security_dialog(parent)

    def __run_security_dialog(self, parent=None):
        #inicializo los campos
        current_login, current_password = self.conf.get_celular_info()
        if current_password is None :
            current_password = ""
        if current_login is None:
            current_login = ""

        self.phone_entry.set_text(current_login)

        if  self.conf.get_ask_password_activate():
            self.password_entry.set_text("")
            self.remember_data_checkbutton.set_active(False)
        else:
            self.password_entry.set_text(current_password)
            self.remember_data_checkbutton.set_active(True)
        self. __security_dialog_entry_changed(self.password_entry,None)

        # Establish the transient relation of the dialog with a suitable parent
        if parent is None:
            parent = tgcm.ui.ThemedDock().get_main_window()
        self.security_dialog.set_transient_for(parent)

        while True:
            response = self.security_dialog.run()
            self.security_dialog.hide()
            login =  self.phone_entry.get_text()
            password = self.password_entry.get_text()
            if response != gtk.RESPONSE_OK:
                break

            try:
                int(login)
                break
            except Exception, msg:
                dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
                dlg.set_markup(MSG_INVALID_PHONE_TITLE)
                dlg.format_secondary_markup(MSG_INVALID_PHONE)
                dlg.run()
                dlg.destroy()

        if response == gtk.RESPONSE_OK and self.remember_data_checkbutton.get_active():
            #salvo los datos
            self.conf.set_celular_info(login,password)
            self.conf.set_ask_password_activate(False)

        return response,login,password

    def __security_dialog_entry_changed(self,widget,data):
        if len(self.password_entry.get_text()) < 1 or len(self.phone_entry.get_text()) < 1:
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)

if __name__ == '__main__':
    a = MSDSecurityManager([1,2,3])
    b = MSDSecurityManager([4,5,6])
