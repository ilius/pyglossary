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

import typing

__all__ = ["KeyData", "RawKeyData"]

RawKeyData: typing.TypeAlias = "tuple[int, int, typing.Sequence[str]]"
"""tuple(priority, parentalControl, keyTextFields)"""


"""
KeyText.data contains:
1. morphological data (opens article "make" when user enters "making")
and data that shows

2. data that encodes that searching "2 per cent", "2 percent",
or "2%" returns the same article
EXAMPLE: <d:index d:value="made" d:title="made (make)"/>
If the entry for "make" contains these <d:index> definitions,
the entry can be searched not only by "make" but also by "makes" or "made".
On the search result list, title value texts like "made" are displayed.
EXAMPLE: <d:index d:value="make it" d:title="make it" d:parental-control="1"
d:anchor="xpointer(//*[@id='make_it'])"/>
EXAMPLE: <d:index d:value="工夫する" d:title="工夫する"
d:yomi="くふうする" d:anchor="xpointer(//*[@id='kufuu-suru'])" />
EXAMPLE: <d:index d:value="'s finest" d:title="—'s finest"
d:DCSEntryTitle="fine" d:anchor="xpointer(//*[@id='m_en_gbus0362750.070'])"/>
	user entered "'s finest", search list we show "—'s finest",
show article with title "fine" and point to element id = 'm_en_gbus0362750.070'
"""


# TODO: switch to dataclass
class KeyData:

	"""
	Dictionary entries are opened by entering different search texts.
	This class contains texts by which entry is searchable and other properties.
	"""

	# keyword_data_id_xml = {
	# 	"DCSKeyword": "d:value",
	# 	# Search key -- if entered in search, this key will provide this definition.
	# 	"DCSHeadword": "d:title",
	# 	# Headword text that is displayed on the search result list.
	# 	# When the value is the same as d:value, it can be omitted.
	# 	# In that case, the value of the d:value is used also for the d:title.
	# 	"DCSAnchor": "d:anchor",
	# 	# Used to highlight a specific part in an entry.
	# 	# For example, it is used to highlight an idiomatic phrase explanation
	# 	# in an entry for a word.
	# 	"DCSYomiWord": "d:yomi",
	# 	# Used only in making Japanese dictionaries.
	# 	"DCSSortKey": "d:DCSSortKey",
	# 	# This value shows sorting (probably for non-english languages)
	# 	"DCSEntryTitle": "d:DCSEntryTitle",
	# 	# Headword displayed as article title
	# }

	__slots__ = [
		"anchor",
		"entryTitle",
		"headword",
		"keyword",
		"parentalControl",
		"priority",
	]

	def __init__(  # noqa: PLR0913
		self,
		priority: int,
		parentalControl: int,
		keyword: str,
		headword: str,
		entryTitle: str,
		anchor: str,
	) -> None:
		self.priority = priority
		self.parentalControl = parentalControl
		self.keyword = keyword
		self.headword = headword
		self.entryTitle = entryTitle
		self.anchor = anchor

	def toDict(self) -> dict[str, typing.Any]:
		return {
			"priority": self.priority,
			"parentalControl": self.parentalControl,
			"keyword": self.keyword,
			"headword": self.headword,
			"entryTitle": self.entryTitle,
			"anchor": self.anchor,
		}

	@staticmethod
	def fromRaw(rawKeyData: RawKeyData, keyTextFieldOrder: list[str]) -> KeyData:
		priority, parentalControl, keyTextFields = rawKeyData
		keyword = ""
		headword = ""
		entryTitle = ""
		anchor = ""

		for i, key_value in enumerate(keyTextFields):
			key_type = keyTextFieldOrder[i]
			if key_type == "DCSKeyword":
				keyword = key_value
			elif key_type == "DCSHeadword":
				headword = key_value
			elif key_type == "DCSEntryTitle":
				entryTitle = key_value
			elif key_type == "DCSAnchor":
				anchor = key_value

		return KeyData(
			priority,
			parentalControl,
			keyword,
			headword,
			entryTitle,
			anchor,
		)
