#!/usr/bin/python
# -*- coding: utf-8 -*-

import dbus

BUS_NAME = 'org.frankhale.helloservice'
OBJECT_PATH = '/org/frankhale/helloservice'

class dbus_error(object):
    def __init__(self, default_value):
        self.default_value = default_value

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                value = func(*args, **kwargs)
            except:
                value = self.default_value
            return value
        return wrapper

class Foo(object):
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.helloservice = self.bus.get_object(BUS_NAME, OBJECT_PATH)

    @dbus_error('Default Hello World!')
    def hello(self):
        hello = self.helloservice.get_dbus_method('hello', BUS_NAME)
        return hello()

    @dbus_error('Default Goodbye World!')
    def goodbye(self):
        goodbye = self.helloservice.get_dbus_method('goodbye', BUS_NAME)
        return goodbye()

    def run(self):
        print self.hello()
        print self.goodbye()

def main():
    foo = Foo()
    foo.run()

if __name__ == '__main__':
    main()
