udevrulesdir = $(UDEV_BASE_DIR)/rules.d
udevrules_DATA = 77-mobile-manager.rules

# -- USBMODE_BIN is checked and set in configure.ac
usbmode_bin = $(USBMODE_BIN)

%.rules: %.rules.in
	@echo "# -- AUTOMATIC GENERATED FILE! DONT EDIT!" > $@
	@sed -e "s|@usbmode_dir@|$(USBMODE_BASE_DIR)|g" -e "s|@usbmode_bin@|$(usbmode_bin)|g" $< >> $@

EXTRA_DIST = $(udevrules_DATA) 
