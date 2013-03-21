#!/bin/bash

gawk '
BEGIN   {in_line = 0 }
/^### THEMES_MAKEFILE_AM INIT ###$/  { in_line = 1 }
/^### THEMES_MAKEFILE_AM END  ###$/  { in_line = 0; next }
{ if(in_line == 1) next; else print}
' ./data/Makefile.am > ./data/Makefile.am.tmp

mv ./data/Makefile.am.tmp ./data/Makefile.am

echo "### THEMES_MAKEFILE_AM INIT ###" >> ./data/Makefile.am
echo "### DON'T TOUCH !!!!###" >> ./data/Makefile.am

DIRS=$(cd ./data/themes && find -L -type d)
EXTRA="EXTRA_DIST="

for D in $DIRS ;
do 
    if [ $(cd ./data/themes && find -L $D -maxdepth 1 -type f | grep -v .svn | sed -e "s:^..::g" | wc -l) -ne 0 ]; then
	if [ "." != $D ]; then
	    FILES=$(cd ./data/themes && find -L $D -maxdepth 1 -type f | grep -v .svn | sed -e "s:^..::g" | sed -e "s:^:themes/:g" | xargs echo)
	    DIR_NAME=$(echo $D | sed -e "s:\.::g" | sed -e "s:/:_:g")
	    echo -n "theme$DIR_NAME" >> ./data/Makefile.am
            echo "dir = \$(datadir)/tgcm/themes/$(echo $D | sed -e "s:^..::g")" >> ./data/Makefile.am
	    echo -n "theme$DIR_NAME" >> ./data/Makefile.am
            echo "_DATA = $FILES" >> ./data/Makefile.am
	    echo -e "\n" >> ./data/Makefile.am
	    EXTRA="$EXTRA \$($(echo -n "theme$DIR_NAME" ; echo "_DATA"))"
	fi
    fi
done

echo $EXTRA >> ./data/Makefile.am
echo "### THEMES_MAKEFILE_AM END ###" >> ./data/Makefile.am
