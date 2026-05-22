# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

import html
import logging
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .qt_imports import QPlainTextEdit

__all__ = ["QtLogHandler"]


class QtLogHandler(logging.Handler):
	def __init__(self, text_widget: QPlainTextEdit) -> None:
		super().__init__()
		self._tw = text_widget
		self._colors = {
			"CRITICAL": "#ff6666",
			"ERROR": "#ff6666",
			"WARNING": "#ffee66",
			"INFO": "#66cc66",
			"DEBUG": "#cccccc",
			"TRACE": "#cccccc",
		}

	def emit(self, record: logging.LogRecord) -> None:
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		if record.exc_info:
			type_, value, tback = record.exc_info
			tback_text = "".join(traceback.format_exception(type_, value, tback))
			msg = msg + "\n" + tback_text if msg else tback_text
		if not msg:
			return
		color = self._colors.get(record.levelname, "#ffffff")
		escaped = html.escape(msg.rstrip("\n")).replace("\n", "<br/>")
		self._tw.appendHtml(f'<span style="color:{color}">{escaped}</span>')
