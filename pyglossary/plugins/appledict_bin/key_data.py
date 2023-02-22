# -*- coding: utf-8 -*-
from typing import TypeAlias

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

RawKeyData: TypeAlias = tuple[int, int, list[str]]
"""tuple(priority, parental_control, key_text_fields)"""


class KeyData:
	"""
	Dictionary entries are opened by entering different search texts.
	This class contains texts by which entry is searchable and other properties.
	"""

	def __init__(
			self,
			priority: int,
			parental_control: int,
			keyword: str,
			headword: str,
			entry_title: str,
			anchor: str,
	):
		self.priority = priority
		self.parental_control = parental_control
		self.keyword = keyword
		self.headword = headword
		self.entry_title = entry_title
		self.anchor = anchor

	@staticmethod
	def from_raw_key_data(raw_key_data: RawKeyData, key_text_field_order: list[str]):
		priority, parental_control, key_text_fields = raw_key_data
		keyword = ''
		headword = ''
		entry_title = ''
		anchor = ''

		for i, key_value in enumerate(key_text_fields):
			key_type = key_text_field_order[i]
			if key_type == 'DCSKeyword':
				keyword = key_value
			elif key_type == 'DCSHeadword':
				headword = key_value
			elif key_type == 'DCSEntryTitle':
				entry_title = key_value
			elif key_type == 'DCSAnchor':
				anchor = key_value

		return KeyData(
			priority,
			parental_control,
			keyword,
			headword,
			entry_title,
			anchor,
		)

	def to_xml_string(self) -> str:
		d_index_xml = '<d:index xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng" '  # noqa: E501
		if self.priority != 0:
			d_index_xml += f' d:priority="{self.priority}"'
		if self.parental_control != 0:
			d_index_xml += f' d:parental-control="{self.parental_control}"'
		if self.keyword:
			d_index_xml += f' d:value="{self.keyword}"'
		if self.headword:
			d_index_xml += f' d:title="{self.headword}"'
		if self.anchor:
			d_index_xml += f' d:anchor="{self.anchor}"'
		d_index_xml += ' />'
		return d_index_xml

	keyword_data_id_xml = {
		'DCSKeyword': 'd:value',
		# Search key -- if entered in search, this key will provide this definition.

		'DCSHeadword': 'd:title',
		# Headword text that is displayed on the search result list.
		# When the value is the same to the d:index value, it can be omitted.
		# In that case, the value of the d:value is used also for the d:title.

		'DCSAnchor': 'd:anchor',
		# Used to highlight a specific part in an entry.
		# For example, it is used to highlight an idiomatic phrase explanation
		# in an entry for a word.

		'DCSYomiWord': 'd:yomi',
		# Used only in making Japanese dictionaries.

		'DCSSortKey': 'd:DCSSortKey',
		# This value shows sorting (probably for non-english languages)

		'DCSEntryTitle': 'd:DCSEntryTitle',
		# Headword displayed as article title
	}
