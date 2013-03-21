%define is_mandrake %(test -e /etc/mandrake-release && echo 1 || echo 0)
%define is_suse %(test -e /etc/SuSE-release && echo 1 || echo 0)
%define is_fedora %(test -e /etc/fedora-release && echo 1 || echo 0)

Name: mobile-manager
Summary: Telefonica Mobile Manager
Version: 8.9
Release: 1
License: GPLv2+
Group: Applications/Internet
Source: tgcm-%{version}.tar.gz

BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Provides: ModemManager
Obsoletes: ModemManager

%if %is_fedora
Requires: python >= 2.7.0
Requires: dbus
Requires: pyusb
Requires: python-gudev
Requires: usb_modeswitch >= 1.2.0
Requires: usb_modeswitch-data >= 20111023
Requires: NetworkManager >= 0.9
%endif

%if %is_suse
Requires: python >= 2.7
Requires: dbus-1-python
Requires: dbus-1
Requires: python-usb
Requires: python-gudev
Requires: usb_modeswitch >= 1.1.7
Requires: usb_modeswitch-data >= 1.1.7
Requires: NetworkManager >= 0.9
%endif 

%if %is_fedora
BuildRequires: python-devel
BuildRequires: dbus-devel >= 0.90
BuildRequires: gcc
BuildRequires: intltool
BuildRequires: libtool
BuildRequires: dbus-python-devel
%endif

%if %is_suse
BuildRequires: dbus-1-python-devel
BuildRequires: dbus-1-devel
BuildRequires: automake
BuildRequires: autoconf
BuildRequires: make
BuildRequires: python-devel
BuildRequires: gettext
BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: intltool
BuildRequires: libtool
BuildRequires: libusb-devel
%endif


%description
This package contains the Mobile Manager for Telefonica Spain. 

%prep
%setup -q 
cd $RPM_BUILD_DIR

%build
%configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
find $RPM_BUILD_ROOT/usr/ -name tgcm | xargs rm -rf
find $RPM_BUILD_ROOT/usr/ -name tgcmlogging | xargs rm -rf
find $RPM_BUILD_ROOT/usr/ -name em* | xargs rm -rf
rm -rf $RPM_BUILD_ROOT/usr/share/applications 
rm -rf $RPM_BUILD_ROOT/usr/share/doc/tgcm
rm -rf $RPM_BUILD_ROOT/usr/share/icons
rm -rf $RPM_BUILD_ROOT/usr/share/locale
rm -rf $RPM_BUILD_ROOT/usr/share/mime
rm -rf $RPM_BUILD_ROOT/usr/share/tgcm
rm -rf $RPM_BUILD_ROOT/usr/bin/tgcm-logging
rm -rf $RPM_BUILD_ROOT/usr/bin/tgcm-clean-config
rm -rf $RPM_BUILD_ROOT/etc/xdg


%files
%{_sbindir}/*
/usr/lib/*
%{_datadir}/*
%{_sysconfdir}/*
%{_localstatedir}/*
/lib/udev/rules.d/*

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/ldconfig

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

%postun
/sbin/ldconfig

# Remove the Devices Table after mobile-manager uninstall
devtable="/var/lib/mobile-manager/device-table.xml"
if test -e "${devtable}"; then
    echo "Removing the Devices Table of the Mobile Manager"
    rm -fv "${devtable}"
fi

%changelog
* Mon Nov 19 2012 David Castellanos Serrano <dcastellanos@indra.es> - 8.9-1
* Fri Jan 13 2012 Jose Maria Gonzalez Calabozo <jmgonzalezc@indra.es> - 8.8-1
* Tue Nov 6 2007 Roberto Majadas <telemaco@openshine.com> - 6.1-1
- Initial

