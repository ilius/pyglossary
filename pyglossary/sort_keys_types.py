from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

if TYPE_CHECKING:
	from pyglossary.icu_types import T_Collator

SortKeyType: TypeAlias = Callable[
	[list[str]],
	Any,
]

SQLiteSortKeyType: TypeAlias = list[tuple[str, str, SortKeyType]]


class SortKeyMakerType(Protocol):
	def __call__(
		self,
		sortEncoding: str = "utf-8",
		**kwargs
	) -> SortKeyType: ...


class SQLiteSortKeyMakerType(Protocol):
	def __call__(
		self,
		sortEncoding: str = "utf-8",
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
