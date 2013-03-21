#!/bin/bash

FINAL_PKGS_DIR=/usr/src/packages
BUILDER_DIR=/root/builder
RPM_DIR=$BUILDER_DIR/rpm
REPOSITORY_DIR=$BUILDER_DIR/repository
OPENSUSE12_REPO_DIR=$REPOSITORY_DIR/opensuse121

FICHERO_INFORME=InformeGeneracion.log
PATH_FICHERO_INFORME=$BUILDER_DIR/$FICHERO_INFORME

INF_INIT() {
    > $PATH_FICHERO_INFORME
}

INF() {
    echo "$1" >> $PATH_FICHERO_INFORME
}


build_packages () {
    rm -fr $REPOSITORY_DIR/*

    find $FINAL_PKGS_DIR -type f -exec rm {} \;
    mkdir -p $OPENSUSE12_REPO_DIR

    find $RPM_DIR -type f -exec rpmbuild --rebuild {} \;
    INF "  * Generacion de paquetes binarios ............................................. [OK]"

    find $FINAL_PKGS_DIR -name *.rpm -type f -exec cp {} $OPENSUSE12_REPO_DIR \;

    find $RPM_DIR -name *.rpm -type f -exec cp {} $OPENSUSE12_REPO_DIR \;

    cd $OPENSUSE12_REPO_DIR
    cp $BUILDER_DIR/contrib/* .
    createrepo .
    INF "  * Actualizacion del repositorio ............................................... [OK]"

    rm -fr $RPM_DIR/*
}

# Parece que si no esta montado el proc se produce un error al acceder a /proc/cpuinfo en la fase de creacion de repositorio
mount /proc
INF_INIT
build_packages
