#!/bin/bash

export LANG=C
export PATH=$PATH:/usr/sbin

BUILDER_DIR="/home/builder"
FLAGS_DIR=$BUILDER_DIR/flags
PKGS_DIR=$BUILDER_DIR/pkgs
SVN_DIR=$BUILDER_DIR/svn

FICHERO_INFORME=InformeGeneracion.log
PATH_FICHERO_INFORME=$BUILDER_DIR/$FICHERO_INFORME

echo Borrando fichero y directorios temporales
rm -fr $PKGS_DIR/*
rm -fr $SVN_DIR/*
mkdir -p $FLAGS_DIR
mkdir -p $PKGS_DIR
mkdir -p $SVN_DIR

INF_INIT() {
    > $PATH_FICHERO_INFORME
}

INF() {
    echo "$1" >> $PATH_FICHERO_INFORME
}

build_src_tgcm_snapshot(){
    touch $FLAGS_DIR/LAST_TGCM_TRUNK_BUILDED
    SVN_TGCM_TRUNK_URL="http://lagar/mlinux/EscritorioLinuxNUI/trunk"
    SVN_TGCM_TRUNK_VERSION=$(svn --username roberto --password openshine info $SVN_TGCM_TRUNK_URL | grep Revision | sed -e "s/Revision: //g")
    LAST_TGCM_TRUNK_BUILD=$(cat $FLAGS_DIR/LAST_TGCM_TRUNK_BUILDED)

    if [ x$SVN_TGCM_TRUNK_VERSION != x$LAST_TGCM_TRUNK_BUILD ];
    then
        INF "  * Comprobacion: Version en SVN ($SVN_TGCM_TRUNK_VERSION) diferente a la ultima utilizada ($LAST_TGCM_TRUNK_BUILD)... [OK]"
        TGCM_SVN_SNAPSHOT_DIR=$SVN_DIR/tgcm/snapshot

        echo Download trunk version of tgcm
        rm -fr $TGCM_SVN_SNAPSHOT_DIR
        svn --username roberto --password openshine export $SVN_TGCM_TRUNK_URL $TGCM_SVN_SNAPSHOT_DIR
        INF "  * Descargado codigo fuente del SVN............................................. [OK]"

        echo Create tarball
        cd $TGCM_SVN_SNAPSHOT_DIR

    echo "$SVN_TGCM_TRUNK_VERSION" > latest-revision

        TGCM_VERSION=$(cat configure.ac | grep VERSION= | sed -e "s:VERSION=::g")

        ./autogen.sh --prefix=/usr --sysconfdir=/etc --localstatedir=/var
        make dist
        INF "  * Compilacion del codigo fuente................................................ [OK]"
        cd $BUILDER_DIR

        echo Copying tarball to pkg place
        TGCM_DEB_SNAPSHOT_DIR=$PKGS_DIR/tgcm-snapshot/
        rm -fr $TGCM_DEB_SNAPSHOT_DIR
        mkdir -p $TGCM_DEB_SNAPSHOT_DIR

        echo Create debian package
        cd $TGCM_DEB_SNAPSHOT_DIR
        TGCM_DEB_DISTRO_SNAPSHOT_DIR=$TGCM_DEB_SNAPSHOT_DIR/distro
        mkdir -p $TGCM_DEB_DISTRO_SNAPSHOT_DIR
        cd $TGCM_DEB_DISTRO_SNAPSHOT_DIR

        cp $TGCM_SVN_SNAPSHOT_DIR/*.tar.gz $TGCM_DEB_DISTRO_SNAPSHOT_DIR
        TGCM_TARBALL=$(ls $TGCM_DEB_DISTRO_SNAPSHOT_DIR)
        tar xvzf $TGCM_TARBALL
        TGCM_SOURCE_DIRNAME=$(echo $TGCM_TARBALL | sed s:.tar.gz::g)
        #cp -a $TGCM_SOURCE_DIRNAME $TGCM_SOURCE_DIRNAME.orig

        cd $TGCM_SOURCE_DIRNAME
        #svn --username roberto --password openshine export $SVN_TGCM_TRUNK_URL/debian
        #INF "  * Descargados ficheros descriptivos de generacion de paquetes .deb............. [OK]"

            # cat debian/control | sed -e "s/^Maintainer.*$/Maintainer: Telefonica Group Connection Manager \<tgcm@telefonica.es\>/g" >  debian/control.tmp
            # mv debian/control.tmp debian/control

        #	    cat debian/changelog | sed -e "s:-- Escritorio Movistar <escritorio_movistar@tid.es>:-- Telefonica Group Connection Manager <tgcm@telefonica.es>:g" > debian/changelog.tmp
        #	    mv debian/changelog.tmp debian/changelog

            # DEBEMAIL="e.tgcm@tid.es" DEBFULLNAME="Telefonica Group Connection Manager"
        DEBEMAIL="tgcmlinuxes@indra.es" DEBFULLNAME="Indra Sistemas" \
        dch -v $TGCM_VERSION"."$SVN_TGCM_TRUNK_VERSION -m "TGCM snapshot" 
            #dch -v $TGCM_VERSION"-"$SVN_TGCM_TRUNK_VERSION"_"$DISTRO -m "TGCM snapshot" --force-distribution -D $DISTRO
        debuild -S -sa -us -uc
        INF "  * Generados paquetes fuentes ............................... [OK]"

        cd $TGCM_DEB_DISTRO_SNAPSHOT_DIR
        rm -fr $TGCM_TARBALL
        rm -fr *_source.changes *_source.build
        rm -fr $TGCM_SOURCE_DIRNAME
        find -maxdepth 1 -type d | grep ./ | xargs rm -fr


        echo $SVN_TGCM_TRUNK_VERSION > $FLAGS_DIR/LAST_TGCM_TRUNK_BUILDED
        cd $BUILDER_DIR
        touch $FLAGS_DIR/PREPARE_BUILDER_TARBALL

    else
        INF "  <WARNING> Comprobacion: Version en SVN ($SVN_TGCM_TRUNK_VERSION) diferente a ultima utilizada ($LAST_TGCM_TRUNK_BUILD)... [NO OK]"

    fi
}

prepare_builder_tarball(){
    echo "Preparing tarball !"
    if [ -e $FLAGS_DIR/PREPARE_BUILDER_TARBALL ];
    then
         cd $BUILDER_DIR
        tar cvzf builder.tgz pkgs
        INF "  * Preparado tarball (.tgz) con los paquetes fuentes generados.................. [OK]"
        rm $FLAGS_DIR/PREPARE_BUILDER_TARBALL
    fi
}

INF_INIT
#build_src_tgcm_snapshot > /dev/null 2>&1
build_src_tgcm_snapshot
prepare_builder_tarball > /dev/null 2>&1
