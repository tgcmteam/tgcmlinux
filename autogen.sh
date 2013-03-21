#!/bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -z "$srcdir" && srcdir=.
REQUIRED_AUTOMAKE_VERSION=1.7
PKG_NAME=tgcm

(test -f $srcdir/configure.ac \
  && test -f $srcdir/src/tgcm/ui/tgcm) || {
    echo -n "**Error**: Directory "\`$srcdir\'" does not look like the"
    echo " top-level $PKG_NAME directory"
    exit 1
}


which gnome-autogen.sh || {
    echo "You need to install gnome-common from the GNOME CVS"
    exit 1
}

SYNCML_DIRS="src/common-libs/ptools src/common-libs/traffic/traffic src/common-libs/traffic/emtrafficmodule"

for conf_dir in $SYNCML_DIRS; do
    cd $conf_dir
    echo "Configuring : $conf_dir"
    autoconf
    cd - > /dev/null
done

USE_GNOME2_MACROS=1 . ./gnome-autogen.sh
