#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Roberto Majadas <roberto.majadas@openshine.com>
#           Cesar Garcia Tapia <tapia@openshine.com>
#
# Copyright (c) 2003-2012, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import os
import gobject
import sqlite3
import re
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree

import tgcm
import Config
import Singleton

from tgcm.ui.MSD.MSDUtils import error_dialog

months = [_("January"), _("February"), _("March"), _("April"), _("May"), _("June"),
          _("July"), _("August") ,_("September"), _("October"), _("November"), _("December")]

#User-defined REGEXP operator
def regexp(expr, item):
    r = re.compile(expr)
    return r.match(item) is not None


class QueryError(Exception):
    pass


class HotSpotsService (gobject.GObject):
    __metaclass__ = Singleton.Singleton

    __gsignals__ = {
        'hotspots-updated' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    VALUE_ALL = _('All')

    class _InitCheck():
        def __init__(self, retval):
            self.__retval = retval

        def __call__(self, func):
            default_return_value = self.__retval
            def newf(self, *args, **kwargs):
                if self.hotspots_db is None:
                    return default_return_value
                return func(self, *args, **kwargs)
            return newf

    def __init__(self):
        gobject.GObject.__init__(self)

        self.hotspots_db = None
        self.hotspots_db_file = os.path.join(tgcm.config_dir, "hotspot-%s.db" % tgcm.country_support)

        if os.path.exists(self.hotspots_db_file):
            self.hotspots_db = sqlite3.connect(self.hotspots_db_file)
            self.hotspots_db.create_function("regexp", 2, regexp)
        else:
            regional_hotspot_file = os.path.join(tgcm.regional_info_dir, tgcm.country_support, "hotspot-list.xml")
            if os.path.exists(regional_hotspot_file):
                self.register_new_hotspot_file(regional_hotspot_file, self.hotspots_db_file)
                self.hotspots_db = sqlite3.connect(self.hotspots_db_file)
                self.hotspots_db.create_function("regexp", 2, regexp)

    def register_new_hotspot_file(self, in_file, out_file=None):
        out_file = self.hotspots_db_file if (out_file is None) else out_file

        try:
            tree = ElementTree()
            tree.parse(in_file)
        except (xml.etree.ElementTree.ParseError, sqlite3.OperationalError), err:
            # -- This failure appears when importing an empty file. In that case ignore the failure
            # -- but don't forget to create the database!
            tgcm.warning("@WARNING: Importing hotspots file '%s', %s" % (in_file, err))
            return False
        except Exception, err:
            config = Config.Config()
            srv_name = config.get_wifi_service_name()
            error_dialog(_("The hotspots list of %s will not be available due an import error.") % srv_name, \
                    markup = _("Unexpected error reading hotspots"), \
                    threaded = False)
            return False
        finally:
            self.hotspots_db = self.__create_db_table(out_file)

        # -- Start processing the input data
        root = tree.getroot()
        c = self.hotspots_db.cursor()
        c.execute('''insert into metadata values ("date", "%s")''' % root.attrib["date"])

        for node in root :
            if node.tag == "country" :
                country = node.attrib["name"]
                for node_s in node :
                    if node_s.tag == "state" :
                        state = node_s.attrib["name"]
                        for node_c in node_s :
                            city = node_c.attrib["name"]
                            if node_c.tag == "city" :
                                for node_h in node_c :
                                    if node_h.tag == "hotspot" :
                                        self.__hotspot_to_sqlite(c, country, state, city, node_h)

        self.hotspots_db.commit()
        self.emit("hotspots-updated")

        return True

    def get_states_list(self):
        if self.hotspots_db == None:
            return []

        c = self.hotspots_db.cursor()
        c.execute('select distinct state from hotspots order by state')

        l = [self.VALUE_ALL]
        for row in c :
            l.append(row[0])

        return l

    #@staticmethod
    def __create_query_condition(self, province=None, city=None, zipcode=None):
        query = [ ]
        if (province is not None) and (province != self.VALUE_ALL):
            query.append("state = '%s'" % province)
        if (city is not None) and (city != self.VALUE_ALL):
            query.append("city = '%s'" % city)
        if (zipcode is not None) and (zipcode != self.VALUE_ALL):
            query.append("zipcode = '%s'" % zipcode)
        if len(query) == 0:
            raise QueryError
        return ' and '.join(query)

    #@staticmethod
    def __create_return_list(self, cursor, all_first=True):
        retval = [ ]
        for row in cursor:
            retval.append(row[0])
        retval.sort()

        if all_first is True:
            retval = [self.VALUE_ALL] + retval
        return retval

    def get_cities_list(self):
        if self.hotspots_db == None:
            return []

        c = self.hotspots_db.cursor()
        c.execute('select distinct city from hotspots order by city')

        l = [self.VALUE_ALL]
        for row in c :
            l.append(row[0])

        return l

    def get_types_list(self):
        if self.hotspots_db == None:
            return []

        c = self.hotspots_db.cursor()
        c.execute('select distinct type from hotspots order by type')

        l = [self.VALUE_ALL]
        for row in c :
            l.append(row[0])

        return l

    def __create_query_select(self, column):
        return "select DISTINCT %s FROM hotspots" % column

    @_InitCheck([ ])
    def get_provinces(self, city=None, zipcode=None):
        try:
            cmd    = self.__create_query_select('state')
            query  = "%s where (%s)" % (cmd, self.__create_query_condition(None, city, zipcode))
        except QueryError:
            query  = cmd

        cursor = self.hotspots_db.cursor()
        cursor.execute(query)
        return self.__create_return_list(cursor, all_first=True)

    def get_provinces_of_city(self, city):
        return self.get_provinces(city=city)

    def get_provinces_of_zipcode(self, zipcode):
        return self.get_provinces(zipcode=zipcode)

    @_InitCheck([ ])
    def get_cities(self, province=None, zipcode=None):
        try:
            cmd    = self.__create_query_select('city')
            query  = "%s where (%s)" % (cmd, self.__create_query_condition(province, None, zipcode))
        except QueryError:
            query  = cmd

        cursor = self.hotspots_db.cursor()
        cursor.execute(query)
        return self.__create_return_list(cursor, all_first=True)

    def get_cities_of_province(self, province):
        return self.get_cities(province=province)

    def get_cities_of_zipcode(self, zipcode):
        return self.get_cities(zipcode=zipcode)

    @_InitCheck([ ])
    def get_zipcodes(self, province=None, city=None):
        try:
            cmd    = self.__create_query_select('zipcode')
            query  = "%s where (%s)" % (cmd, self.__create_query_condition(province, city, None))
        except QueryError:
            query  = cmd

        cursor = self.hotspots_db.cursor()
        cursor.execute(query)
        return self.__create_return_list(cursor, all_first=True)

    def get_zipcodes_of_province(self, province):
        return self.get_zipcodes(province=province)

    def get_zipcodes_of_city(self, city):
        return self.get_zipcodes(city=city)

    def get_zipcodes_list(self):
        if self.hotspots_db == None:
            return []

        c = self.hotspots_db.cursor()
        c.execute('select distinct zipcode from hotspots order by zipcode')

        l = [self.VALUE_ALL]
        for row in c :
            l.append(row[0])

        return l

    def get_update_date(self):
        if self.hotspots_db == None:
            return "--"

        c = self.hotspots_db.cursor()
        c.execute('select value from metadata where key = "date"')

        for row in c :
            y = row[0].split("-")[0]
            #m = months[int(row[0].split("-")[1]) - 1]
            m = row[0].split("-")[1]
            d = row[0].split("-")[2]
            return '%s/%s/%s' % (d, m, y)

        return None

    def search_hotspots(self, state=None, city=None, t=None, zipcode=None, location=None):
        c = self.hotspots_db.cursor()
        sql = "select * from hotspots"
        if state != None or city != None or t != None or zipcode != None or location != None:
            sql += " where "
            count = 0
            if state != None:
                if count > 0:
                    sql += " and "
                s_state = state + "%"
                sql += "state LIKE '%s'" % s_state
                count += 1
            if city != None:
                if count > 0:
                    sql += " and "
                s_city = city + "%"
                sql += "city LIKE '%s'" % s_city
                count += 1
            if t != None:
                if count > 0:
                    sql += " and "
                s_type = "%%%s%%" % t
                sql += "type LIKE '%s'" % s_type
                count += 1
            if zipcode != None:
                if count > 0:
                    sql += " and "
                s_zipcode = "%%%s%%" % zipcode
                sql += "zipcode LIKE '%s'" % s_zipcode
                count += 1
            if location != None:
                if count > 0:
                    sql += " and "
                s_location = "%%%s%%" % location
                sql += "name LIKE '%s'" % s_location
                count += 1

        c.execute(sql)

        #print sql
        ret_list = []
        for row in c :
            name = "<b>%s</b>\n<small>%s</small>\n<small>%s</small>\n<small>%s - %s - %s</small>" % (row[4],
                                                                                                     row[3],
                                                                                                     row[5],
                                                                                                     row[6],
                                                                                                     row[2],
                                                                                                     row[1])
            ret_list.append(name)

        return ret_list

    def __create_db_table(self, destination):
        # -- If the file already exists, remove it first
        if os.path.exists(destination):
            os.unlink(destination)

        # -- Create the connection to the new file
        conn = sqlite3.connect(destination)

        #-- Now create the table with the default columns
        c = conn.cursor()
        c.execute('''create table hotspots (country text, state text, city text, provider text, name text, address text, zipcode text, type text)''')
        c.execute('''create table metadata (key text, value text)''')
        return conn

    def __hotspot_to_sqlite(self, cursor, country, state, city, node_h):
        d = {'provider' : '',
             'name' : '',
             'address' : '',
             'zipcode' : '',
             'type' : ''
             }

        for node in node_h :
            d[node.tag] = node.text

        cursor.execute('''insert into hotspots
        values ("%s","%s","%s","%s","%s","%s","%s","%s")''' % (country, state, city,
                                                               d["provider"],
                                                               d["name"],
                                                               d["address"],
                                                               d["zipcode"],
                                                               d["type"]))

gobject.type_register(HotSpotsService)

if __name__ == '__main__':
    x = HotSpotsService()
    x.register_new_hotspot_file("/usr/share/tgcm/regional-info/uk/hotspot-list.xml", "/tmp/h.db")
