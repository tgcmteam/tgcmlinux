#!/bin/bash

FINAL_PKGS_DIR=/root/rpmbuild/RPMS/
BUILDER_DIR=/root/builder
RPM_DIR=$BUILDER_DIR/rpm
REPOSITORY_DIR=$BUILDER_DIR/repository
FEDORA_REPO_DIR=$REPOSITORY_DIR/fedora16

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
    mkdir -p $FEDORA_REPO_DIR

    find $RPM_DIR -type f -exec rpmbuild --rebuild {} \;
    INF "  * Generacion de paquetes binarios ............................................. [OK]"

    find $FINAL_PKGS_DIR -type f -exec cp {} $FEDORA_REPO_DIR \;

    find $RPM_DIR -type f -exec cp {} $FEDORA_REPO_DIR \;

    cd $FEDORA_REPO_DIR
    cp $BUILDER_DIR/contrib/* .
    createrepo .
    INF "  * Actualizacion del repositorio ............................................... [OK]"

    rm -fr $RPM_DIR/*
}

INF_INIT
build_packages
