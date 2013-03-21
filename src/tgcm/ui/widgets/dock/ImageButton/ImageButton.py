import gtk
import gobject

class ImageButton (gtk.EventBox):

    __gsignals__ = {'clicked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                 (gobject.TYPE_PYOBJECT,))
                   }

    def __init__ (self, image):
        gtk.EventBox.__init__(self)
        self.set_visible_window (False)

        self.image_filename, dot, self.image_extension = image.rpartition ('.')

        self.normal_pixbuf = gtk.gdk.pixbuf_new_from_file ("%s_normal.%s" % (self.image_filename, self.image_extension))
        self.over_pixbuf = gtk.gdk.pixbuf_new_from_file ("%s_over.%s" % (self.image_filename, self.image_extension))
        self.click_pixbuf = gtk.gdk.pixbuf_new_from_file ("%s_click.%s" % (self.image_filename, self.image_extension))

        self.text = ""
        self.text_color = "#ffffff"
        self.centered = True
        self.size = "medium"
        self.__reload (self.normal_pixbuf)

        self.pressed = False

    def set_image (self, image):
        self.image_filename, dot, self.image_extension = image.rpartition ('.')

        self.normal_pixbuf = gtk.gdk.pixbuf_new_from_file ("%s_normal.%s" % (self.image_filename, self.image_extension))
        self.over_pixbuf = gtk.gdk.pixbuf_new_from_file ("%s_over.%s" % (self.image_filename, self.image_extension))
        self.click_pixbuf = gtk.gdk.pixbuf_new_from_file ("%s_click.%s" % (self.image_filename, self.image_extension))

        self.__reload(self.normal_pixbuf)

    def set_text (self, text, centered=True, color=None, size="medium"):
        self.text = text
        if color != None:
            self.text_color = color
        self.centered = centered
        self.size = size
        self.__reload(self.normal_pixbuf)

    def __reload (self, pixbuf):
        child = self.get_child ()
        if child is not None:
            self.remove (child)

        drawable, mask = pixbuf.render_pixmap_and_mask()
        textLay = self.create_pango_layout('')
        textLay.set_markup ('<span color="%s" size="%s">%s</span>' % (self.text_color, self.size, self.text))
        text_w, text_h = textLay.get_pixel_size()
        dw_w, dw_h = drawable.get_size ()
        if self.centered:
            x = dw_w/2 - text_w/2
            y = dw_h/2 - text_h/2
        else:
            x = 10
            y = dw_h/2 - text_h/2
        
        drawable.draw_layout(drawable.new_gc(), x, y, textLay, None, None)
        self.image = gtk.image_new_from_pixmap(drawable, mask)

        self.add (self.image)
        self.show_all()
        
    def do_enter_notify_event (self, event):
        self.__reload (self.over_pixbuf)
        return True

    def do_leave_notify_event (self, event):
        self.__reload (self.normal_pixbuf)
        if self.pressed:
            self.pressed = False 
        return True

    def do_button_press_event (self, event):
        if event.button == 1:
            self.__reload (self.click_pixbuf)
            self.pressed = True
        return False 

    def do_button_release_event (self, event):
        if self.pressed and event.button == 1:
            self.__reload (self.normal_pixbuf)
            self.pressed = False 
            self.emit ('clicked', self)
        return False 

