# slob named record types (pyglossary)
from __future__ import annotations

from collections.abc import Sequence
from types import MappingProxyType
from typing import NamedTuple
from uuid import UUID


class Ref(NamedTuple):
	key: str
	bin_index: int
	item_index: int
	fragment: str


class Header(NamedTuple):
	magic: bytes
	uuid: UUID
	encoding: str
	compression: str
	tags: MappingProxyType[str, str]
	content_types: Sequence[str]
	blob_count: int
	store_offset: int
	refs_offset: int
	size: int
