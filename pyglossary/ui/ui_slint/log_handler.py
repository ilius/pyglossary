# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option) any
# later version.

"""Logging handler that streams pyglossary records into the Slint console."""

from __future__ import annotations

import logging
import weakref
from typing import TYPE_CHECKING

from .utils import levelColor

if TYPE_CHECKING:
	from .ui import UI

__all__ = ["SlintLogHandler"]


class SlintLogHandler(logging.Handler):
	"""
	Log handler that feeds the on-screen Slint console.

	`emit` may run on any thread: it only formats plain strings and posts
	`UI._appendLog` via `UI._post`. The UI is held weakly so the logger global
	never keeps the UI (and its slint window) alive.
	"""

	def __init__(self, ui: UI) -> None:
		logging.Handler.__init__(self)
		self._ui = weakref.ref(ui)

	def emit(self, record: logging.LogRecord) -> None:
		ui = self._ui()
		if ui is None:
			return
		try:
			msg = self.format(record).strip()  # includes the traceback, if any
			if msg:
				color = levelColor(record.levelname)
				ui._post(lambda: ui._appendLog(msg, color))
		except Exception:  # noqa: BLE001 never raise from a log handler
			pass
