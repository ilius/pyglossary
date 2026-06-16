# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

import logging
import traceback

import wx

__all__ = ["WxLogHandler"]


class WxLogHandler(logging.Handler):
	def __init__(self, text_widget: wx.TextCtrl) -> None:
		super().__init__()
		self._tw = text_widget
		self._colors = {
			"CRITICAL": wx.Colour(255, 102, 102),
			"ERROR": wx.Colour(255, 102, 102),
			"WARNING": wx.Colour(255, 238, 102),
			"INFO": wx.Colour(102, 204, 102),
			"DEBUG": wx.Colour(204, 204, 204),
			"TRACE": wx.Colour(204, 204, 204),
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
		color = self._colors.get(record.levelname, wx.Colour(255, 255, 255))
		self._tw.SetDefaultStyle(wx.TextAttr(color))
		self._tw.AppendText(msg.rstrip("\n") + "\n")
