#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Luis Galdos <luisgaldos@gmail.com>
#
# Copyright (c) 2010, Telefonica Móviles España S.A.U.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import os
import sys

import re
import time
from termios import *
import Queue

import gobject
import glib
import gio
import errno
import select
import fcntl
import threading
import thread

from mobilemanager.Logging import info, warning, error
from ModemGsmExceptions import *
from dbus.exceptions import DBusException

TIMEOUT_WAITING_TURN = 4
TIMEOUT_EXECUTION    = 2

class SerialResponseTimeout(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.SerialResponseTimeout'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class TaskQueueTimeout(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.TaskQueueTimeout'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

class TaskAborted(DBusException):

    include_traceback = False
    _dbus_error_name = 'org.freedesktop.ModemManager.Modem.TaskAborted'

    def __init__(self, msg=''):
        DBusException.__init__(self, msg)

def configure_port(fd):
    old_attrs = tcgetattr(fd)
    new_attrs = tcgetattr(fd)

    speed = B9600
    bits = CS8

    new_attrs[0] &= ~(IGNCR | ICRNL | IUCLC | INPCK | IXON | IXOFF | IXANY | IGNPAR );

    new_attrs[1] &= ~(OPOST | OLCUC | OCRNL | ONLCR | ONLRET);

    new_attrs[3] &= ~(ICANON | XCASE | ECHO | ECHOCTL | ECHOE | ECHOK | ECHOKE | ECHONL | ECHOPRT);

    # -- Disable parity, stop bits and other stuff
    new_attrs[2] &= ~(CBAUD | CSIZE | CSTOPB | PARENB | PARODD | CRTSCTS);
    new_attrs[2] |= (bits | CREAD | CLOCAL | HUPCL);

    # -- Set the baud rate for both directions even the driver ignores it, or?
    new_attrs[4] = speed
    new_attrs[5] = speed

    new_attrs[6][VMIN]  = 1;
    new_attrs[6][VTIME] = 5;
    new_attrs[6][VEOF]  = 1;

    tcsetattr(fd, TCSANOW, new_attrs)
    return old_attrs

class Task():

    STATE_IDLE          = 0
    STATE_WAITING_QUEUE = 1
    STATE_WAITING_TASK  = 2
    STATE_WRITING       = 3
    STATE_READING       = 4

    RESULT_OK           = 0
    RESULT_ERROR        = 1
    RESULT_ABORTED      = 2

    def __init__(self, func, msg, timeout_queue=TIMEOUT_WAITING_TURN, timeout_func=TIMEOUT_EXECUTION):
        self.__func          = func
        self.__msg           = msg
        self.__timeout_queue = timeout_queue
        self.__timeout_task  = timeout_func

        self.__cancel        = gio.Cancellable()

        self.__queue_event   = threading.Event()
        self.__task_event    = threading.Event()
        self.__abort_event   = threading.Event()

        self.__state      = self.STATE_IDLE
        self.__result     = None
        self.__id         = self.__new_id(self)
        self.__error      = None
        self.__command    = ""

    def id(self):
        return self.__id

    def msg(self):
        return self.__msg

    def result(self):
        return self.__result

    def timeout_task(self):
        return self.__timeout_task

    def command(self, cmd):
        if len(cmd) > 40:
            self.__command = cmd[0:15] + "..." + cmd[-15:]
        else:
            self.__command = cmd

    @staticmethod
    def __new_id(self):
        _func = self.__new_id
        if not _func.__dict__.has_key('id'):
            _func.__dict__.__setitem__('id', 0)

        ret = _func.id
        _func.id += 1
        return ret

    def aborted(self):
        return self.__abort_event.isSet()

    def abort(self):
        self.__abort_event.set()
        self.__task_event.set()

    def state(self, value=None):
        if value is not None:
            self.__state = value
        return self.__state

    def __timeout_errmsg(self, reason, timeval):
        errmsg = "%s (%is) by task '%s' (num=%i)" % (reason, timeval, self.__msg, self.__id)

        if self.__command != "":
            errmsg += " | Command '%s'" % self.__command

        return errmsg

    def __raise_abort(self, exception, msg, timeout):
        errmsg = self.__timeout_errmsg(msg, timeout)
        error(errmsg)
        self.__error = exception(errmsg)
        self.__abort_event.set()
        raise self.__error

    # -- This function will block until the task function returns or a timeout ocurred
    def wait(self):

        # -- By timeouts waiting for the queue happens, then execute the below steps:
        # -- * Set the error type/message and return
        self.__queue_event.wait(self.__timeout_queue)
        if not self.__queue_event.isSet():
            self.__raise_abort(TaskQueueTimeout, "Queue waiting timeout", self.__timeout_queue)

        self.__task_event.wait(self.__timeout_task)
        if not self.__task_event.isSet():
            self.__raise_abort(SerialResponseTimeout, "Execution timeout (state %i)" % self.__state, self.__timeout_task)

        # -- By errors pass it to the task creator
        if self.__error is not None:
            error("Task '%s' error : %s" % (self.__msg, self.__error))
            raise self.__error

    # -- This is the method that will execute the passed task function
    def execute(self):

        # -- This event is set when a queue timeout has ocurred, here we don't need to continue
        # -- with the task execution but inform the task pool about the aborted execution
        if self.__abort_event.isSet():
            return self.RESULT_ABORTED

        # -- OK, set first the event for the wait function
        self.__queue_event.set()

        # -- Now start the function execution
        try:
            self.__result = self.__func(self)
            retval = self.RESULT_OK
        except Exception as e:
            self.__error = e
            retval = self.RESULT_ERROR
        finally:
            self.__task_event.set()
            return retval

class TaskPool():

    STATE_IDLE    = 0
    STATE_BUSY    = 1
    STATE_STOPPED = 2
    STATE_FAILURE = 3

    WAIT_TASK_ADDED_TIME = 0.010

    # -- After this threshold is reached, a device reset is triggered!
    # -- Arbitraty value used for avoiding deadlocks in the task queue
    ERRORS_THRESHOLD     = 20

    class _TaskLog():

        # -- Disables globally the filters
        DISABLED_FILTERS = False

        def __init__(self):
            # -- Disable the filters per default
            self.__enable(False)
            self.filters([ ])

        def info(self, msg):
            if self.__logging is True:
                info(msg)

        def error(self, msg):
            error(msg)

        def warning(self, msg):
            warning(msg)

        def start(self, task):
            msg = task.msg()
            if self.__filters_enabled is True:
                self.__logging = False if (self.__task_filters.match(msg) is None) else True
            else:
                self.__logging = True

            self.info("Dispatching Task num=%i '%s' :" % (task.id(), task.msg()))

        def end(self, task):
            if self.__logging is True:
                self.info('-' * 20)

        def enable(self, value=None):
            if self.DISABLED_FILTERS is True:
                raise SystemError, "Filters feature is disabled"
            else:
                return self.__enable(value)

        def __enable(self, value=None):
            if value is not None:
                self.__filters_enabled = True if value else False
            return self.__filters_enabled

        def filters(self, commands=None):
            if (commands is not None):
                if not hasattr(commands, '__iter__'):
                    commands = [ commands ]

                self.__task_filters = re.compile(r"%s" % '|'.join(map(lambda cmd: ".*%s.*" % cmd, commands)))
                self.__commands     = commands

                if self.__filters_enabled is True:
                    warning("IMPORTANT: Tasks filter(s) enabled: %s" % repr(commands))

            return self.__commands

    def start(self):
        self.__stop = False
        thread.start_new_thread(self.__start, ( ))

    def __init__(self, device):
        self.__device     = device
        self.__stop       = False
        self.__task_added = threading.Event()
        self.__tasks_lock = threading.Lock()
        self.__tasks      = [ ]
        self.__errors     = 0
        self.__state      = self.STATE_IDLE

        # -- Set the external access to the logger
        self.__tasklog      = self._TaskLog()
        self.filters_enable = self.__tasklog.enable
        self.filters_set    = self.__tasklog.filters

    def info(self, msg):
        self.__tasklog.info(msg)

    def error(self, msg):
        self.__tasklog.error(msg)

    def __start(self):

        while self.__stop is False:
            try:
                self.__task_added.wait(self.WAIT_TASK_ADDED_TIME)
                self.__task_added.clear()

                # -- Now execute the next task of the queue
                _task = self.__pop()
                if _task is not None:

                    # -- Change the state to busy
                    self.__state = self.STATE_BUSY

                    self.__tasklog.start(_task)
                    retval = _task.execute()
                    if retval == _task.RESULT_OK:
                        self.__errors = 0
                    elif retval == _task.RESULT_ERROR:
                        self.__errors += 1

                        # -- Failure threshold reached, so try to reset the device and stop the task queue
                        if self.__errors == self.ERRORS_THRESHOLD:
                            self.stop()
                            self.__device.reset()
                            break

                    # -- Set the state to idle
                    self.__state = self.STATE_IDLE
                    self.__tasklog.end(_task)

            except Exception, err:
                error("Unexpected failure in TaskPool thread, %s" % err)
                self.__state = self.STATE_IDLE

        self.__state = self.STATE_STOPPED
        info("TaskPool stopped | Pending tasks %i" % len(self.__tasks))
        self.__abort_tasks()

    # -- Cancel all the pending tasks remaining in the queue
    def __abort_tasks(self):
        while len(self.__tasks):
            _task = self.__pop()
            if _task is not None:
                info("Going to abort task %i" % _task.id())
                _task.abort()
            else:
                time.sleep(0.100)

    def stop(self):
        self.__stop  = True

    # -- Add a new task to the queue
    def __push(self, task):

        # -- If the lock is held re-schedule this task
        _unblocked = self.__tasks_lock.acquire(False)
        if _unblocked is False:
            thread.start_new_thread(self.__push, (task, ))
            return

        self.__tasks.insert(0, task)
        self.__tasks_lock.release()

    # -- Remove the first task of the queue and return it
    def __pop(self):

        # -- If the lock is held by other thread, then return None
        ret = None
        _unblocked = self.__tasks_lock.acquire(False)
        if _unblocked is True:
            if len(self.__tasks) > 0:
                ret = self.__tasks.pop()
            self.__tasks_lock.release()

        return ret

    def exec_task(self, func, timeout=TIMEOUT_EXECUTION, timeout_waiting=TIMEOUT_WAITING_TURN, task_msg=None):

        if self.__stop is True:
            raise OperationNotAllowed, "Task queue was stopped."

        task = Task(func, task_msg, timeout_waiting, timeout)
        self.__push(task)
        task.wait()
        return task.result()

    def is_idle(self):
        return (self.__state == self.STATE_IDLE)

    def is_busy(self):
        return (self.__state == self.STATE_BUSY)

class SerialPort :

    READ_TIMEOUT_DEFAULT  = 4
    WRITE_TIMEOUT_DEFAULT = 4
    READ_SELECT_TIME      = 0.001
    WRITE_SELECT_TIME     = 0.001

    def __init__(self, dev_path, task_pool):
        self.dev_path  = dev_path
        self.task_pool = task_pool
        self._fd       = None
        self.ignore_input_strings = []

    def open(self):
        self.__open_serial_port()
        self.__old_termios = configure_port(self._fd)

    def close(self):
        self.__deconfigure_serial_port()
        self.__close_serial_port()

    def add_ignore_strings(self, regex):
        try:
            self.ignore_input_strings.append(re.compile(regex))
        except:
            print "add_ignore_strings : error regex"

    def send_query(self, query):
        def simple(res):
            if res[2] == "OK" :
                return True
            else:
                return False

        def sregex(res):
            if res[2] == 'OK':
                pattern = re.compile(query["regex"])
                matched_res = pattern.match(res[1][0])
                if matched_res != None :
                    return True
                else:
                    return False

        def regex(res):
            if res[2] == 'OK':
                pattern = re.compile(query["regex"])
                matched_res = pattern.match(res[1][0])
                res_dict = {}
                if matched_res != None :
                    try:
                        for key in query["r_values"]:
                            str=matched_res.group(key)
                            try:
                                res_dict[key] = str.decode('utf-8')
                            except UnicodeDecodeError:
                                res_dict[key] = str.decode('iso-8859-15')

                    except:
                        return None

                    return res_dict
                else:
                    return None

        # -- If raw is set, the returned expression will not be encoded
        def mregex(res, raw=False):
            response = []
            if res[2] == 'OK':
                pattern = re.compile(query["regex"])

                for item in res[1]:
                    matched_res = pattern.match(item)
                    res_dict = {}
                    try:
                        for key in query["r_values"]:
                            if raw is False:
                                res_dict[unicode(key)] = unicode(matched_res.group(key))
                            else:
                                res_dict[key] = matched_res.group(key)
                    except:
                        continue

                    response.append(res_dict)

            return response

        res = self.__send_query_to_device(query)

        raw = False if (not query.has_key('raw')) else bool(query['raw'])

        if query.has_key("type") :
            if query["type"] == "simple" :
                res = simple(res)
            elif query["type"] == "regex" :
                res = regex(res)
            elif query["type"] == "sregex" :
                res = sregex(res)
            elif query["type"] == "mregex" :
                res = mregex(res, raw=raw)

        return res

    # configuration private methods

    def __open_serial_port(self):
        self._fd = os.open(self.dev_path, os.O_RDWR | os.O_NONBLOCK | os.O_NOCTTY | os.O_NDELAY)

    def __deconfigure_serial_port(self):
       # tcsetattr(self._fd, TCSANOW, self.__old_termios)
       pass

    def __close_serial_port(self):
        try:
            tcflush(self._fd, TCIOFLUSH)
        except:
            warning("Got error flushing port")
        try:
            os.close(self._fd)
        except Exception as err:
            error("Got error closing port: %s" % str(err))

    def __message_contains_error(self, msg):
        return (msg.startswith("ERROR") or msg.startswith("+CME ERROR") or msg.startswith("+CMS ERROR"))

    # Query private methods

    def __normalize_at_response(self, command, tt_res):
        status_response = None

        if tt_res[-1].startswith("OK") or self.__message_contains_error(tt_res[-1]):
            status_response = tt_res.pop(-1)

        #Removing not necesary responses
        for item in tt_res :
            if (item.startswith("OK")) or self.__message_contains_error(item) or (item == command):
                tt_res.pop(tt_res.index(item))

        if len(tt_res) == 0:
            if status_response != None:
                return [command, [], status_response]
        elif len(tt_res) == 1:
            if status_response != None:
                return [command, [tt_res[0]], status_response]
            else:
                if tt_res[0].startswith("+"):
                    return [command, [tt_res[0]], 'OK']
        else:
            if status_response != None:
                return [command, tt_res, status_response]

        return None

    def __check_common_errors(self, response):
        if self.__message_contains_error(response[2]) or ("ERROR" in response[2]):
            error_text = response[2].lower()
            if re.match(".*sim.*pin.*required.*", error_text) != None :
                raise SimPinRequired
            if re.match(".*sim.*puk.*required.*", error_text) != None :
                raise SimPukRequired
            if re.match(".*incorrect.*password.*", error_text) != None :
                raise IncorrectPassword
            if re.match(".*operation.*not.*allowed.*", error_text) != None :
                raise OperationNotAllowed

    @staticmethod
    def __calculate_timeout_loops(value, task, default, select_time):
        if value is not None:
            retval = value
        elif task is not None:
            retval = task.timeout_task()
        else:
            retval = default
        return (retval / select_time)

    # -- @FIXME: Add the support for the characters
    # -- timeout : Read timeout in seconds
    def __do_read_until_chars(self, task=None, stop_chars=None, timeout=None, debug=False):

        # -- Inform the task pool that we are going to start a read operation
        if task is not None:
            task.state(task.STATE_READING)

        _line = ""
        _reopened = False
        timeout_read = self.__calculate_timeout_loops(timeout, task, self.READ_TIMEOUT_DEFAULT, self.READ_SELECT_TIME)

        timeout = timeout_read
        while True:
            ready = select.select([self._fd], [ ], [ ], self.READ_SELECT_TIME)
            if self._fd in ready[0]:

                # -- @FIXME: Read all the available data, but for now we must return only one line!
                _chr = os.read(self._fd, 1)

                if (stop_chars is None) and (_chr == "\n" or _chr == "\r"):
                    break
                if (stop_chars is not None) and (_chr in stop_chars):
                    break

                _line += _chr

            if (task is not None) and task.aborted():
                if debug is True:
                    print "--> read: '%s'" % repr(_line)
                raise TaskAborted, "Task was aborted, stopping read()"

            timeout -= 1
            if timeout == 0:
                if _reopened is False:
                    error("Got timeout in READ select. Reopening port.")
                    self.__reopen_serial_port_for_recover()
                    self.__write(self.__last_cmd, task=task, timeout=timeout, debug=debug)
                    _reopened = True
                    timeout = timeout_read
                else:
                    raise SerialResponseTimeout, "Got timeout in read select"

        return _line

    def __reopen_serial_port_for_recover(self, delay=1):
        try:
            self.close()
            time.sleep(delay)
        except:
            pass
        finally:
            self.open()

    # -- timeout : Timeout for the write operation in seconds
    def __write(self, command, task=None, timeout=None, debug=False):

        # -- Inform the Task pool which command are we going to execute
        if task is not None:
            task.command(command)
            task.state(task.STATE_WRITING)

        _cmd = command + "\r"
        _len = len(_cmd)
        _retries = 4

        # -- We need a timeout otherwise we will have an endless loop!
        _reopened = False
        timeout_write = self.__calculate_timeout_loops(timeout, task, self.WRITE_TIMEOUT_DEFAULT, self.WRITE_SELECT_TIME)

        if debug is True:
            print "--> write: '%s'" % repr(_cmd)

        timeout = timeout_write
        exception = None
        while _len > 0:
            try:
                ready = select.select([ ], [ self._fd ], [ ], self.WRITE_SELECT_TIME)

                if (task is not None) and task.aborted():
                    exception = TaskAborted("Task was aborted, stopping write()")
                    break

                timeout -= 1
                if timeout == 0:
                    if _reopened is False:
                        error("Got timeout in WRITE select. Reopening port.")
                        self.__reopen_serial_port_for_recover()
                        _reopened = True
                        _cmd = command + "\r"
                        _len = len(_cmd)
                        timeout = timeout_write
                        continue
                    else:
                        exception = SerialResponseTimeout("Aborting write operation due timeout")
                        break

                if self._fd in ready[1]:
                    ret = os.write(self._fd, _cmd)
                    _cmd = _cmd[ret:]
                    _len = _len - ret
            except Exception, err:
                if _retries:
                    _retries -= 1
                    error("Unexpected error, %s. Going to reopen the port." % err)
                    self.__reopen_serial_port_for_recover()
                    _cmd = command + "\r"
                else:
                    error("Can't recover from exception, %s" % err)
                    raise Exception, err

        if exception is not None:
            raise exception

    def __send_query_to_device(self, query):

        command      = 'AT' if "cmd" not in query else query["cmd"]
        # -- Backup the last command for the case we need to rewrite it to the port
        self.__last_cmd = command

        snd_part      = None if "snd_part" not in query else query["snd_part"]
        stop_chars    = '>' if "stop_chars" not in query else query["stop_chars"]
        last_try      = False if "last_try" not in query else True
        alt_ok_value  = None if "alt_ok_value" not in query else query["alt_ok_value"]
        task          = None if "task" not in query else query["task"]
        debug         = False if "debug" not in query else query["debug"]
        write_timeout = None if 'write_timeout' not in query else query['write_timeout']
        read_timeout  = None if 'read_timeout'  not in query else query['read_timeout']

        # -- Flush at this point as there are some devices, like the Huawei, that are continiously
        # -- printing some device information during a dialup session (^BOOT, ^DSFLOWRPT, etc.)
        try:
            tcflush(self._fd, TCIFLUSH)
        except:
            pass

        self.__write(command, task=task, timeout=write_timeout, debug=debug)

        if snd_part != None:
            self.__do_read_until_chars(task=task, stop_chars=stop_chars, timeout=read_timeout, debug=debug)
            self.__write(snd_part, task=task, timeout=write_timeout, debug=debug)

        tt_res = []
        while True: # -- Dont need an abort statement as the read operation has a timeout
            res = self.__do_read_until_chars(task=task, timeout=read_timeout, debug=debug)

            if len(res) == 0:
                continue

            if alt_ok_value != None :
                if res.startswith(alt_ok_value) :
                    tt_res.append(res.strip("\r\n"))
                    tt_res.append("OK")
                    break

                if res.startswith("OK") :
                    continue

                if self.__message_contains_error(res):
                    tt_res.append(res.strip("\r\n"))
                    break

            elif res.startswith("OK") or self.__message_contains_error(res):
                if "sim" in res.lower() and "busy" in res.lower():
                    if last_try == False:
                        time.sleep(5)
                        query["last_try"] = True
                        return self.__send_query_to_device(query)
                    else:
                        raise SimBusy

                tt_res.append(res.strip("\r\n"))
                break
            elif command.upper().startswith("ATD") and res.startswith("CONNECT"):
                tt_res.append("OK")
                break
            elif command.upper().startswith("ATD") and (res.startswith("NO CARRIER") or res.startswith("BUSY") or res.startswith("NO ANSWER") or res.startswith("NO DIALTONE")):
                tt_res.append("ERROR")
                break

            # -- Check for the regular expressions to be skipped in the response
            regex_line_detected = False
            for patt in self.ignore_input_strings:
                if patt.match(res) != None:
                    regex_line_detected = True
                    break
            if regex_line_detected:
                continue

            if len(res.strip("\r\n")) > 0:
                tt_res.append(res.strip("\r\n"))

        response = self.__normalize_at_response(command, tt_res)

        if response == None:
            self.task_pool.error("Error normalizating '%s' > [%s, '', 'ERROR']" % (repr(tt_res), command))
            return [command, [], 'ERROR']
        else:
            self.task_pool.info("   AT-CMD (%s) > %s > %s" % (os.path.basename(self.dev_path), response, res))
            self.__check_common_errors(response)
            return response


class CommunicationPort(SerialPort):
    def __init__(self, dev_path, task_pool):
        SerialPort.__init__(self, dev_path, task_pool)

class ModemPort(SerialPort):
    def __init__(self, dev_path, task_pool):
        SerialPort.__init__(self, dev_path, task_pool)
