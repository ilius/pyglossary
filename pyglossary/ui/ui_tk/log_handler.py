# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import tkinter as tk

__all__ = ["TkTextLogHandler"]


class TkTextLogHandler(logging.Handler):
	def __init__(self, tktext: tk.Text) -> None:
		logging.Handler.__init__(self)
		#####
		tktext.tag_config("CRITICAL", foreground="#ff0000")
		tktext.tag_config("ERROR", foreground="#ff0000")
		tktext.tag_config("WARNING", foreground="#ffff00")
		tktext.tag_config("INFO", foreground="#00ff00")
		tktext.tag_config("DEBUG", foreground="#ffffff")
		tktext.tag_config("TRACE", foreground="#ffffff")
		###
		self.tktext = tktext

	def emit(self, record: logging.LogRecord) -> None:
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		###
		if record.exc_info:
			type_, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(type_, value, tback),
			)
			if msg:
				msg += "\n"
			msg += tback_text
		###
		self.tktext.insert(
			"end",
			msg + "\n",
			record.levelname,
		)
