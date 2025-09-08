from __future__ import annotations

from typing import TYPE_CHECKING

from gi.repository import Gtk as gtk

from .log_handler import GtkSingleTextviewLogHandler
from .utils import rgba_parse

if TYPE_CHECKING:
	import logging

	from .log_handler import MainWinType

__all__ = ["ConvertConsole"]


class ConvertConsole(gtk.ScrolledWindow):
	def __init__(
		self,
		mainWin: MainWinType,
		lightTheme: bool = False,
	) -> None:
		gtk.ScrolledWindow.__init__(self)
		self.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		self._textview = textview = gtk.TextView()
		self.set_child(textview)
		##########
		textview.get_style_context().add_class("console")
		self._handler = handler = GtkSingleTextviewLogHandler(mainWin, textview)
		###
		normalColor = rgba_parse("black" if lightTheme else "white")
		errorColor = rgba_parse("red")
		warningColor = rgba_parse("hsl(30, 100%, 50%)" if lightTheme else "yellow")
		###
		handler.setColor("CRITICAL", errorColor)
		handler.setColor("ERROR", errorColor)
		handler.setColor("WARNING", warningColor)
		handler.setColor("INFO", normalColor)
		handler.setColor("DEBUG", normalColor)
		handler.setColor("TRACE", normalColor)
		###
		textview.get_buffer().set_text("Output & Error Console:\n")
		textview.set_editable(False)

	@property
	def handler(self) -> logging.Handler:
		return self._handler

	def set_text(self, text: str) -> None:
		self._textview.get_buffer().set_text(text)
