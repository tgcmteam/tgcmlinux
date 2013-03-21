#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#           Oier Blasco <oierblasco@gmail.com>
#           Alvaro Peña <alvaro.pena@openshine.com>
#           David Castellanos <dcastellanos@indra.es>
#
# Copyright (c) 2003-2013, Telefonica Móviles España S.A.U.
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

import math
import base64
import os
import socket
import struct
import time
import re
import stat
import StringIO
import subprocess
import threading
import webbrowser

import gtk

import tgcm
import tgcm.ui
import tgcm.core.Config
from tgcm.ui.widgets.common import WrapLabel

decode_key = 'EnUnLugarDeLaMancha'

def show_notification(title, msg, urgency="normal", seconds=5000, icon="movistar_icon_notify"):
    return

    if (os.path.exists ("/usr/bin/notify-send") == False):
        if (os.path.exists ("/opt/gnome/bin/notify-send") == False):
            return

    arguments = "-u " + urgency
    arguments += " -t " + str(seconds)
    if icon:
        arguments += " -i " + icon
    arguments += " \"" + title + "\" " + "\"" + msg + "\""

    os.system("notify-send " + arguments)

def format_to_maximun_unit(number,*args):
    n = int(number)
    base = 1024
    #"GBytes","MBytes","Kbytes","bytes")
    max_exponent = len(args) +1
    # determinoo la maxima unidad
    exponent = 0
    for i in range(1,max_exponent):
        exponent = i
        if number <  math.pow(base,i):
            break

    units = list(args)
    units.reverse()
    new_value = float(number) / math.pow(base,exponent-1)
    return "%.2f %s"%(new_value,units[exponent-1])

def format_to_maximun_unit_one_decimal(number,*args):

    n = int(number)
    units = list(args)

    # -- By negative values, return at this point with the lowermost unit
    if n < 0:
        return "0.0 %s" % units[-1]

    base = 1024
    #"GBytes","MBytes","Kbytes","bytes")
    max_exponent = len(args) +1
    # determinoo la maxima unidad
    exponent = 0
    for i in range(1,max_exponent):
        exponent = i
        if number <  math.pow(base,i):
            break

    units.reverse()
    new_value = float(number) / math.pow(base,exponent-1)
    try:
        if str(new_value).split(".")[1][0] == "0" :
            return "%.0f %s"%(new_value,units[exponent-1])
        else:
            return "%.1f %s"%(new_value,units[exponent-1])
    except:
        return "%.1f %s"%(new_value,units[exponent-1])

def format_to_maximun_unit_with_integers(number,*args):
    n = int(number)
    base = 1024
    #"GBytes","MBytes","Kbytes","bytes")
    max_exponent = len(args) +1
    # determinoo la maxima unidad
    exponent = 0
    for i in range(1,max_exponent):
        exponent = i
        if number <  math.pow(base,i):
            break

    units = list(args)
    units.reverse()
    new_value = float(number) / math.pow(base,exponent-1)
    return "%i %s"%(new_value,units[exponent-1])

def seconds_to_hours_minutes_seconds(seconds):
    try:
        secs = int(seconds)
        h = secs / (3600)
        t = secs - (h * 3600)
        m = t / 60
        s = t - (m * 60)
        t = secs - (h * 3600)
        return h,m,s
    except Exception, msg:
        return -1,-1,-1

def seconds_to_time_string(seconds):
    h,m,s = seconds_to_hours_minutes_seconds(seconds)
    return  "%02d:%02d:%02d" %(h,m,s)

def get_month_day (n):
    month_days = {1: _('1st'),
                  2: _('2nd'),
                  3: _('3rd'),
                  4: _('4th'),
                  5: _('5th'),
                  6: _('6th'),
                  7: _('7th'),
                  8: _('8th'),
                  9: _('9th'),
                  10: _('10th'),
                  11: _('11th'),
                  12: _('12th'),
                  13: _('13th'),
                  14: _('14th'),
                  15: _('15th'),
                  16: _('16th'),
                  17: _('17th'),
                  18: _('18th'),
                  19: _('19th'),
                  20: _('20th'),
                  21: _('21st'),
                  22: _('22nd'),
                  23: _('23rd'),
                  24: _('24th'),
                  25: _('25th'),
                  26: _('26th'),
                  27: _('27th'),
                  28: _('28th'),
                  29: _('29th'),
                  30: _('30th'),
                  31: _('31st')
                 }
    return month_days[n]

def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)

def decode_password(encrypted_password_string):
    '''
    La password no se encuentra en claro en los ficheros exportados por ellso hay
    que decodificarla. Esta funcion toma una cadena como parametro que representa
    la password tal como se encuentra escrita en el fichero de servicio
    '''

    encrypted_password = encrypted_password_string.strip()
    if encrypted_password == "":
        return ""

    # convertir en una cadena  base64 valida
    tmp_buf = encrypted_password.replace("*","=")
    #decode base 64
    tmp_buf = base64.decodestring(tmp_buf)
    #XOR

    key_size = len(decode_key)
    clear_password = ''

    for i in range(len(tmp_buf)):
        ch1 = ord(tmp_buf[i])
        ch2 = ord(decode_key[i % key_size])
        clear_ch = chr(ch1 ^ ch2)
        if clear_ch == chr(0):
            clear_ch = chr (ch2)
        clear_password += str(clear_ch)
    return clear_password.strip("\n")

def encode_password(password):
    '''
    Codifica la password para no escribirla en claro en los ficheros exportados
    '''
    #XOR
    if (password is None):
        return None;

    tmp_buf = ""
    key_size = len(decode_key)
    for i in range(len(password)):
        ch1 =  ord(password[i])
        ch2 =  ord(decode_key[i % key_size])
        tmp_ch = chr(ch1 ^ ch2)
        if tmp_ch == chr(0):
            tmp_ch = chr (ch2)
        tmp_buf += str(tmp_ch)

    #base64 encode
    tmp_buf = base64.encodestring(tmp_buf)
    #cambiar = por *
    tmp_buf = tmp_buf.replace("=","*")
    return tmp_buf.strip("\n")

def num_to_dotted_ip (num):
    return socket.inet_ntoa (struct.pack ('>L', num))

def set_active_dev_by_default(mcontroller):
    tgcm.debug("FIXME MM2 : set_active_dev_by_default")

#     dev = mcontroller.get_main_device()
#     if dev != None:
#         fd = open (tgcm.default_device_file, "w")
#         fd.write(dev)
#         tgcm.debug("set by default -> %s" % dev)
#         fd.close()

def gtk_builder_magic(self, filename, prefix=''):
    main_ui_filename = os.path.join(tgcm.glade_files_dir, filename)
    builder = gtk.Builder()
    builder.set_translation_domain(tgcm.LOCALE_DOMAIN)
    builder.add_from_file(main_ui_filename)

    self.builder = builder

    prefix_len = len(prefix)
    for widget in builder.get_objects():
        # Attempt to store references to only those widgets whose name matches
        # the prefix
        try:
            full_name = gtk.Buildable.get_name(widget)   # workaround to get widget's name
            if len(prefix) > 0:
                widget_name = full_name[prefix_len+1:]
            else:
                widget_name = full_name

            widget_prefix = full_name[:prefix_len]
            if widget_prefix == prefix:
                setattr(self, widget_name, widget)

        # It's not possible to get the name of some widgets (e.g. gtk.Adjustment).
        # In that case just ignore them...
        except:
            pass

    return builder

def get_subbitmaps (bitmap, frames, width, height, horizontal=True):
    subbitmaps = []

    top = 0
    left = 0
    for frame in xrange (0, frames):
        subbitmap = gtk.gdk.Pixbuf (gtk.gdk.COLORSPACE_RGB, True, 8, width, height)
        bitmap.copy_area (left, top, width, height, subbitmap, 0, 0)
        subbitmaps.append (subbitmap)

        if horizontal:
            left += width
        else:
            top += height

    return subbitmaps

# -- Sleep for some seconds without blocking the Gtk main thread
def gtk_sleep(seconds):

    if seconds <= 0:
        return

    time_start = time.time()
    time_end   = time_start + seconds

    while time_end > time.time():
        while gtk.events_pending():
            gtk.main_iteration()

def _Dialog(dlg_type, buttons):
    """
    Decorator for displaying different dialog messages
     dlg_type    : GtkMessageType, gtk.MESSAGE_ERROR
     buttons : GtkButtonsType, gtk.BUTTONS_OK_CANCEL
    """
    def dialog(msg, markup=None, title=None, parent=None, buttons=buttons, \
               flags=(gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), \
               icon=None, threaded=False):
        """
        This function will be executed for displaying the dialog
          msg      : Message to be displayed
          markup   : Optional markup (displayed in bold above the message)
          title    : Optional title, otherwise set the application name as title
          buttons  : This is set by the function declaration
          flags    : Options dialog flags
          icon     : Icon name to be imported from ThemeManager
          threaded : Run the dialog with 'gobject.idle_add()'.
                     IMPORTANT: Needs the right Gtk context when enabled
        """

        if title is None:
            conf = tgcm.core.Config.Config()
            title = conf.get_app_name()

        if parent is None:
            parent = tgcm.ui.ThemedDock().get_main_window()

        dlg = gtk.MessageDialog(parent=parent, flags=flags, type=dlg_type, buttons=buttons)
        dlg.set_deletable(False)
        dlg.set_title(title)

        # Avoid the dialog label to get the focus (and to appear
        # highlighted sometimes)
        dlg.label.set_can_focus(False)

        if icon is not None:
            if isinstance(icon, str):
                manager = tgcm.core.Theme.ThemeManager()
                icon = manager.get_icon('icons', icon)
            dlg.set_icon_from_file(icon)

        if markup is not None:
            dlg.set_markup('%s' % markup)
            dlg.format_secondary_markup(msg)
        else:
            dlg.set_markup('%s' % msg)

        if threaded is True:
            return dlg
        else:
            return __dialog_run(dlg)

    def __dialog_run(dlg):
        resp = dlg.run()
        dlg.destroy()
        return resp

    def newf(func):
        return dialog
    return newf

@_Dialog(gtk.MESSAGE_ERROR, gtk.BUTTONS_OK)
def error_dialog():
    pass

@_Dialog(gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO)
def question_dialog():
    pass

@_Dialog(gtk.MESSAGE_WARNING, gtk.BUTTONS_OK)
def warning_dialog():
    pass

@_Dialog(gtk.MESSAGE_INFO, gtk.BUTTONS_OK)
def info_dialog():
    pass

@_Dialog(gtk.MESSAGE_INFO, gtk.BUTTONS_NONE)
def wait_dialog():
    pass

# -- Kindly provided by Matthias:
# -- http://stackoverflow.com/questions/3107290/in-place-substitution-of-pygtk-widgets
def replace_widget(current, new, show=True):
    """
    Replace one widget with another.
    'current' has to be inside a container (e.g. gtk.VBox).
    """
    container = current.parent
    assert container # is "current" inside a container widget?

    # stolen from gazpacho code (widgets/base/base.py):
    props = { }
    for pspec in gtk.container_class_list_child_properties(container):
        props[pspec.name] = container.child_get_property(current, pspec.name)

    gtk.Container.remove(container, current)
    container.add(new)

    for name, value in props.items():
        container.child_set_property(new, name, value)

    if show is True:
        new.show_all()

    return new

# -- Method used for replacing a gtk.Label with a WrapLabel
def replace_wrap_label(current, text=None):
    # -- Paranoic sanity check for the worst case
    if not isinstance(current, gtk.Label):
        raise TypeError, "MSDUtils: Got unexpected class type '%s', gtk.Label needed" % type(current)

    if text is None:
        text = current.get_label()
    new = WrapLabel(text)
    new.set_use_markup(current.get_use_markup())
    return replace_widget(current, new)

# -- @XXX: Need to move the below code to an external file
class ValidationError(Exception):
    pass

class Validate():

    @staticmethod
    def phone(number):
        if type(number) != type(""):
            number = str(number)

        pattern = re.compile(r'^[\+\#\*_]{0,1}[0-9]{3,20}\Z')
        number  = re.sub(r'(?!\+)\W+', '', number)
        if pattern.match(number) is None:
            raise ValidationError, _("Invalid phone number '%s'. Allowed numbers might start with '+', '#', '*' or '_' and have between three and twenty digits.") % number
        return number

    class Spain():

        @staticmethod
        def mobile_phone(number):
            if type(number) != type(""):
                number = str(number)

            number = re.sub(r'(?!\+)\W+', '', number)
            pattern = re.compile(r'^(\+34)?([67][0-9]{8})$')
            if pattern.match(number) is None:
                raise ValidationError, _("Invalid mobile phone number '%s'. Allowed Spain numbers start with 6 or 7 and have at most 9 digits.") % number
            # -- @XXX: Strip the number before returnings its value
            return number

    @staticmethod
    def email(address):
        p = re.compile("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,4}$")
        address = address.strip()
        if p.match(address) is None:
            raise ValidationError, "Invalid email address '%s'" % address

def escape_markup(value):
    return value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def normalize_strength(strength, use_nm_levels = False):
    # Not NM-based, returns 6 levels of signal strength
    if not use_nm_levels:
        if strength > 85:
            return 5
        elif strength > 65:
            return 4
        elif strength > 45:
            return 3
        elif strength > 25:
            return 2
        elif strength > 5:
            return 1
        else:
            return 0

    # NM-based, returns 5 levels of signal strength
    else:
        if strength > 80:
            return 4
        elif strength > 55:
            return 3
        elif strength > 30:
            return 2
        elif strength > 5:
            return 1
        else:
            return 0

def open_url(url):
    def _isexecutable(cmd):
        if os.path.isfile(cmd):
            mode = os.stat(cmd)[stat.ST_MODE]
            if mode & stat.S_IXUSR or mode & stat.S_IXGRP or mode & stat.S_IXOTH:
                return True
        return False

    def _iscommand(cmd):
        path = os.environ.get("PATH")
        if not path:
            return False
        for d in path.split(os.pathsep):
            exe = os.path.join(d, cmd)
            if _isexecutable(exe):
                return True
        return False

    def _do_open_blank_page(browser_name):
        webbrowser.get(browser_name + " %s").open("about:blank")

    def _do_open_zero_length_url():
        default_browser = None
        if _iscommand('x-www-browser'):
            default_browser = 'x-www-browser'
        elif _iscommand('sensible-browser'):
            default_browser = 'sensible-browser'
        elif os.environ.get('BROWSER') and _iscommand(os.environ.get('BROWSER')):
            default_browser = os.environ.get('BROWSER')
        else:
            command = ['xdg-settings', '--list']
            process = subprocess.Popen(command, stdout=subprocess.PIPE, \
                    stderr=subprocess.PIPE)
            stdout = process.communicate()[0]
            stdout = StringIO.StringIO(stdout)

            default_web_browser_available = False
            for line in stdout.readlines():
                if 'default-web-browser' in line:
                    default_web_browser_available = True

            if default_web_browser_available:
                command = ['xdg-settings', 'get', 'default-web-browser']
                process = subprocess.Popen(command, stdout=subprocess.PIPE, \
                        stderr=subprocess.PIPE)
                stdout = process.communicate()[0]
                browser = stdout.replace('.desktop', '')
                if _iscommand(browser):
                    default_browser = browser

        if default_browser is None:
            default_browser = 'firefox'

        # WTF!! webbrowser.open(...) is asynchronous, but
        # webbrowser.get(...).open(...) is synchronous o_O
        foo = threading.Thread(target=_do_open_blank_page, \
                args=(default_browser,))
        foo.start()

    def _do_open_url(url):
        has_uri = False
        for prefix in ('http', 'https', 'ftp'):
            if url.startswidth(prefix):
                has_uri = True

        if not has_uri:
            url = 'http://' + url

        webbrowser.open(url)

    if len(url) == 0:
        _do_open_zero_length_url()
    else:
        _do_open_url(url)
