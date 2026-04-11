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

import tkinter as tk
from tkinter import ttk

__all__ = ["ProgressBar"]


class ProgressBar(ttk.Frame):
	def __init__(  # noqa: PLR0913
		self,
		rootWin: tk.Tk,
		min_: float,
		max_: float,
		width: int,
		height: int,
		appearance: str,  # "sunken"
		fillColor: str,
		background: str,
		labelColor: str,
		labelFont: str,
		value: float = 0,
	) -> None:
		self.min = min_
		self.max = max_
		self.width = width
		self.height = height
		self.value = value
		ttk.Frame.__init__(
			self,
			rootWin,
			relief=appearance,
		)
		self.canvas = tk.Canvas(
			self,
			height=height,
			width=width,
			bd=0,
			highlightthickness=0,
			background=background,
		)
		self.scale = self.canvas.create_rectangle(
			0,
			0,
			width,
			height,
			fill=fillColor,
		)
		self.label = self.canvas.create_text(
			width / 2,
			height / 2,
			text="",
			anchor="center",
			fill=labelColor,
			font=labelFont,
		)
		self.update()
		self.bind("<Configure>", self.update)
		self.canvas.pack(side="top", fill="x", expand=False)

	def updateProgress(
		self,
		value: float,
		max_: float | None = None,
		text: str = "",
	) -> None:
		if max_:
			self.max = max_
		self.value = value
		self.update(None, text)

	def update(self, event: tk.Event | None = None, labelText: str = "") -> None:
		if event:  # instance of tkinter.Event
			width = getattr(event, "width", None) or int(self.winfo_width())
			if width != self.width:  # window is resized
				self.canvas.coords(self.label, width / 2, self.height / 2)
				self.width = width
		else:
			width = self.width

		self.canvas.coords(
			self.scale,
			0,
			0,
			width * max(min(self.value, self.max), self.min) / self.max,
			self.height,
		)

		if labelText:
			# TODO: replace below `// 10` with a number based on current font size
			self.canvas.itemconfig(
				self.label,
				text=labelText[: width // 10],
			)

		self.canvas.update_idletasks()


# class VerticalProgressBar(ProgressBar):
# def update(self, event=None, labelText="") -> None:
# ...
# self.canvas.coords(
# 	self.scale,
# 	0,
# 	self.height * (1 - value / self.max),
# 	width,
# 	self.height,
# )
