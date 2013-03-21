#!/bin/bash 

set -e

export LANG=C

BUILDER_DIR="/root/builder"
RPMBUILD_DIR=$BUILDER_DIR/rpmbuild
RPMBUILD_SRPMS_DIR=$RPMBUILD_DIR/SRPMS
FLAGS_DIR=$BUILDER_DIR/flags
PKGS_DIR=$BUILDER_DIR/pkgs
SVN_DIR=$BUILDER_DIR/svn
LAST_MM_DIR=$BUILDER_DIR/last/mobile-manager
LAST_TGCM_DIR=$BUILDER_DIR/last/tgcm

FICHERO_INFORME=InformeGeneracion.log
PATH_FICHERO_INFORME=$BUILDER_DIR/$FICHERO_INFORME

rm -fr $PKGS_DIR/*
rm -fr $SVN_DIR/*
rm -fr $RPMBUILD_SRPMS_DIR/*
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

        #Download trunk version of tgcm
        rm -fr $TGCM_SVN_SNAPSHOT_DIR
        svn --username roberto --password openshine export $SVN_TGCM_TRUNK_URL $TGCM_SVN_SNAPSHOT_DIR
	INF "  * Descargado codigo fuente del SVN............................................. [OK]"

	#
	# CHAPU PARA QUE SOLO HAYA UN SPEC Y QUE LAS GENRACIONES PARA PRUEBA TARDEN 17 VECES MENOS
	#
	#cp $TGCM_SVN_SNAPSHOT_DIR/specs/escritorio-movistar-argentina.spec $TGCM_SVN_SNAPSHOT_DIR/specs/escritorio-movistar-argentina.spec.copia
	#rm $TGCM_SVN_SNAPSHOT_DIR/specs/*.spec
	#mv $TGCM_SVN_SNAPSHOT_DIR/specs/escritorio-movistar-argentina.spec.copia $TGCM_SVN_SNAPSHOT_DIR/specs/escritorio-movistar-argentina.spec
	# FIN CHAPU

        cd $TGCM_SVN_SNAPSHOT_DIR
	echo "r$SVN_TGCM_TRUNK_VERSION" > latest-revision

        #Create tarball
        TGCM_VERSION=$(cat configure.ac | grep VERSION= | sed -e "s:VERSION=::g")
        patch -p1 < debian/patches/10_gcc4.patch

        ./autogen.sh --prefix=/usr --sysconfdir=/etc --localstatedir=/var --with-init-scripts=fedora
	make dist
	INF "  * Compilacion del codigo fuente................................................ [OK]"

        cd $TGCM_SVN_SNAPSHOT_DIR
        mkdir tmp
        cd tmp
	echo 'TAR xvfz desde: ' `pwd`
        tar xvzf ../tgcm-$TGCM_VERSION.tar.gz 
	for spec in $(find $TGCM_SVN_SNAPSHOT_DIR/specs/  -type f -exec basename {} \; ) ;
	do
	   pkg_name=$(echo $spec | sed -e 's:\.spec::g')
           ln -s tgcm-$TGCM_VERSION $pkg_name-$TGCM_VERSION
        done
        tar cvzf ../tgcm-$TGCM_VERSION.tar.gz * 	
	echo 'CONSTRUIDO TAR tgcm*'
        cd -
        rm -fr tmp
        
        cd $BUILDER_DIR

        #Copying tarball to pkg place
        TGCM_RPM_SNAPSHOT_DIR=$PKGS_DIR/tgcm-snapshot/
        rm -fr $TGCM_RPM_SNAPSHOT_DIR
        mkdir -p $TGCM_RPM_SNAPSHOT_DIR
        cp $TGCM_SVN_SNAPSHOT_DIR/*.tar.gz $TGCM_RPM_SNAPSHOT_DIR
	echo 'Copiado tarball a pkg place'

	for spec in $(find $TGCM_SVN_SNAPSHOT_DIR/specs/  -type f -exec basename {} \; ) ;
	do
            cat $TGCM_SVN_SNAPSHOT_DIR/specs/$spec | sed -e "s/Version.*$/Version: $TGCM_VERSION/g" | sed -e "s/Release.*$/Release: svn$SVN_TGCM_TRUNK_VERSION/g" > $TGCM_RPM_SNAPSHOT_DIR/$spec
	done

	echo 'Copiadas, con modificacion, las specs a dir. PKGS'
	
	rm -fr $RPMBUILD_SRPMS_DIR/*
        for spec in $(find $TGCM_RPM_SNAPSHOT_DIR/ -name *.spec -type f -exec basename {} \;) ;
        do
           pkg_name=$(echo $spec | sed -e 's:\.spec::g')
	   rm -fr $RPMBUILD_DIR/$pkg_name
           ln -s $TGCM_RPM_SNAPSHOT_DIR $RPMBUILD_DIR/$pkg_name
           cd $RPMBUILD_DIR/$pkg_name 
           pwd
	   echo "Lanzando rpmbuild -bs " $spec
           rpmbuild -bs $spec
           cd -
        done
       
	INF "  * Generados paquetes fuentes .................................................. [OK]" 
        cp $RPMBUILD_SRPMS_DIR/* $PKGS_DIR
	rm -fr $LAST_TGCM_DIR/*
        cp $RPMBUILD_SRPMS_DIR/* $LAST_TGCM_DIR
        cd -


        #Create rpm pkg
        echo $SVN_TGCM_TRUNK_VERSION > $FLAGS_DIR/LAST_TGCM_TRUNK_BUILDED
        cd $BUILDER_DIR
        touch $FLAGS_DIR/PREPARE_BUILDER_TARBALL
	rm -fr $TGCM_RPM_SNAPSHOT_DIR

    else
	INF "  <WARNING> Comprobacion: Version en SVN ($SVN_TGCM_TRUNK_VERSION) diferente a ultima utilizada ($LAST_TGCM_TRUNK_BUILD)... [NO OK]"

	#touch $FLAGS_DIR/PREPARE_BUILDER_TARBALL
        #cp $LAST_TGCM_DIR/* $PKGS_DIR
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
build_src_tgcm_snapshot
prepare_builder_tarball
#prepare_builder_tarball > /dev/null 2>&1

