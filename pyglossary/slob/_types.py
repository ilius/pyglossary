# slob named record types (pyglossary)
"""
Named tuple types for SLOB header and reference records.

Defines ``Header`` and ``Ref`` structures shared by the SLOB reader and writer
modules.
"""

from __future__ import annotations

from collections.abc import Sequence
from types import MappingProxyType
from typing import NamedTuple
from uuid import UUID

__all__ = ["Header", "Ref"]


class Ref(NamedTuple):
	"""Ref."""

	key: str
	bin_index: int
	item_index: int
	fragment: str


class Header(NamedTuple):
	"""Header."""

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
