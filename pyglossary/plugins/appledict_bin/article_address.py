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

class ArticleAddress:
	def __init__(self, sectionOffset: int, chunkOffset: int):
		self.sectionOffset = sectionOffset
		self.chunkOffset = chunkOffset

	def __str__(self):
		return f"Addr[{hex(self.sectionOffset)}, {hex(self.chunkOffset)}]"

	def __lt__(self, other):
		if self.sectionOffset == other.sectionOffset:
			return self.chunkOffset < other.chunkOffset
		return self.sectionOffset < other.sectionOffset

	def __eq__(self, other) -> bool:
		if self.sectionOffset != other.sectionOffset:
			return False
		if self.chunkOffset != other.chunkOffset:
			return False
		return True

	def __hash__(self):
		return 31 * hash(self.sectionOffset) + self.chunkOffset
