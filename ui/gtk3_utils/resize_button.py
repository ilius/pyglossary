from . import *
from .utils import *


class ResizeButton(gtk.EventBox):
    def __init__(self, win, edge=gdk.WindowEdge.SOUTH_EAST):
        gtk.EventBox.__init__(self)
        self.win = win
        self.edge = edge
        ###
        self.image = imageFromFile('resize.png')
        self.add(self.image)
        self.connect('button-press-event', self.buttonPress)

    def buttonPress(self, obj, gevent):
        self.win.begin_resize_drag(
            self.edge,
            gevent.button,
            int(gevent.x_root),
            int(gevent.y_root),
            gevent.time,
        )
