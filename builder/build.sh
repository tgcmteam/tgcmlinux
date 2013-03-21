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

#DEB vars
SVN_DEB_TGCM_VERSION='r0000'
DEB_SRC_BUILDER_DIR=$BUILDER_DIR/chroots/deb-src-builder
DEB_SVN_SNAPSHOT_DIR=$DEB_SRC_BUILDER_DIR/root/builder/svn/tgcm/snapshot/
UBUNTU_DISTROS="oneiric"

#RPM vars
SVN_RPM_TGCM_VERSION='r0000'
#RPM_SRC_BUILDER_DIR=$BUILDER_DIR/chroots/rpm-src-builder
#RPM_SVN_SNAPSHOT_DIR=$RPM_SRC_BUILDER_DIR/root/builder/svn/tgcm/snapshot/
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
    logger -t [TGCM-BUILDER] "$1"
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


BUILDER_build_deb_dsc(){
    LOG "Building $1 for $2 in $4 secs"
    sleep $4 || echo $4
    DATE=$(date +%s)
    mkdir -p $RESULTS_DIR/$DATE
    mkdir -p $LOGS_DIR

    #pbuilder --update --basetgz $BASETGZ_DIR/$2.tgz > $LOGS_DIR/$DATE.txt 2>&1
    LOG "	Building packages for $2..."
    #--http-proxy http://tgcmlinuxes:ukanianos@proxy.indra.es:8080 \
    pbuilder --build --basetgz $BASETGZ_DIR/$2.tgz \
        --buildplace $BUILDERPLACE_DIR \
        --buildresult $RESULTS_DIR/$DATE \
        $1 >> $LOGS_DIR/"$3"_"$2"_$DATE.txt 2>&1
    LOG "	Builded packages for $2!"
    INF "  * Generacion de paquetes binarios para 32 bits ................................ [OK]"

    LOG "	Building packages for $264..."
    #--http-proxy http://tgcmlinuxes:ukanianos@proxy.indra.es:8080 \
    x86_64 pbuilder --build --basetgz $BASETGZ_DIR/"$2"64.tgz \
        --buildplace $BUILDERPLACE_DIR \
        --buildresult $RESULTS_DIR/$DATE \
        $1 >> $LOGS_DIR/"$3"_"$2"_"$DATE"_64.txt 2>&1
    LOG "	Builded packages for $264!"
    INF "  * Generacion de paquetes binarios para 64 bits ................................ [OK]"

    cd $ARCHIVE_DIR/ubuntu
    while [ -e ./db/lockfile ] ;
    do
    LOG "	Lock repod db ($1 for $2 in $4 secs)"
    sleep $4
    done
    reprepro remove $2 $3 >> $LOGS_DIR/"$3"_"$2"_Deploy_$DATE.txt 2>&1

    while [ -e ./db/lockfile ] ;
    do
        LOG "	Lock repod db ($1 for $2 in $4 secs)"
        sleep $4
    done
    reprepro --section Net --priority optional includedsc $2 $1 >> $LOGS_DIR/"$3"_"$2"_Deploy_$DATE.txt 2>&1

    LOG "	Updating repository..."
    find $RESULTS_DIR/$DATE -name *.deb -exec reprepro includedeb $2 {} \; >> $LOGS_DIR/"$3"_"$2"_Deploy_$DATE.txt 2>&1
    LOG "	Repository updated!"
    INF "  * Actualizacion del repositorio ............................................... [OK]"
    cd -
    rm -fr $RESULTS_DIR/$DATE
}


BUILDER_update_deb_basetgz(){
    LOG "	Updating debian basetgzs..."

    for distro in $UBUNTU_DISTROS ;
    do
        DATE=$(date +%s)
          pbuilder --update --basetgz $BASETGZ_DIR/$distro.tgz  > $LOGS_DIR/"$distro"_"$DATE"_UPDATE.txt 2>&1 &
        x86_64 pbuilder --update --basetgz $BASETGZ_DIR/"$distro"64.tgz  > $LOGS_DIR/"$distro"_"$DATE"_UPDATE64.txt 2>&1 &
    done

    sleep 5

    for pid in $(jobs -p) ;
    do
        wait $pid
    done

    LOG "	Updated debian basetgzs!"
    INF "  * Actualizacion de basetgzs.................................................... [OK]"
}


BUILDER_build_deb_pkgs(){
    LOG "DEB packages building..."

    INF
    INF "[DEB] Fase de construccion de paquetes fuente..."
    LOG "	Building debian src packages..."
    /usr/sbin/chroot $DEB_SRC_BUILDER_DIR /root/builder/bin/build.sh
    INF_APPEND $DEB_SRC_BUILDER_DIR/$PATH_FICHERO_INFORME

    if [ -e $DEB_SRC_BUILDER_DIR/root/builder/builder.tgz ];
    then
        LOG "	Builded debian src packages!"
        rm -fr $TMP_DIR/deb
        mkdir -p $TMP_DIR/deb
        cd $TMP_DIR/deb
        tar xvzf $DEB_SRC_BUILDER_DIR/root/builder/builder.tgz > /dev/null 2>&1
        rm -fr $DEB_SRC_BUILDER_DIR/root/builder/builder.tgz

        INF "  Construidos paquetes fuente .DEB"

        INF
        INF "[DEB] Fase de construccion de paquetes binarios..."

        BUILDER_update_deb_basetgz

        LOG "	Building debian binary packages..."
        SLEEP_TIME=0
        for distro in $UBUNTU_DISTROS ;
            do
                TGCM_DSC=$(find $TMP_DIR/deb -name tgcm*.dsc | grep $distro || echo "")
                if [ x"$TGCM_DSC" != "x" ];
                then
                    SLEEP_TIME=$(echo "$SLEEP_TIME + 15" | bc)
                    BUILDER_build_deb_dsc $TGCM_DSC $distro "tgcm" $SLEEP_TIME &
                fi
            done

        for pid in $(jobs -p) ;
            do
                wait $pid
            done
        LOG "	Builded debian binary packages!"

        cd -
        cp $DEB_SVN_SNAPSHOT_DIR/latest-revision $BUILDER_DIR/latest-revision-deb

        LOG "DEB packages builded!"
        INF "  Construidos paquetes binarios .DEB"

    else
        INF "  NO construidos paquetes fuente .DEB"

    fi

    SVN_DEB_TGCM_VERSION=$(cat $BUILDER_DIR/latest-revision-deb)
}

BUILDER_build_rpm_pkgs(){
    LOG "RPM packages building..."

    python /root/builder/bin/generadorPaquetesRPM.py -i "$PATH_FICHERO_INFORME" -D DEBUG
    SVN_RPM_TGCM_VERSION=$(cat $BUILDER_DIR/latest-revision-rpm)
    LOG "RPM packages builded!"
}

BUILDER_genMailAviso_pkgs (){
    LOG "Sending mail about disponibility of packages..."
    python /root/builder/bin/genMail.py "$CDATE" "$SVN_DEB_TGCM_VERSION" "$SVN_RPM_TGCM_VERSION" "$PATH_FICHERO_INFORME"
    LOG "Sent mail about disponibility of packages!"
}

BUILDER_publish_pkgs (){
    LOG "Publishing packages..."
    python /root/builder/bin/report.py "$CDATE"
    LOG "Published packages!"
}

#MAIN ----------------------------------
#---------------------------------------

INF_INIT
check_base_dirs
BUILDER_build_deb_pkgs
BUILDER_build_rpm_pkgs
BUILDER_genMailAviso_pkgs
BUILDER_publish_pkgs
