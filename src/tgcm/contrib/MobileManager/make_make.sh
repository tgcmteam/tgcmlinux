#!/bin/bash

DIRS=$(find -L -type d)

echo "mmdir = \$(pythondir)/tgcm/contrib/MobileManager/"
ROOT_FILES=$(ls *.py | sed -e :a -e '$!N;s/\n/ /;ta')
echo "mm_PYTHON = $ROOT_FILES"

for D in $DIRS ;
do 
    if [ $(find -L $D -maxdepth 1 -type f | grep -v .svn | sed -e "s:^..::g" | wc -l) -ne 0 ]; then
	if [ "." != $D ]; then
	    FILES=$(find -L $D -maxdepth 1 -type f | grep -e ".py$" | grep -v .svn | sed -e "s:^..::g" | xargs echo)
	    DIR_NAME=$(echo $D | sed -e "s:\.::g" | sed -e "s:/:_:g")
	    echo -n "mm$DIR_NAME" ; echo "dir = \$(pythondir)/tgcm/contrib/MobileManager/$(echo $D | sed -e "s:^..::g")"
	    echo -n "mm$DIR_NAME" ; echo "_PYTHON = $FILES"
	    echo -e "\n"
	fi
    fi
done

