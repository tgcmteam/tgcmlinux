#!/bin/bash

DIRS=$(find -L -type d)

echo "fdonetdir = \$(pythondir)/tgcm/contrib/freedesktopnet/"
echo "fdonet_PYTHON = __init__.py"

for D in $DIRS ;
do 
    if [ $(find -L $D -maxdepth 1 -type f | grep -v .svn | sed -e "s:^..::g" | wc -l) -ne 0 ]; then
	if [ "." != $D ]; then
	    FILES=$(find -L $D -maxdepth 1 -type f | grep -e ".py$" | grep -v .svn | sed -e "s:^..::g" | xargs echo)
	    DIR_NAME=$(echo $D | sed -e "s:\.::g" | sed -e "s:/:_:g")
	    echo -n "fdonet$DIR_NAME" ; echo "dir = \$(pythondir)/tgcm/contrib/freedesktopnet/$(echo $D | sed -e "s:^..::g")"
	    echo -n "fdonet$DIR_NAME" ; echo "_PYTHON = $FILES"
	    echo -e "\n"
	fi
    fi
done

