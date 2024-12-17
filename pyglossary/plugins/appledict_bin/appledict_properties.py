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

from dataclasses import dataclass
from typing import Any

__all__ = ["AppleDictProperties", "from_metadata"]


@dataclass(slots=True, frozen=True)
class AppleDictProperties:
	# in plist file: IDXDictionaryVersion
	# values := (1 | 2 | 3)
	format_version: int

	# in plist file: HeapDataCompressionType values := (absent | 1 | 2)
	body_compression_type: int

	# in plist file: for field with "IDXDataFieldName" equal "DCSExternalBodyID"
	# "IDXDataSize" value = 4 or 8
	body_has_sections: bool

	# in plist file for key_text_metadata:
	# 'TrieAuxiliaryDataOptions' -> 'HeapDataCompressionType'
	key_text_compression_type: int

	# in plist file: IDXIndexDataFields / "IDXFixedDataFields"
	# Example: ["DCSPrivateFlag"]
	key_text_fixed_fields: list[str]

	# in plist file: IDXIndexDataFields / "IDXVariableDataFields"
	# Example: ["DCSKeyword", "DCSHeadword", "DCSEntryTitle",
	# "DCSAnchor", "DCSYomiWord"]
	key_text_variable_fields: list[str]

	# DCSDictionaryCSS, generally "DefaultStyle.css"
	css_name: str | None


def from_metadata(metadata: dict[str, Any]) -> AppleDictProperties:
	format_version: int = metadata.get("IDXDictionaryVersion", -1)
	dictionaryIndexes: list[dict[str, Any]] | None = metadata.get(
		"IDXDictionaryIndexes",
	)
	key_text_metadata: dict[str, Any] = (
		dictionaryIndexes[0] if dictionaryIndexes else {}
	)
	body_metadata: dict[str, Any] = dictionaryIndexes[2] if dictionaryIndexes else {}

	key_text_data_fields = key_text_metadata.get("IDXIndexDataFields", {})
	key_text_variable_fields = [
		field_data["IDXDataFieldName"]
		for field_data in key_text_data_fields.get("IDXVariableDataFields", [])
	]
	key_text_fixed_field = [
		fixed_field["IDXDataFieldName"]
		for fixed_field in key_text_data_fields.get("IDXFixedDataFields", [])
	]

	external_data_fields = key_text_data_fields.get("IDXExternalDataFields")
	body_compression_type = body_metadata.get("HeapDataCompressionType", 0)
	body_has_sections = (
		body_compression_type == 2 and external_data_fields[0].get("IDXDataSize") == 8
	)

	if (
		"TrieAuxiliaryDataOptions" in key_text_metadata
		and "HeapDataCompressionType" in key_text_metadata["TrieAuxiliaryDataOptions"]
	):
		key_text_compression_type = key_text_metadata["TrieAuxiliaryDataOptions"][
			"HeapDataCompressionType"
		]
	else:
		key_text_compression_type = 0

	css_name = metadata.get("DCSDictionaryCSS")

	return AppleDictProperties(
		format_version=format_version,
		body_compression_type=body_compression_type,
		body_has_sections=body_has_sections,
		key_text_compression_type=key_text_compression_type,
		key_text_fixed_fields=key_text_fixed_field,
		key_text_variable_fields=key_text_variable_fields,
		css_name=css_name,
	)
