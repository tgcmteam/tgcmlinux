SUBDIRS = autostart icons icon-theme mime-stuff regional-info

### THEMES_MAKEFILE_AM INIT ###
### DON'T TOUCH !!!!###

### FIXME ####
convert_icos_scriptdir = $(datadir)/tgcm
convert_icos_script_DATA = extract_icons.py
### FIXME ###


### Spain ###

APPICON_ES_ICO = themes/es/default/icon.ico
APPICON_ES_PNG = themes/es/default/icon.png

$(APPICON_ES_PNG): $(APPICON_ES_ICO)
	./extract_icons.py --main-icon $?

theme_es_defaultdir = $(datadir)/tgcm/themes/es/default
theme_es_default_DATA = themes/es/default/theme.xml themes/es/default/theme.pot $(APPICON_ES_PNG) $(APPICON_ES_ICO)


theme_es_default_bannersdir = $(datadir)/tgcm/themes/es/default/banners
theme_es_default_banners_DATA = themes/es/default/banners/blank.png themes/es/default/banners/settings.png themes/es/default/banners/bar.png themes/es/default/banners/banner_bgnd.png themes/es/default/banners/banners.xml themes/es/default/banners/help.png themes/es/default/banners/movistar.png

TRAYICONS_ES_ICO = themes/es/default/icons/conectado.ico \
	themes/es/default/icons/desconectado.ico \
	themes/es/default/icons/conectado_smspending.ico \
	themes/es/default/icons/desconectado_smspending.ico

FAV_ES_ICO = themes/es/default/icons/fav.ico

SERVICES_ES_ICO = themes/es/default/icons/addressbook.ico \
	themes/es/default/icons/favorites.ico \
	themes/es/default/icons/help.ico \
	themes/es/default/icons/intranet.ico \
	themes/es/default/icons/recarga.ico \
	themes/es/default/icons/settings.ico \
	themes/es/default/icons/sms.ico \
	themes/es/default/icons/traffic.ico \
	themes/es/default/icons/wifi.ico

SERVICES_ES_PNG = themes/es/default/icons/addressbook_service.png \
	themes/es/default/icons/favorites_service.png \
	themes/es/default/icons/help_service.png \
	themes/es/default/icons/intranet_service.png \
	themes/es/default/icons/recarga_service.png \
	themes/es/default/icons/settings_service.png \
	themes/es/default/icons/sms_service.png \
	themes/es/default/icons/traffic_service.png \
	themes/es/default/icons/wifi_service.png

TASKBARS_ES_PNG = themes/es/default/icons/addressbook_taskbar.png \
	themes/es/default/icons/favorites_taskbar.png \
	themes/es/default/icons/help_taskbar.png \
	themes/es/default/icons/intranet_taskbar.png \
	themes/es/default/icons/recarga_taskbar.png \
	themes/es/default/icons/settings_taskbar.png \
	themes/es/default/icons/sms_taskbar.png \
	themes/es/default/icons/traffic_taskbar.png \
	themes/es/default/icons/wifi_taskbar.png

$(SERVICES_ES_PNG): $(SERVICES_ES_ICO)
	./extract_icons.py --service-icon --add-suffix $?

$(TASKBARS_ES_PNG): $(SERVICES_ES_ICO)
	./extract_icons.py --taskbar-icon --add-suffix $?

theme_es_default_iconsdir = $(datadir)/tgcm/themes/es/default/icons
theme_es_default_icons_DATA = $(TRAYICONS_ES_ICO) \
	$(FAV_ES_ICO) \
	$(SERVICES_ES_ICO) $(SERVICES_ES_PNG) \
	$(TASKBARS_ES_PNG)


theme_es_default_notifiersdir = $(datadir)/tgcm/themes/es/default/notifiers
theme_es_default_notifiers_DATA = themes/es/default/notifiers/tbnvcall.png themes/es/default/notifiers/notifiers.xml themes/es/default/notifiers/tbnclose.png themes/es/default/notifiers/tbnhangup.png themes/es/default/notifiers/tbnsms.png themes/es/default/notifiers/tbnpickup.png themes/es/default/notifiers/tbnerror.png themes/es/default/notifiers/tbngen.png


theme_es_default_dockdir = $(datadir)/tgcm/themes/es/default/dock
theme_es_default_dock_DATA = themes/es/default/dock/docking.png themes/es/default/dock/connect.png themes/es/default/dock/trafficgraph.png themes/es/default/dock/led_desconectado.png themes/es/default/dock/signal.png themes/es/default/dock/logo.png themes/es/default/dock/smart.png themes/es/default/dock/lock.png themes/es/default/dock/lan.png themes/es/default/dock/traffic.png themes/es/default/dock/led_conectado.png themes/es/default/dock/disconnect.png themes/es/default/dock/unlock.png themes/es/default/dock/wifisignal.png themes/es/default/dock/bkgnd.png themes/es/default/dock/connecting.png


theme_es_default_devicedir = $(datadir)/tgcm/themes/es/default/device
theme_es_default_device_DATA = themes/es/default/device/device.png themes/es/default/device/home.png themes/es/default/device/available.png themes/es/default/device/roaming.png


theme_es_default_servicesdir = $(datadir)/tgcm/themes/es/default/services
theme_es_default_services_DATA = themes/es/default/services/addressbook.png themes/es/default/services/intranet.png themes/es/default/services/favorites.png themes/es/default/services/sms.png themes/es/default/services/wifi.png themes/es/default/services/more.png themes/es/default/services/recarga.png themes/es/default/services/circle.png


theme_es_default_sysbtndir = $(datadir)/tgcm/themes/es/default/sysbtn
theme_es_default_sysbtn_DATA = themes/es/default/sysbtn/minimize.png themes/es/default/sysbtn/settings.png themes/es/default/sysbtn/close.png themes/es/default/sysbtn/help.png


### Ireland ###

APPICON_IE_ICO = themes/ie/default/icon.ico
APPICON_IE_PNG = themes/ie/default/icon.png

$(APPICON_IE_PNG): $(APPICON_IE_ICO)
	./extract_icons.py --main-icon $?

theme_ie_defaultdir = $(datadir)/tgcm/themes/ie/default
theme_ie_default_DATA = themes/ie/default/theme.xml themes/ie/default/theme.pot $(APPICON_IE_PNG) $(APPICON_IE_ICO)


theme_ie_default_bannersdir = $(datadir)/tgcm/themes/ie/default/banners
theme_ie_default_banners_DATA = themes/ie/default/banners/settings.png themes/ie/default/banners/banner_bgnd.png themes/ie/default/banners/banners.xml themes/ie/default/banners/help.png

TRAYICONS_IE_ICO = themes/ie/default/icons/conectado.ico \
	themes/ie/default/icons/desconectado.ico \
	themes/ie/default/icons/conectado_smspending.ico \
	themes/ie/default/icons/desconectado_smspending.ico

TRAYICONS_IE_PNG = themes/ie/default/icons/conectado.png \
	themes/ie/default/icons/desconectado.png \
	themes/ie/default/icons/conectado_smspending.png \
	themes/ie/default/icons/desconectado_smspending.png

$(TRAYICONS_IE_PNG): $(TRAYICONS_IE_ICO)
	./extract_icons.py --tray-icon $?

FAV_IE_ICO = themes/ie/default/icons/fav.ico

SERVICES_IE_ICO = themes/ie/default/icons/addressbook.ico \
	themes/ie/default/icons/favorites.ico \
	themes/ie/default/icons/help.ico \
	themes/ie/default/icons/settings.ico \
	themes/ie/default/icons/sms.ico \
	themes/ie/default/icons/traffic.ico \
	themes/ie/default/icons/wifi.ico

SERVICES_IE_PNG = themes/ie/default/icons/addressbook_service.png \
	themes/ie/default/icons/favorites_service.png \
	themes/ie/default/icons/help_service.png \
	themes/ie/default/icons/settings_service.png \
	themes/ie/default/icons/sms_service.png \
	themes/ie/default/icons/traffic_service.png \
	themes/ie/default/icons/wifi_service.png

TASKBARS_IE_PNG = themes/ie/default/icons/addressbook_taskbar.png \
	themes/ie/default/icons/favorites_taskbar.png \
	themes/ie/default/icons/help_taskbar.png \
	themes/ie/default/icons/settings_taskbar.png \
	themes/ie/default/icons/sms_taskbar.png \
	themes/ie/default/icons/traffic_taskbar.png \
	themes/ie/default/icons/wifi_taskbar.png

$(SERVICES_IE_PNG): $(SERVICES_IE_ICO)
	./extract_icons.py --service-icon --add-suffix $?

$(TASKBARS_IE_PNG): $(SERVICES_IE_ICO)
	./extract_icons.py --taskbar-icon --add-suffix $?

theme_ie_default_iconsdir = $(datadir)/tgcm/themes/ie/default/icons
theme_ie_default_icons_DATA = $(TRAYICONS_IE_ICO) $(TRAYICONS_IE_PNG) \
	$(FAV_IE_ICO) \
	$(SERVICES_IE_ICO) $(SERVICES_IE_PNG) \
	$(TASKBARS_IE_PNG)


theme_ie_default_notifiersdir = $(datadir)/tgcm/themes/ie/default/notifiers
theme_ie_default_notifiers_DATA = themes/ie/default/notifiers/tbntraffic.png themes/ie/default/notifiers/notifiers.xml themes/ie/default/notifiers/tbnclose.png themes/ie/default/notifiers/tbnsms.png themes/ie/default/notifiers/tbnerror.png themes/ie/default/notifiers/tbngen.png


theme_ie_default_dockdir = $(datadir)/tgcm/themes/ie/default/dock
theme_ie_default_dock_DATA = themes/ie/default/dock/logoo2.png themes/ie/default/dock/docking.png themes/ie/default/dock/connect.png themes/ie/default/dock/trafficgraph.png themes/ie/default/dock/signal.png themes/ie/default/dock/progconn.png themes/ie/default/dock/lock.png themes/ie/default/dock/lan.png themes/ie/default/dock/traffic.png themes/ie/default/dock/disconnect.png themes/ie/default/dock/unlock.png themes/ie/default/dock/wifisignal.png themes/ie/default/dock/bkgnd.png


theme_ie_default_devicedir = $(datadir)/tgcm/themes/ie/default/device
theme_ie_default_device_DATA = themes/ie/default/device/device.png themes/ie/default/device/home.png themes/ie/default/device/available.png themes/ie/default/device/roaming.png


theme_ie_default_servicesdir = $(datadir)/tgcm/themes/ie/default/services
theme_ie_default_services_DATA = themes/ie/default/services/uk-help.png themes/ie/default/services/addressbook.png themes/ie/default/services/uk-settings.png themes/ie/default/services/favorites.png themes/ie/default/services/sms.png themes/ie/default/services/wifi.png themes/ie/default/services/more.png themes/ie/default/services/circle.png


theme_ie_default_sysbtndir = $(datadir)/tgcm/themes/ie/default/sysbtn
theme_ie_default_sysbtn_DATA = themes/ie/default/sysbtn/minimize.png themes/ie/default/sysbtn/close.png


### UK ###

APPICON_UK_ICO = themes/uk/default/icon.ico
APPICON_UK_PNG = themes/uk/default/icon.png

$(APPICON_UK_PNG): $(APPICON_UK_ICO)
	./extract_icons.py --main-icon $?

theme_uk_defaultdir = $(datadir)/tgcm/themes/uk/default
theme_uk_default_DATA = themes/uk/default/theme.xml themes/uk/default/theme.pot $(APPICON_UK_PNG) $(APPICON_UK_ICO)


theme_uk_default_bannersdir = $(datadir)/tgcm/themes/uk/default/banners
theme_uk_default_banners_DATA = themes/uk/default/banners/settings.png themes/uk/default/banners/banner_bgnd.png themes/uk/default/banners/banners.xml themes/uk/default/banners/help.png

TRAYICONS_UK_ICO = themes/uk/default/icons/conectado.ico \
	themes/uk/default/icons/desconectado.ico \
	themes/uk/default/icons/conectado_smspending.ico \
	themes/uk/default/icons/desconectado_smspending.ico

TRAYICONS_UK_PNG = themes/uk/default/icons/conectado.png \
	themes/uk/default/icons/desconectado.png \
	themes/uk/default/icons/conectado_smspending.png \
	themes/uk/default/icons/desconectado_smspending.png

$(TRAYICONS_UK_PNG): $(TRAYICONS_UK_ICO)
	./extract_icons.py --tray-icon $?

FAV_UK_ICO = themes/uk/default/icons/fav.ico

SERVICES_UK_ICO = themes/uk/default/icons/addressbook.ico \
	themes/uk/default/icons/favorites.ico \
	themes/uk/default/icons/help.ico \
	themes/uk/default/icons/intranet.ico \
	themes/uk/default/icons/settings.ico \
	themes/uk/default/icons/sms.ico \
	themes/uk/default/icons/traffic.ico \
	themes/uk/default/icons/wifi.ico

SERVICES_UK_PNG = themes/uk/default/icons/addressbook_service.png \
	themes/uk/default/icons/favorites_service.png \
	themes/uk/default/icons/help_service.png \
	themes/uk/default/icons/intranet_service.png \
	themes/uk/default/icons/settings_service.png \
	themes/uk/default/icons/sms_service.png \
	themes/uk/default/icons/traffic_service.png \
	themes/uk/default/icons/wifi_service.png

TASKBARS_UK_PNG = themes/uk/default/icons/addressbook_taskbar.png \
	themes/uk/default/icons/favorites_taskbar.png \
	themes/uk/default/icons/help_taskbar.png \
	themes/uk/default/icons/intranet_taskbar.png \
	themes/uk/default/icons/settings_taskbar.png \
	themes/uk/default/icons/sms_taskbar.png \
	themes/uk/default/icons/traffic_taskbar.png \
	themes/uk/default/icons/wifi_taskbar.png

$(SERVICES_UK_PNG): $(SERVICES_UK_ICO)
	./extract_icons.py --service-icon --add-suffix $?

$(TASKBARS_UK_PNG): $(SERVICES_UK_ICO)
	./extract_icons.py --taskbar-icon --add-suffix $?

theme_uk_default_iconsdir = $(datadir)/tgcm/themes/uk/default/icons
theme_uk_default_icons_DATA = $(TRAYICONS_UK_ICO) $(TRAYICONS_UK_PNG) \
	$(FAV_UK_ICO) \
	$(SERVICES_UK_ICO) $(SERVICES_UK_PNG) \
	$(TASKBARS_UK_PNG)


theme_uk_default_notifiersdir = $(datadir)/tgcm/themes/uk/default/notifiers
theme_uk_default_notifiers_DATA = themes/uk/default/notifiers/tbntraffic.png themes/uk/default/notifiers/notifiers.xml themes/uk/default/notifiers/tbnclose.png themes/uk/default/notifiers/tbnsms.png themes/uk/default/notifiers/tbnerror.png themes/uk/default/notifiers/tbngen.png


theme_uk_default_dockdir = $(datadir)/tgcm/themes/uk/default/dock
theme_uk_default_dock_DATA = themes/uk/default/dock/logoo2.png themes/uk/default/dock/docking.png themes/uk/default/dock/connect.png themes/uk/default/dock/trafficgraph.png themes/uk/default/dock/signal.png themes/uk/default/dock/progconn.png themes/uk/default/dock/lock.png themes/uk/default/dock/lan.png themes/uk/default/dock/traffic.png themes/uk/default/dock/disconnect.png themes/uk/default/dock/unlock.png themes/uk/default/dock/wifisignal.png themes/uk/default/dock/bkgnd.png


theme_uk_default_devicedir = $(datadir)/tgcm/themes/uk/default/device
theme_uk_default_device_DATA = themes/uk/default/device/device.png themes/uk/default/device/home.png themes/uk/default/device/available.png themes/uk/default/device/roaming.png


theme_uk_default_servicesdir = $(datadir)/tgcm/themes/uk/default/services
theme_uk_default_services_DATA = themes/uk/default/services/uk-help.png themes/uk/default/services/addressbook.png themes/uk/default/services/uk-settings.png themes/uk/default/services/intranet.png themes/uk/default/services/favorites.png themes/uk/default/services/sms.png themes/uk/default/services/wifi.png themes/uk/default/services/more.png themes/uk/default/services/circle.png


theme_uk_default_sysbtndir = $(datadir)/tgcm/themes/uk/default/sysbtn
theme_uk_default_sysbtn_DATA = themes/uk/default/sysbtn/minimize.png themes/uk/default/sysbtn/close.png


### Denmark (default theme) ###

APPICON_DE_ICO = themes/de/default/icon.ico
APPICON_DE_PNG = themes/de/default/icon.png

$(APPICON_DE_PNG): $(APPICON_DE_ICO)
	./extract_icons.py --main-icon $?

theme_de_defaultdir = $(datadir)/tgcm/themes/de/default
theme_de_default_DATA = themes/de/default/theme.xml themes/de/default/theme.pot $(APPICON_DE_PNG) $(APPICON_DE_ICO)


theme_de_default_bannersdir = $(datadir)/tgcm/themes/de/default/banners
theme_de_default_banners_DATA = themes/de/default/banners/settings.png themes/de/default/banners/banner_bgnd.png themes/de/default/banners/banners.xml themes/de/default/banners/help.png

TRAYICONS_DE_ICO = themes/de/default/icons/conectado.ico \
	themes/de/default/icons/desconectado.ico \
	themes/de/default/icons/conectado_smspending.ico \
	themes/de/default/icons/desconectado_smspending.ico

TRAYICONS_DE_PNG = themes/de/default/icons/conectado.png \
	themes/de/default/icons/desconectado.png \
	themes/de/default/icons/conectado_smspending.png \
	themes/de/default/icons/desconectado_smspending.png

$(TRAYICONS_DE_PNG): $(TRAYICONS_DE_ICO)
	./extract_icons.py --tray-icon $?

FAV_DE_ICO = themes/de/default/icons/fav.ico

SERVICES_DE_ICO = themes/de/default/icons/addressbook.ico \
	themes/de/default/icons/favorites.ico \
	themes/de/default/icons/intranet.ico \
	themes/de/default/icons/online_de.ico \
	themes/de/default/icons/prepay.ico \
	themes/de/default/icons/sms.ico \
	themes/de/default/icons/traffic.ico \
	themes/de/default/icons/videocall.ico \
	themes/de/default/icons/wifi.ico

SERVICES_DE_PNG = themes/de/default/icons/addressbook_service.png \
	themes/de/default/icons/favorites_service.png \
	themes/de/default/icons/intranet_service.png \
	themes/de/default/icons/online_de_service.png \
	themes/de/default/icons/prepay_service.png \
	themes/de/default/icons/sms_service.png \
	themes/de/default/icons/traffic_service.png \
	themes/de/default/icons/videocall_service.png \
	themes/de/default/icons/wifi_service.png

TASKBARS_DE_ICO = themes/de/default/icons/help.ico \
	themes/de/default/icons/settings.ico

TASKBARS_DE_PNG = themes/de/default/icons/addressbook_taskbar.png \
	themes/de/default/icons/favorites_taskbar.png \
	themes/de/default/icons/help_taskbar.png \
	themes/de/default/icons/intranet_taskbar.png \
	themes/de/default/icons/online_de_taskbar.png \
	themes/de/default/icons/prepay_taskbar.png \
	themes/de/default/icons/settings_taskbar.png \
	themes/de/default/icons/sms_taskbar.png \
	themes/de/default/icons/traffic_taskbar.png \
	themes/de/default/icons/videocall_taskbar.png \
	themes/de/default/icons/wifi_taskbar.png

$(SERVICES_DE_PNG): $(SERVICES_DE_ICO)
	./extract_icons.py --service-icon --add-suffix $?

$(TASKBARS_DE_PNG): $(SERVICES_DE_ICO) $(TASKBARS_DE_ICO)
	./extract_icons.py --taskbar-icon --add-suffix $?

theme_de_default_iconsdir = $(datadir)/tgcm/themes/de/default/icons
theme_de_default_icons_DATA = $(TRAYICONS_DE_ICO) $(TRAYICONS_DE_PNG) \
	$(FAV_DE_ICO) \
	$(SERVICES_DE_ICO) $(SERVICES_DE_PNG) \
	$(TASKBARS_DE_ICO) $(TASKBARS_DE_PNG)


theme_de_default_notifiersdir = $(datadir)/tgcm/themes/de/default/notifiers
theme_de_default_notifiers_DATA = themes/de/default/notifiers/tbnvcall.png themes/de/default/notifiers/notifiers.xml themes/de/default/notifiers/tbnclose.png themes/de/default/notifiers/tbnhangup.png themes/de/default/notifiers/tbnsms.png themes/de/default/notifiers/tbnpickup.png themes/de/default/notifiers/tbnerror.png themes/de/default/notifiers/tbngen.png


theme_de_default_dockdir = $(datadir)/tgcm/themes/de/default/dock
theme_de_default_dock_DATA = themes/de/default/dock/docking.png themes/de/default/dock/connect.png themes/de/default/dock/trafficgraph.png themes/de/default/dock/signal.png themes/de/default/dock/logo.png themes/de/default/dock/smart.png themes/de/default/dock/lock.png themes/de/default/dock/lan.png themes/de/default/dock/traffic.png themes/de/default/dock/disconnect.png themes/de/default/dock/unlock.png themes/de/default/dock/wifisignal.png themes/de/default/dock/bkgnd.png themes/de/default/dock/connecting.png


theme_de_default_devicedir = $(datadir)/tgcm/themes/de/default/device
theme_de_default_device_DATA = themes/de/default/device/device.png themes/de/default/device/home.png themes/de/default/device/available.png themes/de/default/device/roaming.png


theme_de_default_servicesdir = $(datadir)/tgcm/themes/de/default/services
theme_de_default_services_DATA = themes/de/default/services/addressbook.png themes/de/default/services/intranet.png themes/de/default/services/favorites.png themes/de/default/services/sms.png themes/de/default/services/wifi.png themes/de/default/services/euro_icn_win.png themes/de/default/services/more.png themes/de/default/services/www_icn_win.png themes/de/default/services/circle.png themes/de/default/services/videocall.png


theme_de_default_sysbtndir = $(datadir)/tgcm/themes/de/default/sysbtn
theme_de_default_sysbtn_DATA = themes/de/default/sysbtn/minimize.png themes/de/default/sysbtn/settings.png themes/de/default/sysbtn/close.png themes/de/default/sysbtn/help.png


### Denmark (Eurovia theme) ###

APPICON_DE_EUROVIA_ICO = themes/de/eurovia/icon.ico
APPICON_DE_EUROVIA_PNG = themes/de/eurovia/icon.png

$(APPICON_DE_EUROVIA_PNG): $(APPICON_DE_EUROVIA_ICO)
	./extract_icons.py --main-icon $?

theme_de_euroviadir = $(datadir)/tgcm/themes/de/eurovia
theme_de_eurovia_DATA = themes/de/eurovia/theme.xml themes/de/eurovia/theme.pot $(APPICON_DE_EUROVIA_PNG) $(APPICON_DE_EUROVIA_ICO)


theme_de_eurovia_bannersdir = $(datadir)/tgcm/themes/de/eurovia/banners
theme_de_eurovia_banners_DATA = themes/de/eurovia/banners/settings.png themes/de/eurovia/banners/banner_bgnd.png themes/de/eurovia/banners/banners.xml themes/de/eurovia/banners/help.png

TRAYICONS_DE_EUROVIA_ICO = themes/de/eurovia/icons/conectado.ico \
	themes/de/eurovia/icons/desconectado.ico \
	themes/de/eurovia/icons/conectado_smspending.ico \
	themes/de/eurovia/icons/desconectado_smspending.ico

TRAYICONS_DE_EUROVIA_PNG = themes/de/eurovia/icons/conectado.png \
	themes/de/eurovia/icons/desconectado.png \
	themes/de/eurovia/icons/conectado_smspending.png \
	themes/de/eurovia/icons/desconectado_smspending.png

$(TRAYICONS_DE_EUROVIA_PNG): $(TRAYICONS_DE_EUROVIA_ICO)
	./extract_icons.py --tray-icon $?

FAV_DE_EUROVIA_ICO = themes/de/eurovia/icons/fav.ico

SERVICES_DE_EUROVIA_ICO = themes/de/eurovia/icons/addressbook.ico \
	themes/de/eurovia/icons/favorites.ico \
	themes/de/eurovia/icons/intranet.ico \
	themes/de/eurovia/icons/online_de.ico \
	themes/de/eurovia/icons/prepay.ico \
	themes/de/eurovia/icons/sms.ico \
	themes/de/eurovia/icons/traffic.ico \
	themes/de/eurovia/icons/videocall.ico \
	themes/de/eurovia/icons/wifi.ico

SERVICES_DE_EUROVIA_PNG = themes/de/eurovia/icons/addressbook_service.png \
	themes/de/eurovia/icons/favorites_service.png \
	themes/de/eurovia/icons/intranet_service.png \
	themes/de/eurovia/icons/online_de_service.png \
	themes/de/eurovia/icons/prepay_service.png \
	themes/de/eurovia/icons/sms_service.png \
	themes/de/eurovia/icons/traffic_service.png \
	themes/de/eurovia/icons/videocall_service.png \
	themes/de/eurovia/icons/wifi_service.png

TASKBARS_DE_EUROVIA_ICO = themes/de/eurovia/icons/help.ico \
	themes/de/eurovia/icons/settings.ico

TASKBARS_DE_EUROVIA_PNG = themes/de/eurovia/icons/addressbook_taskbar.png \
	themes/de/eurovia/icons/favorites_taskbar.png \
	themes/de/eurovia/icons/help_taskbar.png \
	themes/de/eurovia/icons/intranet_taskbar.png \
	themes/de/eurovia/icons/online_de_taskbar.png \
	themes/de/eurovia/icons/prepay_taskbar.png \
	themes/de/eurovia/icons/settings_taskbar.png \
	themes/de/eurovia/icons/sms_taskbar.png \
	themes/de/eurovia/icons/traffic_taskbar.png \
	themes/de/eurovia/icons/videocall_taskbar.png \
	themes/de/eurovia/icons/wifi_taskbar.png

$(SERVICES_DE_EUROVIA_PNG): $(SERVICES_DE_EUROVIA_ICO)
	./extract_icons.py --service-icon --add-suffix $?

$(TASKBARS_DE_EUROVIA_PNG): $(SERVICES_DE_EUROVIA_ICO) $(TASKBARS_DE_EUROVIA_ICO)
	./extract_icons.py --taskbar-icon --add-suffix $?

theme_de_eurovia_iconsdir = $(datadir)/tgcm/themes/de/eurovia/icons
theme_de_eurovia_icons_DATA = $(TRAYICONS_DE_EUROVIA_ICO) $(TRAYICONS_DE_EUROVIA_PNG) \
	$(FAV_DE_EUROVIA_ICO) \
	$(SERVICES_DE_EUROVIA_ICO) $(SERVICES_DE_EUROVIA_PNG) \
	$(TASKBARS_DE_EUROVIA_ICO) $(TASKBARS_DE_EUROVIA_PNG)


theme_de_eurovia_notifiersdir = $(datadir)/tgcm/themes/de/eurovia/notifiers
theme_de_eurovia_notifiers_DATA = themes/de/eurovia/notifiers/tbnvcall.png themes/de/eurovia/notifiers/notifiers.xml themes/de/eurovia/notifiers/tbnclose.png themes/de/eurovia/notifiers/tbnhangup.png themes/de/eurovia/notifiers/tbnsms.png themes/de/eurovia/notifiers/tbnpickup.png themes/de/eurovia/notifiers/tbnerror.png themes/de/eurovia/notifiers/tbngen.png


theme_de_eurovia_dockdir = $(datadir)/tgcm/themes/de/eurovia/dock
theme_de_eurovia_dock_DATA = themes/de/eurovia/dock/docking.png themes/de/eurovia/dock/connect.png themes/de/eurovia/dock/trafficgraph.png themes/de/eurovia/dock/signal.png themes/de/eurovia/dock/logo.png themes/de/eurovia/dock/smart.png themes/de/eurovia/dock/lock.png themes/de/eurovia/dock/lan.png themes/de/eurovia/dock/traffic.png themes/de/eurovia/dock/disconnect.png themes/de/eurovia/dock/unlock.png themes/de/eurovia/dock/wifisignal.png themes/de/eurovia/dock/bkgnd.png themes/de/eurovia/dock/connecting.png


theme_de_eurovia_devicedir = $(datadir)/tgcm/themes/de/eurovia/device
theme_de_eurovia_device_DATA = themes/de/eurovia/device/device.png themes/de/eurovia/device/home.png themes/de/eurovia/device/available.png themes/de/eurovia/device/roaming.png


theme_de_eurovia_servicesdir = $(datadir)/tgcm/themes/de/eurovia/services
theme_de_eurovia_services_DATA = themes/de/eurovia/services/addressbook.png themes/de/eurovia/services/intranet.png themes/de/eurovia/services/favorites.png themes/de/eurovia/services/sms.png themes/de/eurovia/services/wifi.png themes/de/eurovia/services/euro_icn_win.png themes/de/eurovia/services/more.png themes/de/eurovia/services/www_icn_win.png themes/de/eurovia/services/circle.png themes/de/eurovia/services/videocall.png


theme_de_eurovia_sysbtndir = $(datadir)/tgcm/themes/de/eurovia/sysbtn
theme_de_eurovia_sysbtn_DATA = themes/de/eurovia/sysbtn/minimize.png themes/de/eurovia/sysbtn/settings.png themes/de/eurovia/sysbtn/close.png themes/de/eurovia/sysbtn/help.png


### Czech Republic ###

APPICON_CZ_ICO = themes/cz/default/icon.ico
APPICON_CZ_PNG = themes/cz/default/icon.png

$(APPICON_CZ_PNG): $(APPICON_CZ_ICO)
	./extract_icons.py --main-icon $?

theme_cz_defaultdir = $(datadir)/tgcm/themes/cz/default
theme_cz_default_DATA = themes/cz/default/theme.xml themes/cz/default/theme.pot $(APPICON_CZ_PNG) $(APPICON_CZ_ICO)


theme_cz_default_bannersdir = $(datadir)/tgcm/themes/cz/default/banners
theme_cz_default_banners_DATA = themes/cz/default/banners/settings.png themes/cz/default/banners/banner_bgnd.png themes/cz/default/banners/banners.xml themes/cz/default/banners/help.png

TRAYICONS_CZ_ICO = themes/cz/default/icons/conectado.ico \
	themes/cz/default/icons/desconectado.ico \
	themes/cz/default/icons/conectado_smspending.ico \
	themes/cz/default/icons/desconectado_smspending.ico

TRAYICONS_CZ_PNG = themes/cz/default/icons/conectado.png \
	themes/cz/default/icons/desconectado.png \
	themes/cz/default/icons/conectado_smspending.png \
	themes/cz/default/icons/desconectado_smspending.png

$(TRAYICONS_CZ_PNG): $(TRAYICONS_CZ_ICO)
	./extract_icons.py --tray-icon $?

SERVICES_CZ_ICO = themes/cz/default/icons/addressbook.ico \
	themes/cz/default/icons/favorites.ico \
	themes/cz/default/icons/internet.ico \
	themes/cz/default/icons/intranet.ico \
	themes/cz/default/icons/prepay.ico \
	themes/cz/default/icons/selfcare.ico \
	themes/cz/default/icons/sms.ico \
	themes/cz/default/icons/traffic.ico \
	themes/cz/default/icons/videocall.ico \
	themes/cz/default/icons/wifi.ico

SERVICES_CZ_PNG = themes/cz/default/icons/addressbook_service.png \
	themes/cz/default/icons/favorites_service.png \
	themes/cz/default/icons/internet_service.png \
	themes/cz/default/icons/intranet_service.png \
	themes/cz/default/icons/prepay_service.png \
	themes/cz/default/icons/selfcare_service.png \
	themes/cz/default/icons/sms_service.png \
	themes/cz/default/icons/traffic_service.png \
	themes/cz/default/icons/videocall_service.png \
	themes/cz/default/icons/wifi_service.png

TASKBARS_CZ_ICO = themes/cz/default/icons/help.ico \
	themes/cz/default/icons/settings.ico

TASKBARS_CZ_PNG = themes/cz/default/icons/addressbook_taskbar.png \
	themes/cz/default/icons/favorites_taskbar.png \
	themes/cz/default/icons/help_taskbar.png \
	themes/cz/default/icons/internet_taskbar.png \
	themes/cz/default/icons/intranet_taskbar.png \
	themes/cz/default/icons/prepay_taskbar.png \
	themes/cz/default/icons/selfcare_taskbar.png \
	themes/cz/default/icons/settings_taskbar.png \
	themes/cz/default/icons/sms_taskbar.png \
	themes/cz/default/icons/traffic_taskbar.png \
	themes/cz/default/icons/videocall_taskbar.png \
	themes/cz/default/icons/wifi_taskbar.png

$(SERVICES_CZ_PNG): $(SERVICES_CZ_ICO)
	./extract_icons.py --service-icon --add-suffix $?

$(TASKBARS_CZ_PNG): $(SERVICES_CZ_ICO) $(TASKBARS_CZ_ICO)
	./extract_icons.py --taskbar-icon --add-suffix $?

theme_cz_default_iconsdir = $(datadir)/tgcm/themes/cz/default/icons
theme_cz_default_icons_DATA = $(TRAYICONS_CZ_ICO) $(TRAYICONS_CZ_PNG) \
	$(SERVICES_CZ_ICO) $(SERVICES_CZ_PNG) \
	$(TASKBARS_CZ_ICO) $(TASKBARS_CZ_PNG)


theme_cz_default_notifiersdir = $(datadir)/tgcm/themes/cz/default/notifiers
theme_cz_default_notifiers_DATA = themes/cz/default/notifiers/tbnvcall.png themes/cz/default/notifiers/notifiers.xml themes/cz/default/notifiers/tbnclose.png themes/cz/default/notifiers/tbnhangup.png themes/cz/default/notifiers/tbnsms.png themes/cz/default/notifiers/tbnpickup.png themes/cz/default/notifiers/tbnerror.png themes/cz/default/notifiers/tbngen.png


theme_cz_default_dockdir = $(datadir)/tgcm/themes/cz/default/dock
theme_cz_default_dock_DATA = themes/cz/default/dock/docking.png themes/cz/default/dock/connect.png themes/cz/default/dock/trafficgraph.png themes/cz/default/dock/signal.png themes/cz/default/dock/logo.png themes/cz/default/dock/smart.png themes/cz/default/dock/lock.png themes/cz/default/dock/lan.png themes/cz/default/dock/traffic.png themes/cz/default/dock/disconnect.png themes/cz/default/dock/unlock.png themes/cz/default/dock/wifisignal.png themes/cz/default/dock/bkgnd.png themes/cz/default/dock/connecting.png


theme_cz_default_devicedir = $(datadir)/tgcm/themes/cz/default/device
theme_cz_default_device_DATA = themes/cz/default/device/device.png themes/cz/default/device/home.png themes/cz/default/device/available.png themes/cz/default/device/roaming.png


theme_cz_default_servicesdir = $(datadir)/tgcm/themes/cz/default/services
theme_cz_default_services_DATA = themes/cz/default/services/addressbook.png themes/cz/default/services/intranet.png themes/cz/default/services/favorites.png themes/cz/default/services/sms.png themes/cz/default/services/wifi.png themes/cz/default/services/euro_icn_win.png themes/cz/default/services/bbselfcare_1.png themes/cz/default/services/more.png themes/cz/default/services/www_icn_win.png themes/cz/default/services/circle.png themes/cz/default/services/videocall.png


theme_cz_default_sysbtndir = $(datadir)/tgcm/themes/cz/default/sysbtn
theme_cz_default_sysbtn_DATA = themes/cz/default/sysbtn/minimize.png themes/cz/default/sysbtn/settings.png themes/cz/default/sysbtn/close.png themes/cz/default/sysbtn/help.png


### Latin America ###

APPICON_AR_ICO = themes/latam/ar/default/icon.ico
APPICON_AR_PNG = themes/latam/ar/default/icon.png

$(APPICON_AR_PNG): $(APPICON_AR_ICO)
	./extract_icons.py --main-icon $?

theme_latam_ar_defaultdir = $(datadir)/tgcm/themes/latam/ar/default
theme_latam_ar_default_DATA = themes/latam/ar/default/theme.xml themes/latam/ar/default/theme.pot $(APPICON_AR_PNG) $(APPICON_AR_ICO)


theme_latam_ar_default_bannersdir = $(datadir)/tgcm/themes/latam/ar/default/banners
theme_latam_ar_default_banners_DATA = themes/latam/ar/default/banners/blank.png themes/latam/ar/default/banners/settings.png themes/latam/ar/default/banners/bar.png themes/latam/ar/default/banners/banner_bgnd.png themes/latam/ar/default/banners/banners.xml themes/latam/ar/default/banners/help.png themes/latam/ar/default/banners/movistar.png

TRAYICONS_AR_ICO = themes/latam/ar/default/icons/conectado.ico \
	themes/latam/ar/default/icons/desconectado.ico \
	themes/latam/ar/default/icons/conectado_smspending.ico \
	themes/latam/ar/default/icons/desconectado_smspending.ico

FAV_AR_ICO = themes/latam/ar/default/icons/fav.ico

SERVICES_AR_ICO = themes/latam/ar/default/icons/addressbook.ico \
	themes/latam/ar/default/icons/app_latam.ico \
	themes/latam/ar/default/icons/backup.ico\
	themes/latam/ar/default/icons/club_latam.ico \
	themes/latam/ar/default/icons/contents_latam.ico \
	themes/latam/ar/default/icons/educacion_latam.ico \
	themes/latam/ar/default/icons/favorites.ico \
	themes/latam/ar/default/icons/fsecure.ico \
	themes/latam/ar/default/icons/help.ico \
	themes/latam/ar/default/icons/internet.ico \
	themes/latam/ar/default/icons/live_latam.ico \
	themes/latam/ar/default/icons/mimovistar.ico\
	themes/latam/ar/default/icons/music_latam.ico \
	themes/latam/ar/default/icons/online_channel.ico\
	themes/latam/ar/default/icons/recharge_latam.ico \
	themes/latam/ar/default/icons/secure.ico \
	themes/latam/ar/default/icons/settings.ico \
	themes/latam/ar/default/icons/shop_latam.ico \
	themes/latam/ar/default/icons/sms.ico \
	themes/latam/ar/default/icons/tones_latam.ico \
	themes/latam/ar/default/icons/traffic.ico \
	themes/latam/ar/default/icons/usage_guide.ico \
	themes/latam/ar/default/icons/videocall.ico \
	themes/latam/ar/default/icons/web_portal.ico

SERVICES_AR_PNG = themes/latam/ar/default/icons/addressbook_service.png \
	themes/latam/ar/default/icons/app_latam_service.png \
	themes/latam/ar/default/icons/backup_service.png \
	themes/latam/ar/default/icons/club_latam_service.png \
	themes/latam/ar/default/icons/contents_latam_service.png \
	themes/latam/ar/default/icons/educacion_latam_service.png \
	themes/latam/ar/default/icons/favorites_service.png \
	themes/latam/ar/default/icons/fsecure_service.png \
	themes/latam/ar/default/icons/help_service.png \
	themes/latam/ar/default/icons/internet_service.png \
	themes/latam/ar/default/icons/live_latam_service.png \
	themes/latam/ar/default/icons/mimovistar_service.png\
	themes/latam/ar/default/icons/music_latam_service.png \
	themes/latam/ar/default/icons/online_channel_service.png \
	themes/latam/ar/default/icons/recharge_latam_service.png \
	themes/latam/ar/default/icons/secure_service.png \
	themes/latam/ar/default/icons/settings_service.png \
	themes/latam/ar/default/icons/shop_latam_service.png \
	themes/latam/ar/default/icons/sms_service.png \
	themes/latam/ar/default/icons/tones_latam_service.png \
	themes/latam/ar/default/icons/traffic_service.png \
	themes/latam/ar/default/icons/usage_guide_service.png \
	themes/latam/ar/default/icons/videocall_service.png \
	themes/latam/ar/default/icons/web_portal_service.png

TASKBARS_AR_PNG = themes/latam/ar/default/icons/addressbook_taskbar.png \
	themes/latam/ar/default/icons/app_latam_taskbar.png \
	themes/latam/ar/default/icons/backup_taskbar.png \
	themes/latam/ar/default/icons/club_latam_taskbar.png \
	themes/latam/ar/default/icons/contents_latam_taskbar.png \
	themes/latam/ar/default/icons/educacion_latam_taskbar.png \
	themes/latam/ar/default/icons/favorites_taskbar.png \
	themes/latam/ar/default/icons/fsecure_taskbar.png \
	themes/latam/ar/default/icons/help_taskbar.png \
	themes/latam/ar/default/icons/internet_taskbar.png \
	themes/latam/ar/default/icons/live_latam_taskbar.png \
	themes/latam/ar/default/icons/mimovistar_taskbar.png\
	themes/latam/ar/default/icons/music_latam_taskbar.png \
	themes/latam/ar/default/icons/online_channel_taskbar.png \
	themes/latam/ar/default/icons/recharge_latam_taskbar.png \
	themes/latam/ar/default/icons/secure_taskbar.png \
	themes/latam/ar/default/icons/settings_taskbar.png \
	themes/latam/ar/default/icons/shop_latam_taskbar.png \
	themes/latam/ar/default/icons/sms_taskbar.png \
	themes/latam/ar/default/icons/tones_latam_taskbar.png \
	themes/latam/ar/default/icons/traffic_taskbar.png \
	themes/latam/ar/default/icons/usage_guide_taskbar.png \
	themes/latam/ar/default/icons/videocall_taskbar.png \
	themes/latam/ar/default/icons/web_portal_taskbar.png

$(SERVICES_AR_PNG): $(SERVICES_AR_ICO)
	./extract_icons.py --service-icon --add-suffix $?

$(TASKBARS_AR_PNG): $(SERVICES_AR_ICO)
	./extract_icons.py --taskbar-icon --add-suffix $?

theme_latam_ar_default_iconsdir = $(datadir)/tgcm/themes/latam/ar/default/icons
theme_latam_ar_default_icons_DATA = $(TRAYICONS_AR_ICO) \
	$(FAV_AR_ICO) \
	$(SERVICES_AR_ICO) $(SERVICES_AR_PNG) \
	$(TASKBARS_AR_PNG)


theme_latam_ar_default_notifiersdir = $(datadir)/tgcm/themes/latam/ar/default/notifiers
theme_latam_ar_default_notifiers_DATA = themes/latam/ar/default/notifiers/tbnvcall.png themes/latam/ar/default/notifiers/notifiers.xml themes/latam/ar/default/notifiers/tbnclose.png themes/latam/ar/default/notifiers/tbnhangup.png themes/latam/ar/default/notifiers/tbnsms.png themes/latam/ar/default/notifiers/tbnpickup.png themes/latam/ar/default/notifiers/tbnerror.png themes/latam/ar/default/notifiers/tbngen.png


theme_latam_ar_default_dockdir = $(datadir)/tgcm/themes/latam/ar/default/dock
theme_latam_ar_default_dock_DATA = themes/latam/ar/default/dock/docking.png themes/latam/ar/default/dock/connect.png themes/latam/ar/default/dock/trafficgraph.png themes/latam/ar/default/dock/led_desconectado.png themes/latam/ar/default/dock/signal.png themes/latam/ar/default/dock/logo.png themes/latam/ar/default/dock/smart.png themes/latam/ar/default/dock/lock.png themes/latam/ar/default/dock/lan.png themes/latam/ar/default/dock/traffic.png themes/latam/ar/default/dock/led_conectado.png themes/latam/ar/default/dock/disconnect.png themes/latam/ar/default/dock/unlock.png themes/latam/ar/default/dock/wifisignal.png themes/latam/ar/default/dock/bkgnd.png themes/latam/ar/default/dock/connecting.png


theme_latam_ar_default_devicedir = $(datadir)/tgcm/themes/latam/ar/default/device
theme_latam_ar_default_device_DATA = themes/latam/ar/default/device/device.png themes/latam/ar/default/device/home.png themes/latam/ar/default/device/available.png themes/latam/ar/default/device/roaming.png


theme_latam_ar_default_servicesdir = $(datadir)/tgcm/themes/latam/ar/default/services
theme_latam_ar_default_services_DATA = themes/latam/ar/default/services/addressbook.png themes/latam/ar/default/services/latam-tones.png themes/latam/ar/default/services/favorites.png themes/latam/ar/default/services/sms.png themes/latam/ar/default/services/latam-contenidos.png themes/latam/ar/default/services/fsecure.png themes/latam/ar/default/services/internet.png themes/latam/ar/default/services/more.png themes/latam/ar/default/services/latam-club.png themes/latam/ar/default/services/latam-recarga.png themes/latam/ar/default/services/latam-aplicaciones.png themes/latam/ar/default/services/latam-musica.png themes/latam/ar/default/services/latam-tiendaonline.png themes/latam/ar/default/services/circle.png themes/latam/ar/default/services/latam-live.png themes/latam/ar/default/services/latam-educacion.png themes/latam/ar/default/services/videocall.png themes/latam/ar/default/services/mimovistar.png themes/latam/ar/default/services/web_portal.png themes/latam/ar/default/services/online_channel.png themes/latam/ar/default/services/usage_guide.png


theme_latam_ar_default_sysbtndir = $(datadir)/tgcm/themes/latam/ar/default/sysbtn
theme_latam_ar_default_sysbtn_DATA = themes/latam/ar/default/sysbtn/minimize.png themes/latam/ar/default/sysbtn/settings.png themes/latam/ar/default/sysbtn/close.png themes/latam/ar/default/sysbtn/help.png

clean-local:
	-rm -rf $(APPICON_ES_PNG) $(APPICON_IE_PNG) $(APPICON_UK_PNG) $(APPICON_DE_PNG) $(APPICON_DE_EUROVIA_PNG) $(APPICON_CZ_PNG) $(APPICON_AR_PNG) \
		$(TRAYICONS_IE_PNG) $(TRAYICONS_UK_PNG) $(TRAYICONS_DE_PNG) $(TRAYICONS_DE_EUROVIA_PNG) $(TRAYICONS_CZ_PNG) \
		$(SERVICES_ES_PNG) $(SERVICES_IE_PNG) $(SERVICES_UK_PNG) $(SERVICES_DE_PNG) $(SERVICES_DE_EUROVIA_PNG) $(SERVICES_CZ_PNG) $(SERVICES_AR_PNG) \
		$(TASKBARS_ES_PNG) $(TASKBARS_IE_PNG) $(TASKBARS_UK_PNG) $(TASKBARS_DE_PNG) $(TASKBARS_DE_EUROVIA_PNG) $(TASKBARS_CZ_PNG) $(TASKBARS_AR_PNG)

EXTRA_DIST= $(convert_icos_script_DATA) $(theme_es_default_DATA) $(theme_es_default_banners_DATA) $(theme_es_default_icons_DATA) $(theme_es_default_notifiers_DATA) $(theme_es_default_dock_DATA) $(theme_es_default_device_DATA) $(theme_es_default_services_DATA) $(theme_es_default_sysbtn_DATA) $(theme_ie_default_DATA) $(theme_ie_default_banners_DATA) $(theme_ie_default_icons_DATA) $(theme_ie_default_notifiers_DATA) $(theme_ie_default_dock_DATA) $(theme_ie_default_device_DATA) $(theme_ie_default_services_DATA) $(theme_ie_default_sysbtn_DATA) $(theme_uk_default_DATA) $(theme_uk_default_banners_DATA) $(theme_uk_default_icons_DATA) $(theme_uk_default_notifiers_DATA) $(theme_uk_default_dock_DATA) $(theme_uk_default_device_DATA) $(theme_uk_default_services_DATA) $(theme_uk_default_sysbtn_DATA) $(theme_de_default_DATA) $(theme_de_default_banners_DATA) $(theme_de_default_icons_DATA) $(theme_de_default_notifiers_DATA) $(theme_de_default_dock_DATA) $(theme_de_default_device_DATA) $(theme_de_default_services_DATA) $(theme_de_default_sysbtn_DATA) $(theme_de_eurovia_DATA) $(theme_de_eurovia_banners_DATA) $(theme_de_eurovia_icons_DATA) $(theme_de_eurovia_notifiers_DATA) $(theme_de_eurovia_dock_DATA) $(theme_de_eurovia_device_DATA) $(theme_de_eurovia_services_DATA) $(theme_de_eurovia_sysbtn_DATA) $(theme_cz_default_DATA) $(theme_cz_default_banners_DATA) $(theme_cz_default_icons_DATA) $(theme_cz_default_notifiers_DATA) $(theme_cz_default_dock_DATA) $(theme_cz_default_device_DATA) $(theme_cz_default_services_DATA) $(theme_cz_default_sysbtn_DATA) $(theme_latam_ar_default_DATA) $(theme_latam_ar_default_banners_DATA) $(theme_latam_ar_default_icons_DATA) $(theme_latam_ar_default_notifiers_DATA) $(theme_latam_ar_default_dock_DATA) $(theme_latam_ar_default_device_DATA) $(theme_latam_ar_default_services_DATA) $(theme_latam_ar_default_sysbtn_DATA)
### THEMES_MAKEFILE_AM END ###
