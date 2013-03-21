import inspect
import sys

from dbus import validate_interface_name, Signature, validate_member_name
from dbus.lowlevel import SignalMessage
from dbus.exceptions import DBusException

from service import method

def prop(dbus_interface, signature='v', property_name=None, perms='r'):
    validate_interface_name(dbus_interface)

    def decorator(func):
        keys = ['fget', 'fset', 'fdel']
 
        func_locals = {'doc':func.__doc__}
        def probeFunc(frame, event, arg):
            if event == 'return':
                locals = frame.f_locals
                func_locals.update(dict((k,locals.get(k)) for k in keys))
                sys.settrace(None)
            return probeFunc
        sys.settrace(probeFunc)
        func()
        
        class custom_property(property):
            __name__ = property_name
            _dbus_is_property = True
            _dbus_interface = dbus_interface
            _dbus_signature = signature
            _dbus_property_name = property_name
            _dbus_property_perms = perms

        prop = custom_property(**func_locals)
        return prop
    
    return decorator

    
