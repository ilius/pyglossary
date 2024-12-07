# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
	TYPE_CHECKING,
	Any,
)

if TYPE_CHECKING:
	from collections.abc import Iterator

__all__ = ["MemSdList"]


class MemSdList:
	def __init__(self) -> None:
		self._l: list[Any] = []

	def append(self, x: Any) -> None:
		self._l.append(x)

	def __len__(self) -> int:
		return len(self._l)

	def __iter__(self) -> Iterator[Any]:
		return iter(self._l)

	def sortKey(self, item: tuple[bytes, Any]) -> tuple[bytes, bytes]:  # noqa: PLR6301
		return (
			item[0].lower(),
			item[0],
		)

	def sort(self) -> None:
		self._l.sort(key=self.sortKey)
