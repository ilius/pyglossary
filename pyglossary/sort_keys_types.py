"""
Protocol types for glossary sort-key factory functions.

Defines ``SortKeyMakerType``, ``SQLiteSortKeyMakerType``, and locale-aware
variants that return callables producing sort keys from headword lists. Shared
between ``sort_keys`` and ``sort_modules`` implementations.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
	from .icu_types import T_Collator

type SortKeyType = Callable[
	[list[str]],
	Any,
]

type SQLiteSortKeyType = list[tuple[str, str, SortKeyType]]


class SortKeyMakerType(Protocol):
	"""Sort Key Maker Type."""

	def __call__(
		self,
		sortEncoding: str = "utf-8",
		**kwargs: Any,
	) -> SortKeyType: ...


class SQLiteSortKeyMakerType(Protocol):
	"""SQ Lite Sort Key Maker Type."""

	def __call__(
		self,
		sortEncoding: str = "utf-8",
		**kwargs: Any,
	) -> SQLiteSortKeyType: ...


class LocaleSortKeyMakerType(Protocol):
	"""Locale Sort Key Maker Type."""

	def __call__(
		self,
		collator: T_Collator,  # noqa: F821
	) -> SortKeyMakerType: ...


class LocaleSQLiteSortKeyMakerType(Protocol):
	"""Locale SQ Lite Sort Key Maker Type."""

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
