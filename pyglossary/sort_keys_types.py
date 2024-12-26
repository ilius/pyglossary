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
		**kwargs,  # noqa: ANN003
	) -> SortKeyType: ...


class SQLiteSortKeyMakerType(Protocol):
	def __call__(
		self,
		sortEncoding: str = "utf-8",
		**kwargs,  # noqa: ANN003
	) -> SQLiteSortKeyType: ...


class LocaleSortKeyMakerType(Protocol):
	def __call__(
		self,
		collator: T_Collator,  # noqa: F821
	) -> SortKeyMakerType: ...


class LocaleSQLiteSortKeyMakerType(Protocol):
	def __call__(
		self,
		collator: T_Collator,  # noqa: F821
	) -> SQLiteSortKeyMakerType: ...


__all__ = [
	"LocaleSQLiteSortKeyMakerType",
	"LocaleSortKeyMakerType",
	"SQLiteSortKeyMakerType",
	"SQLiteSortKeyType",
	"SortKeyMakerType",
	"SortKeyType",
]
