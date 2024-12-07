# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
	TYPE_CHECKING,
	Any,
	Protocol,
	TypeVar,
)

if TYPE_CHECKING:
	from collections.abc import Iterator


T_SDListItem_contra = TypeVar("T_SDListItem_contra", contravariant=True)


class T_SdList(Protocol[T_SDListItem_contra]):
	def append(self, x: T_SDListItem_contra) -> None: ...

	def __len__(self) -> int: ...

	def __iter__(self) -> Iterator[Any]: ...

	def sort(self) -> None: ...
