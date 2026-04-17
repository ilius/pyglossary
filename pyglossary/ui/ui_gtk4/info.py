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

from typing import Any

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

from .utils import HBox, pack

__all__ = ["PreConvertInfoDialog"]


class PreConvertInfoDialog(gtk.Dialog):
	"""Set glossary name and language metadata before conversion (see ui_tk.info)."""

	def __init__(self, main_win: gtk.Window, info: dict[str, str], **kwargs: Any) -> None:
		gtk.Dialog.__init__(self, transient_for=main_win, **kwargs)
		self.set_title("Set Info / Metadata")
		self._info = info
		##
		self.add_action_widget(
			gtk.Button(label="_Cancel", use_underline=True),
			gtk.ResponseType.CANCEL,
		)
		self.add_action_widget(
			gtk.Button(label="_OK", use_underline=True),
			gtk.ResponseType.OK,
		)
		self.connect("response", self._on_response)
		##
		ckey = gtk.EventControllerKey()
		ckey.connect("key-pressed", self._on_key_pressed)
		self.add_controller(ckey)
		##
		vbox = self.get_content_area()
		vbox.set_spacing(8)
		vbox.set_margin_top(12)
		vbox.set_margin_bottom(12)
		vbox.set_margin_start(12)
		vbox.set_margin_end(12)
		##
		self._name_entry = gtk.Entry()
		self._name_entry.set_text(info.get("name", ""))
		row = HBox(spacing=8)
		pack(row, gtk.Label(label="Glossary Name", xalign=0))
		pack(row, self._name_entry, expand=True)
		pack(vbox, row)
		##
		self._source_lang_entry = gtk.Entry()
		self._source_lang_entry.set_text(info.get("sourceLang", ""))
		row = HBox(spacing=8)
		pack(row, gtk.Label(label="Source Language", xalign=0))
		pack(row, self._source_lang_entry, expand=True)
		pack(vbox, row)
		##
		self._target_lang_entry = gtk.Entry()
		self._target_lang_entry.set_text(info.get("targetLang", ""))
		row = HBox(spacing=8)
		pack(row, gtk.Label(label="Target Language", xalign=0))
		pack(row, self._target_lang_entry, expand=True)
		pack(vbox, row)
		##
		self.set_default_size(480, -1)
		vbox.show()

	def _on_key_pressed(
		self,
		_ckey: gtk.EventControllerKey,
		keyval: int,
		_keycode: int,
		_state: gdk.ModifierType,
	) -> bool:
		if keyval == gdk.KEY_Escape:
			self.response(gtk.ResponseType.CANCEL)
			return True
		return False

	def _apply(self) -> None:
		name = self._name_entry.get_text()
		if name:
			self._info["name"] = name
		source_lang = self._source_lang_entry.get_text()
		if source_lang:
			self._info["sourceLang"] = source_lang
		target_lang = self._target_lang_entry.get_text()
		if target_lang:
			self._info["targetLang"] = target_lang

	def _on_response(self, _widget: gtk.Widget, response_id: int) -> None:
		if response_id == gtk.ResponseType.OK:
			self._apply()
		self.destroy()
