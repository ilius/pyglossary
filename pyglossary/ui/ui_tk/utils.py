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
from typing import TYPE_CHECKING, Any

from pyglossary.ui.base import logo

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"centerWindow",
	"decodeGeometry",
	"encodeGeometry",
	"encodeLocation",
	"newButton",
	"newLabelWithImage",
	"newReadOnlyText",
	"set_window_icon",
]


def set_window_icon(window: tk.Toplevel) -> None:
	window.iconphoto(
		True,
		tk.PhotoImage(file=logo),
	)


def newButton(
	master: tk.Widget,
	text: str,
	command: Callable,
	**kwargs: Any,
) -> ttk.Button:
	button = ttk.Button(
		master,
		text=text,
		command=command,
		**kwargs,
	)

	def onEnter(_event: tk.Event) -> None:
		button.invoke()

	button.bind("<Return>", onEnter)
	button.bind("<KP_Enter>", onEnter)
	return button


def newLabelWithImage(parent: tk.Widget, file: str = "") -> ttk.Label:
	image = tk.PhotoImage(file=file)
	label = ttk.Label(parent, image=image)
	# keep a reference:
	label.image = image
	return label


def newReadOnlyText(
	parent: tk.Widget,
	text: str = "",
	borderwidth: int = 10,
	font: tuple[str, int, str] = ("DejaVu Sans", 11, ""),
) -> tk.Text:
	height = len(text.strip().split("\n"))
	widget = tk.Text(
		parent,
		height=height,
		borderwidth=borderwidth,
		font=font,
	)
	widget.insert(1.0, text)
	widget.pack()

	# widget.bind("<Key>", lambda e: break)
	widget.configure(state=tk.DISABLED)

	return widget


def decodeGeometry(gs: str) -> tuple[int, int, int, int]:
	"""
	Example for gs: "253x252+30+684"
	returns (x, y, w, h).
	"""
	p = gs.split("+")
	w, h = p[0].split("x")
	return (int(p[1]), int(p[2]), int(w), int(h))


def encodeGeometry(x: int, y: int, w: int, h: int) -> str:
	return f"{w}x{h}+{x}+{y}"


def encodeLocation(x: int, y: int) -> str:
	return f"+{x}+{y}"


def centerWindow(win: tk.Tk) -> None:
	"""
	Centers a tkinter window
	:param win: the root or Toplevel window to center.
	"""
	win.update_idletasks()
	width = win.winfo_width()
	frm_width = win.winfo_rootx() - win.winfo_x()
	win_width = width + 2 * frm_width
	height = win.winfo_height()
	titlebar_height = win.winfo_rooty() - win.winfo_y()
	win_height = height + titlebar_height + frm_width
	x = win.winfo_screenwidth() // 2 - win_width // 2
	y = win.winfo_screenheight() // 2 - win_height // 2
	win.geometry(encodeGeometry(x, y, width, height))
	win.deiconify()
