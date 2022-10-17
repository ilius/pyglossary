# -*- coding: utf-8 -*-
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

from . import *
from .utils import (
	imageFromFile,
	VBox,
	pack,
)


class AboutTabTitleBox(gtk.Box):
	def __init__(self, title: str, icon: str):
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.set_spacing(8)
		pack(self, gtk.Label())
		if icon:
			pack(self, imageFromFile(icon), expand=0)
		if title:
			pack(self, gtk.Label(label=title), expand=0)
		pack(self, gtk.Label())
		self.set_size_request(80, 80)

	#def do_get_preferred_height_for_width(self, size: int) -> "Tuple[int, int]":
	#	height = int(size * 1.5)
	#	return height, height

	# returns: (minimum: int, natural: int, minimum_baseline: int, natural_baseline: int)
	#def do_measure(self, orientation, for_size):
	#	return (for_size, for_size, for_size, for_size)




class AboutWidget(gtk.Box):
	def __init__(
		self,
		logo: str = "",
		header: str = "",
		about: str = "",
		authors: str = "",
		license: str = "",
		**kwargs,
	):
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		##
		headerBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if logo:
			pack(headerBox, imageFromFile(logo))
		headerLabel = gtk.Label(label=header)
		headerLabel.set_selectable(True)
		pack(headerBox, headerLabel, padding=15)
		headerBox.show()
		pack(self, headerBox)
		##
		notebook = gtk.Notebook()
		self.notebook = notebook
		pack(self, notebook, padding=5, expand=True)
		notebook.set_tab_pos(gtk.PositionType.LEFT)
		##
		tab1_about = self.newTabLabelWidget(about)
		tab2_authors = self.newTabWidgetTextView(authors)
		tab3_license = self.newTabWidgetTextView(license)
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

	# <a href="...">Somethig</a> does not work with TextView
	def newTabWidgetTextView(
		self,
		text: str,
		wrap: bool = False,
		justification: "Optional[gtk.Justification]" = None,
	):
		tv = gtk.TextView()
		if wrap:
			tv.set_wrap_mode(gtk.WrapMode.WORD)
		if justification is not None:
			tv.set_justification(justification)
		tv.set_cursor_visible(False)
		#tv.set_border_width(10)
		buf = tv.get_buffer()
		# buf.insert_markup(buf.get_end_iter(), markup=text, len=len(text.encode("utf-8")))
		buf.set_text(text)
		tv.show()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		#swin.set_border_width(0)
		swin.set_child(tv)
		return swin

	def newTabLabelWidget(
		self,
		text: str,
		wrap: bool = False,
		justification: "Optional[gtk.Justification]" = None,
	):
		box = VBox()
		#box.set_border_width(10)
		label = gtk.Label()
		label.set_selectable(True)
		label.set_xalign(0)
		label.set_yalign(0)
		pack(box, label, 0, 0)
		#if wrap:
		#	tv.set_wrap_mode(gtk.WrapMode.WORD)
		#if justification is not None:
		#	tv.set_justification(justification)
		# label.set_cursor_visible(False)
		# label.set_border_width(10)
		label.set_markup(text)
		label.show()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		#swin.set_border_width(0)
		swin.set_child(box)
		return swin

	def newTabTitle(self, title: str, icon: str):
		return AboutTabTitleBox(title, icon)

