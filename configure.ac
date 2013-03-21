AC_INIT
AC_CONFIG_SRCDIR([src/tgcm/__init__.py.in])

PACKAGE=tgcm
VERSION=8.9

AC_CONFIG_MACRO_DIR([m4])

AC_SUBST(PACKAGE)
AC_SUBST(VERSION)

AM_INIT_AUTOMAKE($PACKAGE, $VERSION)
AC_CONFIG_HEADERS([config.h])

AM_MAINTAINER_MODE

AC_SEARCH_LIBS([strerror],[cposix])
AC_PROG_CC
AC_HEADER_STDC
AC_DISABLE_STATIC([])
LT_INIT

AC_ARG_WITH(init-scripts,
  [  --with-init-scripts=[redhat/debian/suse/None]  Use TCP Wrappers [default=None]],,
  with_init_scripts=None)

dnl check for python
dnl ----------------------------
AM_PATH_PYTHON

PKG_CHECK_MODULES(PYGTK, pygtk-2.0 >= 2.6)
AC_SUBST(PYGTK_CFLAGS)
AC_SUBST(PYGTK_LIBS)

dnl PKG_CHECK_MODULES(PYGNOMEEXTRAS, gnome-python-extras-2.0 >= 2.18)
dnl AC_SUBST(PYGNOMEEXTRAS_CFLAGS)
dnl AC_SUBST(PYGNOMEEXTRAS_LIBS)

PKG_CHECK_MODULES(PYDBUS, dbus-python >= 0.80)
AC_SUBST(PYDBUS_CFLAGS)
AC_SUBST(PYDBUS_LIBS)

AC_PATH_PROG(GCONFTOOL, gconftool-2, no)
if test x"$GCONFTOOL" = xno; then
    AC_MSG_ERROR([gconftool-2 executable not found in your path - should be installed with GConf])
fi
dnl AM_GCONF_SOURCE_2

AC_ARG_WITH(dbus-sys-dir, AS_HELP_STRING([--with-dbus-sys-dir=DIR], [where D-BUS system.d directory is]))

if test -n "$with_dbus_sys_dir" ; then
    DBUS_SYS_DIR="$with_dbus_sys_dir"
else
    DBUS_SYS_DIR="${sysconfdir}/dbus-1/system.d"
fi
AC_SUBST(DBUS_SYS_DIR)

AC_ARG_WITH(udev-base-dir, AS_HELP_STRING([--with-udev-base-dir=DIR], [where udev base directory is]))

if test -n "$with_udev_base_dir" ; then
    UDEV_BASE_DIR="$with_udev_base_dir"
else
    UDEV_BASE_DIR="/lib/udev"
fi
AC_SUBST(UDEV_BASE_DIR)

dnl This is for usb_modeswitch
AC_ARG_WITH(usbmode-base-dir, AS_HELP_STRING([--with-usbmode-base-dir=DIR], [where usb_modeswitch base directory is]))
if test -n "$with_usbmode_base_dir" ; then
    USBMODE_BASE_DIR="$with_usbmode_base_dir"
else
    USBMODE_BASE_DIR="/usr/share/usb_modeswitch"
fi
AC_SUBST(USBMODE_BASE_DIR)

dnl Get the path of the usb_modeswitch binary
usbmode_bin=`which usb_modeswitch`
if test -z "$usbmode_bin" ; then
     AC_MSG_ERROR([Couldnt find the 'usb_modeswitch' executable. Please adapt your 'PATH'])
fi
AC_SUBST(USBMODE_BIN, $usbmode_bin)

AC_ARG_WITH(device-table-dir, AS_HELP_STRING([--with-device-table-dir=DIR], [the directory where the device table file is]))
if test -n "$with_device_table_dir" ; then
    DEVICE_TABLE_DIR="$with_device_table_dir"
else
    DEVICE_TABLE_DIR="${localstatedir}/lib/mobile-manager"
fi
AC_SUBST(DEVICE_TABLE_DIR)

dnl build_date
dnl ------------------------------

TGCM_BUILD_DATE=`date +"%Y-%m-%d %H:%M:%S"`
AC_SUBST(TGCM_BUILD_DATE)

TGCM_DEVELOPMENT_REVISION=`cat latest-revision`
AC_SUBST(TGCM_DEVELOPMENT_REVISION)

dnl check for python headers
dnl ------------------------------
AC_MSG_CHECKING(for shared library Python styff)

PY_PREFIX=`$PYTHON -c 'import sys ; print sys.prefix'`
PY_EXEC_PREFIX=`$PYTHON -c 'import sys ; print sys.exec_prefix'`
PYTHON_LIBS="-lpython$PYTHON_VERSION"
PYTHON_LIB_LOC="-L$PY_EXEC_PREFIX/lib/python$PYTHON_VERSION/config"
PYTHON_CFLAGS="-I$PY_PREFIX/include/python$PYTHON_VERSION"
PYTHON_MAKEFILE="$PY_EXEC_PREFIX/lib/python$PYTHON_VERSION/config/Makefile"
PYTHON_LOCALMODLIBS=`sed -n -e 's/^LOCALMODLIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
PYTHON_BASEMODLIBS=`sed -n -e 's/^BASEMODLIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
PYTHON_OTHER_LIBS=`sed -n -e 's/^LIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
PYTHON_EXTRA_LIBS="$PYTHON_LOCALMODLIBS $PYTHON_BASEMODLIBS $PYTHON_OTHER_LIBS"
AC_SUBST([PYTHON_LIBS])
AC_SUBST([PYTHON_LIB_LOC])
AC_SUBST([PYTHON_CFLAGS])
AC_SUBST([PYTHON_EXTRA_LIBS])

rm -rf testpython
mkdir testpython
cd testpython
cat > testpython.c <<EOF
#include <Python.h>
int testpython (void)
{
Py_Exit (0);
}
EOF

if /bin/sh ../libtool --mode=compile ${CC} $PYTHON_CFLAGS -c testpython.c >/dev/null 2>&1 && \
/bin/sh ../libtool --mode=link ${CC} -o testpython.la -rpath `pwd` -module -avoid-version $PYTHON_LIB_LOC testpython.lo $PYTHON_LIBS $PYTHON_EXTRA_LIBS >/dev/null 2>&1 && \
grep 'dlname.*testpython' testpython.la >/dev/null 2>&1; then
    result=yes
else
    result=yes
fi
cd ..
rm -rf testpython

if test $result != "yes"
then
  AC_MSG_RESULT(not found)
  AC_MSG_ERROR([You need install the headers of Python (python-dev)])
else
  AC_MSG_RESULT(found)
fi

AC_PATH_PROG( PKGCONFIG, pkg-config, no, $PATH:/usr/bin:/usr/local/bin)
  if test "$PKGCONFIG" != "no" ; then
    AC_MSG_CHECKING([PYTHONPATH env variable for PyGTK])
    PYTHONPATH=$($PKGCONFIG --variable=pyexecdir pygtk-2.0)
    AC_SUBST([PYTHONPATH])
    AC_MSG_RESULT($PYTHONPATH)
  fi

export PYTHONPATH=$PYGTK_DIR:$PYTHONPATH

dnl check for libglade
dnl -----------------------------------------
dnl AC_MSG_CHECKING(for gtk.glade)
dnl prog="
dnl import sys
dnl try:
dnl   import gtk.glade
dnl except RuntimeError:
dnl   sys.exit(0)
dnl except ImportError:
dnl   sys.exit(1)
dnl sys.exit(0)
dnl "
dnl
dnl if $PYTHON -c "$prog" 1>&AS_MESSAGE_LOG_FD 2>&AS_MESSAGE_LOG_FD
dnl then
dnl   AC_MSG_RESULT(found)
dnl else
dnl   AC_MSG_RESULT(not found)
dnl   AC_MSG_ERROR([You need to have python libglade bindings installed])
dnl fi


dnl checking for sqlobject
dnl -------------------------------------------
dnl AC_MSG_CHECKING(for sqlobject)
dnl prog="
dnl import sys
dnl try:
dnl   import sqlobject
dnl except RuntimeError:
dnl   sys.exit(0)
dnl except ImportError:
dnl   sys.exit(1)
dnl sys.exit(0)
dnl "
dnl
dnl if $PYTHON -c "$prog" 1>&AS_MESSAGE_LOG_FD 2>&AS_MESSAGE_LOG_FD
dnl then
dnl 	AC_MSG_RESULT(found)
dnl else
dnl 	AC_MSG_RESULT(not found)
dnl   	AC_MSG_ERROR([You need to have python sqlobject installed])
dnl fi


dnl checking for python-sqlite
dnl -------------------------------------------
dnl AC_MSG_CHECKING(for python-sqlite)
dnl prog="
dnl import sys
dnl try:
dnl  import sqlite
dnl except RuntimeError:
dnl  sys.exit(0)
dnl except ImportError:
dnl  sys.exit(1)
dnl sys.exit(0)
dnl "
dnl
dnl if $PYTHON -c "$prog" 1>&AS_MESSAGE_LOG_FD 2>&AS_MESSAGE_LOG_FD
dnl then
dnl   AC_MSG_RESULT(found)
dnl else
dnl   AC_MSG_RESULT(not found)
dnl   AC_MSG_ERROR([You need to have python sqlite installed])
dnl fi

dnl *******************************
dnl Internationalization
dnl *******************************

GETTEXT_PACKAGE=tgcm
AC_DEFINE(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE", "TGCM")
AC_SUBST(GETTEXT_PACKAGE)
dnl AC_CONFIG_MACRO_DIR([m4])
GNOME_DOC_INIT

dnl Add the languages which your application supports here.
ALL_LINGUAS="es en en_GB en_US de cs"

AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL

AS_AC_EXPAND(PYTHONDIR, $pythondir)
AC_SUBST(PYTHONDIR)

AS_AC_EXPAND(MOBILEMANAGER_DIR, $pythondir/mobilemanager)
AC_SUBST(MOBILEMANAGER_DIR)

AC_CONFIG_SUBDIRS([
src/common-libs/ptools/
src/common-libs/traffic/traffic/
src/common-libs/traffic/emtrafficmodule/
])

AC_CONFIG_FILES([
Makefile
po/Makefile.in
data/Makefile
data/autostart/Makefile
data/icons/Makefile
data/icons/theme/Makefile
data/icons/theme/cz/Makefile
data/icons/theme/cz/addressbook/Makefile
data/icons/theme/de/Makefile
data/icons/theme/de/addressbook/Makefile
data/icons/theme/default/Makefile
data/icons/theme/default/addressbook/Makefile
data/icons/theme/default/dock/Makefile
data/icons/theme/default/dock/Systray/Makefile
data/icons/theme/default/dock/TrafficZone/Makefile
data/icons/theme/latam/Makefile
data/icons/theme/latam/dock/Makefile
data/icons/theme/latam/dock/Ads/Makefile
data/icons/theme/latam/dock/Systray/Makefile
data/icons/theme/o2/Makefile
data/icons/theme/o2/dock/Makefile
data/icons/theme/o2/dock/Systray/Makefile
data/icons/theme/uk/Makefile
data/icons/theme/uk/addressbook/Makefile
data/icons/theme/uk/dock/Makefile
data/icons/theme/uk/dock/Systray/Makefile
data/mime-stuff/Makefile
data/mime-stuff/ar/Makefile
data/mime-stuff/ar/tgcm-ar.desktop
data/mime-stuff/de/Makefile
data/mime-stuff/de/tgcm-de.desktop
data/mime-stuff/mx/Makefile
data/mime-stuff/mx/tgcm-mx.desktop
data/mime-stuff/ec/Makefile
data/mime-stuff/ec/tgcm-ec.desktop
data/mime-stuff/pa/Makefile
data/mime-stuff/pa/tgcm-pa.desktop
data/mime-stuff/uy/Makefile
data/mime-stuff/uy/tgcm-uy.desktop
data/mime-stuff/ni/Makefile
data/mime-stuff/ni/tgcm-ni.desktop
data/mime-stuff/ve/Makefile
data/mime-stuff/ve/tgcm-ve.desktop
data/mime-stuff/pe/Makefile
data/mime-stuff/pe/tgcm-pe.desktop
data/mime-stuff/es/Makefile
data/mime-stuff/es/tgcm-es.desktop
data/mime-stuff/uk/Makefile
data/mime-stuff/uk/tgcm-uk.desktop
data/mime-stuff/gt/Makefile
data/mime-stuff/gt/tgcm-gt.desktop
data/mime-stuff/sv/Makefile
data/mime-stuff/sv/tgcm-sv.desktop
data/mime-stuff/co/Makefile
data/mime-stuff/co/tgcm-co.desktop
data/mime-stuff/cz/Makefile
data/mime-stuff/cz/tgcm-cz.desktop
data/mime-stuff/cl/Makefile
data/mime-stuff/cl/tgcm-cl.desktop
data/mime-stuff/cr/Makefile
data/mime-stuff/cr/tgcm-cr.desktop
data/icon-theme/Makefile
data/icon-theme/16x16/Makefile
data/icon-theme/22x22/Makefile
data/icon-theme/24x24/Makefile
data/icon-theme/32x32/Makefile
data/icon-theme/48x48/Makefile
data/regional-info/Makefile
debian/control
doc/Makefile
doc/tgcm/Makefile
doc/manual/Makefile
src/tgcm/__init__.py
src/tgcm/contrib/Makefile
src/tgcm/contrib/pycha/Makefile
src/tgcm/contrib/freedesktopnet/Makefile
src/tgcm/contrib/MobileManager/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/sms/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/mmdbus/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/devices/alcatel/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/devices/huawei/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/devices/novatel/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/devices/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/devices/option/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/devices/zte/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/devices/sierra/Makefile
src/tgcm/contrib/mobile-manager2/src/mobilemanager/__init__.py
src/tgcm/contrib/mobile-manager2/src/Makefile
src/tgcm/contrib/mobile-manager2/data/dbus/Makefile
src/tgcm/contrib/mobile-manager2/data/Makefile
src/tgcm/contrib/mobile-manager2/data/policy/Makefile
src/tgcm/contrib/mobile-manager2/data/udev/Makefile
src/tgcm/contrib/mobile-manager2/data/usb_modeswitch/Makefile
src/tgcm/contrib/mobile-manager2/Makefile
src/tgcm/contrib/tgcm-logging/Makefile
src/tgcm/contrib/tgcm-logging/data/Makefile
src/tgcm/contrib/tgcm-logging/data/dbus/Makefile
src/tgcm/contrib/tgcm-logging/src/Makefile
src/tgcm/contrib/tgcm-logging/src/tgcmlogging/Makefile
src/tgcm/ui/Actions/MSDAIntranet/Makefile
src/tgcm/ui/Actions/MSDASendSMS/Makefile
src/tgcm/ui/Actions/MSDAInternet/Makefile
src/tgcm/ui/Actions/MSDAMovilidad/Makefile
src/tgcm/ui/Actions/MSDABookmarks/Makefile
src/tgcm/ui/Actions/CZRecharge/Makefile
src/tgcm/ui/Actions/DERecharge/Makefile
src/tgcm/ui/Actions/CZSelfcare/Makefile
src/tgcm/ui/Actions/Makefile
src/tgcm/ui/MSD/Makefile
src/tgcm/ui/widgets/Makefile
src/tgcm/ui/widgets/themedwidgets/Makefile
src/tgcm/ui/widgets/chart/Makefile
src/tgcm/ui/widgets/common/Makefile
src/tgcm/ui/widgets/dock/Makefile
src/tgcm/ui/widgets/dock/ConnectionZone/Makefile
src/tgcm/ui/widgets/dock/DeviceMenuPopup/Makefile
src/tgcm/ui/widgets/dock/DeviceZone/Makefile
src/tgcm/ui/widgets/dock/ImageButton/Makefile
src/tgcm/ui/widgets/dock/LinkButton/Makefile
src/tgcm/ui/widgets/dock/Menubar/Makefile
src/tgcm/ui/widgets/dock/ServicesToolbar/Makefile
src/tgcm/ui/widgets/dock/Systray/Makefile
src/tgcm/ui/widgets/dock/TrafficZone/Makefile
src/tgcm/ui/widgets/dock/Window/Makefile
src/tgcm/ui/widgets/settings/Makefile
src/tgcm/ui/widgets/settings/General/Makefile
src/tgcm/ui/widgets/settings/Alerts/Makefile
src/tgcm/ui/widgets/settings/Dock/Makefile
src/tgcm/ui/widgets/settings/Devices/Makefile
src/tgcm/ui/widgets/settings/Connections/Makefile
src/tgcm/ui/widgets/settings/Services/Makefile
src/tgcm/ui/widgets/traffic/Makefile
src/tgcm/ui/widgets/traffic/TrafficGraph/Makefile
src/tgcm/ui/widgets/traffic/TrafficHistoryGraph/Makefile
src/tgcm/ui/widgets/traffic/BillingInfo/Makefile
src/tgcm/ui/widgets/traffic/SessionInfo/Makefile
src/tgcm/ui/widgets/traffic/DataUsedInfo/Makefile
src/tgcm/ui/windows/Makefile
src/tgcm/ui/windows/AddressBook/Makefile
src/tgcm/ui/windows/CarrierDialog/Makefile
src/tgcm/ui/windows/CheckboxDialog/Makefile
src/tgcm/ui/windows/ConnectionDialog/Makefile
src/tgcm/ui/windows/Dialog/Makefile
src/tgcm/ui/windows/HelpDialog/Makefile
src/tgcm/ui/windows/NewsServiceDialog/Makefile
src/tgcm/ui/windows/PinDialog/Makefile
src/tgcm/ui/windows/PukDialog/Makefile
src/tgcm/ui/windows/RecargaSaldo/Makefile
src/tgcm/ui/windows/Settings/Makefile
src/tgcm/ui/windows/Traffic/Makefile
src/tgcm/ui/windows/Generic/Makefile
src/tgcm/ui/windows/UnlockDeviceDialog/Makefile
src/tgcm/ui/Makefile
src/tgcm/core/Makefile
src/tgcm/core/Constants.py
src/tgcm/Makefile
src/Makefile
])
AC_OUTPUT

dnl ----------------------------------------------------------------

echo "
        MOVISTAR DESKTOP
        ================

    prefix:				 ${prefix}
"

