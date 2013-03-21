#!/bin/bash

set -e

BUILDER_DIR="/root/builder"
BASETGZ_DIR=$BUILDER_DIR/basetgzs
BUILDERPLACE_DIR=$BUILDER_DIR/build-place
RESULTS_DIR=$BUILDER_DIR/results
TMP_DIR=$BUILDER_DIR/tmp
ARCHIVE_DIR=$BUILDER_DIR/archive
LOGS_DIR=$BUILDER_DIR/logs

FICHERO_INFORME=InformeGeneracion.log
PATH_FICHERO_INFORME=$BUILDER_DIR/$FICHERO_INFORME

CDATE=$(date)

#RPM vars
RPM_SRC_BUILDER_DIR=$BUILDER_DIR/chroots/rpm-src-builder
RPM_MACH_DIR=/var/tmp/mach/

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

check_base_dirs(){
    LOG "checking base dirs"
    mkdir -p $BASETGZ_DIR
    mkdir -p $BUILDERPLACE_DIR
    mkdir -p $RESULTS_DIR
    mkdir -p $TMP_DIR
    mkdir -p $LOGS_DIR
    rm -fr $LOGS_DIR/*
    LOG "checked base dirs"
}


BUILDER_build_rpm_pkgs(){
    mkdir -p $LOGS_DIR

    LOG "Building rpm.src packages"
    i386 /usr/sbin/chroot $RPM_SRC_BUILDER_DIR /root/builder/bin/build.sh > /dev/null 2>&1
    INF_APPEND $RPM_SRC_BUILDER_DIR/$PATH_FICHERO_INFORME

    if [ -e $RPM_SRC_BUILDER_DIR/root/builder/builder.tgz ];
    then
        LOG "Builded rpm.src packages"
        rm -fr $TMP_DIR/rpm
        mkdir -p $TMP_DIR/rpm
        cd $TMP_DIR/rpm

        LOG "Desempaquetando paquetes rpm..."
        tar xvzf $RPM_SRC_BUILDER_DIR/root/builder/builder.tgz >/dev/null
        LOG "Desempaquetados los paquetes rpm!"
        rm -f $RPM_SRC_BUILDER_DIR/root/builder/builder.tgz

    else
        exit 1

    fi
}


#MAIN ----------------------------------
#---------------------------------------
INF_INIT
check_base_dirs
BUILDER_build_rpm_pkgs
