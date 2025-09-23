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

from typing import Any

from gi.repository import Gtk as gtk

from .utils import (
	FixedSizePicture,
	VBox,
	pack,
)

__all__ = ["AboutWidget"]


class AboutTabTitleBox(gtk.Box):
	def __init__(self, title: str, icon: str) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.set_spacing(10)
		pack(self, VBox(), expand=0)
		if icon:
			pack(self, FixedSizePicture(icon))
		if title:
			pack(self, gtk.Label(label=title), expand=0)
		pack(self, VBox(), expand=0)

	# def do_get_preferred_height_for_width(self, size: int) -> tuple[int, int]:
	# 	height = int(size * 1.5)
	# 	return height, height

	# returns: (minimum: int, natural: int,
	# 	minimum_baseline: int, natural_baseline: int)
	# def do_measure(self, orientation, for_size):
	# 	return (for_size, for_size, for_size, for_size)


class AboutWidget(gtk.Box):
	def __init__(  # noqa: PLR0913
		self,
		logo: str = "",
		header: str = "",
		about: str = "",
		authors: str = "",
		license_text: str = "",
		**_kwargs: Any,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.set_spacing(15)
		##
		headerBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		headerBox.set_spacing(20)
		if logo:
			pack(headerBox, gtk.Label())
			pack(headerBox, FixedSizePicture(logo))
		headerLabel = gtk.Label(label=header)
		headerLabel.set_selectable(True)
		pack(headerBox, headerLabel)
		headerBox.show()
		pack(self, headerBox)
		##
		notebook = gtk.Notebook()
		self.notebook = notebook
		pack(self, notebook, expand=True)
		notebook.set_tab_pos(gtk.PositionType.LEFT)
		##
		tab1_about = self.newTabLabelWidget(about, wrap=True)
		# ^ it keeps selecting all text in this label when I switch back to this tab
		# with textview, it does not automatically render hyperlink (<a>)
		tab2_authors = self.newTabWidgetTextView(authors, wrap=True)
		tab3_license = self.newTabWidgetTextView(license_text, wrap=True)
		##
		tabs = [
			(tab1_about, self.newTabTitle("About", "dialog-information-22.png")),
			(tab2_authors, self.newTabTitle("Authors", "author-22.png")),
			(tab3_license, self.newTabTitle("License", "license-22.png")),
		]
		##
		for widget, titleW in tabs:
			notebook.append_page(widget, titleW)
		##
		self.show()

	# <a href="...">Something</a> does not work with TextView
	@staticmethod
	def newTabWidgetTextView(
		text: str,
		wrap: bool = False,
		justification: gtk.Justification | None = None,
	) -> gtk.ScrolledWindow:
		tv = gtk.TextView()
		if wrap:
			tv.set_wrap_mode(gtk.WrapMode.WORD)
		if justification is not None:
			tv.set_justification(justification)
		tv.set_cursor_visible(False)
		# tv.set_border_width(10)
		buf = tv.get_buffer()
		# buf.insert_markup(buf.get_end_iter(), markup=text,
		# len=len(text.encode("utf-8")))
		buf.set_text(text)
		tv.show()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		# swin.set_border_width(0)
		swin.set_child(tv)
		return swin

	@staticmethod
	def newTabLabelWidget(
		text: str,
		wrap: bool = False,
		# justification: "gtk.Justification | None" = None,
	) -> gtk.ScrolledWindow:
		box = VBox()
		# box.set_border_width(10)
		label = gtk.Label()
		label.set_selectable(True)
		label.set_xalign(0)
		label.set_yalign(0)
		label.set_wrap(wrap)
		pack(box, label, 0, 0)
		# if wrap:
		# 	tv.set_wrap_mode(gtk.WrapMode.WORD)
		# if justification is not None:
		# 	tv.set_justification(justification)
		# label.set_cursor_visible(False)
		# label.set_border_width(10)
		label.set_markup(text)
		label.show()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		# swin.set_border_width(0)
		swin.set_child(box)
		return swin

	@staticmethod
	def newTabTitle(title: str, icon: str) -> AboutTabTitleBox:
		return AboutTabTitleBox(title, icon)
