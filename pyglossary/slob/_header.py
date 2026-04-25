# Slob file header parsing (pyglossary)
from __future__ import annotations

import encodings
from collections.abc import Sequence
from types import MappingProxyType
from uuid import UUID

from ._compressions import COMPRESSIONS
from ._constants import MAGIC, U_CHAR, UTF8
from ._exceptions import UnknownCompression, UnknownEncoding, UnknownFileFormat
from ._multifile import MultiFileReader
from ._struct import StructReader, read_byte_string
from ._types import Header


def read_header(file: MultiFileReader) -> Header:
	file.seek(0)

	magic = file.read(len(MAGIC))
	if magic != MAGIC:
		raise UnknownFileFormat(f"magic {magic!r} != {MAGIC!r}")

	uuid = UUID(bytes=file.read(16))
	encoding = read_byte_string(file, U_CHAR).decode(UTF8)
	if encodings.search_function(encoding) is None:
		raise UnknownEncoding(encoding)

	reader = StructReader(file, encoding)
	compression = reader.read_tiny_text()
	if compression not in COMPRESSIONS:
		raise UnknownCompression(compression)

	def read_tags() -> dict[str, str]:
		count = reader.read_byte()
		return {reader.read_tiny_text(): reader.read_tiny_text() for _ in range(count)}

	tags = read_tags()

	def read_content_types() -> Sequence[str]:
		content_types: list[str] = []
		count = reader.read_byte()
		for _ in range(count):
			content_type = reader.read_text()
			content_types.append(content_type)
		return tuple(content_types)

	content_types = read_content_types()

	blob_count = reader.read_int()
	store_offset = reader.read_long()
	size = reader.read_long()
	refs_offset = reader.tell()

	return Header(
		magic=magic,
		uuid=uuid,
		encoding=encoding,
		compression=compression,
		tags=MappingProxyType(tags),
		content_types=content_types,
		blob_count=blob_count,
		store_offset=store_offset,
		refs_offset=refs_offset,
		size=size,
	)
