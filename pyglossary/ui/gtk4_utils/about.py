# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from . import gtk
from .utils import (
	VBox,
	imageFromFile,
	pack,
)

__all__ = ["AboutWidget"]


class AboutTabTitleBox(gtk.Box):
	def __init__(self, title: str, icon: str) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.set_spacing(10)
		pack(self, VBox(), expand=0)
		if icon:
			image = imageFromFile(icon)
			image.get_pixel_size()
			image.set_size_request(24, 24)
			# I don't know how to stop Gtk from resizing the image
			# I should probably use svg files to avoid blurry images
			pack(self, image, expand=0)
		if title:
			pack(self, gtk.Label(label=title), expand=0)
		pack(self, VBox(), expand=0)
		self.set_size_request(60, 60)

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
		**_kwargs,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.set_spacing(15)
		##
		headerBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if logo:
			pack(headerBox, imageFromFile(logo))
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
		tab1_about = self.newTabLabelWidget(about)
		tab2_authors = self.newTabWidgetTextView(authors)
		tab3_license = self.newTabWidgetTextView(license_text)
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
	):
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
		# wrap: bool = False,
		# justification: "gtk.Justification | None" = None,
	):
		box = VBox()
		# box.set_border_width(10)
		label = gtk.Label()
		label.set_selectable(True)
		label.set_xalign(0)
		label.set_yalign(0)
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
	def newTabTitle(title: str, icon: str):
		return AboutTabTitleBox(title, icon)
