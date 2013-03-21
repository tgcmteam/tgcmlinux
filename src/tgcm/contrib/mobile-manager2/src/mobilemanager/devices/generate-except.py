import sys

list = ["PhoneFailure",
        "NoConnection",
        "LinkReserved",
        "OperationNotAllowed",
        "OperationNotSupported",
        "PhSimPinRequired",
        "PhFSimPinRequired",
        "PhFSimPukRequired",
        "SimNotInserted",
        "SimPinRequired",
        "SimPukRequired",
        "SimFailure",
        "SimBusy",
        "SimWrong",
        "IncorrectPassword",
        "SimPin2Required",
        "SimPuk2Required",
        "MemoryFull",
        "InvalidIndex",
        "NotFound",
        "MemoryFailure",
        "TextTooLong",
        "InvalidChars",
        "DialStringTooLong",
        "InvalidDialString",
        "NoNetwork",
        "NetworkTimeout",
        "NetworkNotAllowed",
        "NetworkPinRequired",
        "NetworkPukRequired",
        "NetworkSubsetPinRequired",
        "NetworkSubsetPukRequired",
        "ServicePinRequired",
        "ServicePukRequired",
        "CorporatePinRequired",
        "CorporatePukRequired",
        "HiddenKeyRequired",
        "EapMethodNotSupported",
        "IncorrectParams",
        "Unknown",
        "GprsIllegalMs",
        "GprsIllegalMe",
        "GprsPlmnNotAllowed",
        "GprsLocationNotAllowed",
        "GprsRoamingNotAllowed",
        "GprsOptionNotSupported",
        "GprsNotSubscribed",
        "GprsOutOfOrder",
        "GprsPdpAuthFailure",
        "GprsUnspecified",
        "GprsInvalidClass",
    ]

for item in list:
    print >> sys.stdout, "class %s(DBusException):" % item
    print >> sys.stdout, ""
    print >> sys.stdout, "    include_traceback = False"
    print >> sys.stdout, "    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.Gsm.%s'" % item
    print >> sys.stdout, ""
    print >> sys.stdout, "    def __init__(self, msg=''):"
    print >> sys.stdout, "        DBusException.__init__(self, msg)"
    print >> sys.stdout, ""
