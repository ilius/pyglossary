from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeAlias

from pyglossary.icu_types import T_Collator

SortKeyType: TypeAlias = Callable[
	[list[str]],
	Any,
]


RawSortKeyType: TypeAlias = Callable[
	[bytes],
	Any,
]

SQLiteSortKeyType: TypeAlias = list[tuple[str, str, SortKeyType]]


class SortKeyMakerType(Protocol):
	def __call__(
		self,
		sortEncoding: str,
		**kwargs
	) -> RawSortKeyType: ...


class SQLiteSortKeyMakerType(Protocol):
	def __call__(
		self,
		sortEncoding: str,
		**kwargs
	) -> SQLiteSortKeyType: ...



class LocaleSortKeyMakerType(Protocol):
	def __call__(
		self,
		collator: T_Collator,  # noqa: F821
	) -> SortKeyMakerType: ...


class SQLiteLocaleSortKeyMakerType(Protocol):
	def __call__(
		self,
		collator: T_Collator,  # noqa: F821
	) -> SQLiteSortKeyType: ...



__all__ = [
	"LocaleSortKeyMakerType",
	"SQLiteSortKeyType",
	"SortKeyMakerType",
	"SortKeyType",
]
