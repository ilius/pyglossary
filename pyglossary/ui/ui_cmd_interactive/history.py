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

"""Input history helpers for path prompts."""

from __future__ import annotations

from os.path import abspath, relpath
from typing import TYPE_CHECKING

from prompt_toolkit.history import FileHistory

if TYPE_CHECKING:
	from collections.abc import Iterable

__all__ = ["AbsolutePathHistory"]


class AbsolutePathHistory(FileHistory):
	"""File-backed input history that stores absolute paths but displays relative ones."""

	def load_history_strings(self) -> Iterable[str]:
		"""Return history entries as paths relative to the current working directory."""
		# pwd = os.getcwd()
		pathList = FileHistory.load_history_strings(self)
		return [relpath(p) for p in pathList]

	def store_string(self, string: str) -> None:
		"""Persist ``string`` as an absolute path so history stays valid across ``cd``."""
		FileHistory.store_string(self, abspath(string))
