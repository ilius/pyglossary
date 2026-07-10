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
"""Compatibility re-exports: the glossary implementation lives in glossary_v3."""

from __future__ import annotations

from .glossary_v3 import (
	ConvertArgs,
	Error,
	ReadError,
	WriteError,
)
from .glossary_v3 import (
	Glossary as GlossaryV3,
)

__all__ = [
	"ConvertArgs",
	"Error",
	"Glossary",
	"ReadError",
	"WriteError",
]


class Glossary(GlossaryV3):
	def getInfo(self, key: str) -> str:
		return self.info[key]

	def setInfo(self, key: str, value: object) -> None:
		self.info[key] = value

	def getExtraInfos(self, excludeKeys: list[str]) -> dict[str, str]:
		return self.info.getExtraInfos(excludeKeys)
