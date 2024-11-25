# -*- coding: utf-8 -*-

# Copyright © 2023 soshial <soshial@gmail.com> (soshial)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from __future__ import annotations

from typing import NamedTuple

__all__ = ["ArticleAddress"]


class ArticleAddress(NamedTuple):
	sectionOffset: int
	chunkOffset: int

	def __str__(self) -> str:
		return f"Addr[{self.sectionOffset:#x}, {self.chunkOffset:#x}]"
