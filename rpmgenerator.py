#!/usr/bin/python

import os
import sys

COUNTRY_INFO = {
    "escritorio-movistar-argentina" : ["ar",
                                       "Argentina Connection Manager",
                                       "This package contains the Connection Manager for Telefonica Argentina. "],
    "escritorio-movistar-chile" : ["cl",
                                   "Chile Connection Manager",
                                   "This package contains the Connection Manager for Telefonica Chile. "],
    "escritorio-movistar-colombia" : ["co",
                                      "Colombia Connection Manager",
                                      "This package contains the Connection Manager for Telefonica Colombia. "],
    "o2-czech-connection-manager" : ["cz",
                                     "Czech Connection Manager",
                                     "This package contains the Connection Manager for O2 Czech Republic. "],
    "mobile-connection-manager" : ["de",
                                   "German Connection Manager",
                                   "This package contains the Connection Manager for O2 Germany. "],
    "escritorio-movistar-ecuador" : ["ec",
                                     "Ecuador Connection Manager",
                                     "This package contains the Connection Manager for Telefonica Ecuador. "],
    "escritorio-movistar-espana" : ["es",
                                    "Spain Connection Manager",
                                    "This package contains the Connection Manager for Telefonica Spain. "],
    "escritorio-movistar-guatemala" : ["gt",
                                       "Guatemala Connection Manager",
                                       "This package contains the Connection Manager for Telefonica Guatemala. "],
    "escritorio-movistar-mexico" : ["mx",
                                    "Mexico Connection Manager",
                                    "This package contains the Connection Manager for Telefonica Mexico."],
    "escritorio-movistar-nicaragua" : ["ni",
                                    "Nicaragua Connection Manager",
                                    "This package contains the Connection Manager for Telefonica Nicaragua. "],
    "escritorio-movistar-panama" : ["pa",
                                    "Panama Connection Manager",
                                    "This package contains the Connection Manager for Telefonica Panama. "],
    "escritorio-movistar-peru" : ["pe",
                                  "Peru Connection Manager",
                                  "This package contains the Connection Manager for Telefonica Peru. "],
    "escritorio-movistar-el-salvador" : ["sv",
                                         "El Salvador Connection Manager",
                                         "This package contains the Connection Manager for Telefonica El Salvador.\nGroup (sv). "],
    "o2-connection-manager" : ["uk",
                               "British Connection Manager",
                               "This package contains the Connection Manager for O2 United Kingdom."],
    "escritorio-movistar-uruguay" : ["uy",
                                     "Uruguay Connection Manager",
                                     "This package contains the Connection Manager for Telefonica Uruguay. "],
    "escritorio-movistar-venezuela" : ["ve",
                                       "Venezuela Connection Manager",
                                       "This package contains the Connection Manager for Telefonica Venezuela."],
    "escritorio-movistar-costa-rica" : ["cr",
                                       "Costa Rica Connection Manager",
                                       "This package contains the Connection Manager for Telefonica Costa Rica."],
    }

def create_spec (name, summary, desc, country_code) :

    fd = open("specs/%s.spec" % name, "w")
    
    fd.write('''%%define is_mandrake %%(test -e /etc/mandrake-release && echo 1 || echo 0)
%%define is_suse %%(test -e /etc/SuSE-release && echo 1 || echo 0)
%%define is_fedora %%(test -e /etc/fedora-release && echo 1 || echo 0)

Name: %s
Summary: %s
Version: 0.1 
Release: 1 
License: GPLv2+
Group: Applications/Internet
Source: tgcm-%%{version}.tar.gz

BuildRoot:  %%{_tmppath}/%%{name}-%%{version}-%%{release}-root-%%(%%{__id_u} -n)

Provides: ModemManager
Obsoletes: ModemManager

%%if %%is_fedora
Requires: gtk2 >= 2.4.0
Requires: python >= 2.7.0
Requires: python-sqlobject
Requires: pygtk2
Requires: dbus
Requires: gnome-python2
Requires: gnome-python2-extras
Requires: wget
Requires: pywebkitgtk 
Requires: python-psutil
Requires: pyusb
Requires: python-gudev
Requires: usb_modeswitch >= 1.2.0
Requires: usb_modeswitch-data >= 20111023
Requires: NetworkManager >= 0.9
%%endif

%%if %%is_suse
Requires: gtk2 >= 2.4.0
Requires: python >= 2.7
Requires: python-sqlobject
Requires: dbus-1-python
Requires: python-gtk
Requires: python-gnome
Requires: python-gnome-extras
Requires: dbus-1
Requires: python-webkitgtk
Requires: gnome-python-desktop 
Requires: python-notify
Requires: python-psutil
Requires: python-usb
Requires: python-gudev
Requires: python-formencode
Requires: usb_modeswitch >= 1.1.7
Requires: usb_modeswitch-data >= 1.1.7
Requires: NetworkManager >= 0.9
%%endif 

%%if %%is_fedora
BuildRequires: python-devel
BuildRequires: pygtk2-devel
BuildRequires: dbus-devel >= 0.90
BuildRequires: gettext
BuildRequires: gcc
BuildRequires: python-sqlobject 
BuildRequires: gnome-doc-utils
BuildRequires: intltool
BuildRequires: libtool
BuildRequires: dbus-python-devel
BuildRequires: sqlite-devel
BuildRequires: gnome-python2-devel 
BuildRequires: gnome-desktop-devel
BuildRequires: gnome-common
BuildRequires: gnome-python2-extras
%%endif

%%if %%is_suse
BuildRequires: python-gtk-devel
BuildRequires: dbus-1-python-devel
BuildRequires: dbus-1-glib-devel
BuildRequires: dbus-1-devel
BuildRequires: automake
BuildRequires: autoconf
BuildRequires: make
BuildRequires: python-devel
BuildRequires: gettext
BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: gnome-doc-utils-devel
BuildRequires: intltool
BuildRequires: libtool
BuildRequires: libusb-devel
%%endif

#BuildRequires: mobile-manager

%%description
%s

%%prep
%%setup -q 
cd $RPM_BUILD_DIR

%%build
%%configure --prefix=/usr --sysconfdir=/etc
make %%{?_smp_mflags}

%%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
find $RPM_BUILD_ROOT/usr/share/applications/ -name tgcm-* | grep -v tgcm-%s | xargs rm -f
find $RPM_BUILD_ROOT/usr/share/doc/tgcm/ -maxdepth 1 -type d | grep -v tgcm/%s | grep -ve "tgcm/$" | xargs rm -fr

%%files
%%{_bindir}/*
%%{_sbindir}/*
%%{_libdir}/*
%%{_datadir}/*
%%{_sysconfdir}/*
/lib/udev/rules.d/*

%%clean
rm -rf $RPM_BUILD_ROOT

%%post
/sbin/ldconfig
/usr/bin/update-mime-database /usr/share/mime
/usr/bin/update-desktop-database /usr/share/applications/
/usr/bin/gtk-update-icon-cache -q /usr/share/icons/hicolor
/usr/bin/gtk-update-icon-cache -q /usr/share/icons/gnome
touch -m /usr/share/icons/hicolor
touch -m /usr/share/icons/gnome

# -- Remove the Devices Table at first before restarting the MM
devtable="/usr/share/pyshared/mobilemanager/DeviceTable.xml"
if test -e "${devtable}"; then
    echo "Removing the Devices Table of the Mobile Manager"
    rm -fv "${devtable}"
fi

devtable="/usr/lib/python2.7/dist-packages/mobilemanager/DeviceTable.xml"
if test -e "${devtable}"; then
    echo "Removing the Devices Table of the Mobile Manager"
    rm -fv "${devtable}"
fi

# -- Kill the modem-manager if it's still running
if ps -C modem-manager > /dev/null; then
    echo "Going to kill the Modem Manager"
    killall --signal 9 modem-manager
fi

# -- Kill the Mobile Manager if it's already running
if ps -C python -o cmd= | grep -q /usr/sbin/mobile-manager; then
    echo "Going to kill the Mobile Manager"
    pkill -9 -f /usr/sbin/mobile-manager
fi

%%if %%is_fedora
/usr/bin/chcon -t texrel_shlib_t /usr/lib/python2.7/site-packages/emsyncmodule.so || echo -n ''
/usr/bin/chcon -t texrel_shlib_t /usr/lib/python2.7/site-packages/emtrafficmodule.so || echo -n ''
%%endif

%%changelog
* Tue Nov 6 2007 Roberto Majadas <telemaco@openshine.com> - 6.1-1
- Initial

''' % (name, summary, desc, country_code, country_code))
    fd.close()

if __name__ == '__main__':
    for key in COUNTRY_INFO.keys() :
        try:
            country, summary, desc = COUNTRY_INFO[key]
        except:
            print key
            exit(0)
        create_spec(key, summary, desc, country)
    
