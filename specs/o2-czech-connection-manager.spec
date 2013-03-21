%define is_64 %(test -e /lib64 && echo 1 || echo 0)
%define is_mandrake %(test -e /etc/mandrake-release && echo 1 || echo 0)
%define is_suse %(test -e /etc/SuSE-release && echo 1 || echo 0)
%define is_fedora %(test -e /etc/fedora-release && echo 1 || echo 0)

Name: o2-czech-connection-manager
Summary: Czech Connection Manager
Version: 8.9
Release: 1
License: GPLv2+
Group: Applications/Internet
Source: tgcm-%{version}.tar.gz

BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%if %is_fedora
Requires: gtk2 >= 2.4.0
Requires: python >= 2.7.0
Requires: python-sqlobject
Requires: pygtk2
Requires: dbus
Requires: gnome-python2
Requires: gnome-python2-extras
Requires: gnome-python2-gconf
Requires: wget
Requires: pywebkitgtk
Requires: python-psutil
Requires: pyusb
Requires: python-gudev
Requires: python-dateutil
Requires: gnome-python2-libwnck
Requires: libproxy-python
Requires: pyxdg
Requires: NetworkManager >= 0.9
Requires: nm-connection-editor
Requires: mobile-manager >= %{version}-%{release}
Requires: xdg-utils
%endif

%if %is_suse
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
Requires: python-dateutil
Requires: python-wnck
Requires: python-libproxy
Requires: python-xdg
Requires: NetworkManager >= 0.9
Requires: NetworkManager-gnome
Requires: mobile-manager >= %{version}-%{release}
Requires: xdg-utils
%endif

%if %is_fedora
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
%endif

%if %is_suse
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
%endif

#BuildRequires: mobile-manager

%description
This package contains the Connection Manager for O2 Czech Republic.

%prep
%setup -q
cd $RPM_BUILD_DIR

%build
%configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
find $RPM_BUILD_ROOT/etc/xdg/autostart/*.desktop -name tgcm-*.desktop | grep -v tgcm-cz.desktop | xargs rm -f
find $RPM_BUILD_ROOT/usr/share/applications/ -name tgcm-* | grep -v tgcm-cz | xargs rm -f
find $RPM_BUILD_ROOT/usr/share/doc/tgcm/ -maxdepth 1 -type d | grep -v tgcm/cz | grep -ve "tgcm/$" | xargs rm -fr
find $RPM_BUILD_ROOT/usr/ -name mobilemanager | xargs rm -rf
rm -rf $RPM_BUILD_ROOT/dbus-1
rm -rf $RPM_BUILD_ROOT/lib
rm -rf $RPM_BUILD_ROOT/usr/sbin
rm -rf $RPM_BUILD_ROOT/etc/dbus-1
rm -rf $RPM_BUILD_ROOT/usr/share/usb_modeswitch
rm -rf $RPM_BUILD_ROOT/var/lib/mobile-manager

%files
%{_bindir}/*
/usr/lib/*
%{_datadir}/*
%{_sysconfdir}/*

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/ldconfig
/usr/bin/update-mime-database /usr/share/mime
/usr/bin/update-desktop-database /usr/share/applications/
/usr/bin/gtk-update-icon-cache -q /usr/share/icons/hicolor
/usr/bin/gtk-update-icon-cache -q /usr/share/icons/gnome
touch -m /usr/share/icons/hicolor
touch -m /usr/share/icons/gnome

%if %is_fedora
/usr/bin/chcon -t texrel_shlib_t /usr/lib/python2.7/site-packages/emsyncmodule.so || echo -n ''
/usr/bin/chcon -t texrel_shlib_t /usr/lib/python2.7/site-packages/emtrafficmodule.so || echo -n ''
%endif

%changelog
* Mon Nov 19 2012 David Castellanos Serrano <dcastellanos@indra.es> - 8.9-1
* Fri Jan 13 2012 Jose Maria Gonzalez Calabozo <jmgonzalezc@indra.es> - 8.8-1
* Tue Nov 6 2007 Roberto Majadas <telemaco@openshine.com> - 6.1-1
- Initial

