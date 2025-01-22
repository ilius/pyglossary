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

from os.path import isabs, join
from typing import TYPE_CHECKING, Any

from gi.repository import Gdk as gdk  # noqa: I001
from gi.repository import GLib as glib
from gi.repository import Gtk as gtk

from pyglossary.core import appResDir

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"FixedSizePicture",
	"HBox",
	"VBox",
	"getWorkAreaSize",
	"gtk_event_iteration_loop",
	"hasLightTheme",
	"pack",
	"rgba_parse",
	"showInfo",
]


def getWorkAreaSize(_w: object) -> tuple[int, int]:
	display = gdk.Display.get_default()
	# monitor = display.get_monitor_at_surface(w.get_surface())
	# if monitor is None:
	monitor = display.get_primary_monitor()
	rect = monitor.get_workarea()
	return rect.width, rect.height


def gtk_event_iteration_loop() -> None:
	ctx = glib.MainContext.default()
	try:
		while ctx.pending():
			ctx.iteration(True)
	except KeyboardInterrupt:
		pass


def VBox(**kwargs: Any) -> gtk.Box:
	return gtk.Box(orientation=gtk.Orientation.VERTICAL, **kwargs)


def HBox(**kwargs: Any) -> gtk.Box:
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


class FixedSizePicture(gtk.Picture):
	def __init__(self, path: str) -> None:
		gtk.Picture.__init__(self)
		# self.size = size
		if not isabs(path):
			path = join(appResDir, path)
		self.set_filename(path)
		self.set_can_shrink(False)


def imageFromFile(path: str) -> gtk.Image:  # the file must exist
	if not isabs(path):
		path = join(appResDir, path)
	im = gtk.Image()
	im.set_from_file(path)
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
		return gtk.Image.new_from_icon_name(iconName)
	try:
		return gtk.Image.new_from_stock(iconName, size)
	except Exception:
		return gtk.Image.new_from_icon_name(iconName)


def rgba_parse(colorStr: str) -> gdk.RGBA:
	rgba = gdk.RGBA()
	if not rgba.parse(colorStr):
		raise ValueError(f"bad color string {colorStr!r}")
	return rgba


def pack(
	box: gtk.Box | gtk.CellLayout,
	child: gtk.Widget | gtk.CellRenderer,
	expand: bool | int = False,
	fill: bool | int = False,  # noqa: ARG001
	padding: int = 0,
) -> None:  # noqa: ARG001
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


def newButtonImageBox(label: str, image: gtk.Image, spacing: int = 0) -> gtk.Box:
	hbox = HBox(spacing=spacing)
	pack(hbox, image, 0, 0)
	if label:
		labelObj = gtk.Label(label=label)
		labelObj.set_use_underline(True)
		labelObj.set_xalign(0)
		pack(hbox, labelObj, 0, 0)
	hbox.show()
	return hbox


buttonIconEnable = True
buttonIconSize = 20


def labelIconButton(
	label: str = "",
	iconName: str = "",
	size: gtk.IconSize = gtk.IconSize.NORMAL,
) -> gtk.Button:
	button = gtk.Button()
	if buttonIconEnable:
		button.set_child(
			newButtonImageBox(
				label,
				imageFromIconName(iconName, size),
				spacing=size / 2,
			),
		)
		return button
	button.set_label(label)
	button.set_use_underline(True)
	return button


def labelImageButton(  # noqa: PLR0913
	label: str = "",
	imageName: str = "",
	size: int = 0,
	func: Callable | None = None,
	tooltip: str = "",
	spacing: int = 10,
) -> gtk.Button:
	button = gtk.Button()
	if buttonIconEnable or not label:
		if size == 0:
			size = buttonIconSize
		button.set_child(
			newButtonImageBox(
				label,
				imageFromFile(imageName, size=size),
				spacing=spacing,
			),
		)
		# TODO: the child(HBox) is not centered in the Button
		# problem can be seen in Preferences window: Apply and OK buttons
		# button.set_alignment(0.5, 0.5)
	else:
		button.set_label(label)
		button.set_use_underline(True)
	if func is not None:
		button.connect("clicked", func)
	if tooltip:
		button.set_tooltip_text(tooltip)
	return button


class MyHButtonBox(gtk.Box):
	def __init__(self) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.get_style_context().add_class("margin_10")
		self._homogeneous = True

	def set_homogeneous(self, homogeneous: bool) -> None:
		# gtk.ButtonBox.set_homogeneous does not work anymore!
		# not sure since when
		self._homogeneous = homogeneous

	def add(self, child: gtk.Widget) -> None:
		self.append(child)  # or prepend?
		if not self._homogeneous:
			self.set_child_non_homogeneous(child, True)
			# New in gi version 3.2.

	def add_button(
		self,
		iconName: str = "",
		imageName: str = "",
		label: str = "",
		onClick: Callable | None = None,
		tooltip: str = "",
	) -> gtk.Button:
		if imageName:
			b = labelImageButton(
				label=label,
				imageName=imageName,
			)
		else:
			b = labelIconButton(
				label,
				iconName,
				gtk.IconSize.NORMAL,
			)
		if onClick:
			b.connect("clicked", onClick)
		if tooltip:
			b.set_tooltip_text(tooltip)
		self.add(b)
		return b

	def add_ok(self, onClick: Callable | None = None) -> gtk.Button:
		return self.add_button(
			# imageName="dialog-ok.svg",
			label="_Confirm",
			onClick=onClick,
		)

	def add_cancel(self, onClick: Callable | None = None) -> gtk.Button:
		return self.add_button(
			# imageName="dialog-cancel.svg",
			label="Cancel",
			onClick=onClick,
		)


def showMsg(  # noqa: PLR0913
	msg: str,
	iconName: str = "",
	parent: gtk.Window | None = None,
	transient_for: gtk.Widget | None = None,
	title: str = "",
	borderWidth: int = 10,  # noqa: ARG001
	iconSize: gtk.IconSize = gtk.IconSize.LARGE,
	selectable: bool = False,
) -> None:
	win = gtk.Window(
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
	vbox = VBox()
	pack(vbox, hbox, 1, 1)

	def onOkClicked(_button: gtk.Button) -> None:
		win.destroy()

	buttonBox = MyHButtonBox()
	buttonBox.add_ok(onClick=onOkClicked)
	hbox2 = HBox()
	pack(hbox2, gtk.Label(), 1, 1)
	pack(hbox2, buttonBox, 0, 0)
	pack(vbox, hbox2, 0, 0)

	win.set_child(vbox)
	# win.resize(600, 1)
	win.show()


def _getLightness(c: gdk.Color) -> float:
	return (max(c.red, c.green, c.blue) + min(c.red, c.green, c.blue)) / 2


def hasLightTheme(widget: gtk.Widget) -> bool:
	fg = widget.get_color()
	# bg = ... no idea how to get it in Gtk4
	# return _getLightness(fg) < _getLightness(bg)
	return _getLightness(fg) < 0.5


def showInfo(msg, **kwargs: Any) -> None:  # noqa: ANN001
	showMsg(msg, iconName="dialog-information", **kwargs)


# def showError(msg, **kwargs) -> None:  # noqa: ANN001
# 	showMsg(msg, iconName="dialog-error", **kwargs)
