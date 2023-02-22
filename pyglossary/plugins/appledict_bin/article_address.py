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
	def __init__(self, section_offset: int, chunk_offset: int):
		self.section_offset = section_offset
		self.chunk_offset = chunk_offset

	def __str__(self):
		return f"Addr[{hex(self.section_offset)}, {hex(self.chunk_offset)}]"

	def __lt__(self, other):
		if self.section_offset == other.section_offset:
			return self.chunk_offset < other.chunk_offset
		return self.section_offset < other.section_offset

	def __eq__(self, other) -> bool:
		if self.section_offset != other.section_offset:
			return False
		if self.chunk_offset != other.chunk_offset:
			return False
		return True

	def __hash__(self):
		return 31 * hash(self.section_offset) + self.chunk_offset
