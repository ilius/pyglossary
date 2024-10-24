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

from pyglossary.core import appResDir

from . import gdk, glib, gtk

__all__ = [
	"HBox",
	"VBox",
	"dialog_add_button",
	"gtk_event_iteration_loop",
	"gtk_window_iteration_loop",
	"imageFromFile",
	"pack",
	"rgba_parse",
	"set_tooltip",
	"showInfo",
]

log = logging.getLogger("pyglossary")


def gtk_window_iteration_loop():
	try:
		while gtk.Window.get_toplevels():
			glib.MainContext.default().iteration(True)
	except KeyboardInterrupt:
		pass


def gtk_event_iteration_loop():
	ctx = glib.MainContext.default()
	try:
		while ctx.pending():
			ctx.iteration(True)
	except KeyboardInterrupt:
		pass


def VBox(**kwargs):
	return gtk.Box(orientation=gtk.Orientation.VERTICAL, **kwargs)


def HBox(**kwargs):
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


def set_tooltip(widget, text):
	try:
		widget.set_tooltip_text(text)  # PyGTK 2.12 or above
	except AttributeError:
		try:
			widget.set_tooltip(gtk.Tooltips(), text)
		except Exception:
			log.exception("")


def imageFromFile(path):  # the file must exist
	if not isabs(path):
		path = join(appResDir, path)
	im = gtk.Image()
	try:
		im.set_from_file(path)
	except Exception:
		log.exception("")
	return im


def imageFromIconName(iconName: str, size: int, nonStock=False) -> gtk.Image:
	# So gtk.Image.new_from_stock is deprecated
	# And the doc says we should use gtk.Image.new_from_icon_name
	# which does NOT have the same functionality!
	# because not all stock items are existing in all themes (even popular themes)
	# and new_from_icon_name does not seem to look in other (non-default) themes!
	# So for now we use new_from_stock, unless it's not a stock item
	# But we do not use either of these two outside this function
	# So that it's easy to switch
	if nonStock:
		return gtk.Image.new_from_icon_name(iconName)
	try:
		return gtk.Image.new_from_stock(iconName, size)
	except Exception:
		return gtk.Image.new_from_icon_name(iconName)


def rgba_parse(colorStr):
	rgba = gdk.RGBA()
	if not rgba.parse(colorStr):
		raise ValueError(f"bad color string {colorStr!r}")
	return rgba


def color_parse(colorStr):
	return rgba_parse(colorStr).to_color()


def pack(box, child, expand=False, fill=False, padding=0):  # noqa: ARG001
	if padding > 0:
		print(f"pack: padding={padding} ignored")
	if isinstance(box, gtk.Box):
		box.append(child)
		if expand:
			if box.get_orientation() == gtk.Orientation.VERTICAL:
				child.set_vexpand(True)
			else:
				child.set_hexpand(True)
		# FIXME: what to do with: fill, padding
	elif isinstance(box, gtk.CellLayout):
		box.pack_start(child, expand)
	else:
		raise TypeError(f"pack: unknown type {type(box)}")


def dialog_add_button(
	dialog,
	_iconName,
	label,
	resId,
	onClicked=None,
	tooltip="",
):
	button = gtk.Button(
		label=label,
		use_underline=True,
		# icon_name=iconName,
	)
	# fixed bug: used to ignore resId and pass gtk.ResponseType.OK
	dialog.add_action_widget(
		button,
		resId,
	)
	if onClicked:
		label.connect("clicked", onClicked)
	if tooltip:
		set_tooltip(label, tooltip)
	return label


def showMsg(  # noqa: PLR0913
	msg,
	iconName="",
	parent=None,
	transient_for=None,
	title="",
	borderWidth=10,  # noqa: ARG001
	iconSize=gtk.IconSize.LARGE,
	selectable=False,
):
	win = gtk.Dialog(
		parent=parent,
		transient_for=transient_for,
	)
	# flags=0 makes it skip task bar
	if title:
		win.set_title(title)
	hbox = HBox(spacing=10)
	# hbox.set_border_width(borderWidth)
	if iconName:
		# win.set_icon(...)
		pack(hbox, imageFromIconName(iconName, iconSize))
	label = gtk.Label(label=msg)
	# set_line_wrap(True) makes the window go crazy tall (taller than screen)
	# and that's the reason for label.set_size_request and win.resize
	# label.set_line_wrap(True)
	# label.set_line_wrap_mode(pango.WrapMode.WORD)
	label.set_size_request(500, 1)
	if selectable:
		label.set_selectable(True)
	pack(hbox, label)
	hbox.show()
	content_area = win.get_content_area()
	pack(content_area, hbox)
	dialog_add_button(
		win,
		"gtk-close",
		"_Close",
		gtk.ResponseType.OK,
	)

	def onResponse(_w, _response_id):
		win.destroy()

	win.connect("response", onResponse)

	# win.resize(600, 1)
	win.show()


def showError(msg, **kwargs):
	# gtk-dialog-error is deprecated since version 3.10:
	# Use named icon “dialog-error”.
	showMsg(msg, iconName="gtk-dialog-error", **kwargs)


def showWarning(msg, **kwargs):
	# gtk-dialog-warning is deprecated since version 3.10:
	# Use named icon “dialog-warning”.
	showMsg(msg, iconName="gtk-dialog-warning", **kwargs)


def showInfo(msg, **kwargs):
	# gtk-dialog-info is deprecated since version 3.10:
	# Use named icon “dialog-information”.
	showMsg(msg, iconName="gtk-dialog-info", **kwargs)
