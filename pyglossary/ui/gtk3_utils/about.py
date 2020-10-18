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
			headerBox.pack_start(imageFromFile(logo), False, False, 0)
		headerLabel = gtk.Label(label=header)
		headerLabel.set_selectable(True)
		headerBox.pack_start(headerLabel, False, False, 15)
		headerBox.show_all()
		self.pack_start(headerBox, False, False, 0)
		##
		notebook = gtk.Notebook()
		self.notebook = notebook
		self.pack_start(notebook, True, True, 5)
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
		self.show_all()

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
		tv.set_border_width(10)
		buf = tv.get_buffer()
		# buf.insert_markup(buf.get_end_iter(), markup=text, len=len(text.encode("utf-8")))
		buf.set_text(text)
		tv.show_all()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.set_border_width(0)
		swin.add(tv)
		return swin

	def newTabLabelWidget(
		self,
		text: str,
		wrap: bool = False,
		justification: "Optional[gtk.Justification]" = None,
	):
		box = VBox()
		box.set_border_width(10)
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
		label.show_all()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.set_border_width(0)
		swin.add(box)
		return swin

	def newTabTitle(self, title: str, icon: str):
		box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		if icon:
			box.pack_start(imageFromFile(icon), False, False, 5)
		if title:
			box.pack_start(gtk.Label(label=title), False, False, 5)
		box.show_all()
		return box

