# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2016-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from os.path import isabs, join
from typing import TYPE_CHECKING

from gi.repository import Pango as pango

from pyglossary.core import appResDir

from . import gdk, gtk

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"HBox",
	"VBox",
	"dialog_add_button",
	"imageFromFile",
	"pack",
	"rgba_parse",
	"showInfo",
]

log = logging.getLogger("pyglossary")


def VBox(**kwargs) -> gtk.Box:
	return gtk.Box(orientation=gtk.Orientation.VERTICAL, **kwargs)


def HBox(**kwargs) -> gtk.Box:
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


def imageFromFile(path: str) -> gtk.Image:  # the file must exist
	if not isabs(path):
		path = join(appResDir, path)
	im = gtk.Image()
	try:
		im.set_from_file(path)
	except Exception:
		log.exception("")
	return im


def imageFromIconName(iconName: str, size: int, nonStock: bool = False) -> gtk.Image:
	# So gtk.Image.new_from_stock is deprecated
	# And the doc says we should use gtk.Image.new_from_icon_name
	# which does NOT have the same functionality!
	# because not all stock items are existing in all themes (even popular themes)
	# and new_from_icon_name does not seem to look in other (non-default) themes!
	# So for now we use new_from_stock, unless it's not a stock item
	# But we do not use either of these two outside this function
	# So that it's easy to switch
	if nonStock:
		return gtk.Image.new_from_icon_name(iconName, size)
	try:
		return gtk.Image.new_from_stock(iconName, size)
	except Exception:
		return gtk.Image.new_from_icon_name(iconName, size)


def rgba_parse(colorStr: str) -> gdk.RGBA:
	rgba = gdk.RGBA()
	if not rgba.parse(colorStr):
		raise ValueError(f"bad color string {colorStr!r}")
	return rgba


def pack(
	box: gtk.Box | gtk.CellLayout,
	child: gtk.Widget | gtk.CellRenderer,
	expand: bool = False,
	fill: bool = False,
	padding: int = 0,
) -> None:
	if isinstance(box, gtk.Box):
		box.pack_start(child, expand, fill, padding)
	elif isinstance(box, gtk.CellLayout):
		box.pack_start(child, expand)
	else:
		raise TypeError(f"pack: unknown type {type(box)}")


def dialog_add_button(
	dialog: gtk.Dialog,
	_iconName: str,  # TODO: remove
	label: str,
	resId: int,
	onClicked: Callable | None = None,
	tooltip: str = "",
) -> None:
	b = dialog.add_button(label, resId)
	if onClicked:
		b.connect("clicked", onClicked)
	if tooltip:
		b.set_tooltip_text(tooltip)


def showMsg(  # noqa: PLR0913
	msg: str,
	iconName: str = "",
	parent: gtk.Widget | None = None,
	transient_for: gtk.Widget | None = None,
	title: str = "",
	borderWidth: int = 10,
	iconSize: gtk.IconSize = gtk.IconSize.DIALOG,
	selectable: bool = False,
) -> None:
	win = gtk.Dialog(
		parent=parent,
		transient_for=transient_for,
	)
	# flags=0 makes it skip task bar
	if title:
		win.set_title(title)
	hbox = HBox(spacing=10)
	hbox.set_border_width(borderWidth)
	if iconName:
		# win.set_icon(...)
		pack(hbox, imageFromIconName(iconName, iconSize))
	label = gtk.Label(label=msg)
	# set_line_wrap(True) makes the window go crazy tall (taller than screen)
	# and that's the reason for label.set_size_request and win.resize
	label.set_line_wrap(True)
	label.set_line_wrap_mode(pango.WrapMode.WORD)
	label.set_size_request(500, 1)
	if selectable:
		label.set_selectable(True)
	pack(hbox, label)
	hbox.show_all()
	pack(win.vbox, hbox)
	dialog_add_button(
		win,
		"gtk-close",
		"_Close",
		gtk.ResponseType.OK,
	)
	win.resize(600, 1)
	win.run()
	win.destroy()


def showError(msg, **kwargs) -> None:  # noqa: ANN001
	# gtk-dialog-error is deprecated since version 3.10:
	# Use named icon “dialog-error”.
	showMsg(msg, iconName="gtk-dialog-error", **kwargs)


def showWarning(msg, **kwargs) -> None:  # noqa: ANN001
	# gtk-dialog-warning is deprecated since version 3.10:
	# Use named icon “dialog-warning”.
	showMsg(msg, iconName="gtk-dialog-warning", **kwargs)


def showInfo(msg, **kwargs) -> None:  # noqa: ANN001
	# gtk-dialog-info is deprecated since version 3.10:
	# Use named icon “dialog-information”.
	showMsg(msg, iconName="gtk-dialog-info", **kwargs)
