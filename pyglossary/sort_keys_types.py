from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

SortKeyType: TypeAlias = Callable[
	[list[str]],
	Any,
]

SQLiteSortKeyType: TypeAlias = list[tuple[str, str, SortKeyType]]

__all__ = [
	"SQLiteSortKeyType",
	"SortKeyType",
]
