# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING, Protocol

from gi.repository import Gtk as gtk

if TYPE_CHECKING:
	from gi.repository import Gdk as gdk

__all__ = ["GtkSingleTextviewLogHandler", "MainWinType"]

log = logging.getLogger("pyglossary")


class MainWinType(Protocol):
	def status(self, msg: str) -> None: ...


class GtkTextviewLogHandler(logging.Handler):
	def __init__(
		self,
		mainWin: MainWinType,
		textview_dict: dict[str, gtk.TextView],
	) -> None:
		logging.Handler.__init__(self)

		self.mainWin = mainWin
		self.buffers = {}
		for levelNameCap in log.levelNamesCap[:-1]:
			levelName = levelNameCap.upper()
			textview = textview_dict[levelName]

			buff = textview.get_buffer()
			tag = gtk.TextTag.new(levelName)
			buff.get_tag_table().add(tag)

			self.buffers[levelName] = buff

	def getTag(self, levelname: str) -> gtk.TextTag:
		return self.buffers[levelname].get_tag_table().lookup(levelname)

	def setColor(self, levelname: str, rgba: gdk.RGBA) -> None:
		self.getTag(levelname).set_property("foreground-rgba", rgba)
		# foreground-gdk is deprecated since Gtk 3.4

	def emit(self, record: logging.LogRecord) -> None:
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		# msg = msg.replace("\x00", "")

		if record.exc_info:
			type_, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(type_, value, tback),
			)
			if msg:
				msg += "\n"
			msg += tback_text

		buff = self.buffers[record.levelname]

		buff.insert_with_tags_by_name(
			buff.get_end_iter(),
			msg + "\n",
			record.levelname,
		)

		if record.levelno == logging.CRITICAL:
			self.mainWin.status(record.getMessage())


class GtkSingleTextviewLogHandler(GtkTextviewLogHandler):
	def __init__(self, mainWin: MainWinType, textview: gtk.TextView) -> None:
		GtkTextviewLogHandler.__init__(
			self,
			mainWin,
			{
				"CRITICAL": textview,
				"ERROR": textview,
				"WARNING": textview,
				"INFO": textview,
				"DEBUG": textview,
				"TRACE": textview,
			},
		)
