# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Slint UI log handler: forwards pyglossary log records onto the on-screen
# console, marshalled onto the Slint event-loop thread.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option) any
# later version.

from __future__ import annotations

import logging
import traceback
import weakref
from typing import TYPE_CHECKING

from .utils import levelColor

if TYPE_CHECKING:
	from .ui import UI

__all__ = ["SlintLogHandler"]


class SlintLogHandler(logging.Handler):
	"""
	Log handler that feeds the on-screen Slint console.

	``emit`` may run on the conversion worker thread (or any other thread that
	logs). It performs only plain-Python work -- formatting the record and
	picking a color name -- and then funnels the line through ``UI._post``,
	which schedules ``UI._appendLog`` on the Slint event-loop thread via
	``slint.native.invoke_from_event_loop``. The ``slint.Color`` is built inside
	``_appendLog`` (on the event-loop thread), so no slint object is ever
	touched on the worker thread.

	The UI is referenced *weakly*: this handler stays registered on the
	module-level "pyglossary" logger for the life of the process, and a strong
	reference here would pin the UI -- and, through it, the main window and
	console list model (unsendable slint objects) -- until interpreter
	finalization, which is exactly the shutdown scenario the rest of this
	module works to avoid. Once the UI is gone, ``emit`` becomes a silent
	no-op.
	"""

	def __init__(self, ui: "UI") -> None:
		logging.Handler.__init__(self)
		self._ui = weakref.ref(ui)

	def emit(self, record: logging.LogRecord) -> None:
		try:
			msg = ""
			if record.getMessage():
				msg = self.format(record)
			if record.exc_info:
				type_, value, tback = record.exc_info
				if msg:
					msg += "\n"
				msg += "".join(traceback.format_exception(type_, value, tback))
			if not msg:
				return
			color = levelColor(record.levelname)
			ui = self._ui()
			if ui is None:
				return
			ui._post(lambda m=msg, c=color: ui._appendLog(m, c))
		except Exception:  # noqa: BLE001 never raise from a log handler
			pass

	def flush(self) -> None:  # noqa: PLR6301 nothing to flush
		pass
