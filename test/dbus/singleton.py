#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import gobject
import dbus
import dbus.mainloop.glib
import dbus.service

BUS_NAME = 'es.indra.Tgcm'

class DBusSingleton(dbus.service.Object):
    def __init__(self):
        bus = dbus.SessionBus()
        if not bus.name_has_owner(BUS_NAME):
            bus.request_name(BUS_NAME)
            dbus.service.Object.__init__(self, bus, '/es/indra/tgcm')
            print 'Adquired D-Bus name: %s' % BUS_NAME
        else:
            print 'Failed to request D-Bus name: "%s"' % BUS_NAME
            sys.exit()

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    singleton = DBusSingleton()

    loop = gobject.MainLoop()
    loop.run()
