@echo off

Echo Paking ES ----------------- >pack.log
CreateThemePak es\default >>pack.log

Echo Paking LATAM -----------------  >>pack.log
CreateThemePak latam\ar\default >>pack.log

Echo Paking UK ----------------- >>pack.log
CreateThemePak uk\default >>pack.log

Echo Paking IE ----------------- >>pack.log
CreateThemePak ie\default >>pack.log

Echo Paking DE ----------------- >>pack.log
CreateThemePak de\default >>pack.log

Echo Paking DE EUROVIA --------- >>pack.log
CreateThemePak de\eurovia >>pack.log

Echo Paking DE FONIC ----------------- >>pack.log
CreateThemePak de_fonic\default >>pack.log

Echo Paking CZ ----------------- >>pack.log
CreateThemePak cz\default >>pack.log

pause
