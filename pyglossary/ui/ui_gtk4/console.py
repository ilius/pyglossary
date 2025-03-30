import logging

from gi.repository import Gtk as gtk

from pyglossary.ui.ui_gtk4.log_handler import GtkSingleTextviewLogHandler, MainWinType
from pyglossary.ui.ui_gtk4.utils import rgba_parse


class ConvertConsole(gtk.ScrolledWindow):
	def __init__(self, mainWin: MainWinType) -> None:
		gtk.ScrolledWindow.__init__(self)
		self.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		self._textview = textview = gtk.TextView()
		self.set_child(textview)
		##########
		textview.get_style_context().add_class("console")
		self._handler = handler = GtkSingleTextviewLogHandler(mainWin, textview)
		###
		handler.setColor("CRITICAL", rgba_parse("red"))
		handler.setColor("ERROR", rgba_parse("red"))
		handler.setColor("WARNING", rgba_parse("yellow"))
		handler.setColor("INFO", rgba_parse("white"))
		handler.setColor("DEBUG", rgba_parse("white"))
		handler.setColor("TRACE", rgba_parse("white"))
		###
		textview.get_buffer().set_text("Output & Error Console:\n")
		textview.set_editable(False)

	@property
	def handler(self) -> logging.Handler:
		return self._handler

	def set_text(self, text: str) -> None:
		self._textview.get_buffer().set_text(text)
