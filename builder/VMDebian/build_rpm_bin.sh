#!/bin/bash

set -e

BUILDER_DIR="/root/builder"
TMP_DIR=$BUILDER_DIR/tmp
ARCHIVE_DIR=$BUILDER_DIR/archive
LOGS_DIR=$BUILDER_DIR/logs

FICHERO_INFORME=InformeGeneracion.log
PATH_FICHERO_INFORME=$BUILDER_DIR/$FICHERO_INFORME

INF_INIT() {
    > $PATH_FICHERO_INFORME
}

INF_APPEND() {
    cat "$1" >> $PATH_FICHERO_INFORME
}

INF() {
    echo "$1" >> $PATH_FICHERO_INFORME
}

LOG() {
    echo ">> $1"
    #logger -t [TGCM-BUILDER] "$1"
}


BUILDER_build_rpm_pkgs(){

    LOG "Reconstruyendo los paquetes rpm..."
    rm -fr $DISTRO_CHROOT/root/builder/rpm/*
    cp -a $TMP_DIR/rpm/* $DISTRO_CHROOT/root/builder/rpm/

    DATE=$(date +%s)
    LOG "   Chroot sobre $DISTRO --> rpmbuild --rebuild..."
    i386 /usr/sbin/chroot $DISTRO_CHROOT /root/builder/bin/build.sh > $LOGS_DIR/$DATE.txt 2>&1
    INF_APPEND $DISTRO_CHROOT/$PATH_FICHERO_INFORME
    LOG "   Done!"
    rm -fr $DISTRO_ARCHIVE

    cp -a $DISTRO_CHROOT/root/builder/repository/* $ARCHIVE_DIR/
    LOG "Reconstruidos los paquetes rpm!"
}


#MAIN ----------------------------------
#---------------------------------------
DISTRO=$1
LOG "Construccion paquetes binarios para $DISTRO"

if [ x"$DISTRO" == "xFEDORA" ];
then
    DISTRO_CHROOT=$BUILDER_DIR/chroots/fedora/16/builder
    DISTRO_ARCHIVE=$ARCHIVE_DIR/fedora16
fi

if [ x"$DISTRO" == "xOPENSUSE" ];
then
    DISTRO_CHROOT=$BUILDER_DIR/chroots/opensuse/12.1/builder
    DISTRO_ARCHIVE=$ARCHIVE_DIR/opensuse121
fi

if [ x"$DISTRO" != "xFEDORA" -a x"$DISTRO" != "xOPENSUSE" ];
then
        LOG "ERROR: Nombre de distribucion no reconocido: $DISTRO"
    exit 1
fi

LOG "   Usando chroot: $DISTRO_CHROOT"
LOG "   Usando archive: $DISTRO_ARCHIVE"

INF_INIT
BUILDER_build_rpm_pkgs
