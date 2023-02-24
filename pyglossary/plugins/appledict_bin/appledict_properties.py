# -*- coding: utf-8 -*-
from typing import Dict, List

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

class AppleDictProperties:
	def __init__(
		self,
		format_version: int,
		body_compression_type: int,
		body_has_sections: bool,
		key_text_compression_type: int,
		key_text_field_order: List[str],
	):
		# in plist file: "IDXDictionaryVersion"
		# values := (1 | 2 | 3)
		self.format_version = format_version

		# in plist file: "HeapDataCompressionType" values := (absent | 1 | 2)
		self.body_compression_type = body_compression_type
		# in plist file: for field with "IDXDataFieldName" equal "DCSExternalBodyID"
		# "IDXDataSize" value = 4 or 8
		self.body_has_sections = body_has_sections

		# in plist file: "IDXIndexDataFields" / "IDXVariableDataFields"
		# Example: ["DCSKeyword", "DCSHeadword", "DCSEntryTitle", "DCSAnchor", "DCSYomiWord"]
		self.key_text_field_order = key_text_field_order

		# in plist file for key_text_metadata:
		# 'TrieAuxiliaryDataOptions' -> 'HeapDataCompressionType'
		self.key_text_compression_type = key_text_compression_type


def from_metadata(metadata: Dict) -> AppleDictProperties:
	format_version = metadata.get("IDXDictionaryVersion")
	key_text_metadata = metadata.get('IDXDictionaryIndexes')[0]
	body_metadata = metadata.get('IDXDictionaryIndexes')[2]

	key_text_data_fields = key_text_metadata.get('IDXIndexDataFields')
	key_text_field_order = [field_data['IDXDataFieldName'] for field_data in
							key_text_data_fields.get('IDXVariableDataFields')]

	external_data_fields = key_text_data_fields.get("IDXExternalDataFields")
	body_has_sections = external_data_fields[0].get("IDXDataSize") == 8
	if 'HeapDataCompressionType' in body_metadata:
		body_compression_type = body_metadata['HeapDataCompressionType']
	else:
		body_compression_type = 0

	if 'TrieAuxiliaryDataOptions' in key_text_metadata and 'HeapDataCompressionType' in \
			key_text_metadata['TrieAuxiliaryDataOptions']:
		key_text_compression_type = \
			key_text_metadata['TrieAuxiliaryDataOptions']['HeapDataCompressionType']
	else:
		key_text_compression_type = 0

	return AppleDictProperties(
		format_version=format_version,
		body_compression_type=body_compression_type,
		body_has_sections=body_has_sections,
		key_text_compression_type=key_text_compression_type,
		key_text_field_order=key_text_field_order,
	)
