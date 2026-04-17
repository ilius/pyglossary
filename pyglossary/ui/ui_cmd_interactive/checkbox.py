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

"""Minimal checkbox widget for boolean prompts."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from prompt_toolkit.formatted_text import StyleAndTextTuples

__all__ = ["MiniCheckBoxPrompt"]


class MiniCheckBoxPrompt:
	"""prompt_toolkit-compatible widget: styled label plus ``[x]`` or ``[ ]``."""

	def __init__(
		self,
		formatted: StyleAndTextTuples,
		value: bool = False,
	) -> None:
		"""``formatted`` is the label; ``value`` is the initial checked state."""
		self.formatted = formatted
		self.value = value

	def __pt_formatted_text__(self) -> StyleAndTextTuples:  # noqa: PLW3201
		"""Return label plus checkbox suffix for prompt_toolkit rendering."""
		return self.formatted + [("", "[x]" if self.value else "[ ]")]
