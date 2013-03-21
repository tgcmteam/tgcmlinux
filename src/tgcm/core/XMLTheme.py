#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Authors : Cesar Garcia Tapia <tapia@openshine.com>
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

import os
import re
from xml.etree import ElementTree

import gtk

import tgcm
import tgcm.core.Singleton


class XMLTheme:
    __metaclass__ = tgcm.core.Singleton.Singleton

    def __init__ (self):
        self.config = tgcm.core.Config.Config()

        self.theme_dir = os.path.join (tgcm.themes_dir, tgcm.country_support, "default")
        if not os.path.exists (self.theme_dir):
            if self.config.is_latam (tgcm.country_support):
                self.theme_dir = os.path.join (tgcm.themes_dir, "latam", "ar", "default")
        self.conf_file = os.path.join (self.theme_dir, "theme.xml")

        self.layout = {}
        self.pixbufs = {}
        self.fonts = {}

    def load_theme (self):
        xml = ElementTree.parse (self.conf_file)
        root = xml.getroot()
        self.__load_file (root)

    def __load_file (self, root, path="."):
        for node in root:
            if node.tag in ('bitmap', 'icon'):
                self.__load_bitmap (node, path)
            elif node.tag == 'font':
                self.__load_font (node)
            elif node.tag == 'layout':
                self.__load_layout (node)
            elif node.tag == 'include':
                self.__include (node)

    def __include (self, root_node):
        if not root_node.attrib.has_key ('file'):
            return

        filename = os.path.join (self.theme_dir, root_node.attrib['file'])

        xml = ElementTree.parse (filename)
        root = xml.getroot()

        self.__load_file (root, os.path.dirname (root_node.attrib['file']))

    def get_window_icon (self):
        # TODO: It must be desirable in a near future to use directly the .ico
        # resource, instead of using the ICO to PNG converted graphic.
        # Unfortunately in PyGTK 2.24.0-2 the 'ico' loader fails miserably to
        # load our original .ico resource.
        new_pixbuf = None
        icon = os.path.join(self.theme_dir, 'icon.png')
        if os.path.exists(icon):
            new_pixbuf = gtk.gdk.pixbuf_new_from_file(icon)
        return new_pixbuf

    def get_layout (self, name):
        if name in self.layout:
            return self.layout[name]
        else:
            return None

    def get_pixbuf(self, name):
        if name in self.pixbufs:
            return self.pixbufs[name]
        else:
            return None

    def __load_bitmap (self, root_node, path="."):
        if not (root_node.attrib.has_key ('name') and root_node.attrib.has_key ('file')):
            return

        name = root_node.attrib['name']
        path = os.path.join (self.theme_dir, path)
        filename = os.path.join (path, root_node.attrib['file'])
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)

        alphacolor = None
        if root_node.attrib.has_key ('alphacolor'):
            if root_node.attrib['alphacolor']:
                alphacolor = root_node.attrib['alphacolor']
                pixbuf = self.__add_alpha_channel (pixbuf, alphacolor)

        if root_node.find ('subbitmap') is not None:
            for node in root_node:
                if node.tag == 'subbitmap':
                    self.__load_subbitmap (node, pixbuf)

        self.pixbufs[name] = pixbuf

    def __load_subbitmap (self, root_node, pixbuf):
        if not (root_node.attrib.has_key ('name') and
                root_node.attrib.has_key ('left') and
                root_node.attrib.has_key ('top') and
                root_node.attrib.has_key ('width') and
                root_node.attrib.has_key ('height')):
            return

        name = root_node.attrib['name']
        left = int (root_node.attrib['left'])
        top = int (root_node.attrib['top'])
        width = int (root_node.attrib['width'])
        height = int (root_node.attrib['height'])

        subpixbuf = gtk.gdk.Pixbuf (gtk.gdk.COLORSPACE_RGB, True, 8, width, height)
        pixbuf.copy_area (left, top, width, height, subpixbuf, 0, 0)

        self.pixbufs [name] = subpixbuf

    def __load_font (self, root_node):
        if not (root_node.attrib.has_key ('name') and
                root_node.attrib.has_key ('face')):
            return

        name = root_node.attrib['name']
        font = {}

        font['face'] = root_node.attrib['face']

        font['height'] = self.__get_node_property (root_node, 'height', None)
        font['weight'] = self.__get_node_property (root_node, 'weight', None)
        font['underline'] = self.__get_node_property (root_node, 'underline', None)
        font['italic'] = self.__get_node_property (root_node, 'italic', None)

        self.fonts [name] = font

    def __load_layout (self, root_node):
        name = root_node.attrib['name']
        width = int (root_node.attrib['width'])
        height = int (root_node.attrib['height'])

        stickyX = int (self.__get_node_property(root_node, 'stickyX', '0'))
        stickyY = int (self.__get_node_property(root_node, 'stickyY', '0'))

        self.layout[name] = {}
        self.layout[name]['size'] = {}
        self.layout[name]['size']['width'] = width
        self.layout[name]['size']['height'] = height
        self.layout[name]['size']['stickyX'] = stickyX
        self.layout[name]['size']['stickyY'] = stickyY

        for node in root_node:
            if node.tag == 'border':
                self.__load_border (node, name)
            elif node.tag == 'background':
                self.__load_background (node, name)
            elif node.tag == 'caption':
                self.__load_caption (node, name)
            elif node.tag == 'shape':
                self.__load_shape (node, name)
            elif node.tag == 'accelerators':
                self.__load_accelerators (node, name)
            elif node.tag == 'widgets':
                self.__load_widgets (node, name)

    def __load_border (self, root_node, layout_name):
        self.layout[layout_name]['border'] = {}
        self.layout[layout_name]['border']['resizeX'] = self.__get_node_property (root_node, 'resizeX', False)
        self.layout[layout_name]['border']['resizeY'] = self.__get_node_property (root_node, 'resizeY', False)
        self.layout[layout_name]['border']['minX'] = int (self.__get_node_property (root_node, 'minX', 0))
        self.layout[layout_name]['border']['minY'] = int (self.__get_node_property (root_node, 'minY', 0))
        self.layout[layout_name]['border']['left'] = int (self.__get_node_property (root_node, 'left', 0))
        self.layout[layout_name]['border']['right'] = int (self.__get_node_property (root_node, 'right', 0))
        self.layout[layout_name]['border']['top'] = int (self.__get_node_property (root_node, 'top', 0))
        self.layout[layout_name]['border']['bottom'] = int (self.__get_node_property (root_node, 'bottom', 0))

    def __load_background (self, root_node, layout_name):
        background = {}

        if root_node.attrib.has_key ('type'):
            if root_node.attrib['type'] == 'image':
                if root_node.attrib.has_key ('bitmap'):
                    background['image'] = root_node.attrib['bitmap']

        for node in root_node:
            if node.tag == "resize":
                self.__load_resize (node, background)

        self.layout[layout_name]['background'] = background

    def __load_caption (self, root_node, layout_name):
        self.layout[layout_name]['caption'] = {}
        self.layout[layout_name]['caption']['type'] = self.__get_node_property (root_node, 'type', 'none')
        self.layout[layout_name]['caption']['top'] = int (self.__get_node_property (root_node, 'top', '0'))
        self.layout[layout_name]['caption']['maximize'] = self.__get_node_property (root_node, 'maximize', True)
        self.layout[layout_name]['caption']['minimize'] = self.__get_node_property (root_node, 'minimize', True)

    def __load_shape (self, root_node, layout_name):
        self.layout[layout_name]['shape'] = {}
        self.layout[layout_name]['shape']['type'] = self.__get_node_property (root_node, 'type', 'none')
        self.layout[layout_name]['shape']['width'] = int (self.__get_node_property (root_node, 'width', '0'))
        if self.layout[layout_name]['shape']['width'] == 0:
            self.layout[layout_name]['shape']['width'] = int (self.__get_node_property (root_node, 'rwidth', '0'))

        self.layout[layout_name]['shape']['height'] = int (self.__get_node_property (root_node, 'height', '0'))
        if self.layout[layout_name]['shape']['height'] == 0:
            self.layout[layout_name]['shape']['height'] = int (self.__get_node_property (root_node, 'rheight', '0'))

        self.layout[layout_name]['shape']['alphacolor'] = self.__get_node_property (root_node, 'alphacolor', None)

    def __load_accelerators (self, root_node, layout_name):
        self.layout[layout_name]['accelerators'] = []
        for node in root_node:
            accelerator = {}
            accelerator['key'] = self.__get_node_property(node, 'key', None)
            accelerator['action'] = self.__get_node_property(node, 'action', None)
            self.layout[layout_name]['accelerators'].append(accelerator)

    def __load_resize (self, root_node, layout_section):
        if root_node.attrib.has_key ('type'):
            if root_node.attrib['type'] == 'frame':
                left = int (root_node.attrib['left'])
                top = int (root_node.attrib['top'])
                right = int (root_node.attrib['right'])
                bottom = int (root_node.attrib['bottom'])

                layout_section['resize'] = {'type': 'frame', 'left': left, 'top': top, 'right': right, 'bottom': bottom}
            elif root_node.attrib['type'] == 'stretch':
                layout_section['resize'] = {'type': 'stretch'}

    def __load_widgets (self, root_node, layout_name):
        self.layout[layout_name]['widgets'] = []

        for node in root_node:
            if node.tag == 'animate' or node.tag == 'animate-linux':
                self.__load_widget_animate (node, layout_name)
            elif node.tag == 'button' or node.tag == 'button-linux':
                self.__load_widget_button (node, layout_name)
            elif node.tag == 'label' or node.tag == 'label-linux':
                self.__load_widget_label (node, layout_name)
            elif node.tag == 'progress' or node.tag == 'progress-linux':
                self.__load_widget_progress (node, layout_name)
            elif node.tag == 'bitmap' or node.tag == 'bitmap-linux':
                self.__load_widget_bitmap (node, layout_name)
            elif node.tag == 'services' or node.tag == 'services-linux':
                self.__load_services (node, layout_name)
            elif node.tag == 'widgetex' or node.tag == 'widgetex-linux':
                self.__load_widget_widgetex (node, layout_name)

    def __load_widget_button (self, root_node, layout_name):
        button = {}
        button['type'] = 'button'

        if root_node.attrib.has_key ('id'):
            button['id'] = root_node.attrib['id']
        else:
            return

        button['anchor_tl'] = self.__get_node_property (root_node, 'anchor-tl', 'none')
        button['anchor_br'] = self.__get_node_property (root_node, 'anchor-br', 'none')
        button['left'] = self.__get_node_property (root_node, 'left', 0)
        button['top'] = self.__get_node_property (root_node, 'top', 0)
        button['width'] = self.__get_node_property (root_node, 'width', 0)
        button['height'] = self.__get_node_property (root_node, 'height', 0)
        image_normal = self.__get_node_property (root_node, 'image-normal', None)
        button['image_normal'] = self.__get_pixbuf_by_name (image_normal)
        image_hot = self.__get_node_property (root_node, 'image-hot', None)
        button['image_hot'] = self.__get_pixbuf_by_name (image_hot)
        image_down = self.__get_node_property (root_node, 'image-down', None)
        button['image_down'] = self.__get_pixbuf_by_name (image_down)
        image_disable = self.__get_node_property (root_node, 'image-disable', None)
        button['image_disable'] = self.__get_pixbuf_by_name (image_disable)
        button['text'] = self.__get_node_property (root_node, 'text', None)
        button['tooltip'] = self.__get_node_property (root_node, 'tooltip', None)
        button['text_align'] = self.__get_node_property (root_node, 'text-align', 'left-center')
        button['text_left'] = self.__get_node_property (root_node, 'text-left', 0)
        button['text_right'] = self.__get_node_property (root_node, 'text-right', 0)
        button['text_top'] = self.__get_node_property (root_node, 'text-top', 0)
        button['text_bottom'] = self.__get_node_property (root_node, 'text-bottom', 0)
        button['multiline'] = self.__get_node_property (root_node, 'multiline', False)
        button['ellipsis'] = self.__get_node_property (root_node, 'ellipsis', False)
        font_normal = self.__get_node_property (root_node, 'font-normal', None)
        button['font_normal'] = self.__get_font_by_name (font_normal)
        font_hot = self.__get_node_property (root_node, 'font-hot', None)
        button['font_hot'] = self.__get_font_by_name (font_hot)
        font_down = self.__get_node_property (root_node, 'font-down', None)
        button['font_down'] = self.__get_font_by_name (font_down)
        font_disable = self.__get_node_property (root_node, 'font-disable', None)
        button['font_disable'] = self.__get_font_by_name (font_disable)
        button['color_normal'] = self.__get_node_property (root_node, 'color-normal', None)
        button['color_hot'] = self.__get_node_property (root_node, 'color-hot', button['color_normal'])
        button['color_down'] = self.__get_node_property (root_node, 'color-down', button['color_normal'])
        button['color_disable'] = self.__get_node_property (root_node, 'color-disable', button['color_normal'])
        button['cursor'] = self.__get_node_property (root_node, 'cursor', None)

        button['on_down'] = self.__get_node_property (root_node, 'ondown', None)
        button['on_click'] = self.__get_node_property (root_node, 'onclick', None)

        button['visible'] = self.__get_node_property (root_node, 'visible', True)
        button['enable'] = self.__get_node_property (root_node, 'enable', True)

        for node in root_node:
            if node.tag == "resize":
                self.__load_resize (node, button)

        self.layout[layout_name]['widgets'].append(button)

    def __load_widget_label (self, root_node, layout_name):
        label = {}
        label['type'] = 'label'

        if root_node.attrib.has_key ('id'):
            label['id'] = root_node.attrib['id']
        else:
            return

        label['anchor_tl'] = self.__get_node_property (root_node, 'anchor-tl', 'none')
        label['anchor_br'] = self.__get_node_property (root_node, 'anchor-br', 'none')
        label['left'] = self.__get_node_property (root_node, 'left', 0)
        label['top'] = self.__get_node_property (root_node, 'top', 0)
        label['width'] = self.__get_node_property (root_node, 'width', 0)
        label['height'] = self.__get_node_property (root_node, 'height', 0)
        font = self.__get_node_property (root_node, 'font', None)
        label['font'] = self.__get_font_by_name (font)
        label['color'] = self.__get_node_property (root_node, 'color', None)
        label['align'] = self.__get_node_property (root_node, 'align', 'left-center')
        label['multiline'] = self.__get_node_property (root_node, 'multiline', False)
        label['ellipsis'] = self.__get_node_property (root_node, 'ellipsis', False)
        label['shadow'] = self.__get_node_property (root_node, 'shadow', False)
        label['text'] = self.__get_node_property (root_node, 'text', None)
        label['text_align'] = self.__get_node_property (root_node, 'text-align', 'left-top')
        label['tooltip'] = self.__get_node_property (root_node, 'tooltip', None)

        label['visible'] = self.__get_node_property (root_node, 'visible', True)

        self.layout[layout_name]['widgets'].append(label)

    def __load_widget_animate (self, root_node, layout_name):
        animate = {}
        animate['type'] = 'animate'

        if root_node.attrib.has_key ('id'):
            animate['id'] = root_node.attrib['id']
        else:
            return

        animate ['left'] = self.__get_node_property (root_node, 'left', 0)
        animate['top'] = self.__get_node_property (root_node, 'top', 0)
        animate['width'] = self.__get_node_property (root_node, 'width', 0)
        animate['height'] = self.__get_node_property (root_node, 'height', 0)
        image = self.__get_node_property (root_node, 'image', None)
        animate['image'] = self.__get_pixbuf_by_name (image)
        animate['frames'] = self.__get_node_property (root_node, 'frames', 0)
        animate['fps'] = self.__get_node_property (root_node, 'fps', 0)
        animate['horizontal'] = self.__get_node_property (root_node, 'horizontal', True)
        #animate['resize'] =
        animate['anchor_tl'] = self.__get_node_property (root_node, 'anchor-tl', 'none')
        animate['anchor_br'] = self.__get_node_property (root_node, 'anchor-br', 'none')
        animate['tooltip'] = self.__get_node_property (root_node, 'tooltip', None)
        animate['visible'] = self.__get_node_property (root_node, 'visible', True)
        animate['play'] = self.__get_node_property (root_node, 'play', '')
        animate['hittest'] = self.__get_node_property (root_node, 'hittest', 'client')

        self.layout[layout_name]['widgets'].append(animate)

    def __load_widget_progress (self, root_node, layout_name):
        progress = {}
        progress['type'] = 'progress'

        if root_node.attrib.has_key ('id'):
            progress['id'] = root_node.attrib['id']
        else:
            return

        progress['left'] = self.__get_node_property (root_node, 'left', 0)
        progress['top'] = self.__get_node_property (root_node, 'top', 0)
        progress['width'] = self.__get_node_property (root_node, 'width', 0)
        progress['height'] = self.__get_node_property (root_node, 'height', 0)
        #progress['resize'] =
        progress['anchor_tl'] = self.__get_node_property (root_node, 'anchor-tl', 'none')
        progress['anchor_br'] = self.__get_node_property (root_node, 'anchor-br', 'none')
        progress['tooltip'] = self.__get_node_property (root_node, 'tooltip', None)
        progress['visible'] = self.__get_node_property (root_node, 'visible', True)
        progress['status'] = self.__get_node_property (root_node, 'status', None)
        image = self.__get_node_property (root_node, 'image', None)
        progress['image'] = self.__get_pixbuf_by_name (image)
        progress['hittest'] = self.__get_node_property (root_node, 'hittest', 'client')

        progress['states'] = []
        for node in root_node:
            if node.tag == 'state':
                if node.attrib.has_key ('image'):
                    image = self.__get_node_property (node, 'image', None)
                    if image:
                        progress['states'].append (self.__get_pixbuf_by_name (image))

        self.layout[layout_name]['widgets'].append(progress)

    def __load_widget_bitmap (self, root_node, layout_name):
        bitmap = {}
        bitmap['type'] = 'bitmap'

        if root_node.attrib.has_key ('id'):
            bitmap['id'] = root_node.attrib['id']
        else:
            return

        bitmap['anchor_tl'] = self.__get_node_property (root_node, 'anchor-tl', 'none')
        bitmap['anchor_br'] = self.__get_node_property (root_node, 'anchor-br', 'none')
        bitmap['left'] = self.__get_node_property (root_node, 'left', 0)
        bitmap['top'] = self.__get_node_property (root_node, 'top', 0)
        bitmap['width'] = self.__get_node_property (root_node, 'width', 0)
        bitmap['height'] = self.__get_node_property (root_node, 'height', 0)
        image = self.__get_node_property (root_node, 'image', None)
        bitmap['image'] = self.__get_pixbuf_by_name (image)
        #bitmap['resize'] =
        bitmap['tooltip'] = self.__get_node_property (root_node, 'tooltip', None)
        bitmap['visible'] = self.__get_node_property (root_node, 'visible', True)

        self.layout[layout_name]['widgets'].append(bitmap)

    def __load_services (self, root_node, layout_name):
        self.layout[layout_name]['services'] = {}
        self.layout[layout_name]['services']['id'] = root_node.attrib['id']
        self.layout[layout_name]['services']['left'] = int (self.__get_node_property (root_node, 'left', 0))
        self.layout[layout_name]['services']['top'] = int (self.__get_node_property (root_node, 'top', 0))
        self.layout[layout_name]['services']['width'] = int (self.__get_node_property (root_node, 'width', 0))
        self.layout[layout_name]['services']['height'] = int (self.__get_node_property (root_node, 'height', 0))
        self.layout[layout_name]['services']['cursor'] = self.__get_node_property (root_node, 'cursor', 'arrow')
        self.layout[layout_name]['services']['anchor_tl'] = self.__get_node_property (root_node, 'anchor-tl', 'none')
        self.layout[layout_name]['services']['anchor_br'] = self.__get_node_property (root_node, 'anchor-br', 'none')
        self.layout[layout_name]['services']['paddingX'] = int (self.__get_node_property (root_node, 'paddingX', 0))
        self.layout[layout_name]['services']['paddingY'] = int (self.__get_node_property (root_node, 'paddingY', 0))
        self.layout[layout_name]['services']['item_height'] = int (self.__get_node_property (root_node, 'item_height', 0))

        self.layout[layout_name]['services']['buttons'] = []

        for node in root_node:
            if node.tag == 'service':
                self.__load_service_button (node, layout_name)
            elif node.tag == 'more':
                self.__load_more_button (node, layout_name)

    def __load_service_button (self, root_node, layout_name):
        service = {}
        service['type'] = 'service'

        if root_node.attrib.has_key ('id'):
            service['id'] = root_node.attrib['id']
        else:
            return

        service['width'] = self.__get_node_property (root_node, 'width', 0)
        service['height'] = self.__get_node_property (root_node, 'height', 0)
        service['cursor'] = self.__get_node_property (root_node, 'cursor', 'arrow')
        service['on_down'] = self.__get_node_property (root_node, 'ondown', None)
        service['on_click'] = self.__get_node_property (root_node, 'onclick', None)
        service['resize'] = self.__get_node_property (root_node, 'resize', 0)

        image_normal = self.__get_node_property (root_node, 'image-normal', None)
        service['image_normal'] = self.__get_pixbuf_by_name (image_normal)
        image_hot = self.__get_node_property (root_node, 'image-hot', None)
        service['image_hot'] = self.__get_pixbuf_by_name (image_hot)
        image_down = self.__get_node_property (root_node, 'image-down', None)
        service['image_down'] = self.__get_pixbuf_by_name (image_down)
        image_disable = self.__get_node_property (root_node, 'image-disable', None)
        service['image_disable'] = self.__get_pixbuf_by_name (image_disable)

        alt_image = self.__get_node_property (root_node, 'alt-image', None)
        service['alt_image'] = self.__get_pixbuf_by_name (alt_image)
        service['alt_left'] = self.__get_node_property (root_node, 'alt-left', 0)
        service['alt_top'] = self.__get_node_property (root_node, 'alt-top', 0)
        service['alt_width'] = self.__get_node_property (root_node, 'alt-width', 0)
        service['alt_height'] = self.__get_node_property (root_node, 'alt-height', 0)
        alt_font = self.__get_node_property (root_node, 'alt-font', None)
        service['alt_font'] = self.__get_font_by_name (alt_font)
        service['alt_color'] = self.__get_node_property (root_node, 'alt-color', 0)

        font_normal = self.__get_node_property (root_node, 'font-normal', None)
        service['font_normal'] = self.__get_font_by_name (font_normal)
        font_hot = self.__get_node_property (root_node, 'font-hot', None)
        service['font_hot'] = self.__get_font_by_name (font_hot)
        font_down = self.__get_node_property (root_node, 'font-down', None)
        service['font_down'] = self.__get_font_by_name (font_down)
        font_disable = self.__get_node_property (root_node, 'font-disable', None)
        service['font_disable'] = self.__get_font_by_name (font_disable)

        service['color_normal'] = self.__get_node_property (root_node, 'color-normal', None)
        service['color_hot'] = self.__get_node_property (root_node, 'color-hot', service['color_normal'])
        service['color_down'] = self.__get_node_property (root_node, 'color-down', service['color_normal'])
        service['color_disable'] = self.__get_node_property (root_node, 'color-disable', service['color_normal'])
        service['text_align'] = self.__get_node_property (root_node, 'text-align', 'left-center')
        service['multiline'] = self.__get_node_property (root_node, 'multiline', False)
        service['ellipsis'] = self.__get_node_property (root_node, 'ellipsis', False)

        self.layout[layout_name]['services']['buttons'].append (service)

    def __load_more_button (self, root_node, layout_name):
        button = {}
        button['type'] = 'more_button'

        if root_node.attrib.has_key ('id'):
            button['id'] = root_node.attrib['id']
        else:
            return

        button['width'] = self.__get_node_property (root_node, 'width', 0)
        button['height'] = self.__get_node_property (root_node, 'height', 0)
        button['cursor'] = self.__get_node_property (root_node, 'cursor', 'arrow')
        button['on_down'] = self.__get_node_property (root_node, 'ondown', None)
        button['on_click'] = self.__get_node_property (root_node, 'onclick', None)
        button['resize'] = self.__get_node_property (root_node, 'resize', 0)

        image_normal = self.__get_node_property (root_node, 'image-normal', None)
        button['image_normal'] = self.__get_pixbuf_by_name (image_normal)
        image_hot = self.__get_node_property (root_node, 'image-hot', None)
        button['image_hot'] = self.__get_pixbuf_by_name (image_hot)
        image_down = self.__get_node_property (root_node, 'image-down', None)
        button['image_down'] = self.__get_pixbuf_by_name (image_down)
        image_disable = self.__get_node_property (root_node, 'image-disable', None)
        button['image_disable'] = self.__get_pixbuf_by_name (image_disable)

        font_normal = self.__get_node_property (root_node, 'font-normal', None)
        button['font_normal'] = self.__get_font_by_name (font_normal)
        font_hot = self.__get_node_property (root_node, 'font-hot', None)
        button['font_hot'] = self.__get_font_by_name (font_hot)
        font_down = self.__get_node_property (root_node, 'font-down', None)
        button['font_down'] = self.__get_font_by_name (font_down)
        font_disable = self.__get_node_property (root_node, 'font-disable', None)
        button['font_disable'] = self.__get_font_by_name (font_disable)

        button['color_normal'] = self.__get_node_property (root_node, 'color-normal', None)
        button['color_hot'] = self.__get_node_property (root_node, 'color-hot', button['color_normal'])
        button['color_down'] = self.__get_node_property (root_node, 'color-down', button['color_normal'])
        button['color_disable'] = self.__get_node_property (root_node, 'color-disable', button['color_normal'])
        button['text_align'] = self.__get_node_property (root_node, 'text-align', 'left-center')
        button['multiline'] = self.__get_node_property (root_node, 'multiline', False)
        button['ellipsis'] = self.__get_node_property (root_node, 'ellipsis', False)
        button['text'] = self.__get_node_property (root_node, 'text', '')
        button['tooltip'] = self.__get_node_property (root_node, 'tooltip', '')
        button['visible'] = self.__get_node_property (root_node, 'visible', True)

        self.layout[layout_name]['services']['buttons'].append (button)

    def __load_widget_widgetex (self, root_node, layout_name):
        widgetex = {}
        widgetex['type'] = 'widgetex'

        if root_node.attrib.has_key('id'):
            widgetex['id'] = root_node.attrib['id']
        else:
            return

        widgetex['class'] = self.__get_node_property(root_node, 'class', None)
        widgetex['params'] = self.__get_node_property(root_node, 'params', None)
        widgetex['anchor_tl'] = self.__get_node_property(root_node, 'anchor-tl', 'none')
        widgetex['anchor_br'] = self.__get_node_property(root_node, 'anchor-br', 'none')
        widgetex['left'] = self.__get_node_property(root_node, 'left', 0)
        widgetex['top'] = self.__get_node_property(root_node, 'top', 0)
        widgetex['width'] = self.__get_node_property(root_node, 'width', 0)
        widgetex['height'] = self.__get_node_property(root_node, 'height', 0)

        self.layout[layout_name]['widgets'].append(widgetex)

    def __get_node_property (self, node, property_name, default_value):
        if node.attrib.has_key (property_name):
            if node.attrib[property_name].lower() == 'true':
                return True
            elif node.attrib[property_name].lower() == 'false':
                return False
            return node.attrib[property_name]
        else:
            return default_value

    def __get_pixbuf_by_name (self, name):
        if name in self.pixbufs:
            return self.pixbufs[name]
        else:
            return None

    def __get_font_by_name (self, name):
        if name in self.fonts:
            return self.fonts[name]
        else:
            return None

    def __add_alpha_channel (self, pixbuf, alphacolor):
        if alphacolor.startswith ("#"):
            R, G, B = self.__hex_to_rgb(alphacolor)
        elif alphacolor.upper().startswith ("RGB"):
            alphacolor = alphacolor.strip().upper()
            regex = "^RGB\s*\(\s*(?P<R>\d+)\s*,\s*(?P<G>\d+)\s*,\s*(?P<B>\d+)\s*\)$"
            m = re.match (regex, alphacolor)
            if m is not None:
                R = int (m.group ("R"))
                G = int (m.group ("G"))
                B = int (m.group ("B"))
            else:
                return pixbuf

        return pixbuf.add_alpha (True, R, G, B)

    def __hex_to_rgb(self, value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))
