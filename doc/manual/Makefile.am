helpdir=$(docdir)/help
help_DATA = $(shell find help -maxdepth 1 -type f | grep -v .svn)

helpcssdir=$(docdir)/help/css
helpcss_DATA = $(shell find help/css -maxdepth 1 -type f | grep -v .svn)

helpimgdir=$(docdir)/help/img
helpimg_DATA = $(shell find help/img -maxdepth 1 -type f | grep -v .svn)

EXTRA_DIST= $(help_DATA) $(helpcss_DATA) $(helpimg_DATA)
