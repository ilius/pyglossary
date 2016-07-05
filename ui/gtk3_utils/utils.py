from . import *
from os.path import isabs, join
from pyglossary.core import appResDir


def set_tooltip(widget, text):
    try:
        widget.set_tooltip_text(text)  # PyGTK 2.12 or above
    except AttributeError:
        try:
            widget.set_tooltip(gtk.Tooltips(), text)
        except:
            myRaise(__file__)


def imageFromFile(path):  # the file must exist
    if not isabs(path):
        path = join(appResDir, path)
    im = gtk.Image()
    try:
        im.set_from_file(path)
    except:
        myRaise()
    return im
