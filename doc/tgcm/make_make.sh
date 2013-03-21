#!/bin/bash

DIRS=$(find -L -type d)
EXTRA="EXTRA_DIST="

for D in $DIRS ;
do 
    if [ $(find -L $D -maxdepth 1 -type f | grep -v .svn | sed -e "s:^..::g" | wc -l) -ne 0 ]; then
	if [ "." != $D ]; then
	    FILES=$(find -L $D -maxdepth 1 -type f | grep -v .svn | sed -e "s:^..::g" | xargs echo)
	    DIR_NAME=$(echo $D | sed -e "s:\.::g" | sed -e "s:/:_:g")
	    echo -n "help$DIR_NAME" ; echo "dir = \$(docdir)/$(echo $D | sed -e "s:^..::g")"
	    echo -n "help$DIR_NAME" ; echo "_DATA = $FILES"
	    echo -e "\n"
	    EXTRA="$EXTRA \$($(echo -n "help$DIR_NAME" ; echo "_DATA"))"
	fi
    fi
done

echo $EXTRA
