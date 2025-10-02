from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.icu_types import T_Collator
	from pyglossary.sort_keys_types import (
		SortKeyMakerType,
		SortKeyType,
		SQLiteSortKeyType,
	)


desc = "Random"


def normal(**_options: Any) -> SortKeyType:
	from random import random

	return lambda _words: random()


def locale(
	collator: T_Collator,  # noqa: ARG001  # noqa: F821
) -> SortKeyMakerType:
	from random import random

	def sortKey(words: list[str]) -> Any:  # noqa: ARG001
		return random()

	def warpper(
		sortEncoding: str = "utf-8",  # noqa: ARG001
		**_options: Any,
	) -> SortKeyType:
		return sortKey

	return warpper


def sqlite(**_options: Any) -> SQLiteSortKeyType:
	from random import random

	return [
		(
			"random",
			"REAL",
			lambda _words: random(),
		),
	]


def sqlite_locale(
	_collator: T_Collator,  # noqa: F821
	**_options: Any,
) -> Callable[..., SQLiteSortKeyType]:
	from random import random

	return lambda **_opt: [
		(
			"random",
			"REAL",
			lambda _words: random(),
		),
	]
