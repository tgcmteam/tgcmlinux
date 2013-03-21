#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Leo Zayas
#
# Copyright (c) 2003-2007, Telefonica Móviles España S.A.U.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import datetime
import gtk.gdk
import cairo
import gobject
import math

import tgcm
import tgcm.core.TrafficManager

from tgcm.ui.MSD.MSDUtils import format_to_maximun_unit_one_decimal

# -- Set the update cycle to 30 seconds
TRAFFIC_HISTORY_GRAPH_UPDATE_TIME_MS = 30*1000

class Rect:
    def __init__(self, left = 0, top = 0, right = 0, bottom = 0):
        self.left=left
        self.top=top
        self.right=right
        self.bottom=bottom

class TrafficHistoryGraph(gtk.DrawingArea):
    def __init__(self, external_info_label):
        gtk.DrawingArea.__init__(self)

        traffic_manager = tgcm.core.TrafficManager.TrafficManager()
        self.traffic_storage = traffic_manager.get_storage()
        self.conf = tgcm.core.Config.Config(tgcm.country_support)

        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

        self.connect("expose-event", self.draw)

        self.external_info_label=external_info_label

        self.vis_cols=6
        self.pos=0
        self.values=[]

        # Tooltip support
        self.props.has_tooltip = True
        self.connect("query-tooltip", self.on_query_tooltip)

        self.reload_data()
        self.timeout=gobject.timeout_add(TRAFFIC_HISTORY_GRAPH_UPDATE_TIME_MS, self.on_timeout)

    def invalidate(self):
        if self.window:
            alloc = self.get_allocation()
            rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)

    def set_values(self, values): # list is [[[val_local, val_roaming],tag], ...]
        last=len(self.values)==0 or self.pos==max(0, len(self.values)-self.vis_cols)
        self.values=values
        if last:
            self.pos=max(0, len(self.values)-self.vis_cols)
        if self.pos>len(self.values)-self.vis_cols:
            self.pos=len(self.values)-self.vis_cols
        if self.pos<0:
            self.pos=0
        self.invalidate()

    def get_visible_columns(self):
        return self.vis_cols

    def get_num_columns(self):
        return len(self.values)

    def get_pos(self):
        return self.pos

    def set_pos(self, pos):
        self.pos=pos
        if self.pos>len(self.values)-self.vis_cols:
            self.pos=len(self.values)-self.vis_cols
        if self.pos<0:
            self.pos=0
        self.invalidate()

    def fill_rect(self, ctx, rect):
        ctx.move_to(rect.left,rect.top)
        ctx.line_to(rect.right,rect.top)
        ctx.line_to(rect.right,rect.bottom)
        ctx.line_to(rect.left,rect.bottom)
        ctx.line_to(rect.left,rect.top)
        ctx.fill()
        ctx.stroke()

    def draw(self, widget, event):

        ctx=widget.window.cairo_create()    # cairo context object
        ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        ctx.clip()

        rc=self.get_allocation()

        is_uk=tgcm.country_support=='uk'


        # YLabel (MBytes)
        text="MBytes"
        ctx.save()
        ext=ctx.text_extents(text)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(10.0)
        ctx.move_to(20, rc.height/2)
        ctx.rotate(3 * math.pi / 2)
        ctx.set_source_rgb(0,0,0)
        ctx.show_text(text)
        ctx.restore()
        ctx.stroke()

        max_data=1.0

        for d in xrange(len(self.values)):
            if d>=self.pos and d-self.pos<self.vis_cols: # scale graph to visible values
                for d2 in xrange(2):
                    max_data=max(max_data, self.values[d][0][d2])

        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(10.0)

        if is_uk:
            ext2=ctx.text_extents(_("Billing"))
            ext3=ctx.text_extents(_("period"))
            ext4=ctx.text_extents(_("Data used (MB)"))

        colors=[
            [ [[0.4,0.4,0.4],[0.4,0.4,0.6],[0.4,0.4,1.0]], [[0.8,0.2,0.2],[0.8,0.2,0.2],[1.0,0.313,0.313]] ],
            [ [[0.0,0.0,0.2],[0.0,0.0,0.4],[0.2,0.2,1.0]], [[0.6,0.0,0.0],[0.6,0.0,0.0],[0.8,0.0,0.0]] ]
        ]

        if not self.conf.is_last_imsi_seen_valid():
            monthly_limit = self.conf.get_default_selected_monthly_limit(is_roaming = False)
        else:
            imsi = self.conf.get_last_imsi_seen()
            monthly_limit = self.conf.get_imsi_based_selected_monthly_limit(imsi, is_roaming = False)
            if monthly_limit == -1:
                monthly_limit = self.conf.get_imsi_based_other_monthly_limit(imsi, is_roaming = False)
        alert_mb = monthly_limit

        # Show the monthly allowance bar if necessary
        if self.conf.is_alerts_available() and (max_data > 0) and \
                (alert_mb > 0) and (alert_mb < max_data):
            text=_("Transference limit")

            # Calculate the size of the graph box. It is necessary to consider some additional
            # space on the right for the "Monthly allowance" mark
            ext=ctx.text_extents(text)
            barras=Rect(50,15,rc.width-ext[2],rc.height-50)

            # Draw the monthly allowance legend and mark
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(10.0)
            ext0=ctx.font_extents()
            ctx.move_to(rc.width-ext[2], barras.bottom-(barras.bottom-barras.top)*alert_mb/max_data-ext0[1]) # descent
            ctx.set_source_rgb(0,0,0)
            ctx.show_text(text)
            ctx.stroke()

            paint=True
            for xx in xrange(barras.left, rc.width, 10):
                if paint:
                    yy=barras.bottom-(barras.bottom-barras.top)*alert_mb/max_data
                    ctx.set_source_rgb(0.6,0.6,0.8)
                    self.fill_rect(ctx, Rect(xx,yy,xx+10,yy+1))
                paint=not paint
        else:
            # Calculate the size of the graph box. As we have not reached the monthly data allowance,
            # it's not necessary to reserve space for it
            barras=Rect(50,15,rc.width-15,rc.height-50)

        if is_uk:
            # Seems that UK uses a custom graph box size
            barras=Rect(10+max(20,ext4[2]/2),15,rc.width-ext[2],rc.height-50)

            text1=_("Billing")
            text2=_("period")

            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(10.0)
            ext0=ctx.font_extents()
            ext=ctx.text_extents(text1)
            ctx.move_to(barras.left-ext[2], barras.bottom+ext0[0]) # ascent
            ctx.set_source_rgb(0,0,0)
            ctx.show_text(text1)
            ctx.stroke()

            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(10.0)
            ext0=ctx.font_extents()
            ext=ctx.text_extents(text2)
            ctx.move_to(barras.left-ext[2], barras.bottom+ext0[0]+ext0[1]+ext0[0]) # ascent descent ascent
            ctx.set_source_rgb(0,0,0)
            ctx.show_text(text2)
            ctx.stroke()

            text=_("Data used (MB)")
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(10.0)
            ext0=ctx.font_extents()
            ext=ctx.text_extents(text)
            ctx.move_to(barras.left-ext[2]/2, barras.top-ext0[1]) # descent
            ctx.set_source_rgb(0,0,0)
            ctx.show_text(text)
            ctx.stroke()

        # Clean cached column information if needed
        self.cached_columns_data = []

        # Draw monthly expenses columns
        for b in xrange(self.vis_cols):
            if self.pos+b>=len(self.values):
                continue;

            if is_uk:
                b2=len(self.values)-1-b
            else:
                b2=b

            x1=barras.left+2+(barras.right-(barras.left+2))*b2/self.vis_cols
            x2=barras.left+2+(barras.right-(barras.left+2))*(b2+1)/self.vis_cols
            w=x2-x1

            centerx=(x1+x2)/2
            x1+=w*10/100
            x2-=w*10/100
            w=x2-x1

            # Store some information needed for building the tooltip
            coords = (x1, x2, barras.top, barras.bottom)
            month_name = self.values[self.pos+b][1]

            expenses = self.values[self.pos+b][0]
            non_roaming = format_to_maximun_unit_one_decimal(expenses[0], "GB","MB")
            roaming = format_to_maximun_unit_one_decimal(expenses[1], "GB","MB")
            expenses_data = (non_roaming, roaming)

            self.cached_columns_data.append({
                'coords' : coords,
                'expenses' : expenses_data,
                'month_name' : month_name,
            })

            # Expenses columns for roaming and non-roaming
            for d in xrange(2):
                l=x1+w*d/2;
                r=x1+w*(d+1)/2 -1;
                if r<l+5:
                    r=l+5;
                data=self.values[self.pos+b][0][d]

                if max_data!=0:
                    h=data*(barras.bottom-barras.top)/max_data;
                else:
                    h=0

                if self.pos+b==len(self.values)-1:
                    col=1
                else:
                    col=0
                color_border=colors[col][d][0]
                color_bar1=colors[col][d][1]
                color_bar2=colors[col][d][2]

                re=Rect(l,barras.bottom-h,r,barras.bottom)
                if re.bottom>=re.top+5:
                    for x in xrange(int(l), int(r-2), 2):
                        re2=Rect(x,re.top+2,x+3,re.bottom-2)
                        rr=color_bar1[0]+(color_bar2[0]-color_bar1[0])*(x-l)/(r-l)
                        gg=color_bar1[1]+(color_bar2[1]-color_bar1[1])*(x-l)/(r-l)
                        bb=color_bar1[2]+(color_bar2[2]-color_bar1[2])*(x-l)/(r-l)
                        ctx.set_source_rgb(rr,gg,bb)
                        self.fill_rect(ctx, re2)

                ctx.set_source_rgb(color_border[0],color_border[1],color_border[2])
                self.fill_rect(ctx, Rect(re.left,re.top,re.left+2,re.bottom))
                if re.top+2<=re.bottom:
                    self.fill_rect(ctx, Rect(re.left,re.top,re.right,re.top+2))
                self.fill_rect(ctx, Rect(re.right-2,re.top,re.right,re.bottom))
                if re.bottom-2>=re.top:
                    self.fill_rect(ctx, Rect(re.left,re.bottom-2,re.right,re.bottom))

                text="%i" % int(data)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                ctx.set_font_size(0.75*10.0)
                extent=ctx.text_extents(text)
                fextent=ctx.font_extents()
                ctx.set_source_rgb(0,0,0)
                ctx.move_to((l+r)/2-extent[2]/2,re.bottom+1+fextent[0]) # ascent
                ctx.show_text(text)
                ctx.stroke()

            if is_uk and (b==len(self.values)-1 or b==len(self.values)-2):
                if b==len(self.values)-1:
                    text1=_("This")
                elif b==len(self.values)-2:
                    text1=_("Last")
                text2=_("month")

                text="0000"
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                ctx.set_font_size(0.75*10.0)
                fextent0=ctx.font_extents()

                text=text1
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(10.0*1.25)
                extent=ctx.text_extents(text)
                fextent=ctx.font_extents()
                ctx.set_source_rgb(0,0,0)
                ctx.move_to((x1+x2)/2-extent[2]/2, barras.bottom+fextent0[2]+fextent[0]) # height + ascent
                ctx.show_text(text)
                ctx.stroke()

                text=text2
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(10.0*1.25)
                extent=ctx.text_extents(text)
                fextent=ctx.font_extents()
                ctx.set_source_rgb(0,0,0)
                ctx.move_to((x1+x2)/2-extent[2]/2, barras.bottom+fextent0[2]+fextent[0]+fextent[2]*0.75) # height + ascent + height
                ctx.show_text(text)
                ctx.stroke()

            else:
                text="0000"
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                ctx.set_font_size(0.75*10.0)
                fextent0=ctx.font_extents()

                if is_uk:
                    text=_("Month %d") % (b2+1)
                else:
                    text=self.values[self.pos+b][1]
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(10.0*1.25)
                extent=ctx.text_extents(text)
                fextent=ctx.font_extents()
                ctx.set_source_rgb(0,0,0)
                ctx.move_to((x1+x2)/2-extent[2]/2, barras.bottom+fextent0[2]+fextent[0]) # height + ascent
                ctx.show_text(text)
                ctx.stroke()

        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(0.75*10.0)
        for s in xrange(1,5):
            y=barras.bottom+(barras.top-barras.bottom)*s/4;
            text="%.2f" % (float(max_data) * s / 4)
            extent=ctx.text_extents(text)
            fextent=ctx.font_extents()
            ctx.move_to(barras.left-extent[2]-2,y-extent[3]/2+fextent[0])
            ctx.show_text(text)
            ctx.stroke()

        # Graph data legend
        rc=Rect(0,0,rc.width,rc.height)

        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(10.0)
        extent=ctx.font_extents()
        fascent=extent[0]
        fdescent=extent[1]
        fheight=extent[2]

        if is_uk:
            text=_("%s network") % self.conf.get_company_name()
            ext=ctx.text_extents(text)
            w1=ext[2]
            text=_("Roaming")
            ext=ctx.text_extents(text)
            w2=ext[2]
            x=rc.right-7-33-w1-10-33-w2
        else:
            x=rc.left+7

        ctx.set_source_rgb(0,0,0.2)
        self.fill_rect(ctx, Rect(x,rc.bottom-10-fdescent,x+30,rc.bottom-10+7-fdescent))
        ctx.set_source_rgb(0.2,0.2,1.0)
        self.fill_rect(ctx, Rect(x+2,rc.bottom-10+2-fdescent,x+30-2,rc.bottom-10+7-2-fdescent))

        x+=33
        text=_("%s network") % self.conf.get_company_name()
        ext=ctx.text_extents(text)
        ctx.move_to(x,rc.bottom-3-fdescent)
        ctx.set_source_rgb(0,0,0)
        ctx.show_text(text)
        ctx.stroke()

        x+=ext[2]+10;
        ctx.set_source_rgb(0.2,0,0)
        self.fill_rect(ctx, Rect(x,rc.bottom-10-fdescent,x+30,rc.bottom-10+7-fdescent))
        ctx.set_source_rgb(0.8,0,0)
        self.fill_rect(ctx, Rect(x+2,rc.bottom-10+2-fdescent,x+30-2,rc.bottom-10+7-2-fdescent))

        x+=33
        text=_("Roaming")
        ext=ctx.text_extents(text)
        ctx.move_to(x,rc.bottom-3-fdescent)
        ctx.set_source_rgb(0,0,0)
        ctx.show_text(text)
        ctx.stroke()

        ctx.set_source_rgb(0.4,0.4,0.4)
        self.fill_rect(ctx, Rect(barras.left,barras.top,barras.left+2,barras.bottom))
        self.fill_rect(ctx, Rect(barras.left-9,barras.bottom-2,barras.right,barras.bottom))

        return False

    def on_timeout(self):
        self.reload_data()
        self.timeout=gobject.timeout_add(TRAFFIC_HISTORY_GRAPH_UPDATE_TIME_MS, self.on_timeout)

    def reload_data(self):
        imsi = self.conf.get_last_imsi_seen()
        dun = self.traffic_storage.get_history(imsi, is_roaming = False)
        dunr = self.traffic_storage.get_history(imsi, is_roaming = True)
        pend = self.traffic_storage.get_pending(imsi, is_roaming = False)
        pendr = self.traffic_storage.get_pending(imsi, is_roaming = True)

        if len(dun)>0:
            minm=dun[0][0][1]*12+dun[0][0][0]-1
            maxm=dun[len(dun)-1][0][1]*12+dun[len(dun)-1][0][0]-1
        if len(dunr)>0:
            if len(dun)==0:
                minm=dunr[0][0][1]*12+dunr[0][0][0]-1
                maxm=dunr[len(dunr)-1][0][1]*12+dunr[len(dunr)-1][0][0]-1
            else:
                minm=min(minm,dunr[0][0][1]*12+dunr[0][0][0]-1)
                maxm=max(maxm,dunr[len(dunr)-1][0][1]*12+dunr[len(dunr)-1][0][0]-1)
        if len(dun)==0 and len(dunr)==0:
            minm=pend[0][1]*12+pend[0][0]-1
            maxm=pend[0][1]*12+pend[0][0]-1
        else:
            minm=min(minm,pend[0][1]*12+pend[0][0]-1)
            maxm=max(maxm,pend[0][1]*12+pend[0][0]-1)
        minm=min(minm,pendr[0][1]*12+pendr[0][0]-1)
        maxm=max(maxm,pendr[0][1]*12+pendr[0][0]-1)

        datas=[]
        min_label=""
        for h in xrange(minm, maxm+1):
            m=h%12
            a=h/12
            data=[[0,0],""]
            for d in xrange(0, len(dun)):
                if dun[d][0][1]==a and dun[d][0][0]-1==m:
                    data[0][0]+=dun[d][1][0]+dun[d][1][1]
                    break
            for d in xrange(0, len(dunr)):
                if dunr[d][0][1]==a and dunr[d][0][0]-1==m:
                    data[0][1]+=dunr[d][1][0]+dunr[d][1][1]
                    break
            if pend[0][1]==a and pend[0][0]-1==m:
                data[0][0]+=pend[1][0]+pend[1][1]
            if pendr[0][1]==a and pendr[0][0]-1==m:
                data[0][1]+=pendr[1][0]+pendr[1][1]

            label=datetime.date(a, m+1, 1).strftime('%b\'%y')
            if h==minm:
                min_label=label
            data[0][0]/=1024*1024
            data[0][1]/=1024*1024
            data[1]=label
            datas=datas+[data]

        self.set_values(datas)

        is_uk=tgcm.country_support=='uk'

        if is_uk:
            self.external_info_label.set_text(_("Summary from %s to current date") % min_label)

    def get_column_data_at_pos(self, x, y):
        for column_data in self.cached_columns_data:
            x1, x2, y1, y2 = column_data['coords']
            if (x >= x1) and (x <= x2) and (y >= y1) and (y <= y2):
                return column_data
        return None

    def on_query_tooltip(self, widget, x, y, keyboard_tip, tooltip):
        column_data = self.get_column_data_at_pos(x, y)
        if column_data is not None:
            month = column_data['month_name']
            non_roaming = column_data['expenses'][0]
            roaming = column_data['expenses'][1]

            message = _("%s used data:\n- National: %s\n- Roaming: %s") % (month, non_roaming, roaming)
            tooltip.set_text(message)
            return True
        else:
            return False
