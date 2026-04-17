# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from prompt_toolkit.completion import Completion, PathCompleter

if TYPE_CHECKING:
	from collections.abc import Iterable

	from prompt_toolkit.completion import CompleteEvent
	from prompt_toolkit.document import Document

__all__ = ["MyPathCompleter"]


class MyPathCompleter(PathCompleter):
	def __init__(
		self,
		reading: bool,  # noqa: ARG002
		fs_action_names: list[str] | None = None,
		**kwargs: Any,
	) -> None:
		PathCompleter.__init__(
			self,
			file_filter=self.file_filter,
			**kwargs,
		)
		self.fs_action_names = fs_action_names or []

	@staticmethod
	def file_filter(_filename: str) -> bool:
		# filename is full/absolute file path
		return True

	# def get_completions_exception(document, complete_event, e):
	# 	log.error(f"Exception in get_completions: {e}")

	def get_completions(
		self,
		document: Document,
		complete_event: CompleteEvent,
	) -> Iterable[Completion]:
		text = document.text_before_cursor

		for action in self.fs_action_names:
			if action.startswith(text):
				yield Completion(
					text=action,
					start_position=-len(text),
					display=action,
				)

		yield from PathCompleter.get_completions(
			self,
			document=document,
			complete_event=complete_event,
		)
